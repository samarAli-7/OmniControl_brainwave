import cv2
import mediapipe as mp
import pyautogui
import time
import threading
import tkinter as tk
import screen_brightness_control as sbc
import math
import pyaudio
import speech_recognition as sr
from collections import deque

# =========================
# SPEECH CONFIGURATION
# =========================
BRIO_MIC_INDEX = None 
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
r = sr.Recognizer()
p = pyaudio.PyAudio()

mic_active_event = threading.Event()

# =========================
# GESTURE CONFIGURATION
# =========================
# Increased these to slow down the "Firing" of gestures
ACTION_HOLD_TIME = 0.8  # Was 0.4 - Time you must hold a gesture to trigger it
MIN_ACTION_GAP = 1.0    # Was 0.4 - Minimum wait time between consecutive actions
ALTTAB_HOLD_TIME = 0.5  # Separate faster timer for Alt-Tab

SCREEN_W, SCREEN_H = pyautogui.size()
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

DYNAMIC_THRESHOLD = 1.1
alt_pressed = False
last_tab_time = 0

GESTURE_MAP = {
    (0, 1, 0, 0, 0): "Cursor Mode",
    (1, 1, 0, 0, 0): "Speech to Text", 
    (0, 1, 1, 0, 0): "Victory / Space",
    (0, 1, 1, 1, 0): "Three / Brightness Up",
    (0, 1, 1, 1, 1): "Four / Brightness Down",
    (1, 1, 1, 1, 1): "Open Palm / Snap",
    (0, 0, 0, 0, 0): "Fist / Alt-Tab"
}

# =========================
# STABILITY HELPERS
# =========================
def get_stable_signature(lms):
    def d(p1_idx, p2_idx):
        return math.hypot(lms[p1_idx].x - lms[p2_idx].x, lms[p1_idx].y - lms[p2_idx].y)

    wrist = 0
    finger_indices = [(8, 5), (12, 9), (16, 13), (20, 17)]
    
    thumb_up = 1 if d(4, 17) > d(2, 17) * 1.2 else 0
    sig = [thumb_up]
    
    for tip, mcp in finger_indices:
        is_up = 1 if d(tip, wrist) > d(mcp, wrist) * DYNAMIC_THRESHOLD else 0
        sig.append(is_up)
        
    return tuple(sig)

# =========================
# SPEECH-TO-TEXT WORKER
# =========================
def speech_worker():  
    while True:
        mic_active_event.wait() 
        
        frames = []
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, frames_per_buffer=CHUNK,
                        input_device_index=BRIO_MIC_INDEX)
        
        print("🎤 Mic Recording...")
        while mic_active_event.is_set():
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        audio_bytes = b"".join(frames)
        if len(audio_bytes) > 2000:
            audio = sr.AudioData(audio_bytes, RATE, 2)
            try:
                text = r.recognize_google(audio).strip()
                if text:
                    pyautogui.write(text + " ")
                    print(f"✅ Typed: {text}")
            except Exception as e:
                print(f"❌ STT Error: {e}")
        
        time.sleep(0.1)

# =========================
# GUI
# =========================
class GestureGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 0.85)
        self.root.geometry("300x110+1550+850")
        self.root.configure(bg="#1e1e1e")

        self.label_status = tk.Label(self.root, text="Scanning...", bg="#1e1e1e", fg="#00FF00", font=("Helvetica", 12, "bold"))
        self.label_status.pack(pady=(10, 0))
        
        self.label_note = tk.Label(self.root, text="", bg="#1e1e1e", fg="#AAAAAA", font=("Helvetica", 9))
        self.label_note.pack()

        self.progress_canvas = tk.Canvas(self.root, width=240, height=4, bg="#333333", highlightthickness=0)
        self.progress_canvas.pack(pady=10)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 4, fill="#00FF00", outline="")

    def update_ui(self, name, progress, note=""):
        self.label_status.config(text=name)
        self.label_note.config(text=note)
        self.progress_canvas.coords(self.progress_bar, 0, 0, int(progress * 240), 4)

