import os
import time
import threading
import asyncio
from datetime import datetime, timedelta, timezone

import pandas as pd
import pandas_ta as ta
from flask import Flask
from telegram import Bot
import finnhub

# =========================
# CONFIG
# =========================
# These pull names from your Render Environment tab
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY"]
LOW_TF = "1"  
HIGH_TF = "5" 

RSI_PERIOD = 5
RSI_UPPER = 90
RSI_LOWER = 10

BB_PERIOD = 20
BB_STD = 2

COOLDOWN_MINUTES = 5
MAX_LOSSES = 2
LOSS_PAUSE_MINUTES = 30

OTC_SESSIONS = [(0, 6), (12, 16)]

# =========================
# HELPERS
# =========================
def utc_now():
    return datetime.now(timezone.utc)

def in_otc_session():
    hour = utc_now().hour
    return any(start <= hour < end for start, end in OTC_SESSIONS)

# Initialize Clients
bot = Bot(token=TELEGRAM_TOKEN)
finnhub_client = finnhub.Client(api_key=FINNHUB_KEY)
app = Flask(__name__)

def send(msg):
    async def _send():
        async with bot:
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    try:
        asyncio.run(_send())
    except Exception as e:
        print(f"Telegram Error: {e}")

# =========================
# STATE
# =========================
cooldown_until = utc_now() - timedelta(minutes=1)
loss_pause_until = utc_now() - timedelta(minutes=1)
open_trade = None
loss_count = 0

# =========================
# DATA (FINNHUB FIXED)
# =========================
def fetch_candles(symbol, tf):
    end = int(time.time())
    start = end - (100 * 60) 
    formatted_symbol = f"OANDA:{symbol.replace('/', '_')}"
    
    try:
        # Changed to stock_candle to support current Finnhub library
        res = finnhub_client.stock_candle(formatted_symbol, tf, start, end)
        
        if res.get('s') == 'ok':
            df = pd.DataFrame(res)
            df = df.rename(columns={'c': 'close', 'h': 'high', 'l': 'low', 'o': 'open', 't': 'time'})
            df['close'] = df['close'].astype(float)
            return df
    except Exception as e:
        print(f"API Error: {e}")
    return None

# =========================
# ANALYSIS
# =========================
def analyze(df):
    if df is None or df.empty: return None
    
    df["rsi"] = ta.rsi(df["close"], length=RSI_PERIOD)
    bb = ta.bbands(df["close"], length=BB_PERIOD, std=BB_STD)
    df = pd.concat([df, bb], axis=1)

    latest = df.iloc[-1]
    
    l_col = [c for c in bb.columns if "BBL" in c][0]
    u_col = [c for c in bb.columns if "BBU" in c][0]

    bb_width = (latest[u_col] - latest[l_col]) / latest["close"]
    if bb_width > 0.01:
        return None  

    if latest["rsi"] >= RSI_UPPER: return "SELL"
    if latest["rsi"] <= RSI_LOWER: return "BUY"
    return None

def multi_tf_confirm(pair):
    low_df = fetch_candles(pair, LOW_TF)
    high_df = fetch_candles(pair, HIGH_TF)
    return analyze(low_df) if analyze(low_df) == analyze(high_df) else None

# =========================
# MAIN LOOP
# =========================
def signal_loop():
    global cooldown_until, open_trade, loss_count, loss_pause_until

    while True:
        try:
            now = utc_now()
            if now < cooldown_until or now < loss_pause_until:
                time.sleep(10); continue

            if not in_otc_session() or open_trade:
                time.sleep(30); continue

            for pair in PAIRS:
                signal = multi_tf_confirm(pair)
                if not signal: continue

                candles = fetch_candles(pair, LOW_TF)
                price = candles.iloc[-1]["close"]
                
                send(f"🚨 *SIGNAL ALERT*\n\n*Pair:* {pair}\n*Dir:* {signal}\n*Price:* {price}")

                open_trade = {"pair": pair, "direction": signal}
                cooldown_until = now + timedelta(minutes=COOLDOWN_MINUTES)
                break

            time.sleep(15) 
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(10)

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
def home(): return "Bot Active and Running"

if __name__ == "__main__":
    threading.Thread(target=signal_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
