"""
Sound Manager for Super Smash Bros - Local Edition

This module manages all game sounds and background music,
providing specific sound effects for different game events.
"""

import os
import random
import time
from sound_player import SoundPlayer

class SoundManager:
    """
    Sound Manager for the game that handles character-specific sounds,
    battle sounds, UI sounds, and background music.
    """
    
    # Sound categories
    UI_SOUNDS = {
        'select': 'Select',
        'start': 'Start',
        'pause': 'Pause',
        'select_alt': 'Select 2',
        'select_alt2': 'Select 3'
    }
    
    HIT_SOUNDS = {
        'weak': ['Small Hit', 'Small Hit 2', 'Small Hit (JAP)', 'Small Hit 2 (JAP)'],
        'medium': ['Moderate Hit', 'Moderate Hit 2', 'Moderate Hit (JAP)', 'Moderate Hit 2 (JAP)'],
        'strong': ['Strong Hit', 'Strong Hit (JAP)', 'Smash Hit', 'Smash Hit (JAP)']
    }
    
    ATTACK_SOUNDS = {
        'weak': ['Small Whiff', 'Small Whoosh', 'Whiff', 'Swiff'],
        'heavy': ['Strong Whiff', 'Strong Whoof', 'Moderate Whiff', 'Moderate Whoof', 'Whoosher']
    }
    
    SHIELD_SOUNDS = {
        'on': 'Shield Block On',
        'off': 'Shield Block Off',
        'break': 'Shield Block Break',
        'hit': ['Ness - Shield Block', 'Ness - Shield Block 2']
    }
    
    # Jump sounds
    JUMP_SOUNDS = {
        'standard': ['Whoosh', 'Swiff', 'Small Whoosh', 'Whiff'],
        'short_hop': ['Whow', 'Twow', 'Swiff'],
        'high_jump': ['Whip', 'Whoosher', 'Strong Whiff']
    }
    
    # Character voice sounds - repurposed from available sounds
    VOICE_SOUNDS = {
        # General voices - used when character-specific not available
        'attack_weak': ['Whow', 'Powp'],
        'attack_heavy': ['Whow', 'Ta-Tap', 'Twow'],
        'jump': ['Whow', 'Powp', 'Twow'],
        'damage_light': ['Whow', 'Twow'],
        'damage_heavy': ['Twow', 'Throw'],
        'shield_break': ['Whow'],
        
        # Character-specific voices
        'Mario': {
            'attack_weak': ['Powp', 'Whow'],
            'attack_heavy': ['Twow', 'Whow'],
            'jump': ['Powp', 'Whow'],
            'damage': ['Twow', 'Whow']
        },
        'Luigi': {
            'attack_weak': ['Powp', 'Whow'],
            'attack_heavy': ['Twow'],
            'jump': ['Powp', 'Whow'],
            'damage': ['Twow', 'Whow']
        },
        'Yoshi': {
            'attack_weak': ['Yoshi - Egg Pop', 'Yoshi - Tongue'],
            'attack_heavy': ['Yoshi - Egg Throw Pop'],
            'jump': ['Yoshi - Egg Pop'],
            'damage': ['Yoshi - Egg Pop']
        },
        'Link': {
            'attack_weak': ['Twow'],
            'attack_heavy': ['Whow', 'Throw'],
            'jump': ['Powp'],
            'damage': ['Twow', 'Whow']
        },
        'Samus': {
            'attack_weak': ['Samus - Beam', 'Samus - Small Beam Blast'],
            'attack_heavy': ['Samus - Beam Blast'],
            'jump': ['Samus - Super High Jump'],
            'damage': ['Samus - Beam Up']
        }
    }
    
    # Character-specific sounds
    CHARACTER_SOUNDS = {
        'Mario': {
            'attack_weak': ['Small Hit', 'Small Hit 2'],
            'attack_heavy': ['Strong Hit', 'Moderate Hit'],
            'victory': '30. Victory! [Super Mario Bros.]',
            'jump': ['Small Whoosh', 'Whoosh']
        },
        'Luigi': {
            'attack_weak': ['Small Hit', 'Small Hit 2'],
            'attack_heavy': ['Strong Hit', 'Moderate Hit'],
            'victory': '30. Victory! [Super Mario Bros.]',
            'jump': ['Small Whoosh', 'Whoosh']
        },
        'Yoshi': {
            'attack_weak': ['Yoshi - Tongue', 'Small Hit'],
            'attack_heavy': ['Yoshi - Egg Throw', 'Yoshi - Egg Throw Pop'],
            'special': ['Yoshi - Egg Pop'],
            'victory': '31. Victory! [Yoshi]',
            'jump': ['Swiff', 'Whoosh']
        },
        'Popo': {
            'attack_weak': ['Small Hit', 'Strong Sword Smack'],
            'attack_heavy': ['Strong Sword Smack', 'Strong Hit'],
            'jump': ['Swiff', 'Small Whoosh']
        },
        'Nana': {
            'attack_weak': ['Small Hit', 'Strong Sword Smack'],
            'attack_heavy': ['Strong Sword Smack', 'Strong Hit'],
            'jump': ['Swiff', 'Small Whoosh']
        },
        'Link': {
            'attack_weak': ['Small Sword Hit', 'Moderate Sword Hit'],
            'attack_heavy': ['Strong Sword Smack', 'Unsheath Sword'],
            'victory': '33. Victory! [Link]',
            'jump': ['Strong Whiff', 'Whoosh']
        },
        'Samus': {
            'attack_weak': ['Samus - Small Beam Blast', 'Samus - Beam'],
            'attack_heavy': ['Samus - Beam Blast', 'Samus - Charging Beam Full'],
            'special': ['Samus - Charging Beam', 'Samus - Bomb Deploy', 'Samus - Grappling Hook'],
            'victory': '34. Victory! [Samus]',
            'jump': ['Samus - Super High Jump', 'Whoosh']
        },
        'Pikachu': {
            'attack_weak': ['Pikachu - Electrical Attack', 'Pikachu - Electric'],
            'attack_heavy': ['Pikachu - Thunderbolt', 'Pikachu - Thunderbolt Rising'],
            'special': ['Pikachu - Electrical', 'Pikachu - Electrical Flow', 'Pikachu - Speed Jump Begin'],
            'victory': '37. Victory! [Pokémon]',
            'jump': ['Whoosh', 'Strong Whiff']
        }
    }
    
    # Background music - now using MP3 files
    BACKGROUND_MUSIC = {
        'menu': ['04. Mode Select', '05. Character Select'],  # Menu music
        'character_select': ['05. Character Select'],  # Specific character select music
        'battle': [
            '07. Hyrule Castle [The Legend of Zelda]',
            '08. Yoshi\'s Island [Yoshi\'s Story]',
            '09. Sector Z [Star Fox 64]',
            '10. Peach\'s Castle [Super Mario Bros.]',
            '11. Saffron City [Pokémon Red, Green & Blue]',
            '12. Kongo Jungle [Donkey Kong Country]',
            '13. Dream Land [Kirby Super Star]',
            '14. Planet Zebes [Metroid]',
            '23. Final Destination'
        ],
        'bonus': ['17. Bonus Stage'],
        'victory': ['30. Victory! [Super Mario Bros.]']  # Default victory music
    }
    
    # Stage-specific music for more variety
    STAGE_MUSIC = {
        'hyrule': '07. Hyrule Castle [The Legend of Zelda]',
        'yoshi': '08. Yoshi\'s Island [Yoshi\'s Story]',
        'sector_z': '09. Sector Z [Star Fox 64]',
        'mushroom': '10. Peach\'s Castle [Super Mario Bros.]',
        'saffron': '11. Saffron City [Pokémon Red, Green & Blue]',
        'kongo': '12. Kongo Jungle [Donkey Kong Country]',
        'dreamland': '13. Dream Land [Kirby Super Star]',
        'zebes': '14. Planet Zebes [Metroid]',
        'final': '23. Final Destination'
    }
    
    def __init__(self):
        """Initialize the Sound Manager"""
        self.current_bg_music = None
        self.mute = False
        
        # Track recent sound effects for display
        self.recent_sounds = []  # List of (timestamp, sound_type, sound_name, description)
        self.recent_sounds_max_age = 4.0  # How many seconds to keep sounds in history
        
    def _add_recent_sound(self, sound_type, sound_name, description=None):
        """
        Add a sound to the recent sounds list
        
        Args:
            sound_type (str): Category of sound (e.g., 'hit', 'jump', 'attack')
            sound_name (str): Name of the sound file or effect
            description (str): Optional additional details (e.g., character name)
        """
        # Create record with current timestamp
        timestamp = time.time()
        
        # Create a friendly description if none provided
        if description is None:
            description = f"{sound_type.capitalize()}: {sound_name}"
        
        # Add to recent sounds
        self.recent_sounds.append((timestamp, sound_type, sound_name, description))
        
        # Clean up old sounds
        self._clean_recent_sounds()
        
    def _clean_recent_sounds(self):
        """Remove sounds older than the max age"""
        current_time = time.time()
        self.recent_sounds = [
            sound for sound in self.recent_sounds 
            if current_time - sound[0] <= self.recent_sounds_max_age
        ]
        
    def get_recent_sounds(self):
        """
        Get list of recent sounds (cleaned of expired sounds)
        
        Returns:
            list: List of (timestamp, sound_type, sound_name, description) tuples
        """
        self._clean_recent_sounds()
        return self.recent_sounds
        
    def play_ui_sound(self, sound_type):
        """Play a UI sound"""
        if self.mute:
            return None
            
        if sound_type in self.UI_SOUNDS:
            sound_name = self.UI_SOUNDS[sound_type]
            # Add to recent sounds
            self._add_recent_sound('ui', sound_name, f"UI: {sound_type}")
            return SoundPlayer.play_sound(sound_name)
        return None
        
    def play_jump_sound(self, character=None, jump_type='standard'):
        """
        Play a jump sound, either character-specific or generic
        
        Args:
            character (str): Character name or character type
            jump_type (str): Type of jump ('standard', 'short_hop', 'high_jump')
            
        Returns:
            pygame.mixer.Sound or None: The sound object if played successfully
        """
        if self.mute:
            return None
            
        # Play both the jump sound effect and the character voice
        jump_sound = None
        sound_name = None
        
        # First try to play character-specific jump sound if available
        if character:
            # Check for exact character name match
            for char_name, sounds in self.CHARACTER_SOUNDS.items():
                if char_name.lower() == character.lower() and 'jump' in sounds:
                    sound_name = random.choice(sounds['jump']) if isinstance(sounds['jump'], list) else sounds['jump']
                    jump_sound = SoundPlayer.play_sound(sound_name)
                    break
                
            # If no exact match, check for partial character name match (e.g., 'mario' in 'LocalMario')
            if not jump_sound:
                for char_name, sounds in self.CHARACTER_SOUNDS.items():
                    if char_name.lower() in character.lower() and 'jump' in sounds:
                        sound_name = random.choice(sounds['jump']) if isinstance(sounds['jump'], list) else sounds['jump']
                        jump_sound = SoundPlayer.play_sound(sound_name)
                        break
                    
        # Fall back to generic jump sound based on jump type
        if not jump_sound and jump_type in self.JUMP_SOUNDS:
            sound_name = random.choice(self.JUMP_SOUNDS[jump_type])
            jump_sound = SoundPlayer.play_sound(sound_name)
            
        # Ultimate fallback
        if not jump_sound:
            sound_name = random.choice(['Whoosh', 'Swiff', 'Small Whoosh'])
            jump_sound = SoundPlayer.play_sound(sound_name)
        
        # Add to recent sounds with character info if available
        char_str = character if character else "Character"
        self._add_recent_sound('jump', sound_name, f"{char_str} {jump_type}")
            
        # Now play the voice sound if available
        if character:
            self.play_voice_sound(character, 'jump')
        
        return jump_sound
        
    def play_voice_sound(self, character=None, action_type='jump', volume=0.7):
        """
        Play a character voice sound for a specific action
        
        Args:
            character (str): Character name or character type
            action_type (str): Type of action ('jump', 'attack_weak', 'attack_heavy', 'damage', etc.)
            volume (float): Volume level from 0.0 to 1.0
            
        Returns:
            pygame.mixer.Sound or None: The sound object if played successfully
        """
        if self.mute:
            return None
            
        # First try character-specific voice
        if character:
            # Get normalized character name
            char_name = None
            
            # Check for exact character match
            for name in self.VOICE_SOUNDS:
                if isinstance(self.VOICE_SOUNDS[name], dict) and name.lower() == character.lower():
                    char_name = name
                    break
                    
            # If no exact match, check for partial character name match
            if not char_name:
                for name in self.VOICE_SOUNDS:
                    if isinstance(self.VOICE_SOUNDS[name], dict) and name.lower() in character.lower():
                        char_name = name
                        break
            
            # If we found a character match
            if char_name:
                # Check if the specific action type exists for this character
                if action_type in self.VOICE_SOUNDS[char_name]:
                    sound_options = self.VOICE_SOUNDS[char_name][action_type]
                    if isinstance(sound_options, list):
                        sound_name = random.choice(sound_options)
                    else:
                        sound_name = sound_options
                    
                    # Add to recent sounds
                    self._add_recent_sound('voice', sound_name, f"{char_name} voice: {action_type}")
                    
                    # Use a slightly lower volume for the voice
                    return SoundPlayer.play_sound(sound_name, volume=volume)
                    
                # If the specific action doesn't exist but 'damage' is available for general damage actions
                elif action_type.startswith('damage') and 'damage' in self.VOICE_SOUNDS[char_name]:
                    sound_options = self.VOICE_SOUNDS[char_name]['damage']
                    if isinstance(sound_options, list):
                        sound_name = random.choice(sound_options)
                    else:
                        sound_name = sound_options
                    
                    # Add to recent sounds
                    self._add_recent_sound('voice', sound_name, f"{char_name} voice: {action_type}")
                    
                    # Use a slightly lower volume for the voice
                    return SoundPlayer.play_sound(sound_name, volume=volume)
        
        # Fallback to generic voice sounds
        if action_type in self.VOICE_SOUNDS:
            sound_options = self.VOICE_SOUNDS[action_type]
            if isinstance(sound_options, list):
                sound_name = random.choice(sound_options)
            else:
                sound_name = sound_options
                
            # Add to recent sounds
            self._add_recent_sound('voice', sound_name, f"Voice: {action_type}")
                
            # Use a slightly lower volume for the voice
            return SoundPlayer.play_sound(sound_name, volume=volume)
            
        return None
        
    def play_hit_sound(self, intensity='medium'):
        """Play a hit sound based on intensity (weak, medium, strong)"""
        if self.mute:
            return None
            
        if intensity in self.HIT_SOUNDS:
            sound_name = random.choice(self.HIT_SOUNDS[intensity])
            # Add to recent sounds
            self._add_recent_sound('hit', sound_name, f"Hit: {intensity}")
            return SoundPlayer.play_sound(sound_name)
        return None
        
    def play_attack_sound(self, attack_type='weak', character=None):
        """
        Play an attack sound (weak or heavy) with character voice
        
        Args:
            attack_type (str): Type of attack ('weak' or 'heavy')
            character (str): Character making the attack (for voice sound)
            
        Returns:
            pygame.mixer.Sound: The attack sound object
        """
        if self.mute:
            return None
            
        # Play the attack sound effect
        attack_sound = None
        if attack_type in self.ATTACK_SOUNDS:
            sound_name = random.choice(self.ATTACK_SOUNDS[attack_type])
            attack_sound = SoundPlayer.play_sound(sound_name)
            
            # Add to recent sounds with character info if available
            char_str = character if character else "Character"
            self._add_recent_sound('attack', sound_name, f"{char_str} {attack_type} attack")
        
        # Play the character voice if specified
        if character:
            voice_action = 'attack_weak' if attack_type == 'weak' else 'attack_heavy'
            self.play_voice_sound(character, voice_action)
            
        return attack_sound
        
    def play_shield_sound(self, shield_action):
        """Play a shield sound (on, off, break, hit)"""
        if self.mute:
            return None
            
        if shield_action in self.SHIELD_SOUNDS:
            sound = self.SHIELD_SOUNDS[shield_action]
            if isinstance(sound, list):
                sound = random.choice(sound)
            
            # Add to recent sounds
            self._add_recent_sound('shield', sound, f"Shield: {shield_action}")
            
            return SoundPlayer.play_sound(sound)
        return None
    
    def play_character_sound(self, character, sound_type):
        """Play a character-specific sound"""
        if self.mute:
            return None
            
        if character in self.CHARACTER_SOUNDS:
            if sound_type in self.CHARACTER_SOUNDS[character]:
                sound_name = random.choice(self.CHARACTER_SOUNDS[character][sound_type]) if isinstance(self.CHARACTER_SOUNDS[character][sound_type], list) else self.CHARACTER_SOUNDS[character][sound_type]
                
                # Add to recent sounds
                self._add_recent_sound('character', sound_name, f"{character}: {sound_type}")
                
                return SoundPlayer.play_sound(sound_name)
        return None
        
    def play_damage_sound(self, damage_amount, character=None):
        """
        Play a damage sound based on damage amount with character voice
        
        Args:
            damage_amount (float): Amount of damage taken
            character (str): Character taking damage (for voice sound)
            
        Returns:
            pygame.mixer.Sound: The damage sound object
        """
        if self.mute:
            return None
            
        # Play appropriate hit sound based on damage amount
        hit_sound = None
        intensity = "weak"
        
        if damage_amount >= 20:
            hit_sound = self.play_hit_sound('strong')
            intensity = "strong"
            # Play character voice for heavy damage
            if character:
                self.play_voice_sound(character, 'damage_heavy')
        elif damage_amount >= 10:
            hit_sound = self.play_hit_sound('medium')
            intensity = "medium"
            # Play character voice for medium damage
            if character:
                self.play_voice_sound(character, 'damage_light')
        else:
            hit_sound = self.play_hit_sound('weak')
            # Don't play voice for very light damage
        
        # Add to recent sounds with damage details
        char_str = character if character else "Character"
        self._add_recent_sound('damage', f"{intensity} hit", f"{char_str} took {damage_amount:.1f}% damage")
            
        return hit_sound
    
    def play_background_music(self, music_type='menu', stage=None, fade_in_ms=500):
        """
        Play background music based on game context
        
        Args:
            music_type (str): Type of music ('menu', 'character_select', 'battle', 'bonus', 'victory')
            stage (str): Optional stage name for stage-specific music
            fade_in_ms (int): Fade in time in milliseconds
        """
        if self.mute:
            return None
            
        # Stop current background music if any
        if self.current_bg_music:
            SoundPlayer.stop_music()
            
        # Play stage-specific music if specified
        if music_type == 'battle' and stage and stage in self.STAGE_MUSIC:
            music_name = self.STAGE_MUSIC[stage]
            self.current_bg_music = SoundPlayer.play_music(music_name, repeat=True, volume=0.7, fade_in_ms=fade_in_ms)
            
            # Add to recent sounds
            self._add_recent_sound('music', music_name, f"Music: {stage} stage")
            
            return self.current_bg_music
            
        # Play music from the selected category
        if music_type in self.BACKGROUND_MUSIC:
            sound_name = random.choice(self.BACKGROUND_MUSIC[music_type])
            self.current_bg_music = SoundPlayer.play_music(sound_name, repeat=True, volume=0.7, fade_in_ms=fade_in_ms)
            
            # Add to recent sounds
            self._add_recent_sound('music', sound_name, f"Music: {music_type}")
            
            return self.current_bg_music
        return None
        
    def play_victory_music(self, character=None):
        """Play victory music for a specific character"""
        if self.mute:
            return None
            
        # Stop current background music if any
        if self.current_bg_music:
            SoundPlayer.stop_music()
            
        # Try to play character-specific victory theme
        if character and character in self.CHARACTER_SOUNDS:
            if 'victory' in self.CHARACTER_SOUNDS[character]:
                victory_theme = self.CHARACTER_SOUNDS[character]['victory']
                self.current_bg_music = SoundPlayer.play_music(victory_theme, repeat=False, volume=0.8)
                
                # Add to recent sounds
                self._add_recent_sound('victory', victory_theme, f"{character} victory theme")
                
                return self.current_bg_music
                
        # Fall back to default victory music
        victory_music = random.choice(self.BACKGROUND_MUSIC['victory'])
        self.current_bg_music = SoundPlayer.play_music(victory_music, repeat=False, volume=0.8)
        
        # Add to recent sounds
        self._add_recent_sound('victory', victory_music, "Victory theme")
        
        return self.current_bg_music
        
    def stop_background_music(self, fade_out_ms=500):
        """Stop the current background music"""
        if self.current_bg_music:
            SoundPlayer.stop_music(fade_out_ms)
            self.current_bg_music = None
            
    def toggle_mute(self):
        """Toggle mute state"""
        self.mute = not self.mute
        if self.mute:
            self.stop_background_music()
        return self.mute
        
    def set_mute(self, mute_state):
        """Set mute state directly"""
        self.mute = bool(mute_state)
        if self.mute:
            self.stop_background_music()
        return self.mute

# Create a global instance
sound_manager = SoundManager() 