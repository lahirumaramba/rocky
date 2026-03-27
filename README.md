# Rocky Sound Generator

A Python script that generates audio phrases mimicking the Eridanian language spoken by Rocky in Andy Weir's *Project Hail Mary*. 

Rocky communicates in musical chords natively, which humans perceive as tones similar to a pipe organ or multiple flutes. This script (`rocky.py`) calculates these multi-frequency sine waves using math arrays and plays them in real-time.

## The Lore-Accurate Language Rules:
- **Consistent Vocabulary:** Specific English words map to specific emotional chords (e.g., "amaze" is a bright E Major chord, "bad" is a low dissonant chord).
- **The "Question" Indicator:** Rocky always appends a specific inquisitive chord at the end of a question.
- **Consistent Word Hashing:** Eridanian is highly structured. Instead of generating random noise for new vocabulary, the script hashes unknown words to mathematically derive 3 distinct, permanent frequencies.
- **Punctuation Inflections:** Words ending with an exclamation mark `!` (or panic words like "danger") are played 33% faster and louder.

---

## 🚀 Quick Start (Poetry)

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Installation:
```bash
# 1. Clone the repository
# 2. Install dependencies
poetry install
```

### Running Rocky:
Use the built-in shortcut to hear Rocky speak:

```bash
poetry run rocky

# Note: On Raspberry Pi, you may need to force the ALSA driver:
SDL_AUDIODRIVER=alsa poetry run rocky
```

---

## 🔧 Prerequisites
- macOS, Linux, or Windows
- Python 3.10+
- `numpy` and `pygame` (handled via Poetry)

## 🥧 Quick Start (Raspberry Pi Zero W)

The Raspberry Pi Zero W uses the ARMv6 architecture. If you're not using Poetry, it's recommended to install dependencies system-wide:

```bash
# 1. Install NumPy and Pygame system-wide
sudo apt-get update
sudo apt-get install python3-numpy python3-pygame

# 2. Run the script directly
# Note: On some Pi setups (like Pi Zero), you may need to force the ALSA driver:
SDL_AUDIODRIVER=alsa python3 rocky.py
```

---

## 🔬 Experimental Projects
- **Astromech Test**: There is an experimental R2-D2 style sound generator included in the `lab/astromech_test/` directory. It can be run using `poetry run r2d2`.
