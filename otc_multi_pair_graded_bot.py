import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# CONFIG
# ======================
TOKEN = os.environ.get("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1003540658518")

# ======================
# FLASK APP
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
    while True:
        await app_tg.bot.send_message(
            chat_id=CHANNEL_ID,
            text="✅ TEST MESSAGE FROM BOT"
        )
        print("Signal sent")
        await asyncio.sleep(60)

# ======================
# TELEGRAM BOT STARTER
# ======================
async def start_bot():
    print("🤖 Starting Telegram bot...")
    app_tg = ApplicationBuilder().token(TOKEN).build()
    asyncio.create_task(send_signals(app_tg))
    await app_tg.run_polling()

# ======================
# RUN BOT IN THREAD
# ======================
def run_bot():
    asyncio.run(start_bot())

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
