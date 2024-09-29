import time
import json
import os
import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import Label, Frame, Button, simpledialog, filedialog, messagebox
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

    def reset_counts(self):
        """Send a POST request to reset the camera counts."""
        reset_xml = '<app name="personcount"><instance name="default"><parameter name="manualReset">true</parameter></instance></app>'
        try:
            response = requests.post(f"{self.base_url}?action=Update", 
                                     auth=HTTPBasicAuth(self.username, self.password), 
                                     data=reset_xml, 
                                     headers={"Content-Type": "text/xml"})
            response.raise_for_status()
            print(f"Successfully reset counts for camera at {self.ip}")
        except requests.exceptions.RequestException as req_err:
            print(f"Failed to reset counts for camera at {self.ip}: {req_err}")

# GUI Application
class Dashboard:
    def __init__(self, master, cameras, occupancy_limit=None, logger=None):
        self.master = master
        self.master.title("People Counting Dashboard")
        self.master.configure(bg="#d1d07d")  # Pastel yellow background

        self.cameras = cameras  # This is the main list of cameras
        self.occupancy_limit = occupancy_limit
        self.logger = logger
        self.is_flashing = False

        # Create a grid system to make resizing responsive
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(2, weight=1)

        # Create the total occupancy display at the top
        self.total_frame = Frame(master, bg="#72a160", bd=0, relief="flat")
        self.total_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(10, 0))
        self.total_frame.columnconfigure(0, weight=1)

        self.total_currently_in_label = Label(self.total_frame, text="Current Occupancy: 0", bg="#72a160", fg="white", font=("Helvetica", 24))
        self.total_currently_in_label.grid(row=0, column=0, sticky="ew")

        if self.occupancy_limit:
            self.occupancy_limit_label = Label(self.total_frame, text=f"Occupancy Limit: {self.occupancy_limit}", bg="#72a160", fg="white", font=("Helvetica", 12))
            self.occupancy_limit_label.grid(row=1, column=0, pady=5, sticky="ew")
        else:
            self.occupancy_limit_label = None

        # White line separator
        self.separator = Frame(master, bg="white", height=2)
        self.separator.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10, 10))

        # Camera and buttons
        self.camera_frames = []
        self.camera_labels = []
        self.add_camera_frame = None

        # Initialize with any provided cameras
        self.create_camera_boxes()

        # Buttons at the bottom
        self.create_bottom_buttons()

        # Start updating the camera data every UPDATE_INTERVAL
        self.update_counts()

    def create_camera_boxes(self):
        """Create camera boxes and ensure the 'Add Camera' button is properly placed."""
        # Clear previous camera frames
        for frame in self.camera_frames:
            frame.grid_forget()
        self.camera_frames.clear()
        self.camera_labels.clear()

        # Clear the "Add Camera" button
        if self.add_camera_frame:
            self.add_camera_frame.grid_forget()

        num_cameras = len(self.cameras)
        columns = min(num_cameras + 1, 4)

        # Configure grid columns to resize dynamically
        for col in range(columns):
            self.master.columnconfigure(col, weight=1)

        # Add camera boxes with rounded corners and no border
        for i, camera in enumerate(self.cameras):
            row = (i // columns) + 2
            column = i % columns

            frame = Frame(self.master, bg="#FF964F", bd=0, relief="flat")
            frame.grid(row=row, column=column, sticky="nsew", padx=10, pady=10)
            frame.grid_propagate(False)
            frame.config(height=100, width=180)
            frame.grid_columnconfigure(0, weight=1)

            cam_label = {
                'ip': Label(frame, text=f"Camera {i + 1}", bg="#FF964F", fg="white", font=("Helvetica", 12, "bold")),
                'entered': Label(frame, text="Entered: 0", bg="#FF964F", fg="white", font=("Helvetica", 12, "bold")),
                'exited': Label(frame, text="Exited: 0", bg="#FF964F", fg="white", font=("Helvetica", 12, "bold")),
            }
            cam_label['ip'].pack(fill="x", padx=5, pady=5)
            cam_label['entered'].pack(fill="x", padx=5, pady=5)
            cam_label['exited'].pack(fill="x", padx=5, pady=5)

            # Add the "Remove" button inside each camera box
            remove_button = Button(frame, text="Remove", bg="red", fg="white", command=lambda idx=i: self.remove_camera(idx))
            remove_button.pack(side="bottom", fill="x", padx=5, pady=5)

            self.camera_frames.append(frame)
            self.camera_labels.append(cam_label)

        # Add the "Add Camera" button in the next available slot
        self.add_camera_button()

    def add_camera_button(self):
        """Add a button for adding a new camera in the next available slot."""
        num_cameras = len(self.cameras)
        columns = min(num_cameras + 1, 4)

        row = (num_cameras // columns) + 2
        column = num_cameras % columns

        self.add_camera_frame = Frame(self.master, bg="#FF964F", bd=0, relief="flat")
        self.add_camera_frame.grid(row=row, column=column, sticky="nsew", padx=10, pady=10)
        self.add_camera_frame.grid_propagate(False)
        self.add_camera_frame.config(height=100, width=180)

        add_camera_label = Label(self.add_camera_frame, text="+", bg="#FF964F", fg="white", font=("Helvetica", 36, "bold"))
        add_camera_label.pack(fill="both", expand=True)

        add_camera_button = Button(self.add_camera_frame, text="New Camera", command=self.add_camera)
        add_camera_button.pack(fill="x", padx=5, pady=5)

    def add_camera(self):
        """Prompt the user to add a new camera."""
        ip = simpledialog.askstring("Input", "Enter IP for new Camera:")
        username = simpledialog.askstring("Input", "Enter Username for new Camera:")
        password = simpledialog.askstring("Input", "Enter Password for new Camera:", show="*")

        if ip and username and password:
            new_camera = Camera(ip, username, password)

            # Prevent adding duplicate cameras
            self.cameras.append(new_camera)
            self.create_camera_boxes()

            # Notify logger to update log for the new camera
            if self.logger:
                self.logger.add_camera_to_log(new_camera)

    def remove_camera(self, index):
        """Remove a camera from the dashboard."""
        del self.cameras[index]
        self.create_camera_boxes()

    def export_config(self):
        """Export the current camera configuration to a JSON file."""
        config_data = {
            "cameras": [
                {
                    "ip": camera.ip,
                    "username": camera.username,
                    "password": camera.password
                } for camera in self.cameras
            ]
        }
        config_file_path = os.path.join(os.getcwd(), 'camera_config.json')
        with open(config_file_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=4)
        messagebox.showinfo("Export Config", f"Configuration exported to {config_file_path}")

    def update_counts(self):
        """Update the counts of entered, exited, and currently in for all cameras."""
        total_currently_in = 0

        for i, camera in enumerate(self.cameras):
            entered, exited, currently_in = camera.get_counts()
            total_currently_in += currently_in

            if i < len(self.camera_labels):
                self.camera_labels[i]['entered'].config(text=f"Entered: {entered}")
                self.camera_labels[i]['exited'].config(text=f"Exited: {exited}")

        # Update the total occupancy box
        self.total_currently_in_label.config(text=f"Current Occupancy: {total_currently_in}")

        # Flash red if over limit
        if self.occupancy_limit and total_currently_in > self.occupancy_limit:
            if not self.is_flashing:
                self.flash_red_background()
                self.is_flashing = True
                self.master.after(FLASH_DURATION, self.reset_to_green)
        else:
            self.reset_to_green()

        # Schedule the next update
        self.master.after(UPDATE_INTERVAL * 1000, self.update_counts)

    def flash_red_background(self):
        """Set the background to red when over limit."""
        self.total_frame.config(bg="#eb3b3b")
        self.total_currently_in_label.config(bg="#eb3b3b")
        if self.occupancy_limit_label:
            self.occupancy_limit_label.config(bg="#eb3b3b")

    def reset_to_green(self):
        """Reset the background to green after flashing or if occupancy is under the limit."""
        self.is_flashing = False
        self.total_frame.config(bg="#72a160")
        self.total_currently_in_label.config(bg="#72a160")
        if self.occupancy_limit_label:
            self.occupancy_limit_label.config(bg="#72a160")

    def reset_all_camera_counts(self):
        """Reset counts for all initialized cameras and log the reset."""
        for i, camera in enumerate(self.cameras):
            camera.reset_counts()
            # Log the reset action
            current_time = time.strftime("%H:%M:%S", time.localtime())
            log_entry = f"{current_time}, Camera {i + 1} reset.\n"
            self.logger.append_to_events_log(log_entry)
            print(f"Camera {i + 1} reset at {current_time}.")

    def create_bottom_buttons(self):
        """Create buttons at the bottom of the dashboard."""
        button_frame = Frame(self.master, bg="#d1d07d", bd=0)
        button_frame.grid(row=10, column=0, columnspan=4, pady=20)

        # Rounded buttons in darker gray with white text
        button_style = {"bg": "#4D4D4D", "fg": "white", "font": ("Helvetica", 12), "relief": "flat"}

        # Export Config Button
        export_button = Button(button_frame, text="Export Config", command=self.export_config, **button_style)
        export_button.grid(row=0, column=0, padx=10)

        # Reset Counts Button
        reset_button = Button(button_frame, text="Reset Counts", command=self.reset_all_camera_counts, **button_style)
        reset_button.grid(row=0, column=1, padx=10)

        # Set Occupancy Limit Button
        occupancy_button = Button(button_frame, text="Occupancy Limit", command=self.set_occupancy_limit, **button_style)
        occupancy_button.grid(row=0, column=2, padx=10)

    def set_occupancy_limit(self):
        """Prompt to set a new occupancy limit."""
        new_limit = simpledialog.askinteger("Input", "Enter new occupancy limit:", parent=self.master)
        if new_limit is not None:
            self.occupancy_limit = new_limit
            if self.occupancy_limit_label:
                self.occupancy_limit_label.config(text=f"Occupancy Limit: {self.occupancy_limit}")

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
        
        # Loop for the specified number of cameras
        for i in range(num_cameras):
            ip = simpledialog.askstring("Input", f"Enter IP for Camera {i + 1}:")
            username = simpledialog.askstring("Input", f"Enter Username for Camera {i + 1}:")
            password = simpledialog.askstring("Input", f"Enter Password for Camera {i + 1}:", show="*")
            
            if ip and username and password:
                cameras.append(Camera(ip, username, password))
            else:
                messagebox.showerror("Error", f"Invalid details for Camera {i + 1}. Please try again.")
                return None, None  # If any field is missing, exit without saving

    occupancy_limit = simpledialog.askinteger("Input", "Enter total room occupancy limit (enter 0 for no limit)", parent=root)
    
    if not occupancy_limit:  # Allow user to skip entering an occupancy limit
        occupancy_limit = None
    
    root.destroy()
    return cameras, occupancy_limit

if __name__ == "__main__":
    cameras, occupancy_limit = get_camera_details()
    if cameras:
        root = tk.Tk()
        root.title("People Counting Dashboard")
        logger = start_logging(cameras)  # Get logger reference
        app = Dashboard(root, cameras, occupancy_limit, logger)
        root.mainloop()
    else:
        print("No cameras were loaded or created.")