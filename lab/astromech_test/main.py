import sys
import os
from ttastromech import TTAstromech

def main():
    """
    R2-D2 Astromech Sound Generator
    Uses the ttastromech library to translate text into droid beeps.
    """
    # Initialize the astromech engine
    try:
        r2 = TTAstromech()
    except Exception as e:
        print(f"Error initializing TTAstromech: {e}")
        print("Note: This script requires a working audio player (e.g., afplay on macOS or aplay on Linux).")
        sys.exit(1)

    # Check for command line arguments
    if len(sys.argv) > 1:
        phrase = " ".join(sys.argv[1:])
        print(f"Astromech is speaking: '{phrase}'")
        r2.speak(phrase.lower())
    else:
        print("--- R2-D2 ASTROMECH SOUND GENERATOR ---")
        print("Enter a phrase for R2-D2 to say (or 'quit' to exit):")
        
        while True:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["quit", "exit"]:
                    print("Beep boop! (Goodbye)")
                    break
                
                print(f"R2-D2 says: {user_input}")
                r2.speak(user_input.lower())
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
