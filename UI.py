#!/usr/bin/env python3
"""
Air Mouse — Hand Gesture System Controller
Uses MediaPipe to track hand gestures and trigger system actions.
Requires: mediapipe, opencv-python, pyautogui, screen-brightness-control, pycaw (Windows) or pactl (Linux)
Install: pip install mediapipe opencv-python pyautogui screen-brightness-control comtypes pycaw
"""

import cv2
import pyautogui
import time
import math
import threading
import subprocess
import platform
import os
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime

# ─── MediaPipe compatibility shim (supports both old 0.9 and new 0.10+) ──────
try:
    import mediapipe as mp
    # Try old API first
    _ = mp.solutions.hands
    MP_OLD_API = True
except AttributeError:
    MP_OLD_API = False
except ImportError:
    raise SystemExit("mediapipe not installed. Run: pip install mediapipe")

# ─── Platform detection ───────────────────────────────────────────────────────
PLATFORM = platform.system()  # 'Windows', 'Linux', 'Darwin'

# ─── Volume control setup ─────────────────────────────────────────────────────
if PLATFORM == "Windows":
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))
        HAS_PYCAW = True
    except Exception:
        HAS_PYCAW = False
        volume_ctrl = None
else:
    HAS_PYCAW = False
    volume_ctrl = None

# ─── Brightness control ───────────────────────────────────────────────────────
try:
    import screen_brightness_control as sbc
    HAS_SBC = True
except Exception:
    HAS_SBC = False

# ─── Config ───────────────────────────────────────────────────────────────────
HOLD_DURATION   = 1.5      # seconds before action fires
COOLDOWN        = 2.0      # seconds between repeated triggers
CAM_INDEX       = 0
SHOW_PREVIEW    = True     # set False to hide camera window

GESTURE_LABELS = {
    "ONE":        "✌ Alt+Tab",
    "PEACE":      "✌ Alt+Tab",
    "FIST":       "✊ Show Desktop",
    "OPEN":       "🖐 Screenshot",
    "THREE":      "3️⃣  Volume Up",
    "FOUR":       "4️⃣  Volume Down",
    "OK":         "👌 Brightness Up",
    "THUMBS_UP":  "👍 Brightness Down",
    "PINCH":      "🤏 Media Play/Pause",
    "CALL":       "🤙 Lock Screen",
}

# ─── Toast Notification Window ────────────────────────────────────────────────
class ToastManager:
    """Shows short floating toast messages in the corner."""
    def __init__(self):
        self._lock = threading.Lock()
        self._queue = []
        self._active = False

    def show(self, message, color="#00ff88", duration=2000):
        threading.Thread(target=self._show, args=(message, color, duration), daemon=True).start()

    def _show(self, message, color, duration):
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.92)
        sw = root.winfo_screenwidth()
        root.geometry(f"+{sw - 360}+60")

        frame = tk.Frame(root, bg="#111111", padx=18, pady=12)
        frame.pack()

        label = tk.Label(
            frame, text=message,
            fg=color, bg="#111111",
            font=("Courier New", 13, "bold"),
            wraplength=300, justify="left"
        )
        label.pack()

        root.after(duration, root.destroy)
        root.mainloop()


