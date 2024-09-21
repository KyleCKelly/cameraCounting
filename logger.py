import os
import time
from datetime import datetime
import threading
from database import insert_log

class Logger:
    def __init__(self, cameras, log_dir="logs"):
        self.cameras = cameras
        self.log_dir = log_dir
        self.current_log_file = None
        self.create_log_file()
        self.last_counts = [{'in': 0, 'out': 0} for _ in cameras]

    def create_log_file(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        today = datetime.now().strftime("%Y-%m-%d")
        log_filename = os.path.join(self.log_dir, f"log_{today}.txt")
        self.current_log_file = log_filename

        with open(self.current_log_file, "w") as f:
            f.write("Camera IPs:\n")
            for i, camera in enumerate(self.cameras):
                f.write(f"Camera {i + 1} = {camera.ip}\n")
            f.write("\n")

    def log_data(self):
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            with open(self.current_log_file, "a") as f:
                for i, camera in enumerate(self.cameras):
                    entered, exited, currently_in = camera.get_counts()
                    
                    if entered > self.last_counts[i]['in']:
                        log_entry = f"{current_time}, Camera {i + 1}, person entered (Occupancy: {currently_in})\n"
                        f.write(log_entry)
                        insert_log(current_time, camera.ip, entered, self.last_counts[i]['out'], currently_in)

                    if exited > self.last_counts[i]['out']:
                        log_entry = f"{current_time}, Camera {i + 1}, person exited (Occupancy: {currently_in})\n"
                        f.write(log_entry)
                        insert_log(current_time, camera.ip, self.last_counts[i]['in'], exited, currently_in)

                    self.last_counts[i] = {'in': entered, 'out': exited}

            time.sleep(1)

    def check_midnight(self):
        while True: 
            now = datetime.now()
            if now.hour == 0 and now.minute == 0:
                self.create_log_file()
            time.sleep(60)

def start_logging(cameras):
    logger = Logger(cameras)
    threading.Thread(target=logger.log_data, daemon=True).start()
    threading.Thread(target=logger.check_midnight, daemon=True).start()