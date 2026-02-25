import sqlite3
import os
import shutil
import logging
import time
from datetime import datetime
import cv2

class StorageManager:
    def __init__(self, data_dir="data", max_disk_usage=90):
        self.data_dir = data_dir
        self.images_dir = os.path.join(data_dir, "images")
        self.db_path = os.path.join(data_dir, "speed_cam.db")
        self.max_disk_usage = max_disk_usage
        
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
            
        self.init_db()
        self.logger = logging.getLogger("StorageManager")

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS events
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp REAL, 
                      speed REAL, 
                      image_path TEXT, 
                      object_id INTEGER)''')
        conn.commit()
        conn.close()

    def save_event(self, event):
        # event: {speed, timestamp, object_id, frame}
        ts = event["timestamp"]
        dt = datetime.fromtimestamp(ts)
        filename = f"{dt.strftime('%Y-%m-%d_%H-%M-%S')}_{int(event['speed'])}kmh.jpg"
        filepath = os.path.join(self.images_dir, filename)
        
        cv2.imwrite(filepath, event["frame"])
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO events (timestamp, speed, image_path, object_id) VALUES (?, ?, ?, ?)",
                  (ts, event["speed"], filename, event["object_id"]))
        conn.commit()
        conn.close()
        
        self.check_disk_usage()
        return filepath

    def get_events(self, limit=50, offset=0):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def check_disk_usage(self):
        try:
            total, used, free = shutil.disk_usage(self.data_dir)
            percent_used = (used / total) * 100
            
            if percent_used > self.max_disk_usage:
                self.logger.warning(f"Disk usage {percent_used:.1f}% > {self.max_disk_usage}%. Cleaning up...")
                self.cleanup_old_events()
        except Exception as e:
            self.logger.error(f"Error checking disk usage: {e}")

    def cleanup_old_events(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get oldest events
        c.execute("SELECT id, image_path FROM events ORDER BY timestamp ASC LIMIT 50")
        rows = c.fetchall()
        
        for row in rows:
            try:
                full_path = os.path.join(self.images_dir, row["image_path"])
                if os.path.exists(full_path):
                    os.remove(full_path)
            except OSError as e:
                self.logger.error(f"Error deleting file {row['image_path']}: {e}")
                pass
            c.execute("DELETE FROM events WHERE id=?", (row["id"],))
            
        conn.commit()
        conn.close()
        self.logger.info(f"Deleted {len(rows)} old events.")
