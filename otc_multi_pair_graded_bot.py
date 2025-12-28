import os
import asyncio
import threading
from datetime import datetime, timedelta
import requests
import pandas as pd
from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003540658518"))

TWELVE_DATA_API = os.getenv("0da718e36a9c4f48a2541dc00d209f62")
PAIR = "EUR/USD"
TIMEFRAME = "10s"  # OTC short-term
RSI_PERIOD = 5
BB_PERIOD = 20
BB_STD = 2
MAX_LOSSES = 2
COOLDOWN_MIN = 15

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
# GLOBALS
# ======================
last_trade = {"direction": None, "entry": None, "time": None}
stats = {"wins": 0, "losses": 0, "streak": 0}
cooldown_until = datetime.utcnow() - timedelta(minutes=1)

# ======================
# UTILITIES
# ======================
def fetch_candles():
    """Fetch latest candles from Twelve Data OTC API"""
    url = f"https://api.twelvedata.com/time_series?symbol={PAIR}&interval={TIMEFRAME}&apikey={TWELVE_DATA_API}&outputsize=10"
    resp = requests.get(url).json()
    return resp.get("values", [])

def calculate_indicators(candles):
    df = pd.DataFrame(candles)
    df['close'] = df['close'].astype(float)
    df['rsi'] = df['close'].diff().apply(lambda x: max(x,0)).rolling(RSI_PERIOD).mean()  # simple RSI
    df['bb_upper'] = df['close'].rolling(BB_PERIOD).mean() + BB_STD * df['close'].rolling(BB_PERIOD).std()
    df['bb_lower'] = df['close'].rolling(BB_PERIOD).mean() - BB_STD * df['close'].rolling(BB_PERIOD).std()
    return df

def check_consolidation(df):
    """Return True if market is consolidating"""
    return (df['close'].max() - df['close'].min()) < 0.001  # small range

def session_allowed():
    """OTC sessions only"""
    h = datetime.utcnow().hour
    return (0 <= h <= 6) or (7 <= h <= 11) or (13 <= h <= 16)

def grade_signal(df, direction):
    """Return signal grade"""
    volatility = df['close'].std()
    if volatility < 0.0005:
        return "A"
    elif volatility < 0.001:
        return "B"
    else:
        return "C"

# ======================
# TELEGRAM LOGIC
# ======================
async def send_signal(app, direction, grade):
    global last_trade, cooldown_until
    if datetime.utcnow() < cooldown_until:
        print("⏱ Cooldown active, skipping signal")
        return
    msg = f"📊 OTC SIGNAL\n*Pair:* {PAIR}\n*Direction:* {direction}\n*Grade:* {grade}"
    await app.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")
    last_trade["direction"] = direction
    last_trade["entry"] = float(fetch_candles()[0]["close"])
    last_trade["time"] = datetime.utcnow()
    print(f"✅ Signal sent: {direction} | Grade {grade}")

async def signal_loop(app):
    while True:
        if not session_allowed():
            await asyncio.sleep(60)
            continue

        candles = fetch_candles()
        if not candles:
            await asyncio.sleep(10)
            continue

        df = calculate_indicators(candles)
        if check_consolidation(df):
            last_price = df['close'].iloc[-1]
            rsi = df['rsi'].iloc[-1]
            bb_upper = df['bb_upper'].iloc[-1]
            bb_lower = df['bb_lower'].iloc[-1]

            # BUY/SELL logic
            if last_price < bb_lower:
                grade = grade_signal(df, "BUY")
                await send_signal(app, "BUY", grade)
            elif last_price > bb_upper:
                grade = grade_signal(df, "SELL")
                await send_signal(app, "SELL", grade)

        await asyncio.sleep(10)  # 10s timeframe

# ======================
# AUTO RESULT TRACKING
# ======================
async def check_trade_result(app):
    global last_trade, stats, cooldown_until
    while True:
        if last_trade["entry"]:
            candles = fetch_candles()
            if not candles:
                await asyncio.sleep(10)
                continue
            current_price = float(candles[0]["close"])
            direction = last_trade["direction"]
            entry = last_trade["entry"]

            profit = (current_price - entry) if direction == "BUY" else (entry - current_price)
            if profit > 0:
                stats["wins"] += 1
                stats["streak"] = 0
            else:
                stats["losses"] += 1
                stats["streak"] += 1
                if stats["streak"] >= MAX_LOSSES:
                    cooldown_until = datetime.utcnow() + timedelta(minutes=COOLDOWN_MIN)
                    await app.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=f"⚠️ Max losses reached. Cooling down for {COOLDOWN_MIN} mins."
                    )
            last_trade.update({"direction": None, "entry": None, "time": None})
        await asyncio.sleep(60)

# ======================
# BOT START
# ======================
async def start_bot():
    app_tg = ApplicationBuilder().token(TOKEN).build()
    await app_tg.initialize()
    await app_tg.start()
    asyncio.create_task(signal_loop(app_tg))
    asyncio.create_task(check_trade_result(app_tg))
    print("🤖 Bot running...")
    while True:
        await asyncio.sleep(3600)

def run_bot_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

# ======================
# MAIN ENTRY
# ======================
if __name__ == "__main__":
    print("🚀 Launching Flask + Telegram bot")
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
