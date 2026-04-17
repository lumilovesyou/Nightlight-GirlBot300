import json
import logging
from dotenv import load_dotenv
import os
import platform
import random
import sys
import requests

load_dotenv()

# Init globals
SITE = "https://nightlightapp.net/"
API_POINT = f"{SITE}nlapi/user"
SESSION = requests.Session()

# Testing username
USERNAME = "felisaraneae"

# Get token
SESSION.post(f"{SITE}account/login", data={"loginusername": USERNAME, "loginpassword": os.getenv("PASSWORD")})
print(SESSION.cookies.get_dict())

# Test using token
request = SESSION.get(f"{API_POINT}?action=getUnreadNotifications")
print(request.text)