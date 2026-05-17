# 🪨 Build Your Own Rocky: Step-by-Step Guide

This guide provides simple, step-by-step instructions to build and configure your own **Rocky** (your personal Eridanian buddy) on a fresh install of **Raspberry Pi OS** on a **Raspberry Pi Zero 2W** with the **PiSugar Whisplay HAT**!

---

## 🛠️ Hardware Requirements
*(Assumed to be already acquired & assembled)*
1. **Raspberry Pi Zero 2W**
2. **PiSugar Whisplay HAT** (Includes: 240x280 SPI LCD screen, Button, RGB LED, and WM8960 Audio DAC/Speaker/Microphone)

---

## 1️⃣ Fresh Raspberry Pi OS Setup
Before doing anything else, make sure your Raspberry Pi Zero 2W is set up with a fresh image.
1. Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash **Raspberry Pi OS (64-bit)**. Choose the **Raspberry Pi OS Lite** (no desktop environment) to save resources.
2. In the Imager settings:
   - Configure **Wi-Fi** so the Pi can connect to your local network.
   - Enable **SSH** and configure a username and password.
3. Insert the card into your Pi Zero 2W, boot it up, and SSH into it from your computer:
   ```bash
   ssh pi@<your_pi_ip_address>
   ```

---

## 2️⃣ Install PiSugar Whisplay Drivers (Automated)
The Whisplay HAT communicates over SPI (for the LCD screen) and I2C/I2S (for the WM8960 audio card). The official PiSugar Whisplay installer fully automates enabling these hardware interfaces and setting up the overlays.

1. **Clone the official PiSugar Whisplay repository:**
   ```bash
   git clone https://github.com/PiSugar/Whisplay.git --depth 1
   ```
2. **Navigate to the Whisplay directory and run the unified installer:**
   ```bash
   cd Whisplay
   sudo bash install_driver.sh
   ```
3. **Reboot the Pi to apply changes:**
   ```bash
   sudo reboot
   ```
4. **Verify the Audio Card is detected:**
   SSH back into your Pi and check if the `wm8960` soundcard is recognized:
   ```bash
   aplay -l
   ```
   You should see `wm8960-soundcard` in the output list. If the sound is too low, you can adjust levels by running `alsamixer`, hitting `F6` to select the `wm8960-soundcard`, and turning up the volumes.

---

## 3️⃣ Clone the Rocky Repository & Install System Headers
1. SSH into the Pi and clone your **Rocky** repository into your home directory:
   ```bash
   cd ~
   git clone https://github.com/lahirumaramba/rocky.git
   cd rocky
   ```
2. **Install low-level system dependencies and C libraries:**
   Because a fresh **Raspberry Pi OS Lite** image does not include desktop or media libraries, we must install these system-level components. While `uv` manages Python packages, it *cannot* install low-level C libraries, OS binaries, or hardware driver interfaces. Run:
   ```bash
   sudo apt-get update
   sudo apt-get install -y libsdl2-2.0-0 libsdl2-mixer-2.0-0 python3-dev libgpiod-dev liblgpio-dev swig
   ```

---

## 4️⃣ Install `uv` & Project Dependencies
We use `uv` to manage Rocky's virtual environment and dependencies.

1. **Install `uv`:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **Reload your shell configuration:**
   ```bash
   source $HOME/.local/bin/env
   ```
3. **Synchronize the project dependencies:**
   From the `rocky` project root directory (`~/rocky`), run:
   ```bash
   uv sync
   ```
   *This automatically builds a virtual environment (`.venv`) and installs the exact packages listed in `pyproject.toml` (including spidev, pygame, pillow, and google-genai).*

---

## 5️⃣ Initial Configuration (No Piper TTS)
We will first configure Rocky to run using his **Eridanian Musical Chords**, before setting up the human voice option.

1. **Create your `.env` file from the example template:**
   ```bash
   cp .env.example .env
   ```
2. **Open `.env` in a text editor (like `nano`):**
   ```bash
   nano .env
   ```
3. **Set the following initial settings:**
   ```ini
   # Disable Piper TTS for the initial version
   USE_PIPER=False
   ```

---

## 6️⃣ Configure the LLM & STT Brain
Rocky supports two operational backends: **Cloud Mode** (using Google Gemini API directly) or **Local Mode** (using LM Studio on your local network).

### Option A: Cloud Mode (Gemini API) — Easiest Setup
This sends recorded audio directly to Gemini to perform the transcription and return Rocky's response.
1. Get a free API Key from [Google AI Studio](https://aistudio.google.com/).
2. Edit your Pi's `.env` file:
   ```ini
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   USE_LOCAL_LLM=False
   ```
3. Run Rocky (Skip to Step 7)!

### Option B: Local Mode (Local LM Studio + STT Server)
This processes audio locally on your computer using `mlx-whisper` (`Whisper-Tiny` model) and pings a local `Gemma` model running in LM Studio.

#### 1. On your Computer (The Brain):
- Make sure `uv` is installed on your computer.
- Clone the Rocky repository:
  ```bash
  git clone https://github.com/lahirumaramba/rocky.git
  cd rocky
  ```
- Install dependencies with the local server extras:
  ```bash
  uv sync --extra mac-server
  ```
- Open **LM Studio**:
  1. Load a 4-bit quantized Gemma model (e.g. [`gemma-4-e2b-it.Q4_K_M.gguf`](https://huggingface.co/lmstudio-community/gemma-4-E2B-it-GGUF)).
  2. Go to the **Local Server** tab (the double-arrows icon on the left panel).
  3. Start the server on port `1234`.
- Run the local Speech-to-Text and LLM Proxy Server on your Computer:
  ```bash
  uv run stt_server.py
  ```
  *This listens on port `8000` of your computer's local network.*
- Find your Computer's local IP address (e.g., `192.168.1.5`). You can find it on your computer under System Settings -> Wi-Fi -> Details, or by running `ipconfig getifaddr en0` in the terminal.

#### 2. On your Raspberry Pi Zero 2W:
- Edit the `.env` file to point to your Computer's IP address:
   ```ini
   USE_LOCAL_LLM=True
   LM_STUDIO_URL=http://<YOUR_COMPUTER_IP_ADDRESS>:1234/v1
   ```
   *(Note: Rocky's backend code is smart, it automatically replaces `1234/v1` with `8000/api/rocky_chat` under the hood to route audio requests to the STT proxy!)*

---

## 7️⃣ Run Rocky (Initial Version)
You are ready to launch! Start the application from your `rocky` project root on the Pi:
```bash
uv run rocky.py
```
### How to Interact:
1. **Boot Screen**: The Whisplay LCD screen will light up showing Rocky's custom boot graphic.
2. **Idle**: The RGB LED glows **blue**, and the screen displays `ROCKY READY / Hold button to speak`.
3. **Record**: **Press and HOLD** the button on the Whisplay board. The LED glows **red** and the screen displays `LISTENING...`. Ask Rocky a question (e.g., *"Rocky, why is a school teacher in space?"*).
4. **Process**: **RELEASE** the button. The LED turns **yellow** and the screen shows a thinking animation.
5. **Respond**: The LED glows **green**, your text response scrolls dynamically on the LCD screen, and Rocky **sings** his Eridanian musical chords!

---

## 🚀 Extended Step: Adding Piper TTS (Human Voice)
If you want Rocky to talk to you in a human voice *in addition* to his musical chords, you can enable **Piper Text-to-Speech**. This runs fully locally on the Pi Zero 2W using pre-compiled binaries!

### 1. Identify Your Pi OS Architecture
Depending on how you flashed your Pi, it might be running a 32-bit or 64-bit OS. Determine your architecture by running:
```bash
uname -m
```
- If it outputs `aarch64`, you are running a **64-bit OS**.
- If it outputs `armv7l`, you are running a **32-bit OS**.

### 2. Download and Install Piper Binary
We will download the pre-compiled standalone binary of Piper and extract it into a directory named `~/piper`.

1. **Create and enter the `~/piper` directory:**
   ```bash
   mkdir -p ~/piper
   cd ~/piper
   ```
2. **Download the archive matching your OS architecture:**
   - **For 64-bit (`aarch64`):**
     ```bash
     wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz
     tar -xzf piper_linux_aarch64.tar.gz
     ```
   - **For 32-bit (`armv7l`):**
     ```bash
     wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_armv7l.tar.gz
     tar -xzf piper_linux_armv7l.tar.gz
     ```
   *This extracts the executable `piper` inside `~/piper/piper/` (creating `~/piper/piper/piper`).*

### 3. Download a Voice Model
Piper needs an ONNX voice model and a configuration `.json` file to generate speech. We download these files into `~/piper/`. Let's download a highly optimized, high-performance low-quality English voice (Lessac Low, perfect for Pi Zero 2W latency):

```bash
cd ~/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/low/en_US-lessac-low.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/low/en_US-lessac-low.onnx.json
```

*Optionally, if you want a natural medium-quality voice, you can download the Joe Medium voice:*
```bash
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx.json
```

### 4. Configure `.env` for Piper
Now, update your Rocky `.env` file to activate Piper TTS.
1. Open the project configuration file:
   ```bash
   cd ~/rocky
   nano .env
   ```
2. Edit or add these variables:
   ```ini
   # Piper TTS Settings
   USE_PIPER=True
   PIPER_MODEL=en_US-lessac-low.onnx
   PIPER_RATE=16000
   ```
   *(If you used the `joe-medium` voice, set `PIPER_MODEL=en_US-joe-medium.onnx` and `PIPER_RATE=22050`)*

### 5. Run Rocky with Piper TTS!
Start the app again:
```bash
uv run rocky.py
```
Now, when Rocky responds, his Eridanian musical chords will play, **and in parallel**, the Piper engine will read the response text out loud through the Whisplay speaker!

---

## 🔧 Troubleshooting Tips
- **No Sound?** Run `alsamixer`, press `F6` to select the `wm8960-soundcard`, and make sure the speaker volumes are not muted (indicated by `MM` - press `M` to unmute, which should change it to `OO`, and use arrow keys to increase volume).
- **Poor Audio Capture?** The microphone gain might be too low. Run `alsamixer`, select the input tab (`Tab` key) and make sure your capture channels are set up and gains are turned up.
- **Latency is high?**
  - If using Local Mode, verify that your Mac and Pi are on a strong, stable 5GHz Wi-Fi network.
  - If using Piper, stick to `low` or `medium` quality models. High-quality models will take too long to synthesize on the Pi Zero 2W.
  - Make sure the Pi Zero 2W has adequate ventilation or a heatsink to avoid thermal throttling under heavy CPU load!

Enjoy your brand new alien rock friend! 🪨✨
