import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# CONFIG
# ======================
# Use a default, but always try to pull from Render Environment Variables first
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003540658518")

# ======================
# FLASK APP (KEEP-ALIVE)
# ======================
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram OTC Bot is running ✅"

@app.route("/health")
def health():
    return "OK", 200

# ======================
# TELEGRAM SIGNAL LOOP
# ======================
async def send_signals(app_tg):
    # Ensure the bot is ready before sending
    await asyncio.sleep(5) 
    while True:
        try:
            await app_tg.bot.send_message(
                chat_id=CHANNEL_ID,
                text="📊 OTC SIGNAL\n\nPair: EURUSD OTC\nDirection: BUY 📈\nGrade: A+\nConfidence: HIGH"
            )
            print("✅ Signal sent to Telegram")
        except Exception as e:
            print(f"❌ Telegram error: {e}")
        
        await asyncio.sleep(60)  # send every 60 seconds

# ======================
# TELEGRAM BOT STARTER
# ======================
async def start_telegram_bot():
    print("🤖 Initializing Telegram bot...")
    # Build the application
    app_tg = ApplicationBuilder().token(TOKEN).build()
    
    # 1. Initialize the application (Required in v21+)
    await app_tg.initialize()
    # 2. Start the bot
    await app_tg.start()
    # 3. Start the polling mechanism
    await app_tg.updater.start_polling()
    
    print("🚀 Bot is now polling.")
    
    # Run the signal loop as a background task
    asyncio.create_task(send_signals(app_tg))
    
    # Keep the async loop alive indefinitely
    while True:
        await asyncio.sleep(3600)

# ======================
# RUN BOT IN THREAD
# ======================
def run_bot():
    # Explicitly create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_telegram_bot())

# ======================
# MAIN ENTRY
# ======================
if __name__ == "__main__":
    print("🚀 Launching Flask + Telegram bot")
    
    # Start the Telegram thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask (Render uses the PORT env var)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)import os
