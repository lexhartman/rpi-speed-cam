import cv2
import time
import logging

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
        self.cap = cv2.VideoCapture(self.source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        if not self.cap.isOpened():
            self.logger.error("Failed to open camera!")
            raise RuntimeError("Camera source could not be opened.")

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
