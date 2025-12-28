import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder

# 1. Setup Flask for Render
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is alive!", 200

# 2. Your Telegram Logic
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003540658518"))

async def send_signals(app):
    await asyncio.sleep(15)
    print("📢 Signal loop started")
    while True:
        try:
            await app.bot.send_message(
                chat_id=CHANNEL_ID,
                text="📊 *OTC SIGNAL*\n\n*Pair:* EURUSD OTC\n*Direction:* BUY 📈",
                parse_mode="Markdown"
            )
            print("✅ Signal sent")
        except Exception as e:
            print("❌ Telegram error:", e)
        await asyncio.sleep(60)

async def run_bot():
    # We use stop_signals=None so it doesn't crash in a background thread
    app = ApplicationBuilder().token(TOKEN).build()
    await app.initialize()
    await app.start()
    app.create_task(send_signals(app))
    
    print("🤖 Telegram bot polling started")
    await app.run_polling(stop_signals=None)

def start_bot_thread():
    asyncio.run(run_bot())

if __name__ == "__main__":
    # Start the bot in the background
    threading.Thread(target=start_bot_thread, daemon=True).start()
    
    # Start Flask on the main thread (Render needs this)
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)
