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
    # Wait for the bot to be fully connected before starting
    await asyncio.sleep(10)
    print("📢 Signal loop started...")
    
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
            print(f"❌ Telegram error: {e}")
        
        await asyncio.sleep(60)

async def start_bot():
    """Initializes and runs the bot."""
    # Build the application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Initialize the bot properly
    await application.initialize()
    await application.start()
    
    # Start the signal task explicitly
    asyncio.create_task(send_signals(application))
    
    # Start polling updates (replaces the broken start_polling)
    # Using updater.start_polling since we are in a custom loop
    await application.updater.start_polling()
    
    print("🤖 Bot is now polling...")
    
    # Keep the loop running forever
    while True:
        await asyncio.sleep(3600)

def run_bot_thread():
    """Sets up the event loop for the background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_bot())
    except Exception as e:
        print(f"🔥 Bot Thread Crash: {e}")

# ======================
# MAIN START
# ======================
if __name__ == "__main__":
    print("🚀 Launching Flask server and Telegram bot thread...")

    # Start bot in background
    t = threading.Thread(target=run_bot_thread, daemon=True)
    t.start()
    
    # Run Flask (Render will bind to this)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
