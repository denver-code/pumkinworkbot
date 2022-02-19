import os
from dotenv import load_dotenv
import requests
from api.database_api import User

load_dotenv()

async def send_message(message):
    url_req = f"https://api.telegram.org/bot{os.getenv('token')}/sendMessage?chat_id={os.getenv('channel')}&text={message}&parse_mode=html"
    f = requests.get(url_req)


class CallApi:
    def __init__(self):
        self.API_URL = "https://pumpkin.work/api"
    

    async def auth(self, userdata):
        response = requests.post(
            f"{self.API_URL}/user/login",
            headers={'Content-Type': "application/json", 'Accept': "application/json"},
            json= userdata)
        return response
    

    async def check_auth(self, userid):
        user = await User.get({"user_id": userid})
        if not user:
            user = {"token":"null"}
        response = requests.post(
            f"{self.API_URL}/user/notification",
            headers={'Content-Type': "application/json", 'Accept': "application/json", "Authorization": user["token"]},
            json= {"id":1}
        )  
        if response.status_code != 401:
            return True
        return False
    

    async def get_services(self):
        response = requests.get(f"{self.API_URL}/service/all")
        return response
    

    async def get_country(self):
        response = requests.get(f"{self.API_URL}/country/all")
        return response
    

    async def get_regions(self, country):
        response = requests.post(
            f"{self.API_URL}/regions/country",
            headers={'Content-Type': "application/json", 'Accept': "application/json"},
            json= {"id":country})
        return response


    async def get_citys(self, country, region):
        response = requests.post(
            f"{self.API_URL}/citys/country",
            headers={'Content-Type': "application/json", 'Accept': "application/json"},
            json= {"countryId":country, "regionId":region})
        return response
    

    async def new_notif(self, userid, body):
        user = await User.get({"user_id": userid})
        response = requests.post(
            f"{self.API_URL}/customer/addnotification",
            headers={'Content-Type': "application/json", 'Accept': "application/json", "Authorization": user["token"]},
            json= body)
        r = response.json()
        if response.status_code == 200:
            await send_message(f"""
New notification!
Name: {r["message"]["requests"]["name"]}
City: {r["message"]["requests"]["city"]["name"] if "city" in r["message"]["requests"] else "Without"}
Region: {r["message"]["requests"]["region"]["name"]}
Country: {r["message"]["requests"]["country"]["name"]}
Service: {r["message"]["requests"]["service"]["nameEN"]}
Reciever: {r["message"]["requests"]["reciever"]["name"]} {r["message"]["requests"]["reciever"]["surname"]}

Telegram reciever mention: <a href="tg://user?id={userid}">TAP</a>
""")
        return response

    async def get_chats(self, userid):
        user = await User.get({"user_id": userid})
        response = requests.post(
            f"{self.API_URL}/notification/request_list_chats",
            headers={'Content-Type': "application/json", 'Accept': "application/json", "Authorization": user["token"]},
            json= {"page":1, "amount":100})
        return response
    
    