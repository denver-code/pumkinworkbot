from aiogram.dispatcher.filters.state import State, StatesGroup

class AuthStates(StatesGroup):
    email = State()
    password = State()
    role = State()

class RegisterStates(StatesGroup):
    role = State()

class CreateNotification(StatesGroup):
    name = State()
    description = State()
    service = State()
    country = State()
    state = State()
    city = State()