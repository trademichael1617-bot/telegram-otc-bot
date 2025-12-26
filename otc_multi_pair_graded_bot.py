import os
import threading
import logging
from flask import Flask

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ======================
# BASIC CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003540658518")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ======================
# FLASK APP (KEEP RENDER ALIVE)
# ======================
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram OTC Bot is running ✅"

# ======================
# TELEGRAM COMMANDS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ OTC Graded Bot is ACTIVE\nUse /signal to test."
    )

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
# START TELEGRAM BOT
# ======================
def start_telegram_bot():
    app_tg = ApplicationBuilder().token(TOKEN).build()

    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("signal", signal))

    logging.info("🤖 Telegram bot started")
    app_tg.run_polling()

# ======================
# MAIN ENTRY
# ======================
if __name__ == "__main__":
    # Start Telegram bot in background thread
    threading.Thread(target=start_telegram_bot).start()

    # Start Flask server
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)





# ================= KEEP ALIVE =================
from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "OTC Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask).start()
# ==============================================

import asyncio
import yfinance as yf
from datetime import datetime, time
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# ---------------- SETTINGS ----------------
TOKEN = "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ"
CHANNEL_ID = -1003540658518

PAIRS = {
    "EURUSD OTC": "EURUSD=X",
    "GBPUSD OTC": "GBPUSD=X",
    "USDJPY OTC": "JPY=X",
    "AUDUSD OTC": "AUDUSD=X",
}

TIMEFRAME = "1m"

RSI_PERIOD = 5
RSI_UPPER = 90
RSI_LOWER = 10

BB_PERIOD = 20
BB_TIGHT = 0.0012
BB_NORMAL = 0.0018

MAX_SIGNALS = 5
MAX_WINS = 3
MAX_LOSSES = 2

SESSIONS = [
    (time(8, 0), time(11, 0)),
    (time(13, 0), time(16, 0)),
]
# -----------------------------------------

signals_sent = 0
wins = 0
losses = 0
last_reset_date = datetime.now().date()
pending = None

def in_session():
    now = datetime.now().time()
    return any(start <= now <= end for start, end in SESSIONS)

def daily_reset():
    global signals_sent, wins, losses, last_reset_date
    today = datetime.now().date()
    if today != last_reset_date:
        signals_sent = wins = losses = 0
        last_reset_date = today

def grade_signal(rsi, band_width, price, upper, lower):
    score = 0

    if rsi <= 8 or rsi >= 92:
        score += 2
    elif rsi <= 10 or rsi >= 90:
        score += 1

    if price <= lower or price >= upper:
        score += 2
    elif abs(price - lower) < abs(upper - price):
        score += 1

    if band_width < BB_TIGHT:
        score += 2
    elif band_width < BB_NORMAL:
        score += 1

    if score >= 5:
        return "A+"
    elif score >= 3:
        return "B"
    else:
        return "C"

def analyze_pair(symbol):
    data = yf.download(symbol, period="1d", interval=TIMEFRAME, progress=False)
    if data.empty:
        return None

    close = data["Close"]
    rsi_series = RSIIndicator(close, RSI_PERIOD).rsi()
    bb = BollingerBands(close, window=BB_PERIOD)

    price = close.iloc[-1]
    rsi = rsi_series.iloc[-1]
    upper = bb.bollinger_hband().iloc[-1]
    lower = bb.bollinger_lband().iloc[-1]

    band_width = (upper - lower) / price

    consolidating = band_width < BB_NORMAL and lower < price < upper

    if not consolidating:
        return None

    signal = None
    if price <= lower and rsi <= RSI_LOWER:
        signal = "📈 CALL"
    elif price >= upper and rsi >= RSI_UPPER:
        signal = "📉 PUT"

    if not signal:
        return None

    grade = grade_signal(rsi, band_width, price, upper, lower)
    return signal, grade

async def check_market(context: ContextTypes.DEFAULT_TYPE):
    global pending
    daily_reset()

    if not in_session() or pending:
        return

    if signals_sent >= MAX_SIGNALS or wins >= MAX_WINS or losses >= MAX_LOSSES:
        return

    for name, symbol in PAIRS.items():
        result = analyze_pair(symbol)
        if result:
            signal, grade = result
            if grade == "C":
                return

            pending = (name, signal, grade)

            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"""⚠️ SETUP DETECTED ({grade})

PAIR: {name}
SIGNAL: {signal}

Reply YES to confirm
Reply NO to ignore
"""
            )
            break

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pending, signals_sent, wins, losses
    text = update.message.text.upper()

    if text == "YES" and pending:
        pair, signal, grade = pending
        signals_sent += 1
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"""✅ CONFIRMED SIGNAL ({grade})

PAIR: {pair}
TYPE: {signal}
TIMEFRAME: 15s
EXPIRY: 1 candle
"""
        )
        pending = None

    elif text == "NO":
        pending = None
        await context.bot.send_message(chat_id=CHANNEL_ID, text="❌ SIGNAL SKIPPED")

    elif text == "WIN":
        wins += 1
    elif text == "LOSS":
        losses += 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 OTC Bot Running")

def main():
    app_tg = ApplicationBuilder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply))
    app_tg.job_queue.run_repeating(check_market, interval=60, first=10)
    print("Graded OTC bot running...")
    app_tg.run_polling()

if __name__ == "__main__":
    main()
