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
    await asyncio.sleep(10)
    while True:
        try:
            msg = "📊 *OTC SIGNAL*\n\n*Pair:* EURUSD OTC\n*Direction:* BUY 📈"
            await application.bot.send_message(
                chat_id=CHANNEL_ID, 
                text=msg, 
                parse_mode="Markdown"
            )
            print("Successfully sent signal")
        except Exception as e:
            print(f"Telegram error: {e}")
        await asyncio.sleep(60)

async def start_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    application.create_task(send_signals(application))
    await application.initialize()
    await application.start_polling()
    while True:
        await asyncio.sleep(1)

def run_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

# ======================
# MAIN START
# ======================
if __name__ == "__main__":
    # Start bot in background
    t = threading.Thread(target=run_bot_thread, daemon=True)
    t.start()
    
    # Run Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
