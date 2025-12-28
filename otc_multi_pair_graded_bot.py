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
