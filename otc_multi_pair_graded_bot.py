import pandas as pd
import numpy as np
import yfinance as yf
import time
import asyncio
from telegram import Bot

# =========================
# SETTINGS
# =========================
SYMBOL = "EURUSD"
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

RSI_PERIOD = 7
RSI_OVERSOLD = 10
RSI_OVERBOUGHT = 90
BB_PERIOD = 25
BB_DEV = 2
CONSOLIDATION_LOOKBACK = 20
BB_WIDTH_THRESHOLD = 0.015

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram_msg(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ... [Keep your rsi, bollinger_bands, and is_consolidating functions here] ...

def fetch_live_data(symbol="EURUSD=X"):
    data = yf.download(tickers=symbol, period="1d", interval="1m", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data[['Close']].rename(columns={'Close': 'close'})

async def main():
    print(f"🚀 Starting Bot for {SYMBOL}...")
    await send_telegram_msg(f"🤖 Bot Started for {SYMBOL}")
    
    while True:
        try:
            df = fetch_live_data("EURUSD=X")
            
            if len(df) < BB_PERIOD + CONSOLIDATION_LOOKBACK:
                time.sleep(10)
                continue

            result = analyze_market(df) # Your logic function
            latest = result.iloc[-1]
            ts = time.strftime('%H:%M:%S')

            if latest["signal"] != "NONE":
                msg = f"📢 {SYMBOL} SIGNAL: {latest['signal']}\n⏰ Time: {ts}\n📉 RSI: {latest['rsi']:.2f}"
                print(msg)
                await send_telegram_msg(msg)
            else:
                print(f"⏸ [{ts}] Monitoring... RSI: {latest['rsi']:.2f}")

        except Exception as e:
            print(f"❌ Error: {e}")

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
