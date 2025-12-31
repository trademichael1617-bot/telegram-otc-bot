import os
import time
import threading
import requests
from datetime import datetime, timedelta, timezone

import pandas as pd
import pandas_ta as ta
from flask import Flask

# API Specific Libraries
import yfinance as yf
import twelvedata
from alpha_vantage.timeseries import TimeSeries

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TD_KEY = os.getenv("TWELVE_DATA_KEY")
AV_KEY = os.getenv("ALPHA_VANTAGE_KEY")

PAIRS = ["EUR/USD"]
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
START_HOUR = 10
END_HOUR = 21

td_client = twelvedata.TDClient(apikey=TD_KEY) if TD_KEY else None
av_client = TimeSeries(key=AV_KEY, output_format='pandas') if AV_KEY else None
app = Flask(__name__)

# =========================
# STABLE SEND ENGINE
# =========================
def send(msg):
    """Reliable synchronous message sending."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code != 200:
            print(f"Telegram API Error: {res.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

# =========================
# DATA ENGINE
# =========================
def fetch_candles(symbol, tf):
    if td_client:
        try:
            ts = td_client.time_series(symbol=symbol, interval=tf, outputsize=50).as_pandas()
            if not ts.empty:
                df = ts.rename(columns={'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'})
                return df.sort_index()
        except Exception: pass

    if av_client:
        try:
            av_symbol = symbol.replace("/", "")
            av_tf = '1min' if '1' in tf else '5min'
            data, _ = av_client.get_intraday(symbol=av_symbol, interval=av_tf, outputsize='compact')
            df = data.copy()
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            return df.sort_index()
        except Exception: pass

    try:
        yf_symbol = symbol.replace("/", "") + "=X"
        yf_tf = '1m' if '1' in tf else '5m'
        df = yf.download(yf_symbol, period="1d", interval=yf_tf, progress=False)
        if not df.empty:
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'})
            return df.sort_index()
    except Exception: pass
    return None

# =========================
# ANALYSIS
# =========================
def analyze(df):
    if df is None or len(df) < BB_PERIOD: return None
    df["rsi"] = ta.rsi(df["close"], length=RSI_PERIOD)
    bb = ta.bbands(df["close"], length=BB_PERIOD, std=BB_STD)
    df = pd.concat([df, bb], axis=1)
    
    latest = df.iloc[-1]
    l_col = [c for c in bb.columns if "BBL" in c][0]
    u_col = [c for c in bb.columns if "BBU" in c][0]

    if (latest[u_col] - latest[l_col]) / latest["close"] > 0.01: return None
    if latest["rsi"] >= RSI_UPPER: return "SELL"
    if latest["rsi"] <= RSI_LOWER: return "BUY"
    return None

def multi_tf_confirm(pair):
    low_df = fetch_candles(pair, LOW_TF)
    high_df = fetch_candles(pair, HIGH_TF)
    sig_low = analyze(low_df)
    sig_high = analyze(high_df)
    if sig_low and sig_low == sig_high:
        return sig_low, round(low_df.iloc[-1]["close"], 5)
    return None, None

# =========================
# CORE LOOP
# =========================
cooldown_until = datetime.now(timezone.utc)
loss_pause_until = datetime.now(timezone.utc)
open_trade = None
loss_count = 0

def signal_loop():
    global cooldown_until, open_trade, loss_count, loss_pause_until
    
    # STARTUP MESSAGE
    send("🚀 *Bot Online: EUR/USD Strategy Active*")
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            if not (START_HOUR <= now.hour < END_HOUR):
                time.sleep(300); continue

            if now < cooldown_until or now < loss_pause_until or open_trade:
                time.sleep(30); continue

            signal, price = multi_tf_confirm("EUR/USD")
            if signal:
                send(f"🚨 *SIGNAL FOUND*\n\n*Pair:* EUR/USD\n*Dir:* {signal}\n*Price:* {price}")
                open_trade = {"pair": "EUR/USD", "direction": signal}
                cooldown_until = now + timedelta(minutes=COOLDOWN_MINUTES)
            
            time.sleep(30)
        except Exception as e:
            print(f"Loop Error: {e}"); time.sleep(10)

@app.route("/trade/<result>")
def trade_result(result):
    global open_trade, loss_count, loss_pause_until
    if not open_trade: return "No active trade"
    if result == "loss":
        loss_count += 1
        send("❌ *RESULT: LOSS*")
    else:
        loss_count = 0
        send("✅ *RESULT: WIN*")
    if loss_count >= MAX_LOSSES:
        loss_pause_until = datetime.now(timezone.utc) + timedelta(minutes=LOSS_PAUSE_MINUTES)
        send("⛔ *MAX LOSS REACHED: PAUSED FOR 30 MIN*")
    open_trade = None
    return "OK"

@app.route("/")
def home():
    return "Bot is running."

if __name__ == "__main__":
    threading.Thread(target=signal_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
