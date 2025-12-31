import os
import time
import threading
import requests
from datetime import datetime, timedelta, timezone

import pandas as pd
import pandas_ta as ta
import yfinance as yf
from flask import Flask

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SYMBOL = "EURUSD=X"
START_HOUR, END_HOUR = 9, 21
MIN_ATR = 0.00008  
COOLDOWN_MIN = 5

app = Flask(__name__)

# --- STABLE SEND ENGINE ---
def send_telegram_msg(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Telegram Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

# --- ANALYSIS ENGINE ---
def analyze(df):
    if df is None or len(df) < 30: return None
    df.columns = [str(col).lower() for col in df.columns]
    
    # 1. Volatility Filter
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)
    if df["atr"] is None or df["atr"].iloc[-1] < MIN_ATR: return None

    # 2. Indicators
    df["rsi"] = ta.rsi(df["close"], length=7)
    
    macd_df = ta.macd(df["close"], fast=5, slow=13, signal=8)
    if macd_df is not None:
        df["macd_line"] = macd_df.iloc[:, 0]
        df["macd_signal"] = macd_df.iloc[:, 2]
    
    stoch_df = ta.stoch(df["high"], df["low"], df["close"], k=5, d=3, smooth_k=3)
    if stoch_df is not None:
        df["st_k"] = stoch_df.iloc[:, 0]
        df["st_d"] = stoch_df.iloc[:, 1]

    # 3. Signal Logic
    latest, prev = df.iloc[-1], df.iloc[-2]
    
    buy = (latest["rsi"] > 50 and 
           latest["macd_line"] > latest["macd_signal"] and 
           latest["st_k"] > latest["st_d"] and prev["st_k"] <= prev["st_d"])
           
    sell = (latest["rsi"] < 50 and 
            latest["macd_line"] < latest["macd_signal"] and 
            latest["st_k"] < latest["st_d"] and prev["st_k"] >= prev["st_d"])

    if buy: return "BUY (CALL) 🟢"
    if sell: return "SELL (PUT) 🔴"
    return None

# --- MAIN LOOP ---
def run_bot():
    last_signal_time = datetime.now(timezone.utc) - timedelta(minutes=COOLDOWN_MIN)
    send_telegram_msg(f"🚀 *EUR/USD Bot Started*")
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            if START_HOUR <= now.hour < END_HOUR and now > last_signal_time + timedelta(minutes=COOLDOWN_MIN):
                # Download only EURUSD
                df = yf.download(SYMBOL, period="1d", interval="1m", progress=False)
                
                if not df.empty:
                    sig = analyze(df)
                    if sig:
                        current_price = round(df["Close"].iloc[-1], 5)
                        msg = (f"🎯 *SIGNAL*: {SYMBOL}\n"
                               f"*Action*: {sig}\n"
                               f"*Price*: {current_price}")
                        
                        send_telegram_msg(msg)
                        last_signal_time = now
            
            time.sleep(60) # Check every minute
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

@app.route('/')
def home(): return "EURUSD Bot Active"

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
