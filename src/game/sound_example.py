"""
Example usage of the SoundPlayer class.

This script demonstrates how to use the SoundPlayer to play sound effects
from the src/audio directory.
"""

import time
import sys
from sound_player import SoundPlayer

print("Sound Player Example")
print("====================")

# Example 1: Play a sound once
print("Playing 'Select.wav' once...")
select_sound = SoundPlayer.play_sound("Select.wav")
time.sleep(1)  # Wait for sound to finish

# Example 2: Play a sound with auto .wav extension
print("Playing 'Small Hit' (auto-adding .wav extension)...")
hit_sound = SoundPlayer.play_sound("Small Hit")
time.sleep(1)  # Wait for sound to finish

# Example 3: Play a sound with volume adjustment
print("Playing 'Shield Block On' at 50% volume...")
shield_sound = SoundPlayer.play_sound("Shield Block On", volume=0.5)
time.sleep(1)  # Wait for sound to finish

# Example 4: Play a repeating sound
print("Playing 'Pikachu - Electrical Flow' on repeat for 3 seconds...")
repeat_sound = SoundPlayer.play_sound("Pikachu - Electrical Flow", repeat=True)
time.sleep(3)  # Let it repeat for 3 seconds
print("Stopping repeated sound...")
SoundPlayer.stop_sound(repeat_sound)

# Example 5: Try to play a non-existent sound
print("Trying to play a non-existent sound 'NonExistentSound.wav'...")
non_existent = SoundPlayer.play_sound("NonExistentSound.wav")
# Should print a warning and return None

print("\nDone with examples!")

# Simple menu to test sounds interactively
print("\nInteractive Sound Test")
print("=====================")
print("Enter a sound name to play (without .wav extension), or 'quit' to exit")
print("Examples: 'Select', 'Small Hit', 'Shield Block On'")

while True:
    user_input = input("\nSound name (or 'quit'): ")
    
    if user_input.lower() == 'quit':
        print("Exiting sound test.")
        break
    
    repeat = 'y' == input("Repeat sound? (y/n): ").lower()
    volume = float(input("Volume (0.0-1.0): ") or "1.0")
    
    sound = SoundPlayer.play_sound(user_input, repeat=repeat, volume=volume)
    
    if sound and repeat:
        input("Press Enter to stop the sound...")
        SoundPlayer.stop_sound(sound)

print("Sound test complete.") 