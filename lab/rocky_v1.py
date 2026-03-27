import numpy as np
import pygame
import time
import hashlib

# Audio Settings
SAMPLE_RATE = 44100
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)

def play_chord(frequencies, duration=0.3, volume=0.5):
    """Generates and plays a polyphonic Eridian chord using Pygame."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    wave = np.zeros_like(t)
    
    # Layer the frequencies
    for f in frequencies:
        # A slight envelope to prevent 'clicking' audio artifacts at the start/end
        envelope = np.sin(np.pi * np.linspace(0, 1, len(t))) 
        wave += (1.0 / len(frequencies)) * np.sin(2 * np.pi * f * t) * envelope

    # Convert to 16-bit PCM
    audio_data = (wave * volume * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(audio_data)
    sound.play()
    
    # Wait for the sound to finish playing, plus a tiny gap between words
    time.sleep(duration + 0.05)


# The "Dictionary" - Mapping specific concepts to frequencies (Hz)
ERIDIAN_LEXICON = {
    # High/Bright (Happy/Excited)
    "amaze": [659.25, 830.61, 987.77],   # E Major 
    "happy": [783.99, 987.77, 1174.66],  # G Major (Higher)
    "yes": [523.25, 659.25, 783.99],     # C Major (Solid/Agreement)
    "fist": [523.25, 659.25, 783.99],    # Same as "yes"

    # Low/Dark (Sad/Bad)
    "bad": [220.00, 233.08, 277.18],     # Low, dark dissonance
    "sad": [293.66, 349.23, 440.00],     # D Minor low 
    "sleep": [261.63, 311.13, 392.00],   # C Minor low (relaxing)
    
    # Dissonant/Urgent
    "danger": [698.46, 740.00, 783.99],  # Clashing high cluster
    "no": [349.23, 370.00, 392.00],      # F, F#, G (Abrupt dismissal)
    
    # Unique Signatures
    "question": [440.00, 466.16],        # Dissonant semitone (Inquiry indicator)
    "grace": [493.88, 622.25, 739.99],   # B Minor (Unique name signature)
    "friend": [440.00, 554.37, 659.25],  # A Major
    "astrophage": [880.00, 932.33, 987.77], # High chromatic cluster
    
    # Names (Long, complex multi-chord melodic sequences!)
    "rocky": [
        [349.23, 440.00, 523.25], # F Major
        [440.00, 554.37, 659.25], # A Major
        [523.25, 659.25, 783.99], # C Major
        [587.33, 739.99, 880.00], # D Major
        [659.25, 830.61, 987.77], # E Major
        [783.99, 987.77, 1174.66] # G Major
    ],
    "adrian": [
        [293.66, 349.23, 440.00], # D Minor
        [329.63, 392.00, 493.88], # E Minor
        [392.00, 466.16, 587.33]  # G Minor
    ]
}


def word_to_chord(word):
    """Generates a consistent, unique chord for any unknown word using its hash.
    Because Eridanian is structured, an unknown word should still sound the exact 
    same way every time Rocky says it!"""
    
    # Use MD5 to get a consistent integer from the word
    hash_val = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
    
    # Derive 3 frequencies between 200Hz and 900Hz based on the hash
    f1 = 200 + (hash_val % 700)
    f2 = 200 + ((hash_val >> 8) % 700)
    f3 = 200 + ((hash_val >> 16) % 700)
    
    return [f1, f2, f3]


def speak_rocky(text):
    print(f"\nRocky says: \"{text}\"")
    
    # Tokenize the text, keeping punctuation conceptually separated
    words = text.lower().replace(",", "").replace(".", "").split()
    
    for word in words:
        is_question = "?" in word
        is_exclamation = "!" in word
        
        # Strip punctuation for dictionary lookup
        clean_word = word.replace("?", "").replace("!", "")
        
        # 1. Determine the chord for this exact word
        if clean_word in ERIDIAN_LEXICON:
            chord = ERIDIAN_LEXICON[clean_word]
        elif clean_word == "":
            continue
        else:
            chord = word_to_chord(clean_word)
            
        # 2. Adjust delivery based on punctuation
        duration = 0.3
        volume = 0.5
        
        if is_exclamation or "amaze" in clean_word or "danger" in clean_word:
            duration = 0.2  # Faster, more excited/urgent cadence
            volume = 0.8
        
        # Check if this word is a multi-chord melodic sequence (like a long name)
        if isinstance(chord[0], list):
            for sequence_chord in chord:
                play_chord(sequence_chord, duration=0.15, volume=volume)
        else:
            # Play a normal, single-chord word
            play_chord(chord, duration=duration, volume=volume)
        
        # 3. If it's a question, Rocky always appends the "question" indicator 
        # at the end of the thought. We'll append it after the word.
        if is_question:
            time.sleep(0.05)
            # Question indicator is played slightly longer and louder to emphasize inquiry
            play_chord(ERIDIAN_LEXICON["question"], duration=0.4, volume=0.7)


if __name__ == "__main__":
    # Give the audio system a split-second to wake up
    time.sleep(0.5)
    
    phrases = [
        "Amaze amaze amaze!!",
        "Friend Grace, sleep question?",
        "Astrophage bad! Danger danger!",
        "Yes, happy! Fist-bump!",
        "I am Rocky.",
        "My mate is Adrian.",
        "Sad... no sleep. Bad astrophage."
    ]
    
    for phrase in phrases:
        speak_rocky(phrase)
        time.sleep(0.4) # Pause between phrases
