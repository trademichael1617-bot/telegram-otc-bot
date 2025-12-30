import os
import time
import threading
from datetime import datetime, timedelta, timezone

import pandas as pd
import pandas_ta as ta
from flask import Flask
from telegram import Bot
from twelvedata import TDClient

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TWELVE_DATA_KEY = os.getenv("TWELVE_DATA_KEY")

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY"]
LOW_TF = "1min"
HIGH_TF = "5min"

RSI_PERIOD = 5
RSI_UPPER = 90
RSI_LOWER = 10

BB_PERIOD = 20
BB_STD = 2

COOLDOWN_MINUTES = 5
MAX_LOSSES = 2
LOSS_PAUSE_MINUTES = 30

NEWS_BLACKOUT_MINUTES = 10

# OTC sessions (UTC)
OTC_SESSIONS = [
    (0, 6),    # Asia
    (12, 16),  # NY OTC overlap
]

# =========================
# HELPERS
# =========================
def utc_now():
    return datetime.now(timezone.utc)

def in_otc_session():
    hour = utc_now().hour
    return any(start <= hour < end for start, end in OTC_SESSIONS)

bot = Bot(token=TELEGRAM_TOKEN)
td = TDClient(apikey=TWELVE_DATA_KEY)
app = Flask(__name__)

# =========================
# STATE
# =========================
cooldown_until = utc_now() - timedelta(minutes=1)
loss_pause_until = utc_now() - timedelta(minutes=1)
open_trade = None
loss_count = 0

# =========================
# DATA
# =========================
def fetch_candles(symbol, tf):
    ts = td.time_series(
        symbol=symbol,
        interval=tf,
        outputsize=100,
        timezone="UTC"
    )
    df = ts.as_pandas().astype(float)
    return df

# =========================
# ANALYSIS
# =========================
def analyze(df):
    df["rsi"] = ta.rsi(df["close"], length=RSI_PERIOD)
    bb = ta.bbands(df["close"], length=BB_PERIOD, std=BB_STD)
    df = pd.concat([df, bb], axis=1)

    latest = df.iloc[-1]

    bb_width = (latest["BBU_20_2.0"] - latest["BBL_20_2.0"]) / latest["close"]
    if bb_width > 0.01:
        return None  # not consolidating

    if latest["rsi"] >= RSI_UPPER:
        return "SELL"
    if latest["rsi"] <= RSI_LOWER:
        return "BUY"

    return None

def multi_tf_confirm(pair):
    low = analyze(fetch_candles(pair, LOW_TF))
    high = analyze(fetch_candles(pair, HIGH_TF))
    return low if low and low == high else None

# =========================
# NEWS BLACKOUT (MANUAL SLOT)
# =========================
def in_news_blackout():
    # Placeholder: block whole hour around major news
    return utc_now().minute >= (60 - NEWS_BLACKOUT_MINUTES)

# =========================
# ALERTS
# =========================
def send(msg):
    bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

# =========================
# MAIN LOOP
# =========================
def signal_loop():
    global cooldown_until, open_trade, loss_count, loss_pause_until

    while True:
        try:
            now = utc_now()

            if now < cooldown_until or now < loss_pause_until:
                time.sleep(10)
                continue

            if not in_otc_session():
                time.sleep(30)
                continue

            if in_news_blackout():
                time.sleep(30)
                continue

            if open_trade:
                time.sleep(10)
                continue

            for pair in PAIRS:
                signal = multi_tf_confirm(pair)
                if not signal:
                    continue

                price = fetch_candles(pair, LOW_TF).iloc[-1]["close"]

                send(
                    f"📊 *OTC ENTRY OPEN*\n\n"
                    f"*Pair:* {pair}\n"
                    f"*Direction:* {signal}\n"
                    f"*Price:* {price}\n"
                    f"*Time:* {now.strftime('%H:%M:%S')} UTC"
                )

                open_trade = {
                    "pair": pair,
                    "direction": signal,
                    "price": price,
                    "time": now
                }

                cooldown_until = now + timedelta(minutes=COOLDOWN_MINUTES)
                break

            time.sleep(10)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

# =========================
# SIMULATED TRADE CLOSE (MANUAL HOOK)
# =========================
@app.route("/trade/<result>")
def trade_result(result):
    global open_trade, loss_count, loss_pause_until

    if not open_trade:
        return "No open trade"

    if result == "loss":
        loss_count += 1
        send("❌ *Trade Closed: LOSS*")
    else:
        loss_count = 0
        send("✅ *Trade Closed: WIN*")

    if loss_count >= MAX_LOSSES:
        loss_pause_until = utc_now() + timedelta(minutes=LOSS_PAUSE_MINUTES)
        send("⛔ *Bot Paused: 2 Losses Hit*")

    open_trade = None
    return "OK"

# =========================
# FLASK
# =========================
@app.route("/")
def home():
    return "OTC Bot Live"

# =========================
# START
# =========================
if __name__ == "__main__":
    threading.Thread(target=signal_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
