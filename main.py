import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import Label, Button, Frame, simpledialog
from logger import start_logging  # Ensure correct import

# Configuration
UPDATE_INTERVAL = 1  # in seconds

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
    def __init__(self, master, cameras):
        self.master = master
        self.master.title("People Counting Dashboard")
        self.master.configure(bg="#002366")
        self.cameras = cameras

        self.frames = []
        self.camera_labels = []

        for i, camera in enumerate(self.cameras):
            frame = Frame(master, bg="black", bd=5, relief="ridge")
            frame.grid(row=0, column=i, sticky="nsew", padx=10, pady=10)

            cam_label = {
                'entered': Label(frame, text=f"Camera {i + 1} Entered: 0", bg="#ffd700", fg="black", font=("Helvetica", 12)),
                'exited': Label(frame, text=f"Camera {i + 1} Exited: 0", bg="#ff0000", fg="white", font=("Helvetica", 12)),
                'currently_in': Label(frame, text=f"Camera {i + 1} Currently In: 0", bg="#00ff00", fg="black", font=("Helvetica", 12))
            }
            cam_label['entered'].pack(fill="x", padx=5, pady=5)
            cam_label['exited'].pack(fill="x", padx=5, pady=5)
            cam_label['currently_in'].pack(fill="x", padx=5, pady=5)

            self.frames.append(frame)
            self.camera_labels.append(cam_label)

        total_frame = Frame(master, bg="black", bd=5, relief="ridge")
        total_frame.grid(row=1, column=0, columnspan=len(self.cameras), sticky="nsew", padx=10, pady=10)

        self.total_entered_label = Label(total_frame, text="Total Entered: 0", bg="#ffd700", fg="black", font=("Helvetica", 16))
        self.total_entered_label.pack(fill="x", padx=5, pady=5)

        self.total_exited_label = Label(total_frame, text="Total Exited: 0", bg="#ff0000", fg="white", font=("Helvetica", 16))
        self.total_exited_label.pack(fill="x", padx=5, pady=5)

        self.total_currently_in_label = Label(total_frame, text="Total Currently In: 0", bg="#00ff00", fg="black", font=("Helvetica", 16))
        self.total_currently_in_label.pack(fill="x", padx=5, pady=5)

        self.reset_button = Button(master, text="Reset", command=self.reset_counts, bg="gray", fg="white", font=("Helvetica", 12))
        self.reset_button.grid(row=2, column=0, columnspan=len(self.cameras), pady=10)

        for i in range(len(self.cameras)):
            master.grid_columnconfigure(i, weight=1, uniform="column")
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)

        self.update_counts()

    def update_counts(self):
        total_entered = 0
        total_exited = 0
        total_currently_in = 0

        for i, camera in enumerate(self.cameras):
            entered, exited, currently_in = camera.get_counts()
            total_entered += entered
            total_exited += exited
            total_currently_in += currently_in

            self.camera_labels[i]['entered'].config(text=f"Camera {i + 1} Entered: {entered}")
            self.camera_labels[i]['exited'].config(text=f"Camera {i + 1} Exited: {exited}")
            self.camera_labels[i]['currently_in'].config(text=f"Camera {i + 1} Currently In: {currently_in}")

        self.total_entered_label.config(text=f"Total Entered: {total_entered}")
        self.total_exited_label.config(text=f"Total Exited: {total_exited}")
        self.total_currently_in_label.config(text=f"Total Currently In: {total_currently_in}")

        self.master.after(UPDATE_INTERVAL * 1000, self.update_counts)

    def reset_counts(self):
        for i in range(len(self.cameras)):
            self.camera_labels[i]['entered'].config(text=f"Camera {i + 1} Entered: 0")
            self.camera_labels[i]['exited'].config(text=f"Camera {i + 1} Exited: 0")
            self.camera_labels[i]['currently_in'].config(text=f"Camera {i + 1} Currently In: 0")

        self.total_entered_label.config(text="Total Entered: 0")
        self.total_exited_label.config(text="Total Exited: 0")
        self.total_currently_in_label.config(text="Total Currently In: 0")


def get_camera_details():
    root = tk.Tk()
    root.withdraw()
    num_cameras = simpledialog.askinteger("Input", "How many cameras are you using?")

    cameras = []
    for i in range(num_cameras):
        ip = simpledialog.askstring("Input", f"Enter IP for Camera {i + 1}:")
        username = simpledialog.askstring("Input", f"Enter Username for Camera {i + 1}:")
        password = simpledialog.askstring("Input", f"Enter Password for Camera {i + 1}:", show="*")
        cameras.append(Camera(ip, username, password))

    root.destroy()
    return cameras


if __name__ == "__main__":
    cameras = get_camera_details()
    root = tk.Tk()
    app = Dashboard(root, cameras)
    start_logging(cameras)  # Correctly start logging
    root.mainloop()