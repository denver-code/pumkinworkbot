import requests
from api.database_api import User

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
        return response
    

    async def get_chats(self, userid):
        user = await User.get({"user_id": userid})
        response = requests.post(
            f"{self.API_URL}/notification/request_list_chats",
            headers={'Content-Type': "application/json", 'Accept': "application/json", "Authorization": user["token"]},
            json= {"page":1, "amount":100})
        return response
    
    