"""
Sound Effect Player for Super Smash Bros - Local Edition

This module provides a simple interface for playing sound effects (.wav files)
and music (.mp3 files) from the src/audio directory. It handles file existence checks 
and provides options for playing sounds once or repeatedly.
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
    
    # Music cache to avoid reloading music
    _music_cache = {}
    
    # Currently playing music file path
    _current_music = None
    
    @staticmethod
    def play_sound(sound_name, repeat=False, volume=1.0):
        """
        Play a sound effect if it exists
        
        Args:
            sound_name (str): The name of the sound file (with or without extension)
            repeat (bool): Whether to play the sound on repeat (loops indefinitely if True)
            volume (float): Volume level from 0.0 to 1.0
            
        Returns:
            pygame.mixer.Sound or None: The sound object if successfully played, None otherwise
        """
        # Auto-detect file extension if not provided
        if not (sound_name.lower().endswith('.wav') or sound_name.lower().endswith('.mp3')):
            # Try with .wav extension first
            wav_name = sound_name + '.wav'
            wav_path = SoundPlayer._get_audio_path(wav_name)
            
            if os.path.exists(wav_path):
                sound_name = wav_name
            else:
                # Try with .mp3 extension
                mp3_name = sound_name + '.mp3'
                mp3_path = SoundPlayer._get_audio_path(mp3_name)
                
                if os.path.exists(mp3_path):
                    sound_name = mp3_name
                else:
                    logger.warning(f"Neither {wav_name} nor {mp3_name} found in the audio directory")
                    return None
            
        # Build path to audio file
        sound_path = SoundPlayer._get_audio_path(sound_name)
        
        # Check if sound exists
        if not os.path.exists(sound_path):
            logger.warning(f"Sound file not found: {sound_path}")
            return None
            
        try:
            # For MP3 files, use the music player (better for longer sounds)
            if sound_name.lower().endswith('.mp3'):
                return SoundPlayer.play_music(sound_name, repeat, volume)
            
            # For WAV files, use the standard Sound objects
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
    def play_music(music_name, repeat=True, volume=1.0, fade_in_ms=500):
        """
        Play a music file (.mp3 or .wav)
        
        Args:
            music_name (str): The name of the music file (with or without extension)
            repeat (bool): Whether to repeat the music (loops indefinitely if True)
            volume (float): Volume level from 0.0 to 1.0
            fade_in_ms (int): Time in milliseconds to fade in the music
            
        Returns:
            str: The path to the music file if successfully loaded, None otherwise
        """
        # Auto-detect file extension if not provided
        if not (music_name.lower().endswith('.mp3') or music_name.lower().endswith('.wav')):
            music_name += '.mp3'  # Default to .mp3 for music
            
        # Build path to audio file
        music_path = SoundPlayer._get_audio_path(music_name)
        
        # Check if music exists
        if not os.path.exists(music_path):
            logger.warning(f"Music file not found: {music_path}")
            return None
            
        try:
            # Stop any currently playing music
            pg.mixer.music.stop()
            
            # Load the music
            pg.mixer.music.load(music_path)
            
            # Set volume
            pg.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            
            # Play the music
            loops = -1 if repeat else 0
            pg.mixer.music.play(loops=loops, fade_ms=fade_in_ms)
            
            # Store current music path
            SoundPlayer._current_music = music_path
            
            logger.info(f"Playing music: {music_name}")
            return music_path
            
        except Exception as e:
            logger.error(f"Error playing music {music_name}: {str(e)}")
            return None
    
    @staticmethod
    def stop_music(fade_out_ms=500):
        """
        Stop the currently playing music
        
        Args:
            fade_out_ms (int): Time in milliseconds to fade out the music
        """
        try:
            pg.mixer.music.fadeout(fade_out_ms)
            SoundPlayer._current_music = None
        except Exception as e:
            logger.error(f"Error stopping music: {str(e)}")
    
    @staticmethod
    def stop_sound(sound):
        """
        Stop a playing sound
        
        Args:
            sound (pygame.mixer.Sound): The sound to stop
        """
        if sound:
            try:
                # If sound is a string (music path), stop the music
                if isinstance(sound, str) and sound == SoundPlayer._current_music:
                    SoundPlayer.stop_music()
                # Otherwise it's a Sound object
                else:
                    sound.stop()
            except Exception as e:
                logger.error(f"Error stopping sound: {str(e)}")
    
    @staticmethod
    def stop_all_sounds():
        """Stop all currently playing sounds and music"""
        try:
            # Stop all sound effects
            pg.mixer.stop()
            
            # Stop music
            pg.mixer.music.stop()
            SoundPlayer._current_music = None
        except Exception as e:
            logger.error(f"Error stopping all sounds: {str(e)}")
    
    @staticmethod
    def _get_audio_path(sound_name):
        """Get the absolute path to a sound file"""
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audio', sound_name) 