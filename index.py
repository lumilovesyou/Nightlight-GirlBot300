from datetime import datetime, timezone
import subprocess
import threading
import logging
import signal
import time
import sys
import os

RESTART_DELAY = 10
MAX_RESTARTS = 10

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

try:
    PROCESSES = {
        "bot": {"launch": True, "cmd": [sys.executable, "bot.py"], "process": None},
        "panel": {"launch": bool(os.getenv("WEB_PANEL", "false")), "cmd": [sys.executable, "control-panel.py"], "process": None},
    }
except:
    logging.fatal("[supervisor] Failed to convert env value!")


### Child handling
def pipeLogs(process, name):
    for line in iter(process.stdout.readline, b""):
        line = line.decode().rstrip()
        if line.startswith("SIGNAL:"):
            handleSignal(line[7:], name)
        else:
            logging.info(f"[{name}] {line}")
            
def handleSignal(signal: str, name: str):
    logging.info(f"[supervisor] Signal \"{signal}\" from {name}")
    match signal:
        case "restart bot":
            process = PROCESSES["bot"]["process"]
            if process:
                process.terminate()

def spawn(name):
    entry = PROCESSES[name]
    process = subprocess.Popen(
        entry["cmd"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
    )
    entry["process"] = process
    thread = threading.Thread(target=pipeLogs, args=(process, name), daemon=True)
    thread.start()
    return process

def watch(name):
    global running
    restarts = 0
    while running:
        process = spawn(name)
        logging.info(f"[supervisor] \"{name}\" started with PID {process.pid}")
        process.wait()
        if not running:
            break
        code = process.returncode
        logging.warning(f"[supervisor] Process \"{name}\" exited with code {code}")
        restarts += 1
        if restarts > MAX_RESTARTS:
            logging.fatal(f"[supervisor] Too many restart attempts! Exceeded {MAX_RESTARTS}.")
            running = False
            break
        logging.info(f"[supervisor] Restarting {name} in {RESTART_DELAY} seconds. (Attempt {restarts})")
        time.sleep(RESTART_DELAY)
###


### Handle graceful shutdown
def shutdown(signum, frame):
    global running
    logging.info("[supervisor] Shutting down...")
    running = False
    for name, entry in PROCESSES.items():
        if entry["process"] and entry["process"].poll() is None:
            logging.info(f"[supervisor] terminating {name}")
            entry["process"].terminate()

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)
###


threads = []
for name in PROCESSES:
    thread = threading.Thread(target=watch, args=(name,), daemon=False)
    thread.start()
    threads.append(thread)
    
for thread in threads:
    thread.join()
    
logging.info("[supervisor] Exited cleanly")