# Super Smash Bros Clone - Project Structure

This document provides a comprehensive overview of the project's directory structure and the role of each Python file in the game.

## Directory Structure

```
.
├── src/
│   ├── game/
│   │   ├── characters/
│   │   │   ├── Mario.py
│   │   │   ├── Luigi.py
│   │   │   ├── Yoshi.py
│   │   │   ├── Popo.py
│   │   │   ├── Nana.py
│   │   │   └── Link.py
│   │   ├── menus/
│   │   │   ├── Intro.py
│   │   │   ├── Start.py
│   │   │   └── Other.py
│   │   ├── objects/
│   │   │   ├── Button.py
│   │   │   ├── CharButton.py
│   │   │   ├── Platform.py
│   │   │   └── ReadyButton.py
│   │   ├── Game.py
│   │   ├── Server.py
│   │   ├── Chat.py
│   │   ├── LocalGame.py
│   │   ├── settings.py
│   │   └── images.py
│   ├── proto/
│   └── images/
├── play_local.py
```

## Core Game Components

### Game.py

The main game file that brings everything together. It initializes the game, manages the game loop, handles player input, updates game state, and renders the game. Key responsibilities include:

- Game initialization and setup
- Menu system management
- Player creation and management
- Communication with the server via UDP
- Chat system integration
- Platform creation and collision detection
- Game state rendering and updates
- Win/loss detection

This is the entry point for players to start the game.

### LocalGame.py

A standalone local multiplayer version of the game that doesn't require a server. Key features:

- Support for two players on a single instance
- Keyboard controls for player 1
- Controller support for player 2 (with keyboard fallback if no controller is connected)
- Character selection for both players
- Local game state management
- Simplified UI for local play

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

The game uses a client-server architecture with:

1. **UDP Communication** (via Server.py): For real-time game state updates where occasional packet loss is acceptable
2. **TCP Communication** (via Chat.py): For reliable chat messaging where all messages must be delivered in order

## Local Multiplayer Mode

The local multiplayer mode allows you to play with two players on a single instance without needing to set up a server.

### How to Play in Local Multiplayer Mode

1. Run the game launcher: `python play_local.py`
2. Use the keyboard and an optional controller to play with two players
3. Select characters for both players (Player 1 selects first, then Player 2)
4. Battle in a local arena without server requirements

### Controls for Local Multiplayer

#### Player 1 (Keyboard)
- Arrow Keys: Move character
- Up Arrow: Jump
- Z: Weak attack
- X: Heavy attack

#### Player 2 (Controller)
- D-pad or Left Analog Stick: Move character
- D-pad Up or Left Stick Up: Jump
- Button A (or equivalent): Weak attack
- Button B (or equivalent): Heavy attack

If no controller is connected, Player 2 can also use the keyboard.

### Advantages of Local Multiplayer
- No server setup required
- Quick to start and play
- Same gameplay experience as the networked version
- Support for gamepads/controllers
- Easy character selection process

## How to Play (Original Network Mode)

1. Start the server: `python Server.py`
2. Launch the game: `python Game.py <server_ip_address>`
3. Enter your player name and select a character
4. Wait for other players to join and press "Ready"
5. Battle other players in the arena!

## Controls

- Arrow keys: Move character
- Z: Weak attack
- X: Heavy attack
- Enter: Toggle chat mode
- R: Request restart (after a game)
- M: Return to main menu (after a game)
- Q: Quit game (after a game)

## Development Notes

- The game uses Pygame for rendering and input handling
- Protocol Buffers are used for TCP message serialization in the chat system
- The game supports 2-6 players in multiplayer mode
- Each game session tracks player stats like health, position, and status 