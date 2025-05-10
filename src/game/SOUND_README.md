# Sound Player for Super Smash Bros - Local Edition

This module provides a robust interface for playing sound effects (.wav files) in the game.

## Features

- Easy playing of sound effects from a single line of code
- Automatic file existence checking (gracefully handles missing files)
- Support for both one-shot and looping sounds
- Volume control
- Sound caching for better performance
- Automatic initialization of the pygame mixer

## Usage

### Basic Usage

```python
from sound_player import SoundPlayer

# Play a sound once (simplest form)
SoundPlayer.play_sound("Select")

# The .wav extension is optional
SoundPlayer.play_sound("Small Hit")
```

### Advanced Usage

```python
# Play a sound at 50% volume
shield_sound = SoundPlayer.play_sound("Shield Block On", volume=0.5)

# Play a sound on repeat
background_sound = SoundPlayer.play_sound("Ambience", repeat=True)

# Stop a specific sound
SoundPlayer.stop_sound(background_sound)

# Stop all playing sounds
SoundPlayer.stop_all_sounds()
```

## Available Sounds

The sound player looks for sound files in the `src/audio` directory. There are many sound effects available, including:

- Character sounds (Yoshi, Pikachu, Samus, etc.)
- Effect sounds (Shield Block, Hits, etc.)
- UI sounds (Select, Start, etc.)
- Environment sounds (Ambience, Tornado, etc.)

Run the `sound_example.py` script to:
1. See examples of how to use the sound player
2. Test sounds interactively

## Sound Example

Run the following to see a demonstration and test sounds:

```
python sound_example.py
```

## Troubleshooting

If you encounter issues with sound playback:

1. Make sure pygame is properly installed
2. Check that the sound file exists in the `src/audio` directory
3. Check the logs for any error messages
4. Ensure the pygame mixer is initialized properly

## Implementation Details

The sound player handles:
- File path resolution
- Sound caching
- Error handling
- Resource management

It logs warnings when a sound file isn't found and errors when playback fails, making it easy to diagnose issues. 