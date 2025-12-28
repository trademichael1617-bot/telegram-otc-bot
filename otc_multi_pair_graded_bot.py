import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder

# 1. SETUP FLASK (To keep Render happy)
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is running!", 200

# 2. TELEGRAM CONFIG
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003540658518"))

async def send_signals(app):
    """The loop that sends signals every 60 seconds"""
    await asyncio.sleep(10) # Wait for bot to fully connect
    print("📢 Signal loop started")
    while True:
        try:
            await app.bot.send_message(
                chat_id=CHANNEL_ID,
                text="📊 *OTC SIGNAL*\n\n*Pair:* EURUSD OTC\n*Direction:* BUY 📈",
                parse_mode="Markdown"
            )
            print("✅ Signal sent to Telegram")
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
        await asyncio.sleep(60)

async def run_bot_logic():
    """Initializes and runs the bot without using run_polling()"""
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Manually start the bot components
    await app.initialize()
    await app.start()
    
    # Start your signal task in the background of this loop
    asyncio.create_task(send_signals(app))
    
    # Start polling for updates (non-blocking in this context)
    # We use a custom loop to keep it alive
    print("🤖 Bot is now polling for updates...")
    await app.updater.start_polling()
    
    # Keep the async loop alive forever
    while True:
        await asyncio.sleep(3600)

def start_background_loop():
    """Creates a fresh event loop for the background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot_logic())

if __name__ == "__main__":
    # Start Telegram in a separate thread with its own loop
    print("🚀 Starting background Telegram thread...")
    t = threading.Thread(target=start_background_loop, daemon=True)
    t.start()

    # Start Flask on the main thread
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Flask server starting on port {port}")
    web_app.run(host="0.0.0.0", port=port)
