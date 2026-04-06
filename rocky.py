import os
import re
import sys
import time
import threading
import subprocess
import base64
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Local Imports
sys.path.append(os.path.abspath("./Driver"))
from WhisPlay import WhisPlayBoard
from synthesizer.rocky import speak_rocky, pre_warm_cache

# ==================== Configuration ====================
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_ID = "gemini-2.5-flash-lite"  # Latest and fastest
TEMP_AUDIO_PATH = "/tmp/rocky_input.wav"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Local LLM config
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "False").lower() in ["true", "1", "yes"]
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")

# UI Config
SHOW_BOOT_SCREEN = os.getenv("SHOW_BOOT_SCREEN", "True").lower() in ["true", "1", "yes"]

# Load the system prompt
try:
    with open("system_prompt.txt", "r") as f:
        SYSTEM_PROMPT = f.read().strip()
except Exception:
    SYSTEM_PROMPT = "You are Rocky from Project Hail Mary. Be brief, inquisitive, and friendly. Answer the user."

# Initialize Client
if USE_LOCAL_LLM:
    print("\n--- Native Gemma 4 Server Backend ---")
    print(f"Routing to: {LM_STUDIO_URL.replace('1234/v1', '8000/api/rocky_chat')}")
    print("-------------------------------------\n")
else:
    if not API_KEY:
        print("\nWARNING: GEMINI_API_KEY not found in environment!")
    client = genai.Client(api_key=API_KEY)
    try:
        print("\n--- Available Gemini Models ---")
        for m in client.models.list():
            name = getattr(m, 'name', '')
            if 'gemini' in name.lower():
                print(f" - {name.replace('models/', '')}")
        print("-------------------------------\n")
    except Exception as e:
        print(f"Could not list models: {e}")

# ==================== Helper Functions ====================
ICON_IMAGE = None

def get_corner_icon():
    global ICON_IMAGE
    if ICON_IMAGE is None:
        try:
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rocky_wave.png")
            if os.path.exists(image_path):
                img = Image.open(image_path).convert("RGBA")
                img.thumbnail((75, 75))  # Keep it relatively small for the corner
                ICON_IMAGE = img
        except Exception:
            pass
    return ICON_IMAGE

def make_text_image(text, width=240, height=280, scroll_y=0, is_thinking=False):
    """Generate RGB565 pixel data with wrapped text for display."""
    img = Image.new('RGB', (width, height), (0, 0, 40))  # Dark blue background
    draw = ImageDraw.Draw(img)
    
    # Load Font
    try:
        font = ImageFont.truetype(FONT_PATH, 20)
    except Exception:
        font = ImageFont.load_default()
        
    # Text Wrapping Logic
    margin = 10
    max_width = width - (margin * 2)
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        # Check current line width
        line_str = " ".join(current_line)
        bbox = draw.textbbox((0, 0), line_str, font=font)
        if (bbox[2] - bbox[0]) > max_width:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    lines.append(" ".join(current_line))
    
    # Draw Lines
    y = margin - int(scroll_y)
    for line in lines:
        if y > -30 and y < height:
            draw.text((margin, y), line, fill=(200, 230, 255), font=font)
        y += 25  # Line height
        
    # Overlay corner icon at bottom right
    icon = get_corner_icon()
    if icon:
        ix, iy = icon.size
        # The 3rd parameter `icon` acts as the transparency mask (RGBA)
        img.paste(icon, (width - ix - 5, height - iy - 5), icon)
        
        # Add thinking bubble if in 'thinking' state
        if is_thinking:
            bubble_w = 48
            bubble_h = 26
            bubble_x = width - ix - bubble_w + 10
            bubble_y = height - iy - bubble_h - 10
            
            # draw bubble background
            draw.rounded_rectangle([bubble_x, bubble_y, bubble_x + bubble_w, bubble_y + bubble_h], 
                                   radius=12, fill=(220, 220, 220))
                                   
            # Small tail dots pointing down towards Rocky's head
            draw.ellipse([bubble_x + bubble_w - 8, bubble_y + bubble_h + 2, bubble_x + bubble_w - 3, bubble_y + bubble_h + 7], fill=(220,220,220))
            draw.ellipse([bubble_x + bubble_w + 2, bubble_y + bubble_h + 10, bubble_x + bubble_w + 5, bubble_y + bubble_h + 13], fill=(220,220,220))
            
            # 3 Typing dots
            dot_r = 3
            dx = bubble_x + 10
            cy = bubble_y + (bubble_h // 2) - dot_r
            for _ in range(3):
                draw.ellipse([dx, cy, dx + dot_r*2, cy + dot_r*2], fill=(100, 100, 100))
                dx += 12
        
    # Convert to RGB565
    pixel_data = []
    for py in range(height):
        for px in range(width):
            r, g, b = img.getpixel((px, py))
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            pixel_data.extend([(rgb565 >> 8) & 0xFF, rgb565 & 0xFF])
    return pixel_data

def load_image_rgb565(filepath, screen_width=240, screen_height=280):
    """Load image file as RGB565 pixel data (scale maintaining aspect ratio + center crop)"""
    try:
        img = Image.open(filepath).convert('RGB')
        original_width, original_height = img.size
        aspect_ratio = original_width / original_height
        screen_aspect_ratio = screen_width / screen_height

        if aspect_ratio > screen_aspect_ratio:
            new_height = screen_height
            new_width = int(new_height * aspect_ratio)
            resized_img = img.resize((new_width, new_height))
            offset_x = (new_width - screen_width) // 2
            cropped_img = resized_img.crop(
                (offset_x, 0, offset_x + screen_width, screen_height))
        else:
            new_width = screen_width
            new_height = int(new_width / aspect_ratio)
            resized_img = img.resize((new_width, new_height))
            offset_y = (new_height - screen_height) // 2
            cropped_img = resized_img.crop(
                (0, offset_y, screen_width, offset_y + screen_height))

        pixel_data = []
        for py in range(screen_height):
            for px in range(screen_width):
                r, g, b = cropped_img.getpixel((px, py))
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                pixel_data.extend([(rgb565 >> 8) & 0xFF, rgb565 & 0xFF])
        return pixel_data
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

# ==================== Main Application ====================

class RockyApp:
    def __init__(self):
        self.board = WhisPlayBoard()
        self.board.set_backlight(60)
        
        # Audio status
        self._record_proc = None
        self._is_recording = False
        
        # Boot Screen Setup
        if SHOW_BOOT_SCREEN:
            boot_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rocky_boot_screen.png")
            if os.path.exists(boot_img_path):
                print("LCD: Loading Boot Screen...")
                img_data = load_image_rgb565(boot_img_path, self.board.LCD_WIDTH, self.board.LCD_HEIGHT)
                if img_data:
                    self.board.draw_image(0, 0, self.board.LCD_WIDTH, self.board.LCD_HEIGHT, img_data)
        
        # Pre-warm voice cache (Perfect loading screen background task!)
        pre_warm_cache()
        
        if SHOW_BOOT_SCREEN:
            time.sleep(1.5) # Force wait 1.5s so the boot screen is actually enjoyed!
            
        # Display Initial screen
        self.show_message("ROCKY READY\nHold button to speak")
        self.board.set_rgb(0, 0, 255)  # Blue ready LED

    def show_message(self, text, is_thinking=False):
        print(f"LCD: {text}")
        data = make_text_image(text, self.board.LCD_WIDTH, self.board.LCD_HEIGHT, is_thinking=is_thinking)
        self.board.draw_image(0, 0, self.board.LCD_WIDTH, self.board.LCD_HEIGHT, data)

    def _get_alsa_device(self):
        """Dynamically find the wm8960 sound card."""
        try:
            out = subprocess.check_output(['arecord', '-l'], text=True)
            for line in out.splitlines():
                if "wm8960" in line.lower() and "card" in line.lower():
                    parts = line.split(":")
                    if len(parts) > 0 and "card" in parts[0]:
                        card_num = parts[0].replace("card", "").strip()
                        return f"hw:{card_num},0"
        except Exception:
            pass
        return "hw:0,0"  # Safest fallback based on user's arecord -l

    def _start_recording(self):
        """Invoke arecord directly to match WhisPlay hardware."""
        print("🎙️ Recording started...")
        self.board.set_rgb(255, 0, 0)  # Red recording LED
        self.show_message("LISTENING...")
        
        alsa_device = self._get_alsa_device()
        
        # The hardware WM8960 is extremely strict. It requires 48000Hz to prevent clock 
        # jitter distortion (PLL divider logic) and natively expects 2-channel capture.
        self._record_proc = subprocess.Popen(
            ['arecord', '-D', alsa_device, '-f', 'S16_LE', '-r', '48000', '-c', '2', '-t', 'wav', TEMP_AUDIO_PATH],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    def _start_scrolling(self, text):
        self._scroll_running = True
        self._scroll_thread = threading.Thread(target=self._scroll_worker, args=(text,))
        self._scroll_thread.start()

    def _stop_scrolling(self):
        self._scroll_running = False
        if hasattr(self, '_scroll_thread') and self._scroll_thread:
            self._scroll_thread.join()

    def _scroll_worker(self, text):
        # Calculate max lines to determine max scroll length
        try: font = ImageFont.truetype(FONT_PATH, 20)
        except Exception: font = ImageFont.load_default()
        
        margin = 10
        img_dummy = Image.new('RGB', (1, 1))
        draw_dummy = ImageDraw.Draw(img_dummy)
        lines = []
        current_line = []
        for word in text.split():
            current_line.append(word)
            bbox = draw_dummy.textbbox((0, 0), " ".join(current_line), font=font)
            if (bbox[2] - bbox[0]) > (self.board.LCD_WIDTH - margin * 2):
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        max_height = len(lines) * 25
        max_scroll = max(0, max_height - (self.board.LCD_HEIGHT - 60)) # leave margin at bottom
        
        scroll_y = 0
        scroll_speed = 1.5 # smooth pixels per frame
        
        # Display the text initially and hold string for 1.5s so user can read the start!
        self.show_message(text)
        start_wait = time.time()
        while self._scroll_running and time.time() - start_wait < 1.5:
            time.sleep(0.05)
            
        # Begin auto-scroll loop
        while self._scroll_running and scroll_y < max_scroll:
            scroll_y += scroll_speed
            data = make_text_image(text, self.board.LCD_WIDTH, self.board.LCD_HEIGHT, scroll_y)
            self.board.draw_image(0, 0, self.board.LCD_WIDTH, self.board.LCD_HEIGHT, data)
            time.sleep(0.05)

    def _stop_recording(self):
        """Stop arecord process."""
        print("⏹️ Recording stopped.")
        if self._record_proc:
            self._record_proc.terminate()
            stdout, stderr = self._record_proc.communicate()
            if not os.path.exists(TEMP_AUDIO_PATH):
                print(f"\n[ALSA Error] arecord failed:\n{stderr.decode('utf-8', errors='ignore')}")
            self._record_proc = None
        
        self.board.set_rgb(255, 255, 0)  # Yellow thinking LED
        self.show_message("THINKING...", is_thinking=True)

        if not os.path.exists(TEMP_AUDIO_PATH):
            err_msg = "Error: arecord failed to record audio."
            self.show_message(err_msg)
            print(err_msg)
            speak_rocky(err_msg)
            # Return to idle (leaving the error text on screen)
            self.board.set_rgb(0, 0, 255)
            return
        
        # Process with LLM
        print(f"🚀 Sending audio payload to {'Local Proxy' if USE_LOCAL_LLM else 'Gemini Cloud'}...")
        start_time = time.time()
        response_text = self.query_llm(TEMP_AUDIO_PATH)
        duration = time.time() - start_time
        
        provider = "Local STT/LM Studio Proxy" if USE_LOCAL_LLM else "Cloud Gemini API"
        print(f"⏱️ [LLM Benchmark] {provider} returned text in {duration:.2f} seconds!")
        
        if response_text:
            self.board.set_rgb(0, 255, 0)  # Green speaking LED
            
            # Start background scrolling while Rocky speaks
            self._start_scrolling(response_text)
            
            # This blocks until Rocky finishes speaking
            speak_rocky(response_text)
            
            # Gracefully end the scrolling thread
            self._stop_scrolling()
            
        # Return to idle (leaving the text on screen so user can read it)
        self.board.set_rgb(0, 0, 255)

    def query_llm(self, audio_filepath):
        """Send audio to Gemini OR a local LM Studio server for transcription and response."""
        try:
            with open(audio_filepath, 'rb') as f:
                audio_bytes = f.read()

            if USE_LOCAL_LLM:
                import urllib.request
                import json
                
                base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
                native_url = LM_STUDIO_URL.replace("1234/v1", "8000/api/rocky_chat")
                
                req_data = json.dumps({
                    "audio_base64": base64_audio,
                    "system_prompt": SYSTEM_PROMPT + "\nIMPORTANT: Do NOT include any audio timestamps in your text output!"
                }).encode('utf-8')
                
                req = urllib.request.Request(native_url, data=req_data, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=120) as response:
                    resp_json = json.loads(response.read().decode())
                    clean_text = resp_json.get("text", "")
            else:
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=[
                        types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type='audio/wav',
                        )
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT + "\nIMPORTANT: Do NOT include any audio timestamps in your text output!"
                    )
                )
                clean_text = response.text
                
            # Remove Gemini's automatic audio timestamps (e.g. "00:03 ", "[00:00]", ":00:")
            clean_text = re.sub(r'(?m)^[^\w\s]*\d{0,2}:\d{2}[^\w\s]*\s*', '', clean_text)
            
            # Replace all question marks with Rocky's signature verbal tick
            clean_text = re.sub(r'\s*\?', ' question?', clean_text)
            
            return clean_text.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return f"Error: {str(e)}"

    def run(self):
        print("Starting Rocky App Loop...")
        try:
            while True:
                # Polling for button hold
                # This matches the 'hold to record' requirement
                if self.board.button_pressed():
                    if not self._is_recording:
                        self._is_recording = True
                        self._start_recording()
                else:
                    if self._is_recording:
                        self._is_recording = False
                        self._stop_recording()
                
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            self.board.cleanup()

def main():
    app = RockyApp()
    app.run()

if __name__ == "__main__":
    main()
