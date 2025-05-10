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

### Controller Support
The game now supports the Nintendo Switch Pro Controller for Player 1:

- **Movement**: Left Stick or D-pad
- **Jump**: Up on D-pad or Left Stick
- **Fast Fall**: Down on D-pad or Left Stick (when falling)
- **Weak Attack**: B button
- **Heavy Attack**: Y button
- **Restart Game**: Plus button (after match)
- **Return to Menu**: Minus button (after match) 
- **Quit Game**: Home button (after match)
- **Toggle Debug**: F1 key (shows controller input values in console)

Note: Controller button mappings may need adjustment depending on your system. Edit the `PRO_CONTROLLER` settings in `config.py` if you experience issues with button assignments.

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
5. **Controller Support**: Player 1 can use a Nintendo Switch Pro Controller or similar gamepad

## Troubleshooting

If you encounter any issues:

- Make sure you're running from the `src/game` directory
- Ensure you have Pygame installed: `pip install pygame`
- Check the console for any error messages

### Controller Troubleshooting

If your controller isn't being detected or working properly:

1. **Run the Controller Test Utility**: 
   ```
   python controller_test.py
   ```
   This will show you real-time information about your controller's inputs.

2. **Connection Issues**:
   - Make sure the controller is connected before launching the game
   - Try unplugging and reconnecting your controller
   - Restart the game after connecting the controller
   - Some controllers work better with USB connections rather than Bluetooth

3. **Driver Issues**:
   - Switch Pro Controllers may need special drivers on Windows
   - Xbox controllers typically work out of the box on Windows
   - PlayStation controllers might require additional software

4. **Button Mapping**:
   - If buttons are detected but mapped incorrectly, use the F1 debug mode
   - Note the button numbers when pressed
   - Edit the button mappings in `config.py` based on the detected values

5. **Still Not Working**:
   - Some controllers aren't compatible with Pygame
   - Try using a different controller if available
   - Default back to keyboard controls if necessary

## Developer Notes

This local version was created by internalizing the server functionality from the original networked game. The implementation maintains compatibility with the original menu system and character classes for a seamless experience. 