import serial
import firebase_admin
from firebase_admin import credentials, db
import time

# 1. Setup Firebase
cred = credentials.Certificate("serviceAccountKey.json") # Download this from Firebase Project Settings
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://omnicontrol-2-default-rtdb.firebaseio.com'
})

# 2. Setup Serial (Check your Arduino IDE for the correct COM port)
ser = serial.Serial('COM3', 9600, timeout=1) 

def update_dashboard():
    nav_state = True
    
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            
            # Handle Ring Finger Toggle (Reset)
            if line == "TOGGLE_NAV":
                nav_state = not nav_state
                db.reference('system/hardware/mouse_nav').set(nav_state)
                print(f"Nav Status Updated: {nav_state}")

            # Handle Thumb (Scroll Lock)
            if line == "SCROLL_LOCK_ACTIVE":
                db.reference('system/hardware/scroll_lock').set(True)
            elif line == "SCROLL_LOCK_OFF":
                db.reference('system/hardware/scroll_lock').set(False)

        # Handle CNN (Example: Logic for when your CNN detects a class)
        # current_gesture = your_cnn_model.predict(frame)
        # db.reference('system/current_gesture').set(current_gesture)
        
        time.sleep(0.01)

if __name__ == "__main__":
    update_dashboard()