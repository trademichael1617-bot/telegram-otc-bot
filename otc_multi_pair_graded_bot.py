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

# =========================
# INDICATORS & LOGIC
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def bollinger_bands(series, period, dev):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + (std * dev)
    lower = sma - (std * dev)
    return upper, lower, sma

def is_consolidating(close, upper_bb, lower_bb):
    bb_width = (upper_bb - lower_bb) / close
    recent_range = (close.rolling(CONSOLIDATION_LOOKBACK).max() - 
                    close.rolling(CONSOLIDATION_LOOKBACK).min()) / close
    return (bb_width < BB_WIDTH_THRESHOLD) & (recent_range < BB_WIDTH_THRESHOLD)

def analyze_market(df):
    df = df.copy()
    df["rsi"] = rsi(df["close"], RSI_PERIOD)
    df["upper_bb"], df["lower_bb"], _ = bollinger_bands(df["close"], BB_PERIOD, BB_DEV)
    df["consolidating"] = is_consolidating(df["close"], df["upper_bb"], df["lower_bb"])
    
    df["signal"] = "NONE"
    buy_condition = (df["rsi"] <= RSI_OVERSOLD) & (df["close"] <= df["lower_bb"]) & (df["consolidating"])
    sell_condition = (df["rsi"] >= RSI_OVERBOUGHT) & (df["close"] >= df["upper_bb"]) & (df["consolidating"])
    
    df.loc[buy_condition, "signal"] = "CALL"
    df.loc[sell_condition, "signal"] = "PUT"
    return df

async def send_telegram_msg(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram Error: {e}")

# =========================
# MAIN LOOP
# =========================
async def main():
    print(f"🚀 Starting Bot for {SYMBOL}...")
    await send_telegram_msg(f"🤖 Bot Started for {SYMBOL}")
    
    last_signal_time = None  # To prevent duplicate alerts for the same candle

    while True:
        try:
            # Fetch data
            data = yf.download(tickers="EURUSD=X", period="1d", interval="1m", progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            df = data[['Close']].rename(columns={'Close': 'close'})
            current_time = df.index[-1] # Get timestamp of the latest candle

            if len(df) < 50:
                await asyncio.sleep(10)
                continue

            # Analyze
            result = analyze_market(df)
            latest = result.iloc[-1]

            # Signal Logic + Duplicate Prevention
            if latest["signal"] != "NONE" and current_time != last_signal_time:
                msg = (f"📢 *{SYMBOL} SIGNAL: {latest['signal']}*\n"
                       f"⏰ Candle: {current_time.strftime('%H:%M')}\n"
                       f"📉 RSI: {latest['rsi']:.2f}\n"
                       f"📏 Price: {latest['close']:.5f}")
                
                print(msg)
                await send_telegram_msg(msg)
                last_signal_time = current_time 
            else:
                print(f"⏸ [{time.strftime('%H:%M:%S')}] Monitoring... RSI: {latest['rsi']:.2f}")

        except Exception as e:
            print(f"❌ Loop Error: {e}")

        await asyncio.sleep(30) # Check every 30 seconds for better responsiveness

if __name__ == "__main__":
    asyncio.run(main())
