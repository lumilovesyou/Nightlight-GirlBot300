import json
import logging
from dotenv import load_dotenv
import mimetypes
import os
import platform
import random
import sys
import requests

load_dotenv()

# Init globals
SITE = "https://nightlightapp.net/"
API_POINT = f"{SITE}nlapi/"
SESSION = requests.Session()

USERNAME = os.getenv("USERNAME")

# Get token
try:
    print("Attempting to get key")
    SESSION.post(f"{SITE}account/login", data={"loginusername": USERNAME, "loginpassword": os.getenv("PASSWORD")})
    if (SESSION.cookies.get_dict()["username"] != USERNAME):
        print("Failed to get token!")
        exit()
except:
    print("Failed to get token!")

# Invalid the previous token (probably a really gross way to do this but I couldn't find an endpoint to grab tokens from)
try:
    print("Attempting to remove tokens")
    grabTokens = SESSION.get(f"{SITE}u/{USERNAME}").text
    grabTokens = json.loads(grabTokens.split("\"loginTokens\":")[1].split("});document.getElementById('notificationdot-notifications')")[0])
    for i in grabTokens:
        if (i["device"] == "python-requests/2.25.1" and not i["active"]):
            # Remove old tokens
            SESSION.post(f"{API_POINT}user", params={"action": "invalidateToken"}, json={"tokenId": i["id"]})
except:
    print("Failed to remove old tokens")
    
print("Ready Mr. Stark!")
    
def createPost(text, category="other", filePath=None):
    files = {}
    if (filePath and os.path.exists(filePath)):
        # Don't really need more than one image right now so... ~~~~~~~~~~
        files = {
            "file0": (
                os.path.basename(filePath),
                open(filePath, "rb"),
                mimetypes.guess_type(filePath)[0] or "application/octet-stream"
            )
        }
        
    response = SESSION.post(f"{API_POINT}post",
        data={
            "content": text,
            "category": category,
            "visibility": 0,
            "views": 2
        },
        files=files
    )
    print(response.text)
    print(response.status_code)
    print(f"Posted \"{text}\"!")

createPost("Automation test, ignore me!", "other", "/Users/felisaraneae/Downloads/celeste.webp")
