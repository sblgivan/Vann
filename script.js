const botSwitch = document.getElementById('botSwitch');
const log = document.getElementById('log');
const statusText = document.getElementById('status');

let botIsRunning = false;

botSwitch.addEventListener('change', function() {
    if (this.checked) {
        statusText.textContent = 'Bot is ON';
        botIsRunning = true;
        logBotActivity('Bot started...');
        // Here you can trigger the Python bot function to start executing trades
        startBot();
    } else {
        statusText.textContent = 'Bot is OFF';
        botIsRunning = false;
        logBotActivity('Bot stopped.');
        // The bot will stop executing trades but continue showing visuals
    }
});

function logBotActivity(message) {
    const currentTime = new Date().toLocaleTimeString();
    log.textContent += `[${currentTime}] ${message}\n`;
    log.scrollTop = log.scrollHeight;
}

function startBot() {
    // Example of how the bot continues running in the background
    if (botIsRunning) {
        logBotActivity('Bot is analyzing market...');
        // Mock: Simulating async trading logic
        setTimeout(() => {
            if (botIsRunning) {
                logBotActivity('Trade executed: Buy');
                // Repeat after some interval
                setTimeout(startBot, 5000);
            }
        }, 3000);
    }
}
