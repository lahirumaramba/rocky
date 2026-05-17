import subprocess
import os
import sys
import time
import argparse
import threading
from PIL import Image, ImageDraw, ImageFont

# Add Driver path for WhisPlay
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Driver")))
from WhisPlay import WhisPlayBoard

# --- Constants & Defaults ---
PIPER_DIR = os.path.expanduser("~/piper")
PIPER_PATH = os.path.join(PIPER_DIR, "piper/piper")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

VOICES = {
    "low": {"model": "en_US-lessac-low.onnx", "rate": "16000"},
    "medium": {"model": "en_US-lessac-medium.onnx", "rate": "22050"},
    "rocky": {"model": "rocky_model.onnx", "rate": "16000"}
}

class PiperTTS:
    def __init__(self, quality, epoch=None):
        voice = VOICES.get(quality, VOICES["medium"])
        model_name = voice["model"]
        
        if quality == "rocky" and epoch:
            model_name = f"rocky_model_{epoch}.onnx"
            
        self.model_path = os.path.join(PIPER_DIR, model_name)
        
        if not os.path.exists(self.model_path):
            print(f"❌ Model not found: {self.model_path}")
            sys.exit(1)
            
        self.sample_rate = voice["rate"]
        
        # Start Piper process
        print(f"Loading model: {self.model_path}")
        self.piper_proc = subprocess.Popen(
            [PIPER_PATH, "--model", self.model_path, "--output_raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Start aplay process to play Piper's output
        self.aplay_proc = subprocess.Popen(
            ["aplay", "-r", self.sample_rate, "-f", "S16_LE", "-t", "raw"],
            stdin=self.piper_proc.stdout,
            stderr=subprocess.DEVNULL
        )
        
        # Thread to monitor Piper's stderr for benchmarks
        self.bench_thread = threading.Thread(target=self._monitor_benchmarks, daemon=True)
        self.bench_thread.start()
        
        self.last_sent_time = None

    def _monitor_benchmarks(self):
        """Read Piper's stderr to extract and print timing information."""
        for line in self.piper_proc.stderr:
            line = line.strip()
            if "sec" in line: # Usually Piper logs have "X.XX sec" or similar
                if self.last_sent_time:
                    latency = time.time() - self.last_sent_time
                    print(f"⏱️ [TTS Benchmark] {line} | Latency to start: {latency:.3f}s")
                    self.last_sent_time = None
                else:
                    print(f"⏱️ [TTS Benchmark] {line}")

    def speak(self, text):
        if self.piper_proc.poll() is None:
            self.last_sent_time = time.time()
            self.piper_proc.stdin.write(text + "\n")
            self.piper_proc.stdin.flush()

    def stop(self):
        self.piper_proc.terminate()
        self.aplay_proc.terminate()
        os.system("pkill aplay")

def make_text_image(text, width=240, height=280):
    """Generate RGB565 pixel data with wrapped text."""
    img = Image.new('RGB', (width, height), (0, 0, 40))  # Dark blue background
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(FONT_PATH, 20)
    except Exception:
        font = ImageFont.load_default()
        
    margin = 10
    max_width = width - (margin * 2)
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        line_str = " ".join(current_line)
        bbox = draw.textbbox((0, 0), line_str, font=font)
        if (bbox[2] - bbox[0]) > max_width:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    lines.append(" ".join(current_line))
    
    y = margin
    for line in lines:
        if y < height:
            draw.text((margin, y), line, fill=(200, 230, 255), font=font)
        y += 25
        
    # Convert to RGB565
    pixel_data = []
    for py in range(height):
        for px in range(width):
            r, g, b = img.getpixel((px, py))
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            pixel_data.extend([(rgb565 >> 8) & 0xFF, rgb565 & 0xFF])
    return pixel_data

def main():
    parser = argparse.ArgumentParser(description="Rocky Show & Speak")
    parser.add_argument("quality", nargs="?", choices=["low", "medium", "rocky"], default="rocky", 
                        help="Voice quality: low (16000Hz) or medium (22050Hz)")
    parser.add_argument("epoch", nargs="?", help="Optional epoch number for 'rocky' voice (e.g., 2607)")
    args = parser.parse_args()

    # Initialize Display
    print("Initializing display...")
    board = WhisPlayBoard()
    board.set_backlight(60)
    
    # Initialize TTS
    print(f"Initializing TTS quality: {args.quality}...")
    tts = PiperTTS(args.quality, args.epoch)
    
    try:
        print("\nType your message and hit Enter.")
        print("Press Ctrl+C to exit.")
        while True:
            text = input("\nSay: ")
            if not text.strip():
                continue
                
            # 1. Update Display
            print(f"LCD: {text}")
            pixel_data = make_text_image(text, board.LCD_WIDTH, board.LCD_HEIGHT)
            board.draw_image(0, 0, board.LCD_WIDTH, board.LCD_HEIGHT, pixel_data)
            
            # 2. Speak
            tts.speak(text)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        tts.stop()
        board.cleanup()

if __name__ == "__main__":
    main()
