import numpy as np
import simpleaudio as sa
import time
import random

SAMPLE_RATE = 44100

def play_eridian_chord(frequencies, duration=0.3, volume=0.5):
    """Generates and plays a chord directly from RAM."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.zeros_like(t)
    
    for f in frequencies:
        # Create sine wave
        tone = np.sin(2 * np.pi * f * t)
        # Apply a quick fade to prevent the MAX98357 from popping
        fade_in_out = np.ones_like(t)
        fade_len = int(SAMPLE_RATE * 0.02) # 20ms fade
        fade_in_out[:fade_len] = np.linspace(0, 1, fade_len)
        fade_in_out[-fade_len:] = np.linspace(1, 0, fade_len)
        wave += (tone * fade_in_out)

    # Normalize and convert to 16-bit PCM
    # We use 2 channels (stereo) to match your dmixer config
    audio_data = (wave / len(frequencies) * volume * 32767).astype(np.int16)
    
    # Duplicate the mono track into two channels for the ALSA dmixer
    stereo_data = np.vstack((audio_data, audio_data)).T.flatten()
    
    # Play immediately
    play_obj = sa.play_buffer(stereo_data, num_channels=2, bytes_per_sample=2, sample_rate=SAMPLE_RATE)
    play_obj.wait_done()

# Mapping words to Eridanian frequency sets (Hz)
LEXICON = {
    "amaze": [659.25, 830.61, 987.77], # E Major
    "question": [440.0, 466.16],       # Dissonant
    "fist": [523.25, 659.25, 783.99],  # C Major
    "bad": [220.0, 233.08, 277.18]     # Low/Dark
}

def speak_rocky(text):
    print(f"Rocky: {text}")
    words = text.lower().replace("!", " !").replace("?", " ?").split()
    
    for word in words:
        if "!" in word or "amaze" in word:
            play_eridian_chord(LEXICON["amaze"], duration=0.2)
        elif "?" in word:
            play_eridian_chord(LEXICON["question"], duration=0.4)
        elif word in LEXICON:
            play_eridian_chord(LEXICON[word])
        else:
            # Procedural chord for unknown words
            base = 400 + (len(word) * 25)
            play_eridian_chord([base, base * 1.2, base * 1.5], duration=0.15)
        time.sleep(0.05)

if __name__ == "__main__":
    speak_rocky("Amaze! Amaze amaze!")
    time.sleep(0.5)
    speak_rocky("Question? Fist-bump!")