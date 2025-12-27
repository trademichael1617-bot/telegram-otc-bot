import os
import asyncio
import threading
# from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# CONFIG
# ======================

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
# TELEGRAM LOOP
# ======================
async def send_signals(application):
    await asyncio.sleep(5)
    while True:
        await application.bot.send_message(
            chat_id=CHANNEL_ID,
            text="📊 OTC SIGNAL\nPair: EURUSD OTC\nDirection: BUY 📈"
        )
        print("✅ Signal sent")
        await asyncio.sleep(60)

async def start_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    application.create_task(send_signals(application))
    await application.run_polling()

def run_bot():
    asyncio.run(start_bot())

# ======================
# MAIN ENTRY (NO INDENT ERRORS)
# ======================
if __name__ == "__main__":
    print("🚀 Starting Flask + Telegram bot")

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


import os
import asyncio
from telegram.ext import ApplicationBuilder

CHANNEL_ID = -1003540658518
async def test_message():
    app_tg = ApplicationBuilder().token(TOKEN).build()
    await app_tg.initialize()
    await app_tg.start()
    
    await app_tg.bot.send_message(
        chat_id=CHANNEL_ID,
        text="✅ Test message from bot is working!"
    )
    
    await app_tg.stop()  # Stop bot after sending

asyncio.run(test_message())



    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
