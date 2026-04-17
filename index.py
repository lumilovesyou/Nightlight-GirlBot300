from dotenv import load_dotenv
from datetime import datetime
import mimetypes
import requests
import logging
import random
import signal
import json
import time
import os

load_dotenv()

# Init consts
SITE = "https://nightlightapp.net/"
API_POINT = f"{SITE}nlapi/"
SESSION = requests.Session()
VERSION = os.getenv("VERSION") or "1.0.0"

USERNAME = os.getenv("USERNAME")

running = True

# Set up logging
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
if (not os.path.exists(f"{os.getcwd()}/logs")):
    os.makedirs(f"{os.getcwd()}/logs")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/bot-{timestamp}.log"),
        logging.StreamHandler()
    ]
)
logging.info("Starting bot...")

# Get token
try:
    logging.info("Attempting to get key")
    SESSION.post(f"{SITE}account/login", data={"loginusername": USERNAME, "loginpassword": os.getenv("PASSWORD")})
    if SESSION.cookies.get_dict()["username"] != USERNAME:
        logging.fatal("Failed to get token!")
        exit()
except Exception as e:
    logging.fatal(f"Failed to get token!\n{e}")

# Invalid the previous token (probably a really gross way to do this but I couldn't find an endpoint to grab tokens from)
try:
    logging.info("Attempting to remove tokens")
    grabTokens = SESSION.get(f"{SITE}u/{USERNAME}").text
    grabTokens = json.loads(grabTokens.split("\"loginTokens\":")[1].split("});document.getElementById('notificationdot-notifications')")[0])
    for i in grabTokens:
        if i["device"] == "python-requests/2.25.1" and not i["active"]:
            # Remove old tokens
            SESSION.post(f"{API_POINT}user", params={"action": "invalidateToken"}, json={"tokenId": i["id"]})
except Exception as e:
    logging.error(f"Failed to remove old tokens\n{e}")
    
logging.info("Ready Mr. Stark!")
    
def createPost(text, category="other", filePath=None):
    files = {}
    if filePath and os.path.exists(filePath):
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
    if response.status_code == 200:
        logging.info(f"Posted \"{text}\"")
    else:
        logging.error(f"Failed to post \"{text}\"!\n{response.status_code}\n{response.reason}")

# Afaik there's not a way to get the ID of the comment you need to reply to so you just need to logic it out manually
def findCommentIDs(messageID, author):
    response = SESSION.get(f"{SITE}responses.php", params={"getAllComments": messageID, "author": author}).json()["comments"]
    validIDs = []
    invalidIDs = []
    for i in response:
        if i["author"]["username"] == USERNAME:
            try:
                replyID = i["comment"]["replyTo"]
                invalidIDs.append(replyID)
            except Exception as e:
                pass
            pass
        text = i["comment"]["content"]
        if f"@{USERNAME}" in text and "coinflip" in text:
            validIDs.append(i["comment"]["id"])
    for i in invalidIDs:
        try:
            validIDs.remove(i)
        except Exception as e:
            pass
    return validIDs

def replyToUnreadMessages():
    logging.info("Attempting to get unread messages")
    try:
        response = SESSION.get(f"{API_POINT}user", params={"action": "getUnreadNotifications"}).json()["data"]
        messages = response["new"]
        for i in messages:
            text = i["content"]
            if f"@{USERNAME}" in text and not "</strong> commented" in text:
                if "coinflip" in text:
                    messageID = i["extra"].split("/")
                    messageID = messageID[len(messageID) - 1]
                    for j in findCommentIDs(messageID, i["owner"]):
                        SESSION.post(f"{API_POINT}comment",
                            data={
                            "content": ["heads", "tails"][random.randint(0, 1)],
                            "post": messageID,
                            "replyTo": j
                        })
                        logging.info(f"Replying with coinflip to {messageID} {j}")       
    except Exception as e:
        logging.error(f"Failed to get unread messages!\n{e}")
        
def checkForUpdateMessage():
    response = SESSION.get(f"{SITE}responses.php", params={"getAllPosts": "girlbot3000", "after": "null", "sort": "newest"}).json()
    for i in response:
        if f"{VERSION}" in i["post"]["content"]:
            return
    createPost(f"Hi! I'm {USERNAME}!\n\nAbout me:\nI'm an experimental bot account by @felisaraneae (v{VERSION})\nI will respond to simple commands when you @ me in comments\n\nCommands:\ncoinflip\n\nMy source:\nhttps://github.com/lumilovesyou/Nightlight-GirlBot300", "programming", "./assets/profilePicture.png")

def shutdown(signum, frame):
    logging.info("Shutting down...")
    running = False

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

try:
    checkForUpdateMessage()
except Exception as e:
    logging.error(f"Failed to check update message!\n{e}")

while running:
    time.sleep(60)
    try:
        replyToUnreadMessages()
    except Exception as e:
        logging.error(f"Failed to do a reply loop!\n{e}")

logging("Successfully stopped cleanly!")