# ─── Floating Enable/Disable Button ──────────────────────────────────────────
class ControlPanel:
    """Always-on-top toggle button to enable/disable gesture recognition."""
    def __init__(self, on_toggle):
        self.enabled = True
        self.on_toggle = on_toggle
        self.thread = threading.Thread(target=self._build, daemon=True)
        self.thread.start()

    def _build(self):
        self.root = tk.Tk()
        self.root.title("Air Mouse")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.90)
        self.root.geometry("+20+20")
        self.root.configure(bg="#0a0a0a")

        # Drag support
        self.root.bind("<ButtonPress-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._do_drag)

        self._build_ui()
        self.root.mainloop()

    def _build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        outer = tk.Frame(self.root, bg="#0a0a0a", padx=2, pady=2)
        outer.pack()

        inner = tk.Frame(outer, bg="#1a1a1a", padx=14, pady=10)
        inner.pack()

        title = tk.Label(inner, text="✋ AIR MOUSE", fg="#888888",
                         bg="#1a1a1a", font=("Courier New", 8, "bold"))
        title.pack()

        color   = "#00ff88" if self.enabled else "#ff4455"
        txt     = "● ACTIVE" if self.enabled else "○ PAUSED"
        self.btn = tk.Button(
            inner, text=txt,
            fg=color, bg="#0f0f0f",
            activeforeground=color, activebackground="#1a1a1a",
            font=("Courier New", 11, "bold"),
            relief="flat", bd=0, padx=10, pady=6,
            cursor="hand2",
            command=self._toggle
        )
        self.btn.pack(pady=(4, 0))

    def _toggle(self):
        self.enabled = not self.enabled
        self.on_toggle(self.enabled)
        self._build_ui()

    def _start_drag(self, e):
        self._x, self._y = e.x, e.y

    def _do_drag(self, e):
        dx = e.x - self._x
        dy = e.y - self._y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")


# ─── System Actions ───────────────────────────────────────────────────────────
def volume_up():
    if PLATFORM == "Windows" and HAS_PYCAW:
        cur = volume_ctrl.GetMasterVolumeLevelScalar()
        volume_ctrl.SetMasterVolumeLevelScalar(min(1.0, cur + 0.1), None)
    elif PLATFORM == "Linux":
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"])
    elif PLATFORM == "Darwin":
        subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"])

def volume_down():
    if PLATFORM == "Windows" and HAS_PYCAW:
        cur = volume_ctrl.GetMasterVolumeLevelScalar()
        volume_ctrl.SetMasterVolumeLevelScalar(max(0.0, cur - 0.1), None)
    elif PLATFORM == "Linux":
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"])
    elif PLATFORM == "Darwin":
        subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"])

def brightness_up():
    if HAS_SBC:
        try:
            cur = sbc.get_brightness(display=0)[0]
            sbc.set_brightness(min(100, cur + 10), display=0)
        except Exception:
            pass
    elif PLATFORM == "Linux":
        subprocess.run("xrandr --output $(xrandr | grep ' connected' | head -1 | cut -d' ' -f1) --brightness 1.0", shell=True)

def brightness_down():
    if HAS_SBC:
        try:
            cur = sbc.get_brightness(display=0)[0]
            sbc.set_brightness(max(10, cur - 10), display=0)
        except Exception:
            pass

def take_screenshot():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{ts}.png")
    pyautogui.screenshot(path)
    return path

def lock_screen():
    if PLATFORM == "Windows":
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    elif PLATFORM == "Linux":
        subprocess.run(["loginctl", "lock-session"])
    elif PLATFORM == "Darwin":
        subprocess.run(["pmset", "displaysleepnow"])

def alt_tab():
    pyautogui.hotkey("alt", "tab")

def show_desktop():
    if PLATFORM == "Windows":
        pyautogui.hotkey("win", "d")
    elif PLATFORM == "Linux":
        subprocess.run(["wmctrl", "-k", "on"])
    elif PLATFORM == "Darwin":
        pyautogui.hotkey("f11")

def media_play_pause():
    pyautogui.press("playpause")


# ─── Gesture Detector ─────────────────────────────────────────────────────────
class _FakeResult:
    """Wraps new mediapipe Tasks output to look like old mp.solutions output."""
    def __init__(self, detection_result):
        self.multi_hand_landmarks = None
        if detection_result and detection_result.hand_landmarks:
            # Convert NormalizedLandmarkList-style objects
            self.multi_hand_landmarks = detection_result.hand_landmarks


class GestureDetector:
    def __init__(self):
        if MP_OLD_API:
            self._init_old()
        else:
            self._init_new()

    # ── Old API (mediapipe < 0.10) ────────────────────────────────────────────
    def _init_old(self):
        self._mode = "old"
        self.mp_hands = mp.solutions.hands
        self.hands    = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.7
        )
        self.mp_draw  = mp.solutions.drawing_utils
        self.mp_style = mp.solutions.drawing_styles
        self.HAND_CONNECTIONS = self.mp_hands.HAND_CONNECTIONS

    # ── New API (mediapipe >= 0.10) ───────────────────────────────────────────
    def _init_new(self):
        self._mode = "new"
        from mediapipe.tasks import python as mp_tasks
        from mediapipe.tasks.python import vision as mp_vision
        from mediapipe.tasks.python.vision import HandLandmarkerOptions

        # Download the model if not already present
        model_path = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
        if not os.path.exists(model_path):
            print("[AirMouse] Downloading hand_landmarker.task model (~5 MB)...")
            import urllib.request
            url = ("https://storage.googleapis.com/mediapipe-models/"
                   "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
            urllib.request.urlretrieve(url, model_path)
            print("[AirMouse] Model downloaded.")

        base_opts = mp_tasks.BaseOptions(model_asset_path=model_path)
        opts = HandLandmarkerOptions(
            base_options=base_opts,
            num_hands=1,
            min_hand_detection_confidence=0.75,
            min_hand_presence_confidence=0.75,
            min_tracking_confidence=0.7,
            running_mode=mp_vision.RunningMode.IMAGE,
        )
        self.landmarker = mp_vision.HandLandmarker.create_from_options(opts)
        self.mp_vision  = mp_vision
        self.mp_draw    = None  # drawing done manually for new API

        # Precompute connection pairs for drawing
        # Standard 21-landmark hand connections
        self.HAND_CONNECTIONS = [
            (0,1),(1,2),(2,3),(3,4),
            (0,5),(5,6),(6,7),(7,8),
            (5,9),(9,10),(10,11),(11,12),
            (9,13),(13,14),(14,15),(15,16),
            (13,17),(17,18),(18,19),(19,20),
            (0,17),
        ]

    def detect(self, frame_rgb):
        if self._mode == "old":
            return self.hands.process(frame_rgb)
        else:
            import mediapipe as _mp
            mp_image = _mp.Image(
                image_format=_mp.ImageFormat.SRGB,
                data=frame_rgb
            )
            raw = self.landmarker.detect(mp_image)
            return _FakeResult(raw)

    def landmarks_to_gesture(self, raw_lm):
        """
        Returns a gesture string based on landmark positions.
        Accepts either old NormalizedLandmark objects or new landmark objects.
        Normalises to list of (x, y, z).
        """
        # Normalise to plain tuples
        lm = []
        for p in raw_lm:
            if hasattr(p, 'x'):
                lm.append((p.x, p.y, p.z))
            else:
                lm.append(p)   # already a tuple
        # Tip indices: thumb=4, index=8, middle=12, ring=16, pinky=20
        # MCP indices: index=5, middle=9, ring=13, pinky=17

        def tip(i):   return lm[i]
        def base(i):  return lm[i - 2]

        def finger_up(tip_i):
            return lm[tip_i][1] < lm[tip_i - 2][1]   # tip y < pip y (inverted)

        thumb_tip  = lm[4]
        index_tip  = lm[8]
        middle_tip = lm[12]
        ring_tip   = lm[16]
        pinky_tip  = lm[20]

        idx_up  = finger_up(8)
        mid_up  = finger_up(12)
        rng_up  = finger_up(16)
        pnk_up  = finger_up(20)

        # Thumb: compare x to thumb base for horizontal spread
        thumb_up_flag = lm[4][0] < lm[3][0]  # flipped for mirrored cam

        fingers_up = [idx_up, mid_up, rng_up, pnk_up]
        count = sum(fingers_up)

        # ── FIST: all down ────────────────────────────────────────────────────
        if count == 0 and not thumb_up_flag:
            return "FIST"

        # ── OPEN PALM: all up ─────────────────────────────────────────────────
        if count == 4:
            return "OPEN"

        # ── THUMBS UP: only thumb, fist shape ────────────────────────────────
        if count == 0 and thumb_up_flag:
            return "THUMBS_UP"

        # ── ONE finger (index only) ───────────────────────────────────────────
        if idx_up and not mid_up and not rng_up and not pnk_up:
            return "ONE"

        # ── PEACE / TWO (index + middle) ─────────────────────────────────────
        if idx_up and mid_up and not rng_up and not pnk_up:
            return "PEACE"

        # ── THREE (index + middle + ring) ────────────────────────────────────
        if idx_up and mid_up and rng_up and not pnk_up:
            return "THREE"

        # ── FOUR (all except thumb) ───────────────────────────────────────────
        if idx_up and mid_up and rng_up and pnk_up:
            return "FOUR"

        # ── CALL ME (index + pinky) ──────────────────────────────────────────
        if idx_up and not mid_up and not rng_up and pnk_up:
            return "CALL"

        # ── OK / PINCH (thumb + index close) ─────────────────────────────────
        dist = math.hypot(thumb_tip[0] - index_tip[0], thumb_tip[1] - index_tip[1])
        if dist < 0.07:
            if mid_up and rng_up and pnk_up:
                return "OK"
            return "PINCH"

        return "UNKNOWN"

    def draw(self, frame, result):
        if not result.multi_hand_landmarks:
            return
        if self._mode == "old":
            for hl in result.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, hl,
                    self.HAND_CONNECTIONS,
                    self.mp_style.get_default_hand_landmarks_style(),
                    self.mp_style.get_default_hand_connections_style()
                )
        else:
            # New API: draw manually
            h, w = frame.shape[:2]
            for hand_lms in result.multi_hand_landmarks:
                pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lms]
                for a, b in self.HAND_CONNECTIONS:
                    cv2.line(frame, pts[a], pts[b], (0, 220, 120), 2)
                for pt in pts:
                    cv2.circle(frame, pt, 4, (255, 255, 255), -1)
                    cv2.circle(frame, pt, 4, (0, 180, 90), 1)


