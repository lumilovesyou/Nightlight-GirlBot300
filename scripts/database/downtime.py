from datetime import datetime, timezone
import sqlite3
import os

class uptimeDatabase():
    def __init__(self, hbInterval, dbPath="/database/uptime.db"):
        dbFullPath = os.getcwd() + dbPath
        dbParentFolder = os.path.dirname(dbFullPath)
        os.makedirs(dbParentFolder, exist_ok=True)
        self.connection = sqlite3.connect(dbFullPath)
        
        self.cursor = self.connection.cursor()
        self._configure()
        self._initDatabase()

        # In seconds
        self.HEARTBEAT_INTERVAL = hbInterval
        self.DOWNTIME_THRESHOLD = 10
        self.WEEK_SECONDS = 7 * 24 * 60 * 60
    
    def _configure(self):
        self.connection.execute("PRAGMA journal_mode=WAL;")
        self.connection.execute("PRAGMA synchronous=NORMAL;")
        
    def _initDatabase(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS heartbeat (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            timestamp INTEGER NOT NULL
        )
        """)
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS downtime (
            timestamp INTEGER NOT NULL,
            duration INTEGER NOT NULL
        )
        """)

        self.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_downtime_timestamp
            ON downtime(timestamp)
        """)
        
        self.connection.commit()
        
    def now(self):
        return int(datetime.now(timezone.utc).timestamp())
    
    def startupCheck(self):
        currentTime = self.now()
        
        self.cursor.execute("""
            SELECT timestamp FROM heartbeat WHERE id = 1
        """)
        
        row = self.cursor.fetchone()

        if not row:
            self.updateHeartbeat()
            return 0
        
        lastHeartbeat = row[0]

        timeGap = currentTime - lastHeartbeat
        downtime = timeGap - self.HEARTBEAT_INTERVAL

        if downtime > self.DOWNTIME_THRESHOLD:
            self.cursor.execute("""
            INSERT INTO downtime (timestamp, duration)
            VALUES (?, ?)
            """, (lastHeartbeat, downtime))

            self.connection.commit()

        self.updateHeartbeat()
        
        return max(downtime, 0)
    
    def updateHeartbeat(self):
        currentTime = self.now()
        
        self.cursor.execute("""
        INSERT OR REPLACE INTO heartbeat (id, timestamp)
        VALUES (1, ?)
        """, (currentTime,))

        self.connection.commit()
        
    def getWeeklyDowntime(self):
        cutoff = int(datetime.now(timezone.utc).timestamp()) - self.WEEK_SECONDS
        
        self.cursor.execute("""
        SELECT COALESCE(SUM(duration), 0)
        FROM downtime
        WHERE timestamp >= ?
        """, (cutoff,))

        return self.cursor.fetchone()[0]
        
    def getWeeklyUptimePercent(self):
        downtime = self.getWeeklyDowntime()
        uptime = 100 * (1 - (downtime / self.WEEK_SECONDS))
        return round(uptime, 5)
    
    def cleanup(self):
        cutOff = int(datetime.now(timezone.utc).timestamp()) - self.WEEK_SECONDS

        self.cursor.execute("""
        DELETE FROM downtime
        WHERE timestamp < ?
        """, (cutOff,))

        self.connection.commit()