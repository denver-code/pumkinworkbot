import requests


class CallApi:
    def __init__(self):
        self.API_URL = "https://pumpkin.work/api"
    
    async def auth(self, userdata):
        response = requests.post(
            f"{self.API_URL}/user/login",
            headers={'Content-Type': "application/json", 'Accept': "application/json"},
            json= userdata)
        return response