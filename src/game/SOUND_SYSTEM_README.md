# Sound System for Super Smash Bros - Local Edition

The sound system provides a comprehensive way to add sound effects and background music to the game. It consists of two main components:

## Components

1. **SoundPlayer**: A low-level class that handles direct playback of .wav and .mp3 files
2. **SoundManager**: A high-level class that manages game sounds by category and context

## Features

- Background music (MP3) for menus and battles
- Character-specific stage music
- Character-specific victory themes
- UI sound effects (button clicks, selections)
- Character-specific attack sounds
- Character-specific jump sounds
- Hit sounds based on damage intensity
- Shield sounds (activation, deactivation, blocking, breaking)
- Sound caching for better performance
- Mute functionality

## How Sounds Are Organized

Sounds are organized in categories within the `SoundManager` class:

- **UI_SOUNDS**: Menu and interface sounds (.wav)
- **HIT_SOUNDS**: Impact sounds when attacks connect (.wav)
- **ATTACK_SOUNDS**: Sounds when characters attack (before hit) (.wav)
- **SHIELD_SOUNDS**: Shield activation/deactivation/breaking sounds (.wav)
- **JUMP_SOUNDS**: Sounds when characters jump (.wav)
- **CHARACTER_SOUNDS**: Character-specific sounds (.wav)
- **BACKGROUND_MUSIC**: Music tracks for different game sections (.mp3)
- **STAGE_MUSIC**: Stage-specific battle music (.mp3)

## Integration Points

The sound system has been integrated at the following points:

1. **Menu Navigation**: 
   - Button clicks
   - Character selection music
   - Menu music
   - Hover effects

2. **Game Actions**:
   - Character attacks (weak and heavy)
   - Taking damage
   - Shield activation/deactivation
   - Shield blocks and breaks
   - Character jumps (standard, short hop, high jump)

3. **Game State Changes**:
   - Starting the game (with stage-specific music)
   - Winning a match (with character-specific victory music)
   - Menu navigation
   - Game restart (with new random stage music)

## Usage Examples

```python
# Play UI sounds
sound_manager.play_ui_sound('select')
sound_manager.play_ui_sound('start')

# Play hit sounds based on damage amount
sound_manager.play_damage_sound(damage_amount)

# Play character-specific sounds
sound_manager.play_character_sound('Mario', 'attack_weak')

# Play jump sounds
sound_manager.play_jump_sound('Mario', 'standard')
sound_manager.play_jump_sound('Samus', 'high_jump')
sound_manager.play_jump_sound(character=None, jump_type='short_hop')  # Generic short hop sound

# Play shield sounds
sound_manager.play_shield_sound('on')
sound_manager.play_shield_sound('hit')

# Play and control background music
sound_manager.play_background_music('menu')
sound_manager.play_background_music('battle', stage='hyrule')
sound_manager.play_background_music('character_select')

# Play victory music
sound_manager.play_victory_music('Mario')

# Stop background music
sound_manager.stop_background_music()

# Mute/unmute sounds
sound_manager.toggle_mute()
```

## Supported File Types

- **WAV**: Used for short sound effects like attacks, hits, UI sounds
- **MP3**: Used for longer music tracks, stage music, and victory themes

## How to Add New Sounds

1. Add sound files to the `src/audio` directory:
   - Short effects as .wav files
   - Music tracks as .mp3 files
2. Update the appropriate category in `SoundManager` class
3. Call the appropriate methods where you want the sounds to play

## Music Organization

The music is organized into specific categories:

1. **Menu Music**: Played in the main menu and character select screens
2. **Battle Music**: Stage-specific music played during battles
3. **Victory Music**: Character-specific victory themes played when a player wins
4. **Bonus Music**: Special music for bonus stages or events

## Jump Sound System

The jump sound system includes three types of jumps:
- **Standard Jump**: Default jump sounds
- **Short Hop**: Quicker, shorter jump sounds
- **High Jump**: More powerful jump sounds (used by characters like Samus)

Character-specific jump sounds are prioritized when available.

## Technical Details

- All sounds are loaded from the `src/audio` directory
- MP3 files are played using pygame's music module for better streaming
- WAV files are played using pygame's Sound objects for minimal latency
- Character-specific sounds are mapped by character name
- Sound effects are chosen randomly from categories to add variety
- Background music loops continuously until stopped or changed
- Audio files are loaded on-demand to improve performance 