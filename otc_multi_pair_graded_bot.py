import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder


# ======================
# CONFIG
# ======================
TOKEN = "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ"
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003540658518"))


app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is active ✅"


@app.route("/health")
def health():
    return "OK", 200


# ======================
# TELEGRAM LOGIC
# ======================
async def send_signals(application):
    """Loop to send messages every 60 seconds."""
    await asyncio.sleep(10) # Wait for bot to connect
    print("📢 Signal loop starting...")
    while True:
        try:
            msg = "📊 *OTC SIGNAL*\n\n*Pair:* EURUSD OTC\n*Direction:* BUY 📈"
            await application.bot.send_message(
                chat_id=CHANNEL_ID, 
                text=msg, 
                parse_mode="Markdown"
            )
            print("✅ Signal sent")
        except Exception as e:
            print(f"❌ Signal Error: {e}")
        await asyncio.sleep(60)


async def start_bot():
    """Custom startup for v20+ in a thread."""
    # 1. Build the app
    application = ApplicationBuilder().token(TOKEN).build()
    
    # 2. Initialize and start the bot engine
    await application.initialize()
    await application.start()
    
    # 3. Start the internal updater (this replaces start_polling)
    if application.updater:
        await application.updater.start_polling()
    
    # 4. Start your custom signal task
    asyncio.create_task(send_signals(application))
    print("🤖 Bot is initialized and polling...")


    # Keep the async loop alive
    while True:
        await asyncio.sleep(3600)


def run_bot_in_thread():
    """Creates a new event loop for the thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())


# ======================
# MAIN START
# ======================
if __name__ == "__main__":
    print("🚀 Launching Flask and Bot...")
    
    # Start bot thread
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()
    
    # Run Flask on main thread
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

