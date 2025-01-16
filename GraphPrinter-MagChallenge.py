import serial
import threading
import queue
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  
from matplotlib.animation import FuncAnimation

# ============================
# Serial Configuration
# ============================

SERIAL_PORT = 'COM4'  #########
BAUD_RATE = 9600
TIMEOUT = 0.1  

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
except serial.SerialException as e:
    print("Serial port error:", e)
    exit()

# ============================
# Thread & Queue Setup
# ============================

line_queue = queue.Queue()

def serial_reader():
    """
    Continuously read from the serial port and add lines to the queue.
    """
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                line_queue.put(line)
        except Exception as e:
            print("Error reading from serial:", e)

# serial reader in a daemon thread
reader_thread = threading.Thread(target=serial_reader, daemon=True)
reader_thread.start()

# ============================
# Plotting Setup
# ============================

fig = plt.figure(figsize=(20, 20))
ax = fig.add_subplot(111, projection='3d')
ax.set_box_aspect([1, 1, 1])
x_limit = [-100, 100]
y_limit = [-100, 100]
z_limit = [-100, 100]
ax.set_xlim(x_limit)
ax.set_ylim(y_limit)
ax.set_zlim(z_limit)
ax.set_xlabel('X Magnetic Field')
ax.set_ylabel('Y Magnetic Field')
ax.set_zlabel('Z Magnetic Field')
ax.set_title('Real-Time 3D Magnetic Field Visualization')

ax.scatter(0, 0, 0, color='black', marker='x', s=100, label='Origin')
ax.text(0, 0, 0, "  Origin", color='red', fontsize=10)

indicator_text = ax.text2D(0.05, 0.95, "", transform=ax.transAxes, fontsize=14, color='black')

x_data, y_data, z_data = [], [], []
colors = []
cmap = plt.cm.jet  

# Normalization range for magnetic field strength (assumed 0 to 150 miliTeslas)
min_strength = 0
max_strength = 150

scatter = ax.scatter([], [], [], c=[], cmap=cmap, marker='o', s=50)

# Global variable to store the last measured magnetic field strength
last_field_strength = 0.0

# ============================
# Parsing the data from COMs
# ============================

def parse_serial_data(line):
    """
    serial data format (from MagMainCode.ino):
      "JoystickX: <value>, JoystickY: <value>, Voltage: <value>, XMag: <value>, YMag: <value>, ZMag: <value>"
      or
      "JoystickX: <value>, JoystickY: <value>, Voltage: <value>, No magnetic field detected"
    """
    data_dict = {}
    parts = line.split(", ")
    for kv in parts:
        if ": " in kv:
            key, value = kv.split(": ", 1)
            data_dict[key] = value
    return data_dict

# ============================
# Animation Updates
# ============================

def update_plot(frame):
    global last_field_strength, x_data, y_data, z_data, colors, scatter

    hall_active = False

    # Processing all available lines from the queue (non-blocking)
    while not line_queue.empty():
        line = line_queue.get()
        data_dict = parse_serial_data(line)
        # Checks for a valid voltage reading from the Hall Effect Switch
        if "Voltage" in data_dict:
            try:
                voltage = float(data_dict["Voltage"])
            except ValueError:
                voltage = None

            # Activating Allegro hall digital switch sensor logic if voltage is below threshold (1v, v increase as magnetic field decrease)
            if voltage is not None and voltage < 1.0:
                hall_active = True
                # If magnetic field components are available
                if all(k in data_dict for k in ("XMag", "YMag", "ZMag")):
                    try:
                        x_mag = float(data_dict["XMag"])
                        y_mag = float(data_dict["YMag"])
                        z_mag = float(data_dict["ZMag"])
                    except ValueError:
                        x_mag = y_mag = z_mag = 0.0
                else:
                    x_mag = y_mag = z_mag = 0.0

                # Calculates magnetic field strength (magnitude)
                strength = np.sqrt(x_mag**2 + y_mag**2 + z_mag**2)
                last_field_strength = strength

                # the new data point
                x_data.append(x_mag)
                y_data.append(y_mag)
                z_data.append(z_mag)
                # field strength for color mapping
                norm_strength = (strength - min_strength) / (max_strength - min_strength)
                norm_strength = np.clip(norm_strength, 0, 1)
                colors.append(cmap(norm_strength))

                if len(x_data) > 200:
                    x_data = x_data[-200:]
                    y_data = y_data[-200:]
                    z_data = z_data[-200:]
                    colors = colors[-200:]
    indicator_text.set_text(
        f"Hall: {'Active' if hall_active else 'Inactive'}    "
        f"Magnetic Field Strength: {last_field_strength:.2f}"
    )

    if scatter:
        scatter.remove()
    scatter = ax.scatter(np.array(x_data), np.array(y_data), np.array(z_data),
                         c=colors, cmap=cmap, marker='o', s=50)
    
    return scatter,

# ============================
# Animation Setup
# ============================

ani = FuncAnimation(fig, update_plot, interval=500)

# Display the plot (this call blocks until the window is closed)
plt.show()

ser.close()
