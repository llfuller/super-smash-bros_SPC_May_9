# Super Smash Bros - Local Two-Player Edition

This version of the game allows you to play with two players on a single computer without requiring a network connection or a separate server.

## How to Run

1. Navigate to the `src/game` directory
2. Run the launcher:
   ```
   python LocalGameLauncher.py
   ```

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

## Troubleshooting

If you encounter any issues:

- Make sure you're running from the `src/game` directory
- Ensure you have Pygame installed: `pip install pygame`
- Check the console for any error messages

## Developer Notes

This local version was created by internalizing the server functionality from the original networked game. The implementation maintains compatibility with the original menu system and character classes for a seamless experience. 