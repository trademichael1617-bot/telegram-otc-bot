import os
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003540658518")
  # replace with your channel ID

app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram OTC Bot is running ✅"

@app.route("/health")
def health():
    return "OK", 200

# ======================
# TELEGRAM HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ OTC Graded Bot is ACTIVE\nUse /signal to test.")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "📊 OTC SIGNAL\n\n"
        "Pair: EURUSD OTC\n"
        "Direction: BUY 📈\n"
        "Grade: A+\n"
        "Confidence: HIGH\n"
    )
    await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
    await update.message.reply_text("✅ Signal sent to channel")

# ======================
# START TELEGRAM BOT
# ======================
async def start_bot():
    print("Starting Telegram bot...")
    app_tg = ApplicationBuilder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("signal", signal))
    print("Telegram bot initialized. Polling now...")
    await app_tg.run_polling()
    print("🤖 Telegram bot started")

# ======================
# RUN BOT + FLASK
# ======================
if __name__ == "__main__":
    # Run bot in asyncio loop
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())

    # Run Flask server
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
