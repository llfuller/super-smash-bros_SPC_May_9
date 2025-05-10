'''
Super Smash Bros - Local Two-Player Edition Launcher

This script launches the local two-player version of the game that doesn't require
a separate server or network connection.
'''

import sys
import os

# Add the src directory to the Python path to allow imports from the game modules
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Set the working directory to the src/game path for proper asset loading
game_dir = os.path.join(src_dir, 'game')
os.chdir(game_dir)

print("=== Super Smash Bros - Local Two-Player Edition Launcher ===")
print()
print("Controls:")
print("Player 1:")
print("- Arrow keys: Movement")
print("- Z: Weak attack")
print("- X: Heavy attack")
print()
print("Player 2:")
print("- WASD keys: Movement")
print("- G: Weak attack")
print("- H: Heavy attack")
print()
print("Starting the game...")

# Import and run the local game
from game.LocalGame import LocalGame

game = LocalGame()
game.new() 