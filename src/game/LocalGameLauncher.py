'''
Super Smash Bros - Local Two-Player Edition Launcher

This script launches the local two-player version of the game that doesn't require
a separate server or network connection.

The game uses authentic Super Smash Bros Melee physics for realistic gameplay.
'''

import sys
import os

# Simply use the current directory as the game directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Just make sure we're in the game directory (already are, but to be safe)
os.chdir(current_dir)

print("=== Super Smash Bros - Local Two-Player Edition Launcher ===")
print()
print("Controls:")
print("Player 1:")
print("- Arrow keys: Movement")
print("- DOWN: Fast fall (when already falling)")
print("- Z: Weak attack")
print("- X: Heavy attack")
print()
print("Player 2:")
print("- WASD keys: Movement")
print("- S: Fast fall (when already falling)")
print("- G: Weak attack")
print("- H: Heavy attack")
print()
print("Game Features:")
print("- Authentic Super Smash Bros Melee physics")
print("- Character sizes match real Melee proportions")
print("- Realistic knockback formula based on damage percentage")
print("- Accurate movement speeds and acceleration values")
print()
print("Starting the game...")

# Since we're already in the game directory, import directly
from LocalGame import LocalGame

game = LocalGame()
game.new() 