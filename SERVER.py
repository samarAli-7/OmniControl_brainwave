import socket
import csv
import pyautogui
import time
from datetime import datetime

# ========== CONFIGURATION ==========
UDP_IP = "0.0.0.0"
UDP_PORT = 5000


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0               

# Mouse sensitivity (pixels per deg/s)
SENSITIVITY = 0.8

# Exponential smoothing (1.0 = no smoothing)
SMOOTHING = 0.8

# Movement threshold (dead zone)
THRESHOLD = 5.0

# Which gyro axes control X and Y
X_AXIS = 'gz'
Y_AXIS = 'gy'

# Reverse direction if needed
REVERSE_X = True
REVERSE_Y = True

# Scroll sensitivity (for future scroll mode)
SCROLL_SENSITIVITY = 10


EXPECT_SCROLL_MODE = False
# ====================================

# CSV setup
csv_filename = f"imu_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
csv_file = open(csv_filename, 'w', newline='')
csv_writer = csv.writer(csv_file)

if EXPECT_SCROLL_MODE:
    csv_writer.writerow(["ax","ay","az","gx","gy","gz","left_click","right_click","scroll_mode"])
else:
    csv_writer.writerow(["ax","ay","az","gx","gy","gz","left_click","right_click"])

print(f"Listening on UDP {UDP_PORT}...")
print(f"Saving to {csv_filename}")
print(f"Mouse sensitivity: {SENSITIVITY}")
print(f"Smoothing: {SMOOTHING}")
print(f"Threshold: {THRESHOLD}")
print("-" * 50)

# UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(None)

# Smoothing state
smooth_x = 0.0
smooth_y = 0.0

# Button state for press/hold/release
last_left = False
last_right = False

try:
    while True:
        data, addr = sock.recvfrom(1024)
        decoded = data.decode().strip()
        if not decoded:
            continue

        parts = decoded.split(',')
        if len(parts) == 8:
            ax, ay, az, gx, gy, gz, left, right = map(float, parts)
            scroll_mode = 0
            has_scroll = False
        elif len(parts) == 9:
            ax, ay, az, gx, gy, gz, left, right, scroll_mode = map(float, parts)
            has_scroll = True
        else:
            print(f"Warning: unexpected format ({len(parts)} fields): {decoded}")
            continue

        # ----- Get raw movement values from selected axes -----
        raw_x = locals()[X_AXIS]
        raw_y = locals()[Y_AXIS]

        # ----- Exponential smoothing (low‑pass filter) -----
        smooth_x = SMOOTHING * raw_x + (1 - SMOOTHING) * smooth_x
        smooth_y = SMOOTHING * raw_y + (1 - SMOOTHING) * smooth_y

        # ----- Apply threshold (dead zone) -----
        dx = smooth_x * SENSITIVITY
        dy = smooth_y * SENSITIVITY
        if abs(smooth_x) < THRESHOLD:
            dx = 0
        if abs(smooth_y) < THRESHOLD:
            dy = 0

        if REVERSE_X:
            dx = -dx
        if REVERSE_Y:
            dy = -dy

        # ----- Apply mouse movement or scroll -----
        if has_scroll and scroll_mode == 1:
            scroll_amount = int(dy * SCROLL_SENSITIVITY)
            if scroll_amount != 0:
                pyautogui.scroll(scroll_amount)
        else:
            if dx != 0 or dy != 0:
                pyautogui.moveRel(dx, dy)

        # ----- Mouse button handling (press/hold/release for dragging) -----
        left_now = bool(left)
        right_now = bool(right)
        
        # Left button: press down when touch starts, release when touch ends
        if left_now and not last_left:
            pyautogui.mouseDown(button='left')
        if not left_now and last_left:
            pyautogui.mouseUp(button='left')
        
        # Right button
        if right_now and not last_right:
            pyautogui.mouseDown(button='right')
        if not right_now and last_right:
            pyautogui.mouseUp(button='right')
        
        last_left = left_now
        last_right = right_now

        # ----- Save to CSV (raw values) -----
        if has_scroll:
            csv_writer.writerow([ax, ay, az, gx, gy, gz, int(left), int(right), int(scroll_mode)])
        else:
            csv_writer.writerow([ax, ay, az, gx, gy, gz, int(left), int(right)])
        csv_file.flush()

except KeyboardInterrupt:
    print("\nStopping server...")
    csv_file.close()
    sock.close()