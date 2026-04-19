from dotenv import load_dotenv
from datetime import datetime, timezone
import mimetypes
import requests
import logging
import random
import signal
import json
import time
import os

from scripts import reminders

load_dotenv()

# Init consts
SITE = "https://nightlightapp.net/"
API_POINT = f"{SITE}nlapi/"
SESSION = requests.Session()
VERSION = os.getenv("VERSION") or "1.0.0"
USERNAME = os.getenv("USERNAME")
COMMANDS = {"coinflip": "coinflip", "random": "random (number) (number)", "reminder": "reminder (number) (days/hours/minutes)"}

running = True

# Set up logging
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
os.makedirs(f"{os.getcwd()}/logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/bot-{timestamp}.log"),
        logging.StreamHandler()
    ]
)
logging.info("Starting bot...")

try:
    COOLDOWN = int(os.getenv("COOLDOWN"))
except:
    logging.fatal("Failed to convert env value!")
    exit()

reminderDatabase = reminders.reminderDatabase()

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
        
def createCommentReply(text, messageID, replyID):
    response = SESSION.post(f"{API_POINT}comment",
        data={
        "content": text,
        "post": messageID,
        "replyTo": replyID
    })
    if response.status_code == 200:
        logging.info(f"Replied to {messageID} {replyID} with \"{text}\" ")
    else:
        logging.error(f"Failed to reply to comment {messageID} {replyID} with \"{text}\"!\n{response.status_code}\n{response.reason}")

# Afaik there's not a way to get the ID of the comment you need to reply to so you just need to logic it out manually
def findCommentIDs(messageID, author, valueToFind):
    response = SESSION.get(f"{SITE}responses.php", params={"getAllComments": messageID, "author": author}).json()["comments"]
    validIDs = {}
    invalidIDs = []
    for i in response:
        if i["author"]["username"] == USERNAME:
            try:
                replyID = i["comment"]["replyTo"]
                invalidIDs.append(replyID)
            except:
                pass
            pass
        text = i["comment"]["content"]
        if f"@{USERNAME}" in text and valueToFind in text:
            validIDs[i["comment"]["id"]] = text
    for i in invalidIDs:
        if i in validIDs.keys():
            validIDs.pop(i)
    return validIDs

def replyToUnreadMessages():
    try:
        response = SESSION.get(f"{API_POINT}user", params={"action": "getUnreadNotifications"}).json()["data"]
        messages = response["new"]
        for i in messages:
            text = i["content"].lower()
            if f"@{USERNAME}" in text and not "</strong> commented" in text:
                foundCommand = next((word for word in COMMANDS.keys() if word in text), None)
                if foundCommand:
                    messageID = i["extra"].split("/")
                    messageID = messageID[len(messageID) - 1]
                    for commentID,commentContent in findCommentIDs(messageID, i["owner"], foundCommand).items():
                        try:
                            match foundCommand:
                                case "coinflip":
                                    content = ["heads", "tails"][random.randint(0, 1)]
                                case "random" | "reminder":
                                    commentContent = commentContent.split(" ")
                                    position = commentContent.index(foundCommand)
                                    if foundCommand == "random":
                                        try:
                                            numOne,numTwo = int(commentContent[position + 1]),int(commentContent[position + 2])
                                            if numOne < numTwo:
                                                content = random.randint(numOne, numTwo + 1)
                                            else:
                                                content = random.randint(numTwo, numOne + 1)
                                        except:
                                            content = "Invalid command format"
                                    else:
                                        content = ""
                                        try:
                                            currentTime,remindTime,timeFormat = int(datetime.now(timezone.utc).timestamp()),int(commentContent[position + 1]),commentContent[position + 2]
                                            match timeFormat:
                                                case "second" | "seconds":
                                                    pass
                                                case "minute" | "minutes":
                                                    remindTime *= 60
                                                case "hour" | "hours":
                                                    remindTime *= 3_600
                                                case "day" | "days":
                                                    remindTime *= 86_400
                                                case _:
                                                    content = "Invalid command format"
                                            if content == "":
                                                remindTime = currentTime + remindTime
                                                reminderDatabase.addReminder(messageID, commentID, remindTime)
                                                content = "Reminder added!"
                                        except:
                                            content = "Invalid command format"
                            logging.info(f"Replying to {messageID} {commentID}")
                            createCommentReply(content, messageID, commentID)
                        except:
                            logging.error(f"Failed to generate response for {foundCommand} to {messageID} {commentID}")   
    except Exception as e:
        logging.error(f"Failed to get unread messages!\n{e}")
        
def manageCommitments():
    for _,messageID,commentID,_ in reminderDatabase.checkReminders():
        createCommentReply("Here's your reminder!", messageID, commentID)
       
def formatMessage(text):
    return text.replace("%v", VERSION).replace("%u", USERNAME).replace("%c", "\n".join(COMMANDS.values()))
        
def checkForUpdateMessage():
    response = SESSION.get(f"{SITE}responses.php", params={"getAllPosts": USERNAME, "after": "null", "sort": "newest"}).json()
    for i in response:
        if f"{VERSION}" in i["post"]["content"]:
            return
    
    if os.getenv("UPDATE_MESSAGE"):
        createPost(formatMessage(os.getenv("ABOUT_MESSAGE")), "programming")
    if os.getenv("ABOUT_MESSAGE"):
        createPost(formatMessage(os.getenv("ABOUT_MESSAGE")), "technology", "./assets/profilePicture.png")

def shutdown(signum, frame):
    global running
    logging.info("Shutting down...")
    running = False

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

try:
    checkForUpdateMessage()
except Exception as e:
    logging.error(f"Failed to check update message!\n{e}")

while running:
    time.sleep(COOLDOWN)
    if (running):
        try:
            replyToUnreadMessages()
        except Exception as e:
            logging.error(f"Failed to do replies!\n{e}")
        try:
            manageCommitments()
        except Exception as e:
            logging.error(f"Failed to finish commitments!\n{e}")

logging.info("Successfully stopped cleanly!")
