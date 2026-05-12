from dotenv import load_dotenv
from scripts.database import downtime, reminders
from datetime import datetime, timezone
from string import Template
from pathlib import Path
import requests
import cherrypy
import os

load_dotenv()

PATH = "./assets/panel/"
SITE = "https://nightlightapp.net/"
API_POINT = f"{SITE}nlapi/"
DOWNTIME_DB = downtime.uptimeDatabase(int(os.getenv("COOLDOWN")))
REMINDER_DB = reminders.reminderDatabase()
INDEX = Template(Path(PATH, "index.html").read_text())
USERNAME = os.getenv("USERNAME")
SESSION = requests.Session()

# Lots of copy-pasted code from bot, will separate it out into its own file next
# Get token
try:
    SESSION.post(f"{SITE}account/login", data={"loginusername": USERNAME, "loginpassword": os.getenv("PASSWORD")})
    if SESSION.cookies.get_dict()["username"] != USERNAME:
        exit()
except Exception as e:
    pass
    
def colouredByPercent(value):
    try:
        value = int(value)
        if value > 99:
            return "green"
        if value > 90:
            return "yellow"
        elif value > 50:
            return "orange"
        else:
            return "red"
    except Exception as e:
        print(e)
        return "white"
    
def formatDate(date):
    return str(date).split(".")[0].split("+")[0]

def getMessageURL(messageID):
    response = SESSION.get(f"{API_POINT}post/{messageID}")
    if response.status_code == 200:
        return response.json()["data"]["author"]["username"]
    return "unknown"
    
def commitmentsTable():
    commitments = REMINDER_DB.getCommitments()
    tableHTML = ""
    for i in commitments:
        tableHTML += f"<tr><td>{i[0]}</td><td>{i[1]}</td><td>{i[2]}</td><td>{formatDate(datetime.fromtimestamp(i[3], timezone.utc))}</td><td><a href=\"{f"https://nightlightapp.net/u/{getMessageURL(i[1])}/{i[1]}"}\" target=\"_blank\">Link</a></td></tr>"
    return tableHTML

def template(html):
    return html.safe_substitute(
        INDEX,
        uptime=DOWNTIME_DB.getWeeklyUptimePercent(),
        colouredUptime=colouredByPercent(
            DOWNTIME_DB.getWeeklyUptimePercent()
        ),
        name=os.getenv("USERNAME"),
        commitmentsTable=commitmentsTable(),
        time=formatDate(datetime.now(timezone.utc))
    )

def sendSignal(text):
    print(f"SIGNAL:{text}")

class controlPanel(object):
    @cherrypy.expose
    def index(self):
        return template(INDEX)
    
    @cherrypy.expose
    def restart_bot(self):
        sendSignal("restart bot")
        return template(INDEX)
    
if __name__ == '__main__':
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 7889
    })
    
    config = {
        '/': {
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './assets/panel'
        }
    }
    cherrypy.quickstart(controlPanel(), "/", config)
