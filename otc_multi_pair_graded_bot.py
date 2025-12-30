import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask
from twelvedata import TDClient
import threading

# --- 1. CONFIGURATION ---
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
TD_API_KEY = "YOUR_TWELVE_DATA_API_KEY"

# We check these pairs (Keeping it small saves API credits)
SYMBOLS = ["EUR/USD", "GBP/USD", "USD/JPY"]

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Pocket Option Strategy Bot is Running!", 200

# --- 2. TELEGRAM FUNCTION ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

# --- 3. THE STRATEGY (RSI + BB) ---
def analyze_markets():
    td = TDClient(apikey=TD_API_KEY)
    
    for symbol in SYMBOLS:
        try:
            # Fetch 1-minute candles
            ts = td.time_series(symbol=symbol, interval="1min", outputsize=40).as_pandas()
            
            # Indicators
            bb = ta.bbands(ts['close'], length=20, std=2)
            rsi = ta.rsi(ts['close'], length=14)
            
            curr_price = ts['close'].iloc[-1]
            lower_b = bb['BBL_20_2.0'].iloc[-1]
            upper_b = bb['BBU_20_2.0'].iloc[-1]
            curr_rsi = rsi.iloc[-1]

            # Logic for signals
            if curr_price <= lower_b and curr_rsi <= 30:
                grade = "GRADE A" if curr_rsi <= 25 else "GRADE B"
                msg = f"🟢 *{grade} CALL SIGNAL*\nAsset: {symbol}\nPrice: {curr_price}\nRSI: {curr_rsi:.2f}"
                send_telegram(msg)

            elif curr_price >= upper_b and curr_rsi >= 70:
                grade = "GRADE A" if curr_rsi >= 75 else "GRADE B"
                msg = f"🔴 *{grade} PUT SIGNAL*\nAsset: {symbol}\nPrice: {curr_price}\nRSI: {curr_rsi:.2f}"
                send_telegram(msg)

        except Exception as e:
            print(f"Error on {symbol}: {e}")

# --- 4. THE LOOP ---
def run_bot():
    while True:
        analyze_markets()
        # Sleep 5 mins (300s) to keep Twelve Data Free Credits safe
        time.sleep(300)

if __name__ == "__main__":
    # Start bot in background, Flask in foreground
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
