import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram import Update

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003540658518")

# ======================
# FLASK APP (KEEP-ALIVE)
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
async def send_signals(app_tg: ApplicationBuilder):
    while True:
        try:
            message = (
                "📊 OTC SIGNAL\n\n"
                "Pair: EURUSD OTC\n"
                "Direction: BUY 📈\n"
                "Grade: A+\n"
                "Confidence: HIGH\n"
            )
            await app_tg.bot.send_message(chat_id=CHANNEL_ID, text=message)
            print("✅ Signal sent to Telegram")
        except Exception as e:
            print("❌ Telegram error:", e)
        await asyncio.sleep(60)  # send every 60 seconds

# ======================
# OPTIONAL /start COMMAND
# ======================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is active ✅")

# ======================
# TELEGRAM BOT STARTER
# ======================
async def start_telegram_bot():
    print("🤖 Starting Telegram bot...")
    app_tg = ApplicationBuilder().token(TOKEN).build()

    # Add optional /start command
    app_tg.add_handler(
        app_tg.handler_factory("start", start_command)
    )

    # Start background signal loop
    asyncio.create_task(send_signals(app_tg))

    # Run the bot
    await app_tg.run_polling()

# ======================
# RUN BOT IN THREAD (RENDER FIX)
# ======================
def run_bot():
    asyncio.run(start_telegram_bot())

# ======================
# MAIN ENTRY
# ======================
if __name__ == "__main__":
    print("🚀 Launching Flask + Telegram bot")
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
