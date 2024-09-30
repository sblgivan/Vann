from flask import Flask, render_template
import threading
import asyncio
import os
from deriv_api import DerivAPI
from deriv_api import APIError
import talib
import numpy as np

app_id = 64037
api_token = os.getenv('DERIV_TOKEN', 'pfm6nudgLi4aNys')

if len(api_token) == 0:
    sys.exit("DERIV_TOKEN environment variable is not set")

async def get_candles(api, symbol, interval=60, count=1000):
    candles = await api.ticks_history({
        "ticks_history": symbol,
        "adjust_start_time": 1,
        "count": count,
        "end": "latest",
        "start": 1,
        "style": "candles",
        "granularity": interval
    })
    return candles['candles']

async def analyze_market(api, symbol):
    candles = await get_candles(api, symbol)
    
    # Extract OHLC data
    close = np.array([float(candle['close']) for candle in candles])
    high = np.array([float(candle['high']) for candle in candles])
    low = np.array([float(candle['low']) for candle in candles])
    
    # Get indicators
    ma = talib.SMA(close, timeperiod=20)
    upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    fractals_high = talib.FRACTALSHIGHEST(high, timeperiod=5)
    fractals_low = talib.FRACTALSLOWEST(low, timeperiod=5)
    
    # Analyze candle 3 and 2
    candle3 = candles[-3]
    candle2 = candles[-2]
    
    def analyze_candle(candle):
        total_range = float(candle['high']) - float(candle['low'])
        body = abs(float(candle['open']) - float(candle['close']))
        if float(candle['open']) < float(candle['close']):  # Bullish candle
            upper_wick = float(candle['high']) - float(candle['close'])
            lower_wick = float(candle['open']) - float(candle['low'])
        else:  # Bearish candle
            upper_wick = float(candle['high']) - float(candle['open'])
            lower_wick = float(candle['close']) - float(candle['low'])
        
        return {
            'body_percent': (body / total_range) * 100,
            'upper_wick_percent': (upper_wick / total_range) * 100,
            'lower_wick_percent': (lower_wick / total_range) * 100
        }
    
    candle3_analysis = analyze_candle(candle3)
    candle2_analysis = analyze_candle(candle2)
    
    # Determine if elfigue is bullish or bearish
    elfigue = 'bullish' if float(candle2['close']) > float(candle3['close']) else 'bearish'
    
    # Get support and resistance
    support = min(low[-10:])
    resistance = max(high[-10:])
    
    return {
        'elfigue': elfigue,
        'support': support,
        'resistance': resistance,
        'ma': ma[-1],
        'bbands': (upper[-1], middle[-1], lower[-1]),
        'fractals_high': fractals_high[-1],
        'fractals_low': fractals_low[-1],
        'candle3': candle3_analysis,
        'candle2': candle2_analysis
    }

async def execute_trade(api, symbol, analysis, balance):
    # Define conditions for buy
    buy_condition1 = analysis['elfigue'] == 'bullish'
    buy_condition2 = close[-1] > analysis['ma']
    buy_condition3 = close[-1] < analysis['bbands'][0]  # Price below upper Bollinger Band
    
    # Define conditions for sell
    sell_condition1 = analysis['elfigue'] == 'bearish'
    sell_condition2 = close[-1] < analysis['ma']
    sell_condition3 = close[-1] > analysis['bbands'][2]  # Price above lower Bollinger Band
    
    # Risk management
    risk_percent = 0.02  # Risk 2% of balance per trade
    stop_loss_pips = 50
    take_profit_pips = 100
    
    if buy_condition1 and buy_condition2 and buy_condition3:
        # Execute buy order
        amount = balance * risk_percent
        response = await api.buy({
            "buy": 1,
            "parameters": {
                "amount": amount,
                "basis": "stake",
                "contract_type": "CALL",
                "currency": "USD",
                "duration": 5,
                "duration_unit": "m",
                "symbol": symbol
            }
        })
        print("Buy order executed:", response)
        
    elif sell_condition1 and sell_condition2 and sell_condition3:
        # Execute sell order
        amount = balance * risk_percent
        response = await api.buy({
            "buy": 1,
            "parameters": {
                "amount": amount,
                "basis": "stake",
                "contract_type": "PUT",
                "currency": "USD",
                "duration": 5,
                "duration_unit": "m",
                "symbol": symbol
            }
        })
        print("Sell order executed:", response)
    
    # Monitor trade
    while True:
        profit_loss = await api.profit_table({"contract_type": ["CALL", "PUT"], "date_from": "today", "sort": "DESC"})
        if profit_loss['profit_table']:
            latest_trade = profit_loss['profit_table'][0]
            if latest_trade['is_completed']:
                print(f"Trade result: {'Win' if float(latest_trade['profit']) > 0 else 'Loss'}")
                print(f"Profit/Loss: {latest_trade['profit']}")
                break
        await asyncio.sleep(1)

async def run_bot():
    api = DerivAPI(app_id=app_id)
    
    # Authorize
    authorize = await api.authorize(api_token)
    print("Authorized:", authorize)
    
    # Get Balance
    balance_info = await api.balance()
    balance = float(balance_info['balance']['balance'])
    currency = balance_info['balance']['currency']
    print(f"Current balance: {currency} {balance}")
    
    symbol = "R_100"  # Example symbol, replace with your preferred asset
    
    while True:
        try:
            analysis = await analyze_market(api, symbol)
            print("Market analysis:", analysis)
            
            await execute_trade(api, symbol, analysis, balance)
            
            # Wait for the current candle to close
            await asyncio.sleep(60)  # Wait for 1 minute
        except APIError as e:
            print(f"API Error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(run_bot())

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint for bot status
@app.route('/toggle_bot', methods=['POST'])
def toggle_bot():
    # Logic to start or stop the bot
    return "Bot toggled!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Run the bot asynchronously in the background
    asyncio.run(run_bot())  # This runs your trading bot
