import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# CONFIG
# ======================
TOKEN = os.getenv(
    "BOT_TOKEN",
    "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ"
)

CHANNEL_ID = os.getenv(
    "CHANNEL_ID",
    "-1003540658518"
)

# ======================
# FLASK APP (RENDER KEEP-ALIVE)
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
async def send_signals(tg_app):
    while True:
        try:
            message = (
                "📊 OTC SIGNAL\n\n"
                "Pair: EURUSD OTC\n"
                "Direction: BUY 📈\n"
                "Grade: A+\n"
                "Confidence: HIGH\n"
            )

            await tg_app.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message
            )

            print("✅ Signal sent to Telegram")

        except Exception as e:
            print("❌ Telegram error:", e)

        await asyncio.sleep(60)  # send every 60 seconds

# ======================
# TELEGRAM BOT STARTER
# ======================
async def start_telegram_bot():
    print("🤖 Starting Telegram bot...")

    tg_app = ApplicationBuilder().token(TOKEN).build()

    # start background signal task
    asyncio.create_task(send_signals(tg_app))

    await tg_app.run_polling()

# ======================
# RUN BOT IN SEPARATE THREAD (RENDER FIX)
# ======================
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_telegram_bot())

# ======================
# MAIN ENTRY
# ======================
if __name__ == "__main__":
    print("🚀 Launching Flask + Telegram bot")

    bot_thread = threading.Thread(
        target=run_bot,
        daemon=True
    )
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
