from flask import Flask, render_template
import threading
import asyncio
# Import your bot's code here

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
