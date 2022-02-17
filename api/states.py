from aiogram.dispatcher.filters.state import State, StatesGroup

class AuthStates(StatesGroup):
    email = State()
    password = State()
    role = State()

class RegisterStates(StatesGroup):
    role = State()