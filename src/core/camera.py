import cv2
import time
import logging
import glob
import os

class Camera:
    def __init__(self, source=0, width=1280, height=720, fps=30):
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.logger = logging.getLogger("Camera")
        
    def start(self):
        self.logger.info(f"Starting camera from source: {self.source}")
        
        # Try configured source first
        if self._try_open(self.source):
            self.logger.info(f"Camera started successfully on {self.source}")
            return

        self.logger.warning(f"Failed to open configured source {self.source}. Starting auto-discovery...")

        # Find all video devices
        devices = sorted(glob.glob('/dev/video*'))
        if not devices:
            self.logger.error("No video devices found in /dev/video*")
            raise RuntimeError("No camera devices available.")

        for dev in devices:
            # Avoid re-trying the same if source was a path string
            if str(dev) == str(self.source):
                continue

            self.logger.info(f"Trying discovered device: {dev}")
            if self._try_open(dev):
                self.logger.info(f"Auto-discovery successful! Using device: {dev}")
                self.source = dev
                return

        self.logger.error("Auto-discovery failed. No working camera found.")
        raise RuntimeError("Camera source could not be opened and auto-discovery failed.")

    def _try_open(self, source):
        try:
            # Open source
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                return False

            # Configure
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, self.fps)

            # Read a test frame to ensure it really works
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                self.cap = cap
                return True
            else:
                cap.release()
                return False
        except Exception as e:
            self.logger.warning(f"Error checking source {source}: {e}")
            return False

    def get_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return None
            
        ret, frame = self.cap.read()
        if not ret:
            self.logger.warning("Failed to read frame.")
            return None
            
        return frame

    def stop(self):
        if self.cap:
            self.cap.release()
            self.logger.info("Camera released.")

class MockCamera(Camera):
    def __init__(self, video_path, loop=True):
        super().__init__(source=video_path)
        self.loop = loop
        
    def get_frame(self):
        frame = super().get_frame()
        if frame is None and self.loop:
            # Restart video
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return super().get_frame()
        return frame
