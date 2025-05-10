'''
Game configuration settings
'''

import pygame as pg

# Player 1 controls
PLAYER1_CONTROLS = {
    'up': pg.K_UP,
    'left': pg.K_LEFT,
    'right': pg.K_RIGHT,
    'weak_attack': pg.K_z,
    'heavy_attack': pg.K_x
}

# Player 2 controls
PLAYER2_CONTROLS = {
    'up': pg.K_w,
    'left': pg.K_a,
    'right': pg.K_d,
    'weak_attack': pg.K_g,
    'heavy_attack': pg.K_h
}

# Controls for game management
GAME_CONTROLS = {
    'restart': pg.K_r,
    'menu': pg.K_m,
    'quit': pg.K_q
}

# Initial player positions
PLAYER1_POSITION = (157, 480)
PLAYER2_POSITION = (534, 480)

# Initial player directions
PLAYER1_DIRECTION = 'right'
PLAYER2_DIRECTION = 'left'

# Default health
DEFAULT_HEALTH = 100.0

# Default game settings
DEFAULT_SETTINGS = {
    'auto_player2': True,  # Automatically setup player 2
    'default_layout': 'standard',  # Default platform layout
    'fullscreen': False,  # Fullscreen mode
    'music_volume': 0.5,  # Background music volume (0.0 to 1.0)
    'sfx_volume': 0.7     # Sound effects volume (0.0 to 1.0)
}

def get_player_controls(player_index):
    """Get the control scheme for a specific player"""
    if player_index == 0:
        return PLAYER1_CONTROLS
    return PLAYER2_CONTROLS

def get_player_initial_position(player_index):
    """Get the initial position for a specific player"""
    if player_index == 0:
        return PLAYER1_POSITION
    return PLAYER2_POSITION

def get_player_initial_direction(player_index):
    """Get the initial direction for a specific player"""
    if player_index == 0:
        return PLAYER1_DIRECTION
    return PLAYER2_DIRECTION 