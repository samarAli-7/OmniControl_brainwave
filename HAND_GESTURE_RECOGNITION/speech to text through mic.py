import pyaudio
import keyboard
import time
import speech_recognition as sr

BRIO_MIC_INDEX = None 

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

HOTKEY = "f8"   

r = sr.Recognizer()

print("✅ Push-to-Talk Typing Ready")
print(f"➡️ Hold {HOTKEY.upper()} to talk")
print(f"⬅️ Release {HOTKEY.upper()} to stop & type")
print("❌ Press ESC to quit\n")

p = pyaudio.PyAudio()

def record_while_key_held():
   
    frames = []

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=BRIO_MIC_INDEX
    )

    print(f"🎧 Recording... (release {HOTKEY.upper()} to stop)")

    while keyboard.is_pressed(HOTKEY):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    return b"".join(frames)

while True:
    if keyboard.is_pressed("esc"):
        print("👋 Exiting...")
        break

  
    keyboard.wait(HOTKEY)

    audio_bytes = record_while_key_held()

    if len(audio_bytes) < 2000:
        print("⚠️ No audio captured.\n")
        time.sleep(0.2)
        continue

    audio = sr.AudioData(audio_bytes, RATE, 2)

    print("🧠 Recognizing...")
    try:
        text = r.recognize_google(audio).strip()
        print("✅ Recognized:", text)

        if text:
            time.sleep(0.2)
            keyboard.write(text + " ")
            print("⌨️ Typed!\n")
        else:
            print("⚠️ Empty result.\n")

    except sr.UnknownValueError:
        print("❌ Could not understand.\n")
    except sr.RequestError as e:
        print("❌ Google STT failed:", e, "\n")

    time.sleep(0.25)

p.terminate()
