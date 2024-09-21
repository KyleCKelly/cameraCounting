import time
import json
import os
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import Label, Frame, simpledialog, filedialog, messagebox
from logger import start_logging

# Configuration
UPDATE_INTERVAL = 2  # Check every 2 seconds
FLASH_DURATION = 1000  # 1 second in milliseconds for flashing red

class Camera:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{ip}/iAPI/apps.cgi"

    def send_request(self):
        """Send a GET request to the API to retrieve the person count data."""
        try:
            response = requests.get(f"{self.base_url}?action=read&path=personcount.default", 
                                    auth=HTTPBasicAuth(self.username, self.password))
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        return ""

    def get_counts(self):
        """Retrieve the in and out counts from the API."""
        try:
            response_text = self.send_request()
            print(f"Response Text from {self.ip}:", response_text)

            if response_text.startswith("Content-Type: text/xml"):
                response_text = response_text.split("\n", 1)[1].strip()

            root = ET.fromstring(response_text)

            in_count = root.find(".//parameter[@name='inCountTotal']").text if root.find(".//parameter[@name='inCountTotal']") is not None else "0"
            out_count = root.find(".//parameter[@name='outCountTotal']").text if root.find(".//parameter[@name='outCountTotal']") is not None else "0"
            currently_in = str(int(in_count) - int(out_count))

            return int(in_count), int(out_count), int(currently_in)

        except ET.ParseError as parse_err:
            print(f"XML parse error occurred: {parse_err}")
            return 0, 0, 0

# GUI Application
class Dashboard:
    def __init__(self, master, cameras, occupancy_limit=None):
        self.master = master
        self.master.title("People Counting Dashboard")
        self.master.configure(bg="#d1d07d")
        self.cameras = cameras
        self.occupancy_limit = occupancy_limit
        self.is_flashing = False  # Track whether we're in a flash period

        # Create the total occupancy display with full width and solid background from top down
        self.total_frame = Frame(master, bg="#72a160", bd=0, relief="ridge")
        self.total_frame.grid(row=0, column=0, columnspan=len(self.cameras), sticky="nsew", padx=0, pady=0)

        self.total_currently_in_label = Label(self.total_frame, text="Current Occupancy: 0", bg="#72a160", fg="white", font=("Helvetica", 24))
        self.total_currently_in_label.pack(fill="x", padx=5, pady=5)

        # Only display occupancy limit if it was provided
        if self.occupancy_limit:
            self.occupancy_limit_label = Label(self.total_frame, text=f"Occupancy Limit: {self.occupancy_limit}", bg="#72a160", fg="white", font=("Helvetica", 12))
            self.occupancy_limit_label.pack(side="bottom", pady=5)
        else:
            self.occupancy_limit_label = None

        # Create camera info frames with pastel orange and updated labels
        self.camera_frames = []
        self.camera_labels = []

        self.create_camera_boxes()
        self.update_counts()

    def create_camera_boxes(self):
        """Create dynamically arranged camera info boxes."""
        num_cameras = len(self.cameras)
        columns = min(num_cameras, 4)
        for i, camera in enumerate(self.cameras):
            frame = Frame(self.master, bg="#FF964F", bd=5, relief="ridge")
            frame.grid(row=(i // columns) + 1, column=i % columns, sticky="nsew", padx=10, pady=10)

            cam_label = {
                'ip': Label(frame, text=f"Camera {i + 1}", bg="#FF964F", fg="white", font=("Helvetica", 12, "bold")),
                'entered': Label(frame, text="Entered: 0", bg="#FF964F", fg="white", font=("Helvetica", 12, "bold")),
                'exited': Label(frame, text="Exited: 0", bg="#FF964F", fg="white", font=("Helvetica", 12, "bold")),
            }
            cam_label['ip'].pack(fill="x", padx=5, pady=5)
            cam_label['entered'].pack(fill="x", padx=5, pady=5)
            cam_label['exited'].pack(fill="x", padx=5, pady=5)

            self.camera_frames.append(frame)
            self.camera_labels.append(cam_label)

        # Dynamically adjust column weight based on the number of cameras
        for i in range(columns):
            self.master.grid_columnconfigure(i, weight=1, uniform="column")

    def update_counts(self):
        total_currently_in = 0

        for i, camera in enumerate(self.cameras):
            entered, exited, currently_in = camera.get_counts()
            total_currently_in += currently_in

            self.camera_labels[i]['entered'].config(text=f"Entered: {entered}")
            self.camera_labels[i]['exited'].config(text=f"Exited: {exited}")

        # Update the total occupancy box
        self.total_currently_in_label.config(text=f"Current Occupancy: {total_currently_in}")

        # Check every 2 seconds and flash red for 1 second if over the limit
        if self.occupancy_limit and total_currently_in > self.occupancy_limit:
            if not self.is_flashing:
                self.flash_red_background()  # Start flashing red for 1 second
                self.is_flashing = True  # Mark that we're in a flash period
                self.master.after(FLASH_DURATION, self.reset_to_green)  # Reset to green after 1 second
        else:
            self.reset_to_green()  # Ensure it's green when under limit

        # Check again in 2 seconds
        self.master.after(UPDATE_INTERVAL * 1000, self.update_counts)

    def flash_red_background(self):
        """Set the background to red when over limit."""
        self.total_frame.config(bg="#eb3b3b")  # Flash red
        self.total_currently_in_label.config(bg="#eb3b3b")
        if self.occupancy_limit_label:
            self.occupancy_limit_label.config(bg="#eb3b3b")

    def reset_to_green(self):
        """Reset the background to green after flashing or if occupancy is under the limit."""
        self.is_flashing = False
        self.total_frame.config(bg="#72a160")  # Set it to green
        self.total_currently_in_label.config(bg="#72a160")
        if self.occupancy_limit_label:
            self.occupancy_limit_label.config(bg="#72a160")

def load_config_file():
    """Prompt user to load a config file and return camera details from the config."""
    config_file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not config_file:
        return None
    
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    cameras = [Camera(cam['ip'], cam['username'], cam['password']) for cam in config_data['cameras']]
    return cameras

def get_camera_details():
    root = tk.Tk()
    root.withdraw()
    
    # Ask if user wants to use a config file
    use_config = messagebox.askyesno("Config File", "Do you want to use a config file?")
    
    if use_config:
        cameras = load_config_file()
        if not cameras:
            messagebox.showerror("Error", "Failed to load config file.")
            return None, None
    else:
        num_cameras = simpledialog.askinteger("Input", "How many cameras are you using?")
        cameras = []
        for i in range(num_cameras):
            ip = simpledialog.askstring("Input", f"Enter IP for Camera {i + 1}:")
            username = simpledialog.askstring("Input", f"Enter Username for Camera {i + 1}:")
            password = simpledialog.askstring("Input", f"Enter Password for Camera {i + 1}:", show="*")
            cameras.append(Camera(ip, username, password))

    occupancy_limit = simpledialog.askinteger("Input", "Enter total room occupancy limit (enter 0 for no limit)", parent=root)
    
    if not occupancy_limit:  # Allow user to skip entering an occupancy limit
        occupancy_limit = None
    
    root.destroy()
    return cameras, occupancy_limit

if __name__ == "__main__":
    cameras, occupancy_limit = get_camera_details()
    if cameras:
        root = tk.Tk()
        app = Dashboard(root, cameras, occupancy_limit)
        start_logging(cameras)
        root.mainloop()