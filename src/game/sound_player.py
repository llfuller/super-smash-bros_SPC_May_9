"""
Sound Effect Player for Super Smash Bros - Local Edition

This module provides a simple interface for playing sound effects (.wav files)
from the src/audio directory. It handles file existence checks and provides
options for playing sounds once or repeatedly.
"""

import os
import pygame as pg
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sound_player')

# Initialize pygame mixer if not already initialized
if not pg.mixer.get_init():
    try:
        pg.mixer.init(44100, -16, 2, 2048)
        logger.info("Pygame mixer initialized")
    except pg.error:
        logger.error("Failed to initialize pygame mixer")


class SoundPlayer:
    """
    A class for playing sound effects in the game.
    """
    
    # Sound cache to avoid reloading sounds
    _sound_cache = {}
    
    @staticmethod
    def play_sound(sound_name, repeat=False, volume=1.0):
        """
        Play a sound effect if it exists
        
        Args:
            sound_name (str): The name of the sound file (with or without .wav extension)
            repeat (bool): Whether to play the sound on repeat (loops indefinitely if True)
            volume (float): Volume level from 0.0 to 1.0
            
        Returns:
            pygame.mixer.Sound or None: The sound object if successfully played, None otherwise
        """
        # Ensure sound name has .wav extension
        if not sound_name.lower().endswith('.wav'):
            sound_name += '.wav'
            
        # Build path to audio file
        # Look in src/audio directory
        audio_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audio')
        sound_path = os.path.join(audio_dir, sound_name)
        
        # Check if sound exists
        if not os.path.exists(sound_path):
            logger.warning(f"Sound file not found: {sound_path}")
            return None
            
        try:
            # Check if sound is in cache
            if sound_path in SoundPlayer._sound_cache:
                sound = SoundPlayer._sound_cache[sound_path]
            else:
                # Load and cache the sound
                sound = pg.mixer.Sound(sound_path)
                SoundPlayer._sound_cache[sound_path] = sound
                
            # Set volume
            sound.set_volume(max(0.0, min(1.0, volume)))
            
            # Play the sound
            loops = -1 if repeat else 0
            sound.play(loops=loops)
            return sound
            
        except Exception as e:
            logger.error(f"Error playing sound {sound_name}: {str(e)}")
            return None
    
    @staticmethod
    def stop_sound(sound):
        """
        Stop a playing sound
        
        Args:
            sound (pygame.mixer.Sound): The sound to stop
        """
        if sound:
            try:
                sound.stop()
            except Exception as e:
                logger.error(f"Error stopping sound: {str(e)}")
    
    @staticmethod
    def stop_all_sounds():
        """Stop all currently playing sounds"""
        try:
            pg.mixer.stop()
        except Exception as e:
            logger.error(f"Error stopping all sounds: {str(e)}") 