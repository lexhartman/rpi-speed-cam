import unittest
import shutil
import os
import cv2
import numpy as np
import time
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.storage_manager import StorageManager

class TestStorageManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = "tests/data_temp"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_event(self):
        sm = StorageManager(data_dir=self.test_dir, max_disk_usage=90)
        
        # Save an event
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        event = {
            "speed": 50.5,
            "timestamp": time.time(),
            "object_id": 1,
            "frame": frame
        }
        
        path = sm.save_event(event)
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "speed_cam.db")))
        
        # Check DB
        events = sm.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["speed"], 50.5)

if __name__ == '__main__':
    unittest.main()
