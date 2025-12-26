import os
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003540658518")
  # replace with your channel ID

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

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

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=message
    )

    await update.message.reply_text("✅ Signal sent to channel")

# ======================
# TELEGRAM BOT THREAD
# ======================
def start_telegram_bot():
    app_tg = ApplicationBuilder().token(TOKEN).build()

    # add command handlers
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("signal", signal))

    logging.info("🤖 Telegram bot started")
    app_tg.run_polling()

# ======================
# MAIN
# ======================
if __name__ == "__main__":
    # Start Telegram bot in a background thread
    threading.Thread(target=start_telegram_bot).start()

    # Start Flask server (Render PORT)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)





