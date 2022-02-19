import motor.motor_asyncio
import requests

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://127.0.0.1:27017")

db = client["PumpkinTech"]
users = db["users"]


class User:
    async def new(data):
        return await users.insert_one(data)

    async def get(querry):
        return await users.find_one(querry)

    async def update(find, update):
        return await users.update_one(find, {"$set": update}, upsert=True)

    async def delete(obj):
        return await users.delete_one(obj)
    
    async def exist(data):
        return bool(await User.get(data))
