from datetime import datetime, timezone
import sqlite3
import os

class reminderDatabase():
    def __init__(self, dbPath="/database/reminders.db"):
        dbFullPath = os.getcwd() + dbPath
        dbParentFolder = os.path.dirname(dbFullPath)
        os.makedirs(dbParentFolder, exist_ok=True)
        self.connection = sqlite3.connect(dbFullPath)
        
        self.cursor = self.connection.cursor()
        self._configure()
        self._initDatabase()
        
    def _initDatabase(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY,
            message_id TEXT,
            comment_id TEXT,
            remind_at INTEGER
        )
        """)
        self.cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_remind_at
        ON reminders(remind_at)
        """)
        self.connection.commit()
    
    def _configure(self):
        self.connection.execute("PRAGMA journal_mode=WAL;")
        self.connection.execute("PRAGMA synchronous=NORMAL;")
    
    def addReminder(self, messageID, commentID, time):
        self.cursor.execute("""
        INSERT INTO reminders (message_id, comment_id, remind_at)
        VALUES (?, ?, ?)
        """, (messageID, commentID, time))
        self.connection.commit() 
    
    def checkReminders(self):
        currentTime = int(datetime.now(timezone.utc).timestamp())
        
        with self.connection:
            self.cursor.execute("""
            SELECT * FROM reminders WHERE remind_at <= ?
            """, (currentTime,))
            dueReminders = self.cursor.fetchall()
            
            self.cursor.execute("""
            DELETE FROM reminders WHERE remind_at <= ?
            """, (currentTime,))
            
        return dueReminders