import json
import logging
import time
from dotenv import load_dotenv
import mimetypes
import os
import platform
import signal
import random
import sys
import requests
import random

load_dotenv()

# Init globals
SITE = "https://nightlightapp.net/"
API_POINT = f"{SITE}nlapi/"
SESSION = requests.Session()
VERSION = "1.0.0"

USERNAME = os.getenv("USERNAME")

running = True

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
    if (response.status_code == 200):
        print(f"Posted \"{text}\"")
    else:
        print(f"Failed to post \"{text}\"!")

# Afaik there's not a way to get the ID of the comment you need to reply to so you just need to logic it out manually
def findCommentIDs(messageID, author):
    response = SESSION.get(f"{SITE}responses.php", params={"getAllComments": messageID, "author": author}).json()["comments"]
    print(response)
    validIDs = []
    invalidIDs = []
    for i in response:
        print(i["author"]["username"])
        if i["author"]["username"] == USERNAME:
            try:
                replyID = i["comment"]["replyTo"]
                print(f"Reply ID: {replyID}")
                invalidIDs.append(replyID)
            except:
                pass
            pass
        text = i["comment"]["content"]
        print(f"TEXT: {text}")
        if f"@{USERNAME}" in text and "coinflip" in text:
            validIDs.append(i["comment"]["id"])
    for i in invalidIDs:
        try:
            validIDs.remove(i)
        except:
            pass
    print(f"Found valid IDs: {validIDs}")
    return validIDs

def replyToUnreadMessages():
    print("Attempting to get unread messages")
    try:
        response = SESSION.get(f"{API_POINT}user", params={"action": "getUnreadNotifications"}).json()["data"]
        messages = response["new"]
        print(messages)
        for i in messages:
            text = i["content"]
            if (f"@{USERNAME}" in text and not "</strong> commented" in text):
                if ("coinflip" in text):
                    messageID = i["extra"].split("/")
                    messageID = messageID[len(messageID) - 1]
                    print(f"Message ID: {messageID}")
                    for j in findCommentIDs(messageID, i["owner"]):
                        SESSION.post(f"{API_POINT}comment",
                            data={
                            "content": ["heads", "tails"][random.randint(0, 1)],
                            "post": messageID,
                            "replyTo": j
                        })
                    print("coinflip!")
                else:
                    print("Invalid command!")
                    
    except:
        print("Failed to get unread messages!")
        
def checkForUpdateMessage():
    response = SESSION.get(f"{SITE}responses.php", params={"getAllPosts": "girlbot3000", "after": "null", "sort": "newest"}).json()
    for i in response:
        if f"{VERSION}" in i["post"]["content"]:
            return
    createPost(f"Hi! I'm {USERNAME}!\n\nAbout me:\nI'm a bot account by @felisaraneae (v{VERSION})\nI will respond to simple commands when you @ me in comments\n\nCommands:\ncoinflip\n\nMy source: ", "programming", "/Users/felisaraneae/Downloads/profilePicture.png")

def shutdown(signum, frame):
    print("Shutting down...")
    running = False

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

try:
    checkForUpdateMessage()
except:
    pass

exit()

while running:
    time.sleep(60)
    try:
        replyToUnreadMessages()
    except:
        pass

print("Successfully stopped cleanly!")