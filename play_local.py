#!/usr/bin/env python3

'''
Super Smash Bros Local Multiplayer Launcher

This script launches the local version of the game with two player support
using keyboard and controller without needing to set up a server.

Usage:
  python play_local.py

Requirements:
  - Pygame installed (pip install pygame)
  - One keyboard for player 1
  - One controller (optional) for player 2
    - Can also use keyboard for both players if no controller is available
'''

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # Import and run the local game
    from game.LocalGame import LocalGame
    
    print("========== SUPER SMASH BROS - LOCAL MULTIPLAYER ==========")
    print("Player 1 controls: Arrow keys to move, Z for weak attack, X for heavy attack")
    print("Player 2 controls: Controller D-pad/analog stick to move, A for weak attack, B for heavy attack")
    print("                   (or keyboard if no controller is connected)")
    print()
    
    game = LocalGame()
    game.run()
    
except ImportError as e:
    print(f"Error importing game: {e}")
    print("Make sure all required files are present in the src/game directory.")
    
except Exception as e:
    print(f"Error running game: {e}")
    print("Please report this issue if it persists.") 