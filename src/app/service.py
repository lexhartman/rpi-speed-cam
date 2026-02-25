import threading
import time
import yaml
import logging
import cv2
import os
from src.core import Camera, MockCamera, SpeedDetector, StorageManager, NotificationManager

class SpeedCameraService:
    def __init__(self, config_path="config/config.yaml"):
        self.config_path = config_path
        self.running = False
        self.thread = None
        self.latest_frame = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger("Service")
        self.camera = None
        self.detector = None
        self.storage = None
        self.notifier = None
        
        self.load_config()
        self.init_components()

    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.config = {} # Should ideally use defaults

    def save_config(self, new_config):
        try:
            with open(self.config_path, "w") as f:
                yaml.dump(new_config, f)
            self.config = new_config
            
            # Reload components if needed
            self.detector.update_config(self.config["detection"])
            self.notifier.update_config(self.config["notifications"])
            self.logger.info("Configuration updated.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False

    def init_components(self):
        # Camera
        dev = self.config["camera"]["device_id"]
        w = self.config["camera"]["width"]
        h = self.config["camera"]["height"]
        fps = self.config["camera"]["fps"]
        
        if isinstance(dev, str) and (dev.endswith(".mp4") or dev.endswith(".avi") or dev.endswith(".mkv")):
             self.camera = MockCamera(dev)
        else:
             self.camera = Camera(dev, w, h, fps)
             
        # Detector
        self.detector = SpeedDetector(self.config["detection"])
        
        # Storage
        limit = self.config["limits"].get("max_disk_usage_percent", 90)
        self.storage = StorageManager(max_disk_usage=limit)
        
        # Notifications
        self.notifier = NotificationManager(self.config["notifications"])

    def start(self):
        if self.running:
            return
        
        self.camera.start()
        self.running = True
        self.thread = threading.Thread(target=self.run_loop, daemon=True)
        self.thread.start()
        self.logger.info("Service started.")

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.camera.stop()
        self.logger.info("Service stopped.")

    def run_loop(self):
        while self.running:
            frame = self.camera.get_frame()
            if frame is None:
                time.sleep(0.01)
                continue
            
            # Process frame
            processed_frame, events = self.detector.process_frame(frame)
            
            # Handle events
            if events:
                for event in events:
                    self.handle_event(event)
            
            with self.lock:
                self.latest_frame = processed_frame

    def handle_event(self, event):
        speed = event["speed"]
        limit = self.config["limits"]["speed_limit_kmh"]
        
        self.logger.info(f"Event Detected: {speed} km/h")
        
        # Save event
        path = self.storage.save_event(event)
        
        # Notify if speeding
        if limit > 0 and speed > limit:
            msg = f"Speed Violation! {speed} km/h (Limit: {limit} km/h)"
            self.notifier.notify(msg, path)
            
    def get_latest_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy()
            
    def get_jpeg_frame(self):
        frame = self.get_latest_frame()
        if frame is None:
            return None
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            return None
        return jpeg.tobytes()
