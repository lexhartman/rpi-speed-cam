import cv2
import time
import math
import numpy as np

class CentroidTracker:
    def __init__(self, max_disappeared=50):
        self.next_object_id = 0
        self.objects = {}  # ID -> centroid
        self.disappeared = {}  # ID -> frames_disappeared
        self.max_disappeared = max_disappeared

    def register(self, centroid):
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, rects):
        if len(rects) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            input_centroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(input_centroids)):
                self.register(input_centroids[i])
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Compute distance matrix between object centroids and input centroids
            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue

                object_id = object_ids[row]
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0
                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            if D.shape[0] >= D.shape[1]:
                for row in unused_rows:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            else:
                for col in unused_cols:
                    self.register(input_centroids[col])

        return self.objects


class SpeedDetector:
    def __init__(self, config=None):
        # Config is a dict or object with line settings
        # line format: [x1, y1, x2, y2]
        self.config = config if config else {}
        self.line1 = self.config.get("line1", [0, 0, 0, 0])
        self.line2 = self.config.get("line2", [0, 0, 0, 0])
        self.real_distance = self.config.get("real_distance_meters", 5.0)
        self.min_area = self.config.get("min_area", 5000)
        
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
        self.tracker = CentroidTracker(max_disappeared=40)
        
        # Track entry/exit times: {object_id: {"entry": timestamp, "exit": timestamp, "speed": speed, "start_pos": (x,y)}}
        self.tracked_data = {} 
        self.previous_centroids = {} # Store previous positions for line crossing logic

    def update_config(self, config):
        self.line1 = config.get("line1", self.line1)
        self.line2 = config.get("line2", self.line2)
        self.real_distance = config.get("real_distance_meters", self.real_distance)
        self.min_area = config.get("min_area", self.min_area)

    def process_frame(self, frame):
        if frame is None:
            return None, []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fgmask = self.fgbg.apply(gray)
        _, fgmask = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)
        fgmask = cv2.dilate(fgmask, None, iterations=2)

        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rects = []
        for c in contours:
            if cv2.contourArea(c) < self.min_area:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            rects.append((x, y, x + w, y + h))
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        objects = self.tracker.update(rects)
        
        new_events = []

        for (object_id, centroid) in objects.items():
            # Get previous position
            prev_centroid = self.previous_centroids.get(object_id)
            
            if prev_centroid is not None:
                # Check crossing Line 1 (Entry)
                if self.check_line_crossing(prev_centroid, centroid, self.line1):
                    if object_id not in self.tracked_data:
                        self.tracked_data[object_id] = {"entry": time.time(), "exit": None, "speed": None}
                        # print(f"Object {object_id} crossed Line 1 at {self.tracked_data[object_id]['entry']}")

                # Check crossing Line 2 (Exit)
                if self.check_line_crossing(prev_centroid, centroid, self.line2):
                    if object_id in self.tracked_data and self.tracked_data[object_id]["entry"] is not None:
                         if self.tracked_data[object_id]["exit"] is None:
                            exit_time = time.time()
                            entry_time = self.tracked_data[object_id]["entry"]
                            time_diff = exit_time - entry_time
                            
                            if time_diff > 0.1: # Min time threshold
                                speed_mps = self.real_distance / time_diff
                                speed_kmh = speed_mps * 3.6
                                
                                self.tracked_data[object_id]["exit"] = exit_time
                                self.tracked_data[object_id]["speed"] = speed_kmh
                                
                                event = {
                                    "speed": round(speed_kmh, 2),
                                    "timestamp": exit_time,
                                    "object_id": object_id,
                                    "frame": frame.copy() # Save the frame of the event
                                }
                                new_events.append(event)
                                # print(f"Object {object_id} Speed: {speed_kmh} km/h")

            # Draw centroid
            cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 0, 255), -1)
            cv2.putText(frame, f"ID {object_id}", (centroid[0] - 10, centroid[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Draw speed if available
            if object_id in self.tracked_data and self.tracked_data[object_id]["speed"]:
                 speed = self.tracked_data[object_id]["speed"]
                 cv2.putText(frame, f"{speed:.1f} km/h", (centroid[0], centroid[1] - 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

        # Update previous centroids
        self.previous_centroids = objects.copy()

        # Draw lines
        cv2.line(frame, (int(self.line1[0]), int(self.line1[1])), (int(self.line1[2]), int(self.line1[3])), (255, 0, 0), 2)
        cv2.line(frame, (int(self.line2[0]), int(self.line2[1])), (int(self.line2[2]), int(self.line2[3])), (0, 0, 255), 2)
        
        return frame, new_events

    def check_line_crossing(self, p1, p2, line):
        # line: [x1, y1, x2, y2]
        # p1: (x, y) previous
        # p2: (x, y) current
        
        # Segment A: p1 -> p2 (Object movement)
        # Segment B: (x1, y1) -> (x2, y2) (Virtual line)
        
        A = (p1[0], p1[1])
        B = (p2[0], p2[1])
        C = (line[0], line[1])
        D = (line[2], line[3])

        return self.intersect(A, B, C, D)

    def ccw(self, A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def intersect(self, A, B, C, D):
        return (self.ccw(A, C, D) != self.ccw(B, C, D)) and (self.ccw(A, B, C) != self.ccw(A, B, D))