# ─── Main Controller ──────────────────────────────────────────────────────────
class AirMouseController:
    def __init__(self):
        self.toast     = ToastManager()
        self.panel     = ControlPanel(self._on_toggle)
        self.detector  = GestureDetector()
        self.enabled   = True

        # Hold-to-fire state
        self.current_gesture  = None
        self.gesture_start    = None
        self.last_fired       = {}   # gesture -> timestamp
        self.fired_this_hold  = False

        self.actions = {
            "PEACE":      (alt_tab,          "Alt+Tab switched window"),
            "ONE":        (alt_tab,          "Alt+Tab switched window"),
            "FIST":       (show_desktop,     "Show Desktop"),
            "OPEN":       (self._screenshot, "Screenshot saved to Desktop"),
            "THREE":      (volume_up,        "Volume +10%"),
            "FOUR":       (volume_down,      "Volume -10%"),
            "OK":         (brightness_up,    "Brightness +10%"),
            "THUMBS_UP":  (brightness_down,  "Brightness -10%"),
            "PINCH":      (media_play_pause, "Play / Pause"),
            "CALL":       (lock_screen,      "Screen Locked"),
        }

        self.GESTURE_COLORS = {
            "PEACE":     "#00ddff",
            "ONE":       "#00ddff",
            "FIST":      "#ff9944",
            "OPEN":      "#aaff44",
            "THREE":     "#ffdd00",
            "FOUR":      "#ff6644",
            "OK":        "#bb88ff",
            "THUMBS_UP": "#ff88cc",
            "PINCH":     "#44ffcc",
            "CALL":      "#ff4444",
        }

    def _on_toggle(self, state):
        self.enabled = state
        msg = "✅ Gestures ENABLED" if state else "⛔ Gestures PAUSED"
        color = "#00ff88" if state else "#ff4455"
        self.toast.show(msg, color=color, duration=1500)

    def _screenshot(self):
        path = take_screenshot()
        return path   # message handled separately

    def run(self):
        cap = cv2.VideoCapture(CAM_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.toast.show("✋ Air Mouse started!\nHold a gesture 1.5s to fire.", duration=3000)

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.detector.detect(rgb)

            gesture = "NONE"
            if self.enabled and result.multi_hand_landmarks:
                hl = result.multi_hand_landmarks[0]
                # Old API: hl has .landmark; New API: hl is already iterable
                raw = hl.landmark if hasattr(hl, "landmark") else hl
                gesture = self.detector.landmarks_to_gesture(raw)
                self.detector.draw(frame, result)
                self._process_gesture(gesture)
            else:
                self._reset_hold()

            if SHOW_PREVIEW:
                self._draw_hud(frame, gesture)
                cv2.imshow("Air Mouse — Preview  [Q to quit]", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        cap.release()
        cv2.destroyAllWindows()

    def _process_gesture(self, gesture):
        now = time.time()

        if gesture == "UNKNOWN" or gesture == "NONE":
            self._reset_hold()
            return

        # New gesture started
        if gesture != self.current_gesture:
            self.current_gesture = gesture
            self.gesture_start   = now
            self.fired_this_hold = False
            return

        # Same gesture held — check if hold threshold reached
        elapsed = now - self.gesture_start
        if elapsed >= HOLD_DURATION and not self.fired_this_hold:
            last = self.last_fired.get(gesture, 0)
            if now - last >= COOLDOWN:
                self._fire(gesture)
                self.last_fired[gesture] = now
                self.fired_this_hold = True

    def _reset_hold(self):
        self.current_gesture  = None
        self.gesture_start    = None
        self.fired_this_hold  = False

    def _fire(self, gesture):
        if gesture not in self.actions:
            return
        fn, msg = self.actions[gesture]
        color = self.GESTURE_COLORS.get(gesture, "#ffffff")

        if gesture == "OPEN":
            path = fn()
            full_msg = f"📸 {msg}\n{os.path.basename(path)}"
        else:
            fn()
            full_msg = f"⚡ {msg}"

        self.toast.show(full_msg, color=color, duration=2200)

    def _draw_hud(self, frame, gesture):
        h, w = frame.shape[:2]
        overlay = frame.copy()

        # Dark top bar
        cv2.rectangle(overlay, (0, 0), (w, 48), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        status = "ACTIVE" if self.enabled else "PAUSED"
        s_color = (0, 255, 136) if self.enabled else (55, 68, 255)
        cv2.putText(frame, f"AIR MOUSE [{status}]", (10, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, s_color, 2)

        # Gesture label
        if gesture not in ("NONE", "UNKNOWN"):
            label = GESTURE_LABELS.get(gesture, gesture)
            cv2.putText(frame, label, (10, h - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

            # Hold progress bar
            if self.gesture_start:
                elapsed  = time.time() - self.gesture_start
                progress = min(elapsed / HOLD_DURATION, 1.0)
                bar_w    = int((w - 20) * progress)
                bar_color = (0, 255, 136) if progress < 1.0 else (0, 220, 255)
                cv2.rectangle(frame, (10, h - 30), (10 + bar_w, h - 14), bar_color, -1)
                cv2.rectangle(frame, (10, h - 30), (w - 10, h - 14), (80, 80, 80), 1)
        else:
            cv2.putText(frame, "No gesture", (10, h - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)

        # Gesture cheatsheet (right side)
        sheet = [
            "GESTURES:",
            "1 finger  → Alt+Tab",
            "Peace     → Alt+Tab",
            "Fist      → Show Desktop",
            "Open hand → Screenshot",
            "3 fingers → Vol Up",
            "4 fingers → Vol Down",
            "OK sign   → Bright Up",
            "Thumbs Up → Bright Down",
            "Pinch     → Play/Pause",
            "Call sign → Lock Screen",
        ]
        for i, line in enumerate(sheet):
            cv2.putText(frame, line, (w - 260, 70 + i * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                        (200, 200, 200) if i > 0 else (0, 200, 255), 1)


# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pyautogui.FAILSAFE = False
    ctrl = AirMouseController()
    ctrl.run()