import os
import logging


if not os.path.isdir("logs"):
    os.mkdir("logs")


file_log = logging.FileHandler("logs/bot.log")
console_out = logging.StreamHandler()
logging.basicConfig(handlers=(file_log, console_out),
                            format='[%(asctime)s | %(levelname)s]: %(message)s',
                            datefmt='%m.%d.%Y %H:%M:%S',
                            level=logging.INFO)


from dotenv import load_dotenv


load_dotenv()


from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage


from api.states import AuthStates, RegisterStates
from api.backend_api import CallApi


storage = MemoryStorage()
bot = Bot(token=os.getenv("token"))
dp = Dispatcher(bot, storage=storage)


async def set_bot_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="Show welcome message, and auth status")
    ]
    await bot.set_my_commands(commands)

async def on_startup(_):
    await set_bot_commands(bot)


@dp.callback_query_handler(state=["*"])
async def callback_event(query: types.CallbackQuery, state: FSMContext):

    if query.data == "haveaccount":
        await query.message.delete()
        await query.message.answer("Your email:")
        await AuthStates.email.set()

    elif "register" in query.data:
        role = query.data.split("=")[-1]
        await query.message.delete()
        if role == "provider":
            url = "https://pumpkin.work/ProviderRegistration"
        else:
            url = "https://pumpkin.work/Registration"
        await query.message.answer(f"You need to go to our website, and register there, then go to the bot, and log in!\nLink: {url}\nUse command /start for retry auth")
        await state.finish()

    elif query.data == "donthaveaccount":
        await query.message.delete()
        await RegisterStates.role.set()
        buttons = [
            types.InlineKeyboardButton(text="Request a service", callback_data=f"register=getService"),
            types.InlineKeyboardButton(text="Provide service", callback_data=f"register=provider")
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await query.message.answer("You want:", reply_markup=keyboard)

    elif "role" in query.data:
        
        role = query.data.split("=")[1]
        async with state.proxy() as data:
            data["role"] = role
            userdata = {
                "client_id": data["email"],
                "password": data["password"],
                "role_request": role
            }
            response = await CallApi().auth(userdata)
            response = response.json()
            if "error" in response:
                if "user with role" in response["error"]:
                    await query.message.delete()
                    await state.finish()
                    return await query.message.answer("A user with inserted email isn’t found. Please, check the email, the password, and the role you inserted and try again.")
                elif response["error"] == "Username and password don't match":
                    await query.message.delete()
                    await state.finish()
                    return await query.message.answer("A user with inserted email isn’t found. Please, check the email, the password, and the role you inserted and try again.")
            await query.message.answer("Your login success!\nAnother logic comming soon!")
        await state.finish()
        await query.message.delete()


@dp.message_handler(state=[AuthStates.email], content_types=["text"])
async def email_event(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["email"] = message.text
        await message.answer("Password:")
        await AuthStates.next()


@dp.message_handler(state=[RegisterStates.role])
async def select_role_event(message: types.Message, state: FSMContext):
    buttons = [
            types.InlineKeyboardButton(text="Request a service", callback_data=f"register=getService"),
            types.InlineKeyboardButton(text="Provide service", callback_data=f"register=provider")
        ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await message.answer("You want:", reply_markup=keyboard)


@dp.message_handler(state=[AuthStates.password], content_types=["text"])
async def password_event(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["password"] = message.text
        buttons = [
            types.InlineKeyboardButton(text="Request a service", callback_data=f"role=getService"),
            types.InlineKeyboardButton(text="Provide service", callback_data=f"role=provider")
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await message.answer("You want:", reply_markup=keyboard)



@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text="Yes", callback_data=f"haveaccount"),
        types.InlineKeyboardButton(text="No", callback_data=f"donthaveaccount")
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await message.answer("Welcome!\nYou have account on pumpkin.work?", reply_markup=keyboard)


@dp.message_handler(commands=["ping"])
async def ping_event(message: types.Message):
    await message.reply("Pong!")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)