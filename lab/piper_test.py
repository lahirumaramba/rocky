import subprocess
import os
import signal
import sys

# Configuration
PIPER_PATH = "./piper/piper"  # Path to your binary
MODEL_PATH = "en_US-lessac-low.onnx"
SAMPLE_RATE = "16000"

class PiperTTS:
    def __init__(self):
        # Start Piper process: Text in -> Raw Audio out -> aplay
        # We use bufsize=1 to ensure text is sent immediately
        self.process = subprocess.Popen(
            f"{PIPER_PATH} --model {MODEL_PATH} --output_raw | aplay -r {SAMPLE_RATE} -f S16_LE -t raw",
            shell=True,
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL, # Hide Piper's logs to keep terminal clean
            text=True,
            bufsize=1
        )

    def speak(self, text):
        if self.process.poll() is None: # Check if process is still running
            self.process.stdin.write(text + "\n")
            self.process.stdin.flush()

    def stop(self):
        self.process.terminate()
        os.system("pkill aplay") # Ensure audio stops immediately

# --- Usage ---
tts = PiperTTS()

try:
    print("TTS Engine Ready. Type your message and hit Enter.")
    print("Press Ctrl+C to exit.")
    while True:
        user_input = input("Say: ")
        tts.speak(user_input)
except KeyboardInterrupt:
    tts.stop()
    print("\nShutting down...")
