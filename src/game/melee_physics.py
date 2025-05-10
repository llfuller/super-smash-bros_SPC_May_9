'''
Super Smash Bros Melee Physics Constants

This file contains all physics constants extracted from Super Smash Bros Melee
to make our game feel as close as possible to the real thing.
'''

# Global timing
FPS = 60
FRAME_DURATION_S = 1/60  # 0.0166667 seconds per frame

# Units conversion
GAME_UNIT_TO_METER = 0.1  # 1 game unit = 10cm

# Character dimensions (in game units)
MARIO_HEIGHT = 15  # ~152.4cm
MARIO_WIDTH = 5    # ~1/3 of height

# Movement - Ground
GROUND_MOVEMENT = {
    # Character-specific values
    'mario': {
        'walk_speed': 1.2,         # units per frame
        'dash_speed': 1.6,         # units per frame
        'run_speed': 1.8,          # units per frame
        'ground_accel_base': 0.01,  # units per frame^2
        'ground_accel_additional': 0.08,  # units per frame^2
        'traction': 0.08,          # units per frame^2
    },
    'luigi': {
        'walk_speed': 1.1,         # units per frame
        'dash_speed': 1.4,         # units per frame 
        'run_speed': 1.6,          # units per frame
        'ground_accel_base': 0.01,  # units per frame^2
        'ground_accel_additional': 0.08,  # units per frame^2
        'traction': 0.044,         # units per frame^2 (Luigi has lowest traction)
    },
    # Generic values for other characters
    'generic': {
        'walk_speed': 1.1,          # units per frame
        'dash_speed': 1.6,          # units per frame
        'run_speed': 1.7,           # units per frame
        'ground_accel_base': 0.01,   # units per frame^2
        'ground_accel_additional': 0.08,  # units per frame^2
        'traction': 0.08,           # units per frame^2
        'dash_to_run_transition_frames': 12,  # frames before dash transitions to run
        'traction_multiplier_if_speed_gt_walk': 2.0  # extra traction when speed > walk_speed
    }
}

# Movement - Air
AIR_MOVEMENT = {
    'mario': {
        'air_speed': 1.0,          # max horizontal air speed in units per frame
        'air_accel_base': 0.01,    # units per frame^2
        'air_accel_additional': 0.08,  # units per frame^2
        'gravity': 0.09,           # units per frame^2
        'fall_speed': 1.7,         # max fall speed in units per frame
        'fast_fall_multiplier': 1.6  # multiply fall_speed by this for fast fall
    },
    'luigi': {
        'air_speed': 0.9,          # max horizontal air speed in units per frame
        'air_accel_base': 0.01,    # units per frame^2
        'air_accel_additional': 0.07,  # units per frame^2
        'gravity': 0.07,           # units per frame^2
        'fall_speed': 1.6,         # max fall speed in units per frame
        'fast_fall_multiplier': 1.6  # multiply fall_speed by this for fast fall
    },
    'generic': {
        'air_speed': 1.0,          # max horizontal air speed in units per frame
        'air_accel_base': 0.01,    # units per frame^2
        'air_accel_additional': 0.07,  # units per frame^2
        'gravity': 0.08,           # units per frame^2
        'fall_speed': 1.7,         # max fall speed in units per frame
        'fast_fall_multiplier': 1.6  # multiply fall_speed by this for fast fall
    }
}

# Landing lag
LANDING_LAG = {
    'normal_landing_lag_frames': 4,  # frames of landing lag (non-attack)
    'aerial_lag_frames_range': (4, 30),  # min/max range for aerial landing lag frames
    'l_cancel_window_frames': 7,  # window for L-cancel input
    'l_cancel_factor': 0.5  # multiplier for landing lag when L-cancel succeeds
}

# Knockback formula: K = (((p/10) + (p*d/20)) * 1.4 * (200/(w+100)) + 18) * (KBG/100) + BKB
# where:
# p = defender percent after hit
# d = attack damage
# w = defender weight (Mario = 100)
# KBG = knockback growth (default 100)
# BKB = base knockback
KNOCKBACK = {
    'weight': {
        'mario': 100,
        'luigi': 95,
        'generic': 100
    },
    'knockback_growth_default': 100,
    'multipliers': {
        'damage_ratio': 1.0,  # default multiplier
        'crouch_cancel': 0.666667,  # 2/3 knockback when crouching
        'hit_during_smash_charge': 1.2  # +20% knockback when hit during smash charge
    }
}

# Launch and stun values
LAUNCH_AND_STUN = {
    'initial_velocity_factor': 0.03,  # initial velocity = 0.03 * K
    'horizontal_knockback_decel': 0.051,  # deceleration per frame
    'hitstun_frames_factor': 0.4,  # hitstun frames = floor(0.4 * K)
    'tumble_threshold': 80  # K value for entering tumble state (32 hitstun frames)
}

# Pre-calculated values for common knockback scenarios
KNOCKBACK_EXAMPLES = {
    'weak': {
        'damage': 5,
        'base_knockback': 20,
        'knockback_growth': 80
    },
    'medium': {
        'damage': 10,
        'base_knockback': 35,
        'knockback_growth': 100
    },
    'strong': {
        'damage': 15,
        'base_knockback': 40,
        'knockback_growth': 120
    }
}

# Function to calculate knockback value K
def calculate_knockback(defender_percent, attack_damage, defender_weight, knockback_growth, base_knockback, multiplier=1.0):
    """
    Calculate Melee knockback value K using the formula:
    K = (((p/10) + (p*d/20)) * 1.4 * (200/(w+100)) + 18) * (KBG/100) + BKB
    
    Args:
        defender_percent: Current percent of the defender (after hit)
        attack_damage: Damage of the attack
        defender_weight: Weight value of the defender (Mario = 100)
        knockback_growth: Knockback growth of the attack
        base_knockback: Base knockback of the attack
        multiplier: Optional knockback multiplier (crouch cancel, etc.)
        
    Returns:
        The knockback value K
    """
    percent_term = (defender_percent / 10) + (defender_percent * attack_damage / 20)
    weight_factor = 200 / (defender_weight + 100)
    
    # Apply the formula
    k = ((percent_term * 1.4 * weight_factor) + 18) * (knockback_growth / 100) + base_knockback
    
    # Apply any multipliers (crouch cancel, etc.)
    k *= multiplier
    
    return k

# Function to convert knockback to velocity
def knockback_to_velocity(knockback, angle_degrees=45):
    """
    Convert knockback K to initial velocity vector
    
    Args:
        knockback: The knockback value K
        angle_degrees: The launch angle in degrees (default 45)
        
    Returns:
        (vx, vy) tuple with initial velocity values
    """
    import math
    
    # Convert angle to radians
    angle_radians = math.radians(angle_degrees)
    
    # Calculate initial speed
    speed = LAUNCH_AND_STUN['initial_velocity_factor'] * knockback
    
    # Calculate x and y components
    vx = speed * math.cos(angle_radians)
    vy = -speed * math.sin(angle_radians)  # Negative because y is down in PyGame
    
    # Note: The character update loop now handles gradual gravity reintroduction
    # during hitstun. Gravity is disabled for the first half of hitstun, then
    # gradually increases from 0 to full during the second half.
    
    return (vx, vy)

# Function to calculate hitstun frames
def calculate_hitstun(knockback):
    """
    Calculate hitstun frames from knockback
    
    Args:
        knockback: The knockback value K
        
    Returns:
        Number of frames the character will be in hitstun
    """
    import math
    return math.floor(LAUNCH_AND_STUN['hitstun_frames_factor'] * knockback) 