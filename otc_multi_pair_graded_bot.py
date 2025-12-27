

import os
import asyncio
from telegram.ext import ApplicationBuilder

TOKEN = "8574406761:AAFSLmSLUNtuTIc2vtl7K8JMDIXiM2IDxNQ"
CHANNEL_ID = -1003540658518
async def test_message():
    app_tg = ApplicationBuilder().token(TOKEN).build()
    await app_tg.initialize()
    await app_tg.start()
    
    await app_tg.bot.send_message(
        chat_id=CHANNEL_ID,
        text="✅ Test message from bot is working!"
    )
    
    await app_tg.stop()  # Stop bot after sending

asyncio.run(test_message())



    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
