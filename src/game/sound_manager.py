"""
Sound Manager for Super Smash Bros - Local Edition

This module manages all game sounds and background music,
providing specific sound effects for different game events.
"""

import os
import random
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
    
    # Character-specific sounds
    CHARACTER_SOUNDS = {
        'Mario': {
            'attack_weak': ['Small Hit', 'Small Hit 2'],
            'attack_heavy': ['Strong Hit', 'Moderate Hit'],
            'victory': '30. Victory! [Super Mario Bros.]'
        },
        'Luigi': {
            'attack_weak': ['Small Hit', 'Small Hit 2'],
            'attack_heavy': ['Strong Hit', 'Moderate Hit'],
            'victory': '30. Victory! [Super Mario Bros.]'
        },
        'Yoshi': {
            'attack_weak': ['Yoshi - Tongue', 'Small Hit'],
            'attack_heavy': ['Yoshi - Egg Throw', 'Yoshi - Egg Throw Pop'],
            'special': ['Yoshi - Egg Pop'],
            'victory': '31. Victory! [Yoshi]'
        },
        'Popo': {
            'attack_weak': ['Small Hit', 'Strong Sword Smack'],
            'attack_heavy': ['Strong Sword Smack', 'Strong Hit']
        },
        'Nana': {
            'attack_weak': ['Small Hit', 'Strong Sword Smack'],
            'attack_heavy': ['Strong Sword Smack', 'Strong Hit']
        },
        'Link': {
            'attack_weak': ['Small Sword Hit', 'Moderate Sword Hit'],
            'attack_heavy': ['Strong Sword Smack', 'Unsheath Sword'],
            'victory': '33. Victory! [Link]'
        },
        'Samus': {
            'attack_weak': ['Samus - Small Beam Blast', 'Samus - Beam'],
            'attack_heavy': ['Samus - Beam Blast', 'Samus - Charging Beam Full'],
            'special': ['Samus - Charging Beam', 'Samus - Bomb Deploy', 'Samus - Grappling Hook'],
            'victory': '34. Victory! [Samus]'
        },
        'Pikachu': {
            'attack_weak': ['Pikachu - Electrical Attack', 'Pikachu - Electric'],
            'attack_heavy': ['Pikachu - Thunderbolt', 'Pikachu - Thunderbolt Rising'],
            'special': ['Pikachu - Electrical', 'Pikachu - Electrical Flow', 'Pikachu - Speed Jump Begin'],
            'victory': '37. Victory! [Pokémon]'
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
        
    def play_ui_sound(self, sound_type):
        """Play a UI sound"""
        if self.mute:
            return None
            
        if sound_type in self.UI_SOUNDS:
            return SoundPlayer.play_sound(self.UI_SOUNDS[sound_type])
        return None
        
    def play_hit_sound(self, intensity='medium'):
        """Play a hit sound based on intensity (weak, medium, strong)"""
        if self.mute:
            return None
            
        if intensity in self.HIT_SOUNDS:
            sound_name = random.choice(self.HIT_SOUNDS[intensity])
            return SoundPlayer.play_sound(sound_name)
        return None
        
    def play_attack_sound(self, attack_type='weak'):
        """Play an attack sound (weak or heavy)"""
        if self.mute:
            return None
            
        if attack_type in self.ATTACK_SOUNDS:
            sound_name = random.choice(self.ATTACK_SOUNDS[attack_type])
            return SoundPlayer.play_sound(sound_name)
        return None
        
    def play_shield_sound(self, shield_action):
        """Play a shield sound (on, off, break, hit)"""
        if self.mute:
            return None
            
        if shield_action in self.SHIELD_SOUNDS:
            sound = self.SHIELD_SOUNDS[shield_action]
            if isinstance(sound, list):
                sound = random.choice(sound)
            return SoundPlayer.play_sound(sound)
        return None
    
    def play_character_sound(self, character, sound_type):
        """Play a character-specific sound"""
        if self.mute:
            return None
            
        if character in self.CHARACTER_SOUNDS:
            if sound_type in self.CHARACTER_SOUNDS[character]:
                sound_name = random.choice(self.CHARACTER_SOUNDS[character][sound_type]) if isinstance(self.CHARACTER_SOUNDS[character][sound_type], list) else self.CHARACTER_SOUNDS[character][sound_type]
                return SoundPlayer.play_sound(sound_name)
        return None
        
    def play_damage_sound(self, damage_amount):
        """Play a damage sound based on damage amount"""
        if self.mute:
            return None
            
        if damage_amount >= 20:
            return self.play_hit_sound('strong')
        elif damage_amount >= 10:
            return self.play_hit_sound('medium')
        else:
            return self.play_hit_sound('weak')
    
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
            return self.current_bg_music
            
        # Play music from the selected category
        if music_type in self.BACKGROUND_MUSIC:
            sound_name = random.choice(self.BACKGROUND_MUSIC[music_type])
            self.current_bg_music = SoundPlayer.play_music(sound_name, repeat=True, volume=0.7, fade_in_ms=fade_in_ms)
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
                return self.current_bg_music
                
        # Fall back to default victory music
        self.current_bg_music = SoundPlayer.play_music(random.choice(self.BACKGROUND_MUSIC['victory']), repeat=False, volume=0.8)
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