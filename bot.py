import asyncio
import logging
import os
from dotenv import load_dotenv

from state import storage
from handlers import handlers, callbacks

from aiogram import Bot, Dispatcher

load_dotenv()
token = os.getenv('TOKEN')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(storage=storage.storage)

async def main():
    dp.include_router(handlers.router)
    dp.include_router(callbacks.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Stop polling. Exit..')
    except Exception as e:
        print(e)