# =========================
# MAIN DETECTION LOOP
# =========================
def run_detection(gui):
    global alt_pressed, last_tab_time
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, max_num_hands=1, model_complexity=0)
    cap = cv2.VideoCapture(0)

    SMOOTHING = 0.25
    curr_x, curr_y = pyautogui.position()
    current_action = "None"
    action_start_time = time.time()
    last_action_time = 0.0
    sig_buffer = deque(maxlen=5)

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok: break
        frame = cv2.flip(frame, 1)
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        detected = "Scanning..."
        progress = 0
        note = ""

        if results.multi_hand_landmarks:
            lms = results.multi_hand_landmarks[0].landmark
            sig = get_stable_signature(lms)
            sig_buffer.append(sig)
            voted_sig = max(set(sig_buffer), key=sig_buffer.count)

            if voted_sig == (1, 0, 0, 0, 0):
                detected = "Volume Up" if lms[4].y < lms[3].y else "Volume Down"
            else:
                detected = GESTURE_MAP.get(voted_sig, "Unknown")

            # --- SPEECH TO TEXT TRIGGER (STAYS FAST/INSTANT) ---
            if detected == "Speech to Text":
                if not mic_active_event.is_set():
                    mic_active_event.set()
                note = "🔴 RECORDING..."
                progress = 1.0
            else:
                if mic_active_event.is_set():
                    mic_active_event.clear()
                    note = "Processing Audio..."

            # --- CURSOR LOGIC (STAYS FAST) ---
            if detected == "Cursor Mode":
                tx, ty = (lms[8].x - 0.1) * (SCREEN_W / 0.8), (lms[8].y - 0.1) * (SCREEN_H / 0.8)
                curr_x += (tx - curr_x) * SMOOTHING
                curr_y += (ty - curr_y) * SMOOTHING
                pyautogui.moveTo(int(curr_x), int(curr_y), _pause=False)
                if math.hypot(lms[4].x - lms[8].x, lms[4].y - lms[8].y) < 0.04:
                    if time.time() - last_action_time > 0.3:
                        pyautogui.click(); last_action_time = time.time(); note = "Click ✅"

            # --- ACTION LOGIC ---
            if detected != current_action:
                current_action = detected; action_start_time = time.time()
            
            stable_time = time.time() - action_start_time
            since_last = time.time() - last_action_time

            # ALT-TAB LOGIC (USES SEPARATE TIMER)
            if detected == "Fist / Alt-Tab":
                progress = min(stable_time / ALTTAB_HOLD_TIME, 1.0)
                if stable_time >= ALTTAB_HOLD_TIME:
                    if not alt_pressed:
                        pyautogui.keyDown("alt"); alt_pressed = True; pyautogui.press("tab")
                        last_tab_time = time.time(); note = "ALT HELD"
                    elif time.time() - last_tab_time > 1.0: # Tab cycle speed
                        pyautogui.press("tab"); last_tab_time = time.time()
            elif alt_pressed:
                pyautogui.keyUp("alt"); alt_pressed = False; note = "SWITCHED"

            # SLOWED DOWN GESTURES (Victory, Brightness, Snap, Volume)
            elif detected not in ["Unknown", "Scanning...", "Cursor Mode", "Speech to Text"]:
                progress = min(stable_time / ACTION_HOLD_TIME, 1.0)
                if progress == 1.0 and since_last > MIN_ACTION_GAP:
                    if detected == "Victory / Space": pyautogui.press("space")
                    elif "Brightness Up" in detected: sbc.set_brightness(min(sbc.get_brightness()[0]+10, 100))
                    elif "Brightness Down" in detected: sbc.set_brightness(max(sbc.get_brightness()[0]-10, 0))
                    elif "Snap" in detected: pyautogui.screenshot(f"snap_{int(time.time())}.png")
                    elif "Volume Up" in detected: pyautogui.press("volumeup")
                    elif "Volume Down" in detected: pyautogui.press("volumedown")
                    last_action_time = time.time(); note = "FIRED ✅"

        gui.update_ui(detected, progress, note)
        cv2.imshow("Debug Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release(); cv2.destroyAllWindows(); p.terminate()

if __name__ == "__main__":
    app = GestureGUI()
    threading.Thread(target=run_detection, args=(app,), daemon=True).start()
    threading.Thread(target=speech_worker, daemon=True).start()
    app.root.mainloop()