import os

API_KEY = os.getenv("API_KEY")

import httpx
import asyncio

async def fetch_candle(pair="EUR/USD", interval="1min"):
    url = f"https://api.twelvedata.com/time_series"
    params = {
        "symbol": pair,
        "interval": interval,
        "apikey": API_KEY,
        "format": "JSON",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        return data.get("values", [])  # list of candles
async def main():
    candles = await fetch_candle()
    print("Last 3 candles:", candles[:3])

asyncio.run(main())
import numpy as np

def rsi(prices, period=5):
    """Calculate RSI for a list of prices."""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
def is_consolidating(prices, threshold=0.0005):
    """Return True if last few prices are within a small range."""
    recent = prices[-5:]  # last 5 closes
    return max(recent) - min(recent) <= threshold
async def analyze_market(pair="EUR/USD"):
    candles = await fetch_candle(pair)
    closes = [float(c["close"]) for c in candles]
    
    current_rsi = rsi(closes)
    consolidating = is_consolidating(closes)
    
    return {
        "rsi": current_rsi,
        "consolidating": consolidating
    }

import os
import asyncio
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# CONFIG
# ======================

TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003540658518"))

# Set TEST_MODE=True to send a test message instantly
TEST_MODE = True

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
    """Loop to send messages every 60 seconds."""
    await asyncio.sleep(10)  # wait for bot to connect
    print("📢 Signal loop starting...")
    while True:
        try:
            msg = "📊 *OTC SIGNAL*\n\n*Pair:* EURUSD OTC\n*Direction:* BUY 📈"
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text=msg,
                parse_mode="Markdown"
            )
            print("✅ Signal sent")
        except Exception as e:
            print(f"❌ Signal Error: {e}")
        await asyncio.sleep(60)

async def send_test_message(application):
    """Send a single test message immediately."""
    try:
        msg = "✅ Test message — bot is working!"
        await application.bot.send_message(
            chat_id=CHANNEL_ID,
            text=msg
        )
        print("📩 Test message sent")
    except Exception as e:
        print(f"❌ Test message error: {e}")

async def start_bot():
    """Custom startup for v20+."""
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Initialize and start bot
    await application.initialize()
    await application.start()
    
    # Optionally send a test message
    if TEST_MODE:
        await send_test_message(application)
    
    # Start regular signal loop
    asyncio.create_task(send_signals(application))
    print("🤖 Bot initialized and polling...")
    
    # Keep the async loop alive
    while True:
        await asyncio.sleep(3600)

def run_bot_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

# ======================
# MAIN START
# ======================
if __name__ == "__main__":
    print("🚀 Launching Flask + Bot...")
    
    # Start bot in separate thread
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()
    
    # Run Flask on main thread
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
import random  # For demo purposes

# ======================
# TELEGRAM LOGIC
# ======================
def get_signal_grade():
    """
    Generate a signal grade.
    Example:
      - A / B / C
      - Could also be numeric (1-5)
    """
    grades = ["A ✅", "B ⚡", "C ⚠️"]
    return random.choice(grades)

async def send_signals(application):
    """Loop to send messages every 60 seconds."""
    await asyncio.sleep(10)
    print("📢 Signal loop starting...")
    
    while True:
        try:
            grade = get_signal_grade()  # get current signal grade
            msg = (
                f"📊 *OTC SIGNAL*\n\n"
                f"*Pair:* EURUSD OTC\n"
                f"*Direction:* BUY 📈\n"
                f"*Grade:* {grade}"
            )
            await application.bot.send_message(
                chat_id=CHANNEL_ID,
                text=msg,
                parse_mode="Markdown"
            )
            print(f"✅ Signal sent with grade {grade}")
        except Exception as e:
            print(f"❌ Signal Error: {e}")
        
        await asyncio.sleep(60)
