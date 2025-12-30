import os
import time
import threading
import asyncio
from datetime import datetime, timedelta, timezone

import pandas as pd
import pandas_ta as ta
from flask import Flask
from telegram import Bot

# API Specific Libraries
import yfinance as yf
import twelvedata
from alpha_vantage.timeseries import TimeSeries

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Keys for Failover
TD_KEY = os.getenv("TWELVE_DATA_KEY")
AV_KEY = os.getenv("ALPHA_VANTAGE_KEY")

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY"]
LOW_TF = "1min"   # Twelve Data and Alpha Vantage use '1min'
HIGH_TF = "5min" 

RSI_PERIOD = 5
RSI_UPPER = 90
RSI_LOWER = 10
BB_PERIOD = 20
BB_STD = 2

COOLDOWN_MINUTES = 5
MAX_LOSSES = 2
LOSS_PAUSE_MINUTES = 30
OTC_SESSIONS = [(0, 6), (12, 16)]

# Initialize Clients
bot = Bot(token=TELEGRAM_TOKEN)
td_client = twelvedata.TDClient(apikey=TD_KEY) if TD_KEY else None
av_client = TimeSeries(key=AV_KEY, output_format='pandas') if AV_KEY else None
app = Flask(__name__)

# =========================
# DATA ENGINE (FAILOVER)
# =========================
def fetch_candles(symbol, tf):
    """Tries Multiple APIs in order: Twelve Data -> Alpha Vantage -> Yahoo Finance"""
    
    # --- 1. TWELVE DATA ---
    if td_client:
        try:
            ts = td_client.time_series(symbol=symbol, interval=tf, outputsize=50).as_pandas()
            if not ts.empty:
                df = ts.rename(columns={'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'})
                return df.sort_index()
        except Exception as e:
            print(f"TwelveData Fail for {symbol}: {e}")

    # --- 2. ALPHA VANTAGE ---
    if av_client:
        try:
            av_symbol = symbol.replace("/", "")
            # AV uses different interval strings
            av_tf = '1min' if '1' in tf else '5min'
            data, _ = av_client.get_intraday(symbol=av_symbol, interval=av_tf, outputsize='compact')
            df = data.copy()
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            return df.sort_index()
        except Exception as e:
            print(f"AlphaVantage Fail for {symbol}: {e}")

    # --- 3. YAHOO FINANCE (Unlimited Backup) ---
    try:
        yf_symbol = symbol.replace("/", "") + "=X"
        yf_tf = '1m' if '1' in tf else '5m'
        df = yf.download(yf_symbol, period="1d", interval=yf_tf, progress=False)
        if not df.empty:
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns] # Fix multi-index
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'})
            return df.sort_index()
    except Exception as e:
        print(f"YahooFinance Fail for {symbol}: {e}")

    return None

# =========================
# HELPERS & ANALYSIS
# =========================
def utc_now():
    return datetime.now(timezone.utc)

def in_otc_session():
    hour = utc_now().hour
    return any(start <= hour < end for start, end in OTC_SESSIONS)

def send(msg):
    async def _send():
        async with bot:
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    try: asyncio.run(_send())
    except Exception as e: print(f"Telegram Error: {e}")

def analyze(df):
    if df is None or len(df) < BB_PERIOD: return None
    
    df["rsi"] = ta.rsi(df["close"], length=RSI_PERIOD)
    bb = ta.bbands(df["close"], length=BB_PERIOD, std=BB_STD)
    df = pd.concat([df, bb], axis=1)

    latest = df.iloc[-1]
    l_col = [c for c in bb.columns if "BBL" in c][0]
    u_col = [c for c in bb.columns if "BBU" in c][0]

    bb_width = (latest[u_col] - latest[l_col]) / latest["close"]
    if bb_width > 0.01: return None  

    if latest["rsi"] >= RSI_UPPER: return "SELL"
    if latest["rsi"] <= RSI_LOWER: return "BUY"
    return None

def multi_tf_confirm(pair):
    low_df = fetch_candles(pair, LOW_TF)
    high_df = fetch_candles(pair, HIGH_TF)
    
    sig_low = analyze(low_df)
    sig_high = analyze(high_df)
    
    return sig_low if sig_low and sig_low == sig_high else None

# =========================
# STATE & LOOPS
# =========================
cooldown_until = utc_now()
loss_pause_until = utc_now()
open_trade = None
loss_count = 0

def signal_loop():
    global cooldown_until, open_trade, loss_count, loss_pause_until
    while True:
        try:
            now = utc_now()
            if now < cooldown_until or now < loss_pause_until or open_trade or not in_otc_session():
                time.sleep(30); continue

            for pair in PAIRS:
                signal = multi_tf_confirm(pair)
                if signal:
                    df = fetch_candles(pair, LOW_TF)
                    price = round(df.iloc[-1]["close"], 5)
                    send(f"🚨 *STRATEGY SIGNAL*\n\n*Pair:* {pair}\n*Dir:* {signal}\n*Price:* {price}")
                    open_trade = {"pair": pair, "direction": signal}
                    cooldown_until = now + timedelta(minutes=COOLDOWN_MINUTES)
                    break
            time.sleep(20)
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
        loss_pause_until = utc_now() + timedelta(minutes=LOSS_PAUSE_MINUTES)
        send("⛔ *PAUSED: MAX LOSS REACHED*")
    open_trade = None
    return "OK"

@app.route("/")
def home(): return "Multi-API Bot Active"

if __name__ == "__main__":
    threading.Thread(target=signal_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
