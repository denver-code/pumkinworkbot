import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, types 
from aiogram.utils import executor

bot = Bot(token=os.getenv("token"))
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply(message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)