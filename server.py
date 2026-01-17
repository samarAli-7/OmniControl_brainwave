from flask import Flask
import subprocess

app = Flask(__name__)

@app.get("/run")
def run_script():
    subprocess.Popen(["python", "HAND_GESTURE_RECOGNITION/main.py"])
    return "✅ Script triggered!"

if __name__ == "__main__":
    # allow other devices (ESP32) to access it
    app.run(host="0.0.0.0", port=5000)  