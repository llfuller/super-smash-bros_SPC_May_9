'''
Super Smash Bros - Local Two-Player Edition Launcher

This script launches the local two-player version of the game that doesn't require
a separate server or network connection.
'''

import sys
import os

# Get the directory where this script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)  # Change to this directory to ensure relative paths work

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
from LocalGame import LocalGame

game = LocalGame()
game.new() 