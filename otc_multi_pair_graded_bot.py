import os
import asyncio
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timezone
from twelvedata import TDClient
from telegram.ext import ApplicationBuilder
# --- CONFIGURATION ---
TOKEN = os.getenv("BOT_TOKEN", "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003540658518"))

# FIXED: Hardcoded key or proper env lookup
TWELVE_DATA_API = os.getenv("TD_API_KEY", "0da718e36a9c4f48a2541dc00d209f62")
PAIR = "EUR/USD OTC" # Or your preferred OTC pair


# Global variables to prevent spam/repeats
last_signal_time = None
last_signal_type = None

# Initialize Twelve Data
td = TDClient(apikey=API_KEY)

def fetch_and_analyze():
    """Fetches data and calculates indicators."""
    try:
        # Fetch 50 candles (1min interval)
        ts = td.time_series(symbol=PAIR, interval="1min", outputsize=50).as_pandas()
        
        # Calculate Indicators using pandas_ta
        ts['rsi'] = ta.rsi(ts['close'], length=14)
        bb = ta.bbands(ts['close'], length=20, std=2)
        ts = pd.concat([ts, bb], axis=1)

        # Get the latest row
        latest = ts.iloc[-1]
        
        signal_data = {
            "time": latest.name,
            "price": round(latest['close'], 5),
            "rsi": latest['rsi'],
            "upper": latest['BBU_20_2.0'],
            "lower": latest['BBL_20_2.0'],
            "direction": None,
            "grade": "C"
        }

        # Strategy Logic (Bollinger + RSI)
        if signal_data['price'] > signal_data['upper'] and signal_data['rsi'] > 70:
            signal_data['direction'] = "SELL 📉"
            signal_data['grade'] = "A+" if signal_data['rsi'] > 80 else "B"
        elif signal_data['price'] < signal_data['lower'] and signal_data['rsi'] < 30:
            signal_data['direction'] = "BUY 📈"
            signal_data['grade'] = "A+" if signal_data['rsi'] < 20 else "B"

        return signal_data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

async def signal_loop(tg_app):
    global last_signal_time, last_signal_type
    
    print("📢 Scanner started. Monitoring EUR/USD...")
    
    while True:
        data = fetch_and_analyze()
        
        if data and data['direction']:
            # This check ensures we only alert once per candle time/direction
            if data['time'] != last_signal_time or data['direction'] != last_signal_type:
                msg = (
                    f"🎯 *NEW SIGNAL DETECTED*\n\n"
                    f"💎 *Pair:* {PAIR}\n"
                    f"↕️ *Action:* {data['direction']}\n"
                    f"💵 *Entry Price:* {data['price']}\n"
                    f"⭐ *Grade:* {data['grade']}\n"
                    f"🕒 *Time:* {data['time'].strftime('%H:%M')} UTC\n\n"
                    f"📊 *RSI:* {round(data['rsi'], 2)}"
                )
                
                await tg_app.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")
                
                # Update memory to prevent repeating the same signal
                last_signal_time = data['time']
                last_signal_type = data['direction']
                print(f"✅ Signal Sent: {data['direction']} at {data['price']}")
            else:
                print(f"⏳ Already alerted for {data['direction']} at {data['time']}. Waiting...")
        else:
            p = data['price'] if data else "N/A"
            print(f"🔎 Scanning... No signal. Price: {p}")

        # Wait 30 seconds between checks
        await asyncio.sleep(30)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Run the background scanner
    loop = asyncio.get_event_loop()
    loop.create_task(signal_loop(app))
    
    print("Bot is initializing...")
    app.run_polling()import os
