# People Counting Dashboard

This is a **People Counting Dashboard** built with Python and Tkinter. The dashboard communicates with cameras via API to count the number of people entering and exiting a space in real-time. The occupancy limit can be set by the user, and the dashboard will visually indicate when the limit is exceeded.

## Features

- **Real-time counting** of people entering and exiting through connected cameras.
- **Configurable occupancy limit** with visual flashing alerts when the limit is exceeded.
- **Dynamic dashboard layout** that updates when new cameras are added.
- **Logging** of camera events to a text file and SQLite database.
- **Support for multiple cameras** and the ability to add new cameras dynamically at runtime.
- **Config file support** to load camera details automatically.
- **Export config support** to generate new config files based on current setup
- **Remove cameras** to take cameras off of the dashboard
- **Manual count reset** to send API calls to reset the counts for all cameras at once

## Requirements

- Python 3.7 or later
- Tkinter (for GUI)
- `requests` (for API communication)
- SQLite3 (for logging)

To install dependencies, run:
bash
pip install requests

Clone the repository:
bash
git clone https://github.com/yourusername/cameraCounting.git
cd cameraCounting

On startup, you can either:

Manually input camera IPs and credentials, or
Load a JSON config file containing camera information.

The dashboard will show the current occupancy, with separate boxes for each camera showing entry and exit counts.

Optionally set a total occupancy limit. The dashboard will flash red when the limit is exceeded.

Run the main Python file to start the dashboard:
bash
python main.py

JSON Config Format

You can load a config file with the following format to automatically load camera details:

json

{
"cameras": [
{
"ip": "<ip>",
"username": "<user>",
"password": "<pass>"
},
{
"ip": "<ip>",
"username": "<user>",
"password": "<pass>"
}
]
}

Features in Detail
Dynamic Camera Addition

Click the Add Camera button on the dashboard to add a new camera during runtime. The camera will be dynamically added to the dashboard and the logger will update accordingly.
Logging

Camera events (entries and exits) are logged in both:

    A daily text log file (located in the logs folder), and
    An SQLite database (people_counting.db).

Alerts

If an occupancy limit is set, the top of the dashboard will flash red when the current total occupancy exceeds the limit. The flashing will stop when occupancy falls back below the limit.
Logging Format

Each log file is saved in the logs/ directory and follows this format:
Camera IPs:
Camera 1 = IP
Camera 2 = IP

23:05:03, Camera 1, person entered (Occupancy: X)
23:06:33, Camera 1, person exited (Occupancy: X-1)
23:07:12, Camera 2, person entered (Occupancy: X+1)
