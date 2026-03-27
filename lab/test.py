import numpy as np
import wave
import subprocess
import random
import time
import os
import platform

def generate_chord(frequencies, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    chord = np.zeros_like(t)
    for freq in frequencies:
        # Generate sine wave for each frequency
        wave_data = np.sin(2 * np.pi * freq * t)
        # Apply an envelope to make it sound less harsh (fade in/out)
        envelope = np.ones_like(t)
        fade_len = int(sample_rate * 0.05) # 50ms fade
        if len(t) > fade_len * 2:
            envelope[:fade_len] = np.linspace(0, 1, fade_len)
            envelope[-fade_len:] = np.linspace(1, 0, fade_len)
        chord += wave_data * envelope
    
    # Normalize by number of notes to prevent clipping
    chord = chord / len(frequencies)
    return chord

def play_rocky_phrase():
    # Rocky communicates using chords. We'll use combinations of frequencies 
    # to simulate his speech patterns (Eridanian language).
    
    # Let's use an alien-sounding, musical scale (minor pentatonic with some odd higher notes)
    base_freqs = [
        # Octave 1
        261.63, 311.13, 349.23, 392.00, 466.16, 
        # Octave 2
        523.25, 622.25, 698.46, 783.99, 932.33,
        # Octave 3 (higher, since Rocky is small and his voice is described as musical)
        1046.50, 1244.51, 1396.91, 1567.98, 1864.66
    ]
    
    sample_rate = 44100
    sequence_length = random.randint(3, 8)
    
    all_audio = []
    
    for _ in range(sequence_length):
        # Pick 3 or 4 random notes for a chord
        num_notes = random.randint(3, 4)
        chord_notes = random.sample(base_freqs, num_notes)
        duration = random.uniform(0.05, 0.3) # Fast cadence
        
        chord_audio = generate_chord(chord_notes, duration, sample_rate)
        all_audio.append(chord_audio)
        
        # Add a tiny pause between chords
        pause_duration = random.uniform(0.01, 0.05)
        pause_audio = np.zeros(int(sample_rate * pause_duration))
        all_audio.append(pause_audio)
        
    full_audio = np.concatenate(all_audio)
    
    # Convert to 16-bit PCM
    audio_data = np.int16(full_audio * 32767)
    
    filename = f"rocky_phrase_{random.randint(1000, 9999)}.wav"
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2) # 2 bytes = 16 bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
            
    # Play the sound using native OS playback
    system = platform.system()
    if system == "Darwin":
        # macOS
        subprocess.run(["afplay", filename])
    elif system == "Linux":
        # Linux / Raspberry Pi
        subprocess.run(["aplay", "-q", filename])
    elif system == "Windows":
        # Windows
        import winsound
        winsound.PlaySound(filename, winsound.SND_FILENAME)
    else:
        print(f"Cannot automatically play sound on {system}. File saved as {filename}")
    
    # Clean up the audio file
    if os.path.exists(filename):
        os.remove(filename)

if __name__ == "__main__":
    print("🎵 Rocky is speaking (Eridanian language) ...")
    phrases = ["Amaze!", "Amaze, amaze, amaze!", "Question?", "Happy!"]
    
    for phrase in phrases:
        print(phrase)
        play_rocky_phrase()
        time.sleep(random.uniform(0.2, 0.6))
