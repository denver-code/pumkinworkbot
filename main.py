import os
import logging
from functools import wraps

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


from api.states import *
from api.backend_api import CallApi
from api.database_api import User

storage = MemoryStorage()
bot = Bot(token=os.getenv("token"))
dp = Dispatcher(bot, storage=storage)


def need_auth(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        response = await CallApi().check_auth(args[0].chat.id)
        if response:
            return await func(*args, **kwargs)
        return await args[0].answer("You not authed, please use /start command for authorize.")
    return wrapper


async def set_bot_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="Show welcome message, and auth status")
    ]
    await bot.set_my_commands(commands)

async def on_startup(_):
    await set_bot_commands(bot)


@dp.message_handler(commands=["menu"])
@need_auth
async def menu_event(message: types.Message):
    user = await User.get({"user_id":message.chat.id})
    role = user["role"]
    buttons_getter = [
        types.InlineKeyboardButton(text="My Profile", callback_data=f"myprofile"),
        types.InlineKeyboardButton(text="Service responses", callback_data=f"service_responses"),
        types.InlineKeyboardButton(text="Publish service", callback_data=f"add_notification"),
        types.InlineKeyboardButton(text="My Profile on Site", url=f"https://pumpkin.work/EditProfile"),
        types.InlineKeyboardButton(text="Exit", callback_data=f"exit"),
    ]
    buttons_provider = [
        types.InlineKeyboardButton(text="My Profile", callback_data=f"myprofile"),
        types.InlineKeyboardButton(text="Orders taken", callback_data=f"provider_chats"),
        types.InlineKeyboardButton(text="Orders channel", url=f"https://t.me/+TfvWDm9hIC5kZTAy"),
        types.InlineKeyboardButton(text="My Profile on Site", url=f"https://pumpkin.work/ViewProvideProfile/-1"),
        types.InlineKeyboardButton(text="Exit", callback_data=f"exit"),
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    if role == "provider":
        buttons = buttons_provider
    else:
        buttons = buttons_getter
    keyboard.add(*buttons)
    await message.answer("You want:", reply_markup=keyboard)


@dp.callback_query_handler(state=["*"])
async def callback_event(query: types.CallbackQuery, state: FSMContext):

    if query.data == "haveaccount":
        await query.message.delete()
        await query.message.answer("Your email:")
        await AuthStates.email.set()

    if query.data == "add_notification":
        await query.message.delete()
        await CreateNotification.name.set()
        await query.message.answer("Request Title:")

    elif query.data == "provider_chats":
        await query.message.delete()
        message_text = "All taken:\n"
        response = await CallApi().get_chats(query.from_user.id)
        response = response.json()
        if len(response["message"]["chats"]) != 0:
            for i in response["message"]["chats"]:
                if i["agreementProvide"] == 1 and i["agreementRequest"] == 1:
                    message_text += f"""<a href="https://pumpkin.work/chat/{i["id"]}">Notification: {i["notification"]["name"]}\nRequest: {i["request"]["name"]} {i["request"]["surname"]}\nProvide: {i["provide"]["name"]}\n(provide) (request):\nAgreement: {i["agreementProvide"]} {i["agreementRequest"]}\nComplete: {i["completeProvide"]} {i["completeRequest"]}</a>\n\n"""
        buttons = [
            types.InlineKeyboardButton(text="Back", callback_data=f"menu")
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await query.message.answer(message_text, parse_mode="Html", reply_markup=keyboard)

    elif query.data == "service_responses":
        await query.message.delete()
        message_text = ""
        response = await CallApi().get_chats(query.from_user.id)
        response = response.json()
        for i in response["message"]["chats"]:
            message_text += f"""<a href="https://pumpkin.work/chat/{i["id"]}">Notification: {i["notification"]["name"]}\nRequest: {i["request"]["name"]} {i["request"]["surname"]}\nProvide: {i["provide"]["name"]}\n(provide) (request):\nAgreement: {i["agreementProvide"]} {i["agreementRequest"]}\nComplete: {i["completeProvide"]} {i["completeRequest"]}</a>\n\n"""
        buttons = [
            types.InlineKeyboardButton(text="Back", callback_data=f"menu")
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await query.message.answer(message_text, parse_mode="Html", reply_markup=keyboard)

    elif query.data == "menu":
        await query.message.delete()
        await menu_event(query.message)

    elif query.data == "myprofile":
        await query.message.delete()
        user = await User.get({"user_id": query.from_user.id})
        message_text = "Your Profile:"
        for i in user["profile"]:
            message_text += f"{i.capitalize()}: {user['profile'][i]}\n"

        buttons = [
            types.InlineKeyboardButton(text="Back", callback_data=f"menu")
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)

        await query.message.answer(message_text, reply_markup=keyboard)


    elif query.data == "exit":
        await query.message.delete()
        await User.delete({"user_id":query.from_user.id})
        await query.message.answer("Success!\nUse /start for auth again.")


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

    elif "service" in query.data:
        await query.message.delete()
        async with state.proxy() as data:
            service_id = query.data.split("=")[1]
            data["service"] = service_id
            buttons = []
            response = await CallApi().get_country()
            response = response.json()
            for i in response["message"]["countrys"]:
                buttons.append(types.InlineKeyboardButton(f"{i['name']}", callback_data=f"country={i['id']}"))
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(*buttons)
            await query.message.answer("Select Country:", reply_markup=keyboard)
            await CreateNotification().next()


    elif "country" in query.data:
        await query.message.delete()
        async with state.proxy() as data:
            country_id = query.data.split("=")[1]
            data["country"] = country_id
            buttons = []
            response = await CallApi().get_regions(country_id)
            response = response.json()
            for i in response["message"]["regions"]:
                buttons.append(types.InlineKeyboardButton(f"{i['name']}", callback_data=f"region={i['id']}"))
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(*buttons)
            await query.message.answer("Select Region:", reply_markup=keyboard)
            await CreateNotification().next()
        
    elif "region" in query.data:
        await query.message.delete()
        async with state.proxy() as data:
            region_id = query.data.split("=")[1]
            data["region"] = region_id
            buttons = []
            response = await CallApi().get_citys(data["country"], region_id)
            response = response.json()
            if len(response["message"]["сitys"]) != 0:
                for i in response["message"]["сitys"]:
                    buttons.append(types.InlineKeyboardButton(f"{i['name']}", callback_data=f"city={i['id']}"))
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(*buttons)
                await query.message.answer("Select City:", reply_markup=keyboard)
                await CreateNotification().next()

            else:
                await CallApi().new_notif(query.from_user.id, {
                        "name":data["name"],
                        "description":data["desc"],
                        "country":data["country"],
                        "city":0,
                        "region":data["region"],
                        "service":data["service"]
                })
                await state.finish()
                await query.message.answer("Success! Use /menu for another operation.")

    elif "city" in query.data:
        await query.message.delete()
        async with state.proxy() as data:
            city_id = query.data.split("=")[1]
            data["city"] = city_id
            buttons = []
            response = await CallApi().new_notif(query.from_user.id, {
            "name":data["name"],
            "description":data["desc"],
            "country":data["country"],
            "city":city_id,
            "region":data["region"],
            "service":data["service"]
            })
            await state.finish()
            await query.message.answer("Success! Use /menu for another operation.")


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
            token = response.headers.get("Authorization")
            response = response.json()
            print(response)
            if "error" in response:
                if "user with role" in response["error"]:
                    await query.message.delete()
                    await state.finish()
                    return await query.message.answer("A user with inserted email isn’t found. Please, check the email, the password, and the role you inserted and try again.")
                elif response["error"] == "Username and password don't match":
                    await query.message.delete()
                    await state.finish()
                    return await query.message.answer("A user with inserted email isn’t found. Please, check the email, the password, and the role you inserted and try again.")
            if not await User.exist({"email": response["message"]["profile"]["email"]}):
                await User.new({
                "user_id": query.from_user.id,
                "token": token,
                "email": response["message"]["profile"]["email"],
                "role": role,
                "profile": response["message"]["profile"]
            })
            else:
                await User.update({"email": response["message"]["profile"]["email"]}, {
                "user_id": query.from_user.id,
                "token": token,
                "email": response["message"]["profile"]["email"],
                "role": role,
                "profile": response["message"]["profile"]
            })
            await query.message.answer("Your login success!\nUse /menu for continue!")

        await state.finish()
        await query.message.delete()


@dp.message_handler(commands=["test"])
async def test_event(message: types.Message):
    response = await CallApi().get_country()
    response = response.json()
    for i in response["message"]["countrys"]:
        print(i)


@dp.message_handler(state=[CreateNotification.name], content_types=["text"])
async def parse_name_event(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["name"] = message.text
        await message.answer("Description:")
        await CreateNotification().next()
    

@dp.message_handler(state=[CreateNotification.description], content_types=["text"])
async def parse_desc_event(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["desc"] = message.text
        buttons = []
        response = await CallApi().get_services()
        response = response.json()
        for i in response["message"]["services"]:
            buttons.append(types.InlineKeyboardButton(text=f"{i['nameEN']}", callback_data=f"service={i['id']}"))
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)
        await message.answer("Select type of service:", reply_markup=keyboard)
        await CreateNotification().next()


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