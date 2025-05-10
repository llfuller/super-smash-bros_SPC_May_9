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

# Switch Pro Controller button mapping
# These are default values that can be changed based on user preferences
# Button indices may vary between controllers and systems
PRO_CONTROLLER = {
    'up': 0,          # Up on D-pad
    'left': 1,        # Left on D-pad
    'right': 2,       # Right on D-pad
    'down': 3,        # Down on D-pad
    'y_button': 0,    # Y button - Jump (Top button)
    'x_button': 1,    # X button - Jump (Left button)
    'b_button': 2,    # B button - Weak attack (Right button)
    'a_button': 3,    # A button - Strong attack (Bottom button)
    'l_button': 9,    # L button - Shield (corrected from 4 to 9)
    'r_button': 10,   # R button - Shield (corrected from 5 to 10)
    'zl_button': 6,   # ZL button - Shield
    'zr_button': 7,   # ZR button - Shield
    'minus': 8,       # Minus button
    'plus': 9,        # Plus button
    'l_stick': 10,    # Left stick press
    'r_stick': 11,    # Right stick press
    'home': 12,       # Home button
    'capture': 13,    # Capture button
    'l_stick_x': 0,   # Left stick X axis
    'l_stick_y': 1,   # Left stick Y axis
    'r_stick_x': 2,   # Right stick X axis
    'r_stick_y': 3,   # Right stick Y axis
    
    # Additional shield button fallbacks for different controller types
    # These may be different on non-Switch controllers
    'shield_buttons': [9, 10, 6, 7, 4, 5]  # L, R, ZL, ZR + fallbacks
}

# Default game settings
DEFAULT_SETTINGS = {
    'auto_player2': True,        # Automatically setup player 2
    'default_layout': 'standard', # Default platform layout
    'fullscreen': False,         # Fullscreen mode
    'music_volume': 0.5,         # Background music volume (0.0 to 1.0)
    'sfx_volume': 0.7,           # Sound effects volume (0.0 to 1.0)
    'use_controller': True,     # Enable game controller
    'controller_deadzone': 0.15, # Analog stick deadzone
}

# Initial player positions
PLAYER1_POSITION = (157, 480)
PLAYER2_POSITION = (534, 480)

# Initial player directions
PLAYER1_DIRECTION = 'right'
PLAYER2_DIRECTION = 'left'

# Default health
DEFAULT_HEALTH = 100.0

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