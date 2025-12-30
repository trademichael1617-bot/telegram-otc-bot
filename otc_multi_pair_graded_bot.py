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

# FIXED: Hardcoded key or proper env lookup
TWELVE_DATA_API = os.getenv("TD_API_KEY", "0da718e36a9c4f48a2541dc00d209f62")

PAIR = "EUR/USD"
TIMEFRAME = "1min"  # Twelve Data free tier usually supports 1min+, check your plan for 10s
RSI_PERIOD = 5
BB_PERIOD = 20
BB_STD = 2
MAX_LOSSES = 2
COOLDOWN_MIN = 15

app = Flask(__name__)

@app.route("/")
def home(): return "Telegram OTC Bot is running ✅"

@app.route("/health")
def health(): return "OK", 200

# ======================
# GLOBALS & STATE
# ======================
last_trade = {"direction": None, "entry": None, "time": None}
stats = {"wins": 0, "losses": 0, "streak": 0}
cooldown_until = utc_now() - timedelta(minutes=1)

# ======================
# LOGIC & INDICATORS
# ======================
def fetch_candles():
    """Fetch latest candles from Twelve Data API"""
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={PAIR}&interval={TIMEFRAME}&apikey={TWELVE_DATA_API}&outputsize=30"
        resp = requests.get(url).json()
        if "values" not in resp:
            print(f"⚠️ API Error: {resp.get('message', 'Unknown error')}")
            return []
        return resp.get("values", [])
    except Exception as e:
        print(f"❌ Fetch Error: {e}")
        return []

def calculate_indicators(candles):
    df = pd.DataFrame(candles)
    df['close'] = df['close'].astype(float)
    df = df.iloc[::-1] # Reverse to chronological order
    
    # Correct RSI Calculation
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_PERIOD).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['sma'] = df['close'].rolling(window=BB_PERIOD).mean()
    df['std'] = df['close'].rolling(window=BB_PERIOD).std()
    df['bb_upper'] = df['sma'] + (BB_STD * df['std'])
    df['bb_lower'] = df['sma'] - (BB_STD * df['std'])
    return df



def grade_signal(df):
    volatility = df['close'].std()
    if volatility < 0.0005: return "A (High Probability)"
    if volatility < 0.001: return "B (Moderate)"
    return "C (High Volatility)"

# ======================
# ASYNC TASKS
# ======================
async def signal_loop(tg_app):
    global last_trade
    print("📢 Signal scanner started...")
    while True:
        if utcnow() < cooldown_until:
            await asyncio.sleep(30)
            continue

        candles = fetch_candles()
        if len(candles) < BB_PERIOD:
            await asyncio.sleep(20)
            continue

        df = calculate_indicators(candles)
        last_row = df.iloc[-1]
        
        # BUY Logic: Price below Lower Band + RSI Oversold
        if last_row['close'] < last_row['bb_lower'] and last_row['rsi'] < 30:
            grade = grade_signal(df)
            await send_signal(tg_app, "BUY 📈", grade, last_row['close'])
            
        # SELL Logic: Price above Upper Band + RSI Overbought
        elif last_row['close'] > last_row['bb_upper'] and last_row['rsi'] > 70:
            grade = grade_signal(df)
            await send_signal(tg_app, "SELL 📉", grade, last_row['close'])

        await asyncio.sleep(30)

async def send_signal(tg_app, direction, grade, price):
    global last_trade
    msg = (f"📊 *OTC SIGNAL*\n\n"
           f"*Pair:* {PAIR}\n"
           f"*Direction:* {direction}\n"
           f"*Entry:* {price}\n"
           f"*Grade:* {grade}\n"
           f"*Time:* {datetime.utcnow().strftime('%H:%M:%S')} UTC")
    
    await tg_app.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")
    last_trade.update({"direction": direction.split()[0], "entry": price, "time": datetime.utcnow()})

async def start_bot():
    tg_app = ApplicationBuilder().token(TOKEN).build()
    await tg_app.initialize()
    await tg_app.start()
    asyncio.create_task(signal_loop(tg_app))
    print("🤖 Telegram logic initialized")
    while True: await asyncio.sleep(3600)

def run_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

if __name__ == "__main__":
    threading.Thread(target=run_bot_thread, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
