# Super Smash Bros - Local Two-Player Edition

This version of the game allows you to play with two players on a single computer without requiring a network connection or a separate server.

## How to Run

Simply run the launcher from the root directory:
```
python LocalGameLauncher.py
```

No need to navigate to the src/game directory or set up a server!

## Controls

### Player 1
- **Movement**: Arrow keys
- **Jump**: Up arrow
- **Weak Attack**: Z key
- **Heavy Attack**: X key

### Player 2 
- **Movement**: WASD keys
- **Jump**: W key
- **Weak Attack**: G key
- **Heavy Attack**: H key

## Game Flow

1. Start at the intro screen
2. Enter your name and select your character for Player 1
3. **Player 2 is automatically set up** with a random character
4. Battle in the arena immediately after Player 1 is ready
5. Winner is determined when one player's health reaches 0
6. After the match:
   - **R**: Restart the game with the same characters
   - **M**: Return to the main menu
   - **Q**: Quit the game

## How It Works

The local version maintains the same gameplay mechanics as the original networked version, but:

1. **Eliminates Network Requirements**: All game state is handled locally without socket communications
2. **Two Player Management**: Supports two players on the same keyboard with different control schemes
3. **Same Game Features**: Maintains character selection, platforming, attacking, and win detection
4. **Automatic Player 2**: Sets up the second player automatically when Player 1 is ready
5. **Separate Controls**: Each player has their own dedicated control scheme to avoid conflicts

## Key Improvements

Compared to the original networked game, this local version offers:

1. **Simplified Setup**: No server needed, just run a single file
2. **Immediate Play**: Get into the action with minimal setup
3. **Local Gameplay**: Perfect for playing with a friend on the same computer
4. **No Self-Damage**: Players can't damage themselves when attacking
5. **Custom Controls**: Designed specifically for two-player local play

## Troubleshooting

If you encounter any issues:

- Ensure you have Pygame installed: `pip install pygame`
- Run from the root directory of the project
- Make sure both control schemes are working (arrow keys for Player 1, WASD for Player 2)
- Check the console for any error messages

## Developer Notes

This local version was created by internalizing the server functionality from the original networked game. The implementation uses:

- A custom `LocalCharacter` class to handle different control schemes
- Player-specific enemy groups to prevent self-damage
- Automatic Player 2 setup for streamlined gameplay
- Path handling that works from the root directory 