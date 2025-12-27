import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# CONFIG
# ======================
# Hardcoded token for now as per your snippet
TOKEN = "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ"
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003540658518"))

# ======================
# FLASK APP (RENDER NEEDS THIS)
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
async def send_signals(application):
    """Background task to send signals every 60 seconds."""
    await asyncio.sleep(5)  # Let the bot initialize first
    while True:
        try:
            # Using Markdown for a cleaner look
            message = (
                "📊 *NEW OTC SIGNAL*\n\n"
                "*Pair:* EURUSD OTC\n"
                "*Direction:* BUY 📈\n"
                "*Grade:* A+\n"
                "*Confidence:* HIGH"
            )
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode="Markdown"
            )
            print("✅ Signal sent successfully")
        except Exception as e:
            print(f"❌ Error sending signal: {e}")
        
        await asyncio.sleep(60)

async def start_bot():
    """Builds and runs the Telegram bot."""
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Schedule the signal task inside the Telegram loop
    application.create_task(send_signals(application))
    
    # Initialize and start polling
    await application.initialize()
    await application.start_polling()
    
    # Keep the async loop alive
    while True:
        await asyncio.sleep(1)

def run_bot_in_thread():
    """Runs the asyncio event loop in a background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

# ======================
# MAIN ENTRY
# ======================
if __name__ == "__main__":
    print("🚀 Launching Flask server and Telegram bot thread...")

    # Start the bot in a background thread so Flask can run on the main thread
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()

    # Get the port from Render's environment, default to 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
