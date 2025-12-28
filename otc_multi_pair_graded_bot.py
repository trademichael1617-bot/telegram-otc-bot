import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ") 
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003540658518"))

if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

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
    """Background loop to send signals."""
    await asyncio.sleep(15) # Wait for bot connection to stabilize
    print("📢 Signal loop started")

    while True:
        try:
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text="📊 *OTC SIGNAL*\n\n*Pair:* EURUSD OTC\n*Direction:* BUY 📈",
                parse_mode="Markdown"
            )
            print("✅ Signal sent")
        except Exception as e:
            print(f"❌ Telegram error: {e}")

        await asyncio.sleep(60)

async def start_bot():
    """Initializes and runs the bot with thread-safe settings."""
    application = ApplicationBuilder().token(TOKEN).build()

    # 1. Initialize the application components
    await application.initialize()
    await application.start()
    
    # 2. Schedule background task
    application.create_task(send_signals(application))

    print("🤖 Telegram bot polling started (Signals Disabled)")
    
    # 3. run_polling with stop_signals=None is required for background threads
    await application.run_polling(stop_signals=None, close_loop=False)

def run_bot_in_thread():
    """Creates a dedicated event loop for the background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_bot())
    except Exception as e:
        print(f"🔥 Bot Thread Error: {e}")

# ======================
# MAIN ENTRY
# ======================
if __name__ == "__main__":
    print("🚀 Starting Flask + Telegram bot")

    # Start bot in background thread
    threading.Thread(target=run_bot_in_thread, daemon=True).start()

    # Start Flask on main thread
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
