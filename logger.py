# logger.py

import os
import time
from datetime import datetime
import threading
from database import insert_log

class Logger:
    def __init__(self, cameras, log_dir="logs"):
        self.cameras = cameras  # Reference, don't modify
        self.log_dir = log_dir
        self.current_log_file = None
        self.create_log_file()
        self.last_counts = [{'in': 0, 'out': 0} for _ in self.cameras]
        self.logging_threads = []

        for camera in cameras:
            self.start_logging(camera)

    def create_log_file(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        today = datetime.now().strftime("%Y-%m-%d")
        log_filename = os.path.join(self.log_dir, f"log_{today}.txt")
        self.current_log_file = log_filename

        with open(self.current_log_file, "w") as f:
            f.write("--CAMERAS--\n")
            for i, camera in enumerate(self.cameras):
                f.write(f"Camera {i + 1} = {camera.ip}\n")
            f.write("\n--EVENTS--\n")

    def start_logging(self, camera):
        """Start a logging thread for a new camera."""
        thread = threading.Thread(target=self.log_camera_data, args=(camera,), daemon=True)
        thread.start()
        self.logging_threads.append(thread)

    def log_camera_data(self, camera):
        """Log the data for a specific camera."""
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            entered, exited, currently_in = camera.get_counts()

            camera_index = self.cameras.index(camera)

            if entered > self.last_counts[camera_index]['in']:
                log_entry = f"{current_time}, Camera {camera_index + 1}, person entered (Occupancy: {currently_in})\n"
                self.append_to_events_log(log_entry)
                insert_log(current_time, camera.ip, entered, self.last_counts[camera_index]['out'], currently_in)

            if exited > self.last_counts[camera_index]['out']:
                log_entry = f"{current_time}, Camera {camera_index + 1}, person exited (Occupancy: {currently_in})\n"
                self.append_to_events_log(log_entry)
                insert_log(current_time, camera.ip, self.last_counts[camera_index]['in'], exited, currently_in)

            self.last_counts[camera_index] = {'in': entered, 'out': exited}

            time.sleep(1)

    def append_to_events_log(self, entry):
        """Append an entry to the events log section."""
        with open(self.current_log_file, "a") as f:
            f.write(entry)

    def add_camera_to_log(self, camera):
        """Reference the camera but don't append it to self.cameras here!"""
        # Start logging for the new camera
        self.last_counts.append({'in': 0, 'out': 0})  # Initialize last counts for the new camera

        # Append new camera details to the log file
        with open(self.current_log_file, "a") as f:
            f.write(f"Camera {len(self.last_counts)} = {camera.ip}\n")  # Update log with the new camera
        
        self.start_logging(camera)

def start_logging(cameras):
    """Initialize and start logging for the provided cameras."""
    logger = Logger(cameras)
    return logger