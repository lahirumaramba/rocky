import numpy as np
import pygame
import time

# Audio Settings
SAMPLE_RATE = 44100
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)

def play_chord(frequencies, duration=0.4, volume=0.5):
    """Generates a polyphonic Eridian chord."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.zeros_like(t)
    
    # Layer the frequencies
    for f in frequencies:
        # We add a slight fade-in/out to prevent 'clicking'
        envelope = np.sin(np.pi * np.linspace(0, 1, len(t))) 
        wave += (1.0 / len(frequencies)) * np.sin(2 * np.pi * f * t) * envelope

    # Convert to 16-bit PCM
    audio_data = (wave * volume * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(audio_data)
    sound.play()
    time.sleep(duration + 0.05)

# The "Dictionary" - Mapping words/punctuation to frequencies (Hz)
ERIDIAN_LEXICON = {
    "amaze": [659.25, 830.61, 987.77], # E Major (Bright/Happy)
    "question": [440.00, 466.16],      # Dissonant semitone (Inquiry)
    "bad": [220.00, 233.08, 277.18],   # Low, dark minor-ish
    "fist": [523.25, 659.25, 783.99],  # C Major (Solid/Agreement)
    "default": [440, 554, 659]         # Standard A Major
}

def speak_rocky(text):
    print(f"Rocky says: {text}")
    words = text.lower().replace("!!", " !").replace("?", " ?").split()
    
    for word in words:
        if "!" in word or "amaze" in word:
            # High-pitched, excited chords
            play_chord(ERIDIAN_LEXICON["amaze"], duration=0.3)
        elif "?" in word:
            # Rising tone for a question
            play_chord(ERIDIAN_LEXICON["question"], duration=0.5)
        elif word in ERIDIAN_LEXICON:
            play_chord(ERIDIAN_LEXICON[word])
        else:
            # Generate a consistent chord based on word length for unknown words
            base_f = 300 + (len(word) * 20)
            play_chord([base_f, base_f * 1.25, base_f * 1.5])

# --- Run the "Amaze" test ---
speak_rocky("Amaze amaze amaze!!")
speak_rocky("Question? Fist-bump!")
speak_rocky("bad, bad bad bad question")