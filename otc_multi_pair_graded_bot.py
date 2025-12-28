import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# CONFIG (USE ENV VARS)
# ======================
TOKEN = "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ"
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003540658518"))


if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

# ======================
# FLASK APP (RENDER NEEDS THIS)
# ======================
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
    print("📢 Signal loop started")

    while True:
        try:
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text="📊 *OTC SIGNAL*\n\n*Pair:* EURUSD OTC\n*Direction:* BUY 📈",
                parse_mode="Markdown"
            )
            print("✅ Signal sent")
        except Exception as e:
            print("❌ Telegram error:", e)

        await asyncio.sleep(60)

async def start_bot():
    application = ApplicationBuilder().token(TOKEN).build()

    # schedule background task
    application.create_task(send_signals(application))

    print("🤖 Telegram bot polling started")
    await application.run_polling()

def run_bot():
    asyncio.run(start_bot())

# ======================
# MAIN ENTRY
# ======================
if __name__ == "__main__":
    print("🚀 Starting Flask + Telegram bot")

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
