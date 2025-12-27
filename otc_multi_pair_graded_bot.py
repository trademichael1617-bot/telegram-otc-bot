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
    """Background loop to send signals."""
    await asyncio.sleep(15)  # Longer wait to ensure bot is ready
    print("📢 Signal loop starting...")
    while True:
        try:
            msg = "📊 *OTC SIGNAL*\n\n*Pair:* EURUSD OTC\n*Direction:* BUY 📈"
            await application.bot.send_message(
                chat_id=CHANNEL_ID, 
                text=msg, 
                parse_mode="Markdown"
            )
            print("✅ Signal sent successfully")
        except Exception as e:
            print(f"❌ Signal Error: {e}")
        await asyncio.sleep(60)

async def start_bot():
    """Simplified startup for v21.6"""
    # 1. Build application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # 2. Schedule the signal loop
    application.create_task(send_signals(application))
    
    # 3. Use the built-in run_polling which handles init/start internally
    # This is safer than manual start() calls in a thread
    print("🤖 Bot is starting polling...")
    await application.run_polling(close_loop=False)

def run_bot_thread():
    """Sets up the event loop for the background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

# ======================
# MAIN START
# ======================
if __name__ == "__main__":
    print("🚀 Launching Flask + Telegram Bot...")

    # Start bot in a single daemon thread
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    # Run Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
