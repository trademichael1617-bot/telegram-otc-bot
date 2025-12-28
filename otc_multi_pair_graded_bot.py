import os
import asyncio
from telegram.ext import ApplicationBuilder

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003540658518"))

if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

async def send_signals(app):
    await asyncio.sleep(10)
    print("📢 Signal loop started")

    while True:
        try:
            await app.bot.send_message(
                chat_id=CHANNEL_ID,
                text="📊 OTC SIGNAL\nPair: EURUSD OTC\nDirection: BUY 📈"
            )
            print("✅ Signal sent")
        except Exception as e:
            print("❌ Telegram error:", e)

        await asyncio.sleep(60)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.create_task(send_signals(app))

    print("🤖 Telegram bot polling started")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
