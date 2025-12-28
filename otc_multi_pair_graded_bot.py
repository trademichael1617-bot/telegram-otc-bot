import os
import asyncio
import threading
import random  # Added for the mock data provider
from statistics import mean, stdev
from flask import Flask
from telegram.ext import ApplicationBuilder

# ======================
# 1. CONFIGURATION
# ======================
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003540658518"))
PORT = int(os.environ.get("PORT", 10000))

# ======================
# 2. DATA PROVIDER
# ======================
def get_price_data(pair="EURUSD_OTC", count=50):
    """
    🔌 DATA PLUGIN: Replace this with your actual API call (e.g., Pocket Option or MT5)
    Returns a list of closing prices.
    """
    # Placeholder: Generates random prices for testing
    return [1.0800 + (random.random() * 0.0050) for _ in range(count)]

# ======================
# 3. INDICATORS
# ======================
def calculate_rsi(prices, period=5):
    if len(prices) < period + 1: return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

    avg_gain = mean(gains[-period:])
    avg_loss = mean(losses[-period:])
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def bollinger_bands(prices, period=20, deviation=2):
    if len(prices) < period: return 0, 0, 0
    sma = mean(prices[-period:])
    std = stdev(prices[-period:])
    return sma + (deviation * std), sma, sma - (deviation * std)

def is_consolidating(upper, lower, price):
    # Tight range check: Band width is less than 0.15% of price
    return (upper - lower) < (price * 0.0015)

# ======================
# 4. SIGNAL ENGINE
# ======================
def generate_signal(prices):
    rsi = calculate_rsi(prices)
    upper, mid, lower = bollinger_bands(prices)
    price = prices[-1]

    if not is_consolidating(upper, lower, price):
        return None, rsi

    if rsi <= 15 and price <= lower:
        return "BUY 📈", rsi
    if rsi >= 85 and price >= upper:
        return "SELL 📉", rsi

    return None, rsi

# ======================
# 5. ASYNC BOT LOGIC
# ======================
async def signal_loop(app):
    """The background task that checks markets and sends signals"""
    await asyncio.sleep(10)
    print("📢 Strategy engine started")

    while True:
        try:
            prices = get_price_data()
            if not prices:
                print("⚠️ No price data received")
            else:
                signal, rsi_val = generate_signal(prices)
                if signal:
                    message = (
                        "📊 *OTC SIGNAL*\n\n"
                        "*Pair:* EURUSD OTC\n"
                        f"*Direction:* {signal}\n"
                        f"*RSI:* {rsi_val:.2f}\n"
                        "*Condition:* Consolidation Found"
                    )
                    await app.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=message,
                        parse_mode="Markdown"
                    )
                    print(f"✅ Signal sent: {signal}")
        except Exception as e:
            print(f"❌ Error in signal loop: {e}")

        await asyncio.sleep(60)

async def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    await app.initialize()
    await app.start()
    
    # Start the signal task inside the bot's event loop
    asyncio.create_task(signal_loop(app))
    
    print("🤖 Bot is polling...")
    await app.updater.start_polling()
    while True: await asyncio.sleep(3600)

# ======================
# 6. WEB SERVER & MAIN
# ======================
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is healthy!", 200

def start_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

if __name__ == "__main__":
    # Start Telegram background thread
    threading.Thread(target=start_bot_thread, daemon=True).start()
    
    # Start Flask (Render's primary process)
    print(f"🌐 Server running on port {PORT}")
    web_app.run(host="0.0.0.0", port=PORT)
