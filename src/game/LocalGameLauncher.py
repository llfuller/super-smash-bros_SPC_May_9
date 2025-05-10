'''
Super Smash Bros - Local Two-Player Edition Launcher

This script launches the local two-player version of the game that doesn't require
a separate server or network connection.

The game uses authentic Super Smash Bros Melee physics for realistic gameplay.
'''

import sys
import os
import pygame as pg
import time
from sound_player import SoundPlayer  # Import the SoundPlayer class

# Simply use the current directory as the game directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Just make sure we're in the game directory (already are, but to be safe)
os.chdir(current_dir)

# Check for command line arguments
if len(sys.argv) > 1:
    # Check for GIANT MODE flag
    if '--giant-mode' in sys.argv:
        print("🔥 GIANT MODE ENABLED! 🔥")
        # Import settings to set GIANT_MODE_ENABLED
        from settings import *
        # Enable GIANT MODE
        sys.modules['settings'].GIANT_MODE_ENABLED = True
        
# Initialize pygame to check for controllers
pg.init()
pg.joystick.init()

print("=== Super Smash Bros - Local Two-Player Edition Launcher ===")
print()

# Play startup sound
SoundPlayer.play_sound("Select")

# Display GIANT MODE status
from settings import GIANT_MODE_ENABLED
if GIANT_MODE_ENABLED:
    print("🔥 GIANT MODE ACTIVE - Characters will be supersized! 🔥")
    print()

# Check for controllers
controller_found = False
controller_name = "None"

# Wait a moment for controller detection
time.sleep(0.5)  # Give system time to detect controller

# Try to initialize the controller
if pg.joystick.get_count() > 0:
    try:
        joystick = pg.joystick.Joystick(0)
        joystick.init()
        controller_name = joystick.get_name()
        controller_found = True
        print(f"Switch Pro Controller detected: {controller_name}")
        print("Controller will be used for Player 1.")
        
        # Simple controller diagnostic test
        print("\nPerforming quick controller test...")
        print("Press any button on your controller to see its number...")
        
        # Run a quick test showing button presses
        test_start = time.time()
        test_active = True
        while test_active and (time.time() - test_start < 5):  # Run for 5 seconds
            for event in pg.event.get():
                if event.type == pg.JOYBUTTONDOWN:
                    print(f"Button pressed: {event.button}")
                    if event.button in [9, 10]:
                        print(">>> This is a Shield button (L or R)! <<<")
                        
            # End test early if 3 seconds have passed
            if time.time() - test_start > 3:
                test_active = False
                
        print("Controller test complete!\n")
    except Exception as e:
        print(f"Controller detected but initialization failed: {e}")
        print("Falling back to keyboard controls.")
else:
    print("No controllers detected. Using keyboard controls only.")
    print("Troubleshooting:")
    print("1. Make sure controller is connected before starting the game")
    print("2. Try unplugging and reconnecting your controller")
    print("3. Some controllers require specific drivers")
    print("4. Press F1 in-game to see controller debug information")
    print("5. Run controller_test.py to test your controller")

print()
print("Controls:")
print("Player 1:")
if controller_found:
    print("- Left Stick/D-pad: Movement")
    print("- Left Stick/D-pad DOWN: Fast fall (when already falling)")
    print("- A button (left) / B button (top): Jump (tap for short hop, hold for full jump)")
    print("- Y button (right): Weak attack")
    print("- X button (bottom): Strong attack")
    print("- L/R buttons (9/10): Shield (hold to activate)")
    print("- ZL/ZR buttons: Shield (hold to activate)")
    print("- Plus button: Restart game (after match)")
    print("- Minus button: Return to menu (after match)")
    print("- Home button: Quit game (after match)")
    print("- F1 key: Toggle controller debugging mode")
else:
    print("- Arrow keys: Movement")
    print("- DOWN: Fast fall (when already falling)")
    print("- UP: Jump (tap quickly for short hop, hold for full jump)")
    print("- Z: Weak attack")
    print("- X: Heavy attack")
    print("- LEFT SHIFT: Shield (hold to activate)")

print()
print("Player 2:")
print("- WASD keys: Movement")
print("- S: Fast fall (when already falling)")
print("- W: Jump (tap quickly for short hop, hold for full jump)")
print("- G: Weak attack")
print("- H: Heavy attack")
print("- E: Shield (hold to activate)")
print()
print("Game Features:")
print("- Authentic Super Smash Bros Melee physics")
print("- Character sizes match real Melee proportions")
print("- Realistic knockback formula based on damage percentage")
print("- Accurate movement speeds and acceleration values")
print("- Shield blocking to prevent damage (visible as colored bubble)")
print("- GIANT MODE: Run with '--giant-mode' flag for supersized characters!")
print("  Example: python LocalGameLauncher.py --giant-mode")
print()
print("Shield Troubleshooting:")
print("- For Pro Controller: Use L/R buttons (9/10) to activate shield")
print("- Make sure to HOLD the button (not just tap)")
print("- Shield shows as a colored bubble around character")
print("- Press F1 to see detailed controller debugging info")
print()
print("Starting the game...")

# Import settings
from config import DEFAULT_SETTINGS

# Initialize the unified input handler
from input_handler import input_handler

# Since we're already in the game directory, import directly
from LocalGame import LocalGame

# Create a game instance
game = LocalGame()

# Enable controller support if a controller was found
if controller_found:
    # Enable controller in both game settings and input handler
    game.settings['use_controller'] = True
    
    # IMPORTANT: Make sure the input handler knows controller is enabled
    # This is the key flag that allows controller initialization when player1 is added
    input_handler.controller_enabled = True
    print(f"Controller support enabled in input handler: {input_handler.controller_enabled}")
    
    # Ensure controllers are prioritized over keyboard for input
    input_handler.controller_priority = True
    print("Controller input prioritized over keyboard input")
    
    print(f"Controller support enabled for {controller_name}")
    
    # We'll try to auto-detect the controller type
    if "pro" in controller_name.lower() or "switch" in controller_name.lower():
        print("Detected as Nintendo Switch Pro Controller")
    elif "xbox" in controller_name.lower():
        print("Detected as Xbox controller - button mappings may need adjustment")
    elif "ps4" in controller_name.lower() or "playstation" in controller_name.lower():
        print("Detected as PlayStation controller - button mappings may need adjustment")
    else:
        print("Unknown controller type - you may need to adjust button mappings in config.py")

# Force debug mode to be on initially to help diagnose controller issues
game.controller_debug = True
print("Controller debug mode enabled by default - press F1 to toggle")

# Enable shield debug mode to help diagnose shield rendering issues
game.shield_debug = True
print("Shield debug mode enabled to diagnose rendering issues")

game.new() 