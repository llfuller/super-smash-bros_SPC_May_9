# Super Smash Bros Clone - Project Structure

This document provides a comprehensive overview of the project's directory structure and the role of each Python file in the game.

## Directory Structure

```
.
├── LocalGameLauncher.py     # Root launcher for the local two-player game
├── src/
│   ├── game/
│   │   ├── characters/
│   │   │   ├── Mario.py
│   │   │   ├── Luigi.py
│   │   │   ├── Yoshi.py
│   │   │   ├── Popo.py
│   │   │   ├── Nana.py
│   │   │   ├── Link.py
│   │   │   └── LocalCharacter.py  # Base character class for local multiplayer
│   │   ├── menus/
│   │   │   ├── Intro.py
│   │   │   ├── Start.py
│   │   │   └── Other.py
│   │   ├── objects/
│   │   │   ├── Button.py
│   │   │   ├── CharButton.py
│   │   │   ├── Platform.py
│   │   │   └── ReadyButton.py
│   │   ├── Game.py           # Original networked game
│   │   ├── LocalGame.py      # Local two-player game
│   │   ├── Server.py
│   │   ├── Chat.py
│   │   ├── settings.py
│   │   └── images.py
│   ├── proto/
│   └── images/
```

## Core Game Components

### Game.py

The main game file for the networked version. It initializes the game, manages the game loop, handles player input, updates game state, and renders the game. Key responsibilities include:

- Game initialization and setup
- Menu system management
- Player creation and management
- Communication with the server via UDP
- Chat system integration
- Platform creation and collision detection
- Game state rendering and updates
- Win/loss detection

This is the entry point for players to start the networked game.

### LocalGame.py

A modified version of the game that supports local two-player gameplay without requiring network connectivity. Features include:

- Local game state management without a server
- Support for two players on the same keyboard
- Automatic creation of Player 2 after Player 1 is ready
- Dedicated controls for each player (Arrow keys vs. WASD)
- Same gameplay mechanics as the networked version

### LocalGameLauncher.py

Located in the root directory, this is the entry point for starting the local two-player game. It:

- Sets up the Python path to properly import game modules
- Changes the working directory for asset loading
- Displays control information
- Launches the LocalGame

### Server.py

The server component that enables multiplayer functionality using UDP. It handles:

- Player connections and disconnections
- Player name validation
- Character selection
- Game state synchronization
- Attack and damage calculations
- Win detection
- Game restart functionality

The server maintains a shared game state for all connected players and broadcasts updates to keep all clients synchronized.

### Chat.py

Implements a TCP-based chat system using Protocol Buffers for message serialization. Features include:

- Creating and joining chat lobbies
- Sending and receiving chat messages
- Player connection/disconnection notifications
- Message history management

This module works alongside the main game to provide communication between players.

### settings.py

Contains all game configuration constants, including:

- Game dimensions and FPS settings
- Game state enumerations
- Character names
- Player direction and movement constants
- Physics values (friction, velocity)
- Color definitions

This centralized configuration makes it easy to tweak game parameters.

### images.py

Manages all game images and assets, loading them into memory for use by other components.

## Character System

The `characters/` directory contains a class for each playable character:

- **Mario.py, Luigi.py, Yoshi.py, Popo.py, Nana.py, Link.py**: Each file defines a character class with unique attributes, animations, and attack patterns. All characters share a common base structure but have different sprites and potentially different abilities.

- **LocalCharacter.py**: A base character class for the local two-player game that doesn't rely on hardcoded keyboard input. It provides a more modular approach to character control, allowing different key mappings for different players.

Each character implements movement mechanics, attack patterns, health management, and collision detection.

## Menu System

The `menus/` directory contains classes for different game screens:

- **Intro.py**: Handles the main introduction screen with game title and menu options.
- **Start.py**: Manages the character selection and game setup screens.
- **Other.py**: Implements auxiliary screens like the guide and about pages.

These menu classes handle user input, screen transitions, and UI rendering for their respective screens.

## Game Objects

The `objects/` directory contains classes for various game elements:

- **Button.py**: Base button class for UI interaction.
- **CharButton.py**: Specialized button for character selection.
- **ReadyButton.py**: Button used to indicate player readiness.
- **Platform.py**: Creates platforms in the game arena that players can stand on and interact with.

## Networking Architecture

The game offers two play modes:

1. **Networked Mode**:
   - Uses a client-server architecture with UDP for game state and TCP for chat
   - Requires running the Server.py separately
   - Supports 2-6 players across different computers

2. **Local Mode**:
   - Plays entirely on one computer
   - Supports two players with different control schemes
   - No network connectivity required

## How to Play

### Networked Mode:
1. Start the server: `python Server.py`
2. Launch the game: `python Game.py <server_ip_address>`
3. Enter your player name and select a character
4. Wait for other players to join and press "Ready"
5. Battle other players in the arena!

### Local Mode:
1. Run from the root directory: `python LocalGameLauncher.py`
2. Enter a name and select a character for Player 1
3. Player 2 will be automatically set up
4. Battle in the arena with two players on the same keyboard!

## Controls

### Networked Mode (All Players):
- Arrow keys: Move character
- Z: Weak attack
- X: Heavy attack
- Enter: Toggle chat mode

### Local Mode:
**Player 1:**
- Arrow keys: Move character
- Z: Weak attack
- X: Heavy attack

**Player 2:**
- WASD: Move character
- G: Weak attack
- H: Heavy attack

**Both Modes (After a Game):**
- R: Request restart
- M: Return to main menu
- Q: Quit game

## Development Notes

- The game uses Pygame for rendering and input handling
- Protocol Buffers are used for TCP message serialization in the chat system
- The networked game supports 2-6 players
- The local game supports exactly 2 players on the same keyboard
- Each game session tracks player stats like health, position, and status 