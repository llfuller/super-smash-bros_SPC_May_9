'''
Melee Physics Mixin

This mixin class provides Super Smash Bros Melee physics to any character class.
It should be used alongside LocalCharacter to enhance the physics model.
'''

import pygame as pg
import math
import sys

# Import melee physics constants
sys.path.append("..")
# Import everything from melee_physics to ensure all constants are available
from melee_physics import *
from settings import *  # Import constants from settings

# Also add LANDING since it's defined in LocalCharacter but used here
LANDING = 'landing'

# Pygame vector
vec = pg.math.Vector2

class MeleePhysicsMixin:
    """
    Mixin class that adds Melee-accurate physics to any character class.
    This is designed to work with the LocalCharacter class.
    """
    
    def init_melee_physics(self, character_type='generic'):
        """Initialize Melee physics values"""
        self.character_type = character_type.lower()
        
        # Set character dimensions
        self.height_units = MARIO_HEIGHT if self.character_type == 'mario' else MARIO_HEIGHT
        self.width_units = MARIO_WIDTH if self.character_type == 'mario' else MARIO_WIDTH
        
        # Initialize physics state variables
        self.dash_frame_counter = 0  # Track frames in dash state
        self.is_dashing = False
        self.is_running = False
        self.is_fast_falling = False
        self.hitstun_frames = 0
        self.tumble_state = False
        self.l_cancel_window = 0
        self.l_cancel_successful = False
        
        # Get physics values for the character type, defaulting to generic if not found
        self.ground_physics = GROUND_MOVEMENT.get(self.character_type, GROUND_MOVEMENT['generic'])
        self.air_physics = AIR_MOVEMENT.get(self.character_type, AIR_MOVEMENT['generic'])
        self.weight = KNOCKBACK['weight'].get(self.character_type, KNOCKBACK['weight']['generic'])
        
        # Override acceleration with Melee values
        self.acce = self.ground_physics['ground_accel_base'] + self.ground_physics['ground_accel_additional']
        
        # Print debug info
        print(f"Initialized Melee physics for {self.name} as {character_type}")
        print(f"  Ground Speed: {self.ground_physics['walk_speed']}")
        print(f"  Air Speed: {self.air_physics['air_speed']}")
        print(f"  Gravity: {self.air_physics['gravity']}")
        print(f"  Weight: {self.weight}")
    
    def update_melee_physics(self):
        """Update physics state based on Melee rules"""
        # Skip physics update if character is defeated
        if hasattr(self, 'is_defeated') and self.is_defeated():
            return
            
        # Get input state from self (assumes these attributes exist on the character)
        # These should be set by the controller or AI
        moving_left = hasattr(self, 'moving_left') and self.moving_left
        moving_right = hasattr(self, 'moving_right') and self.moving_right
        is_jumping = hasattr(self, 'is_jumping') and self.is_jumping
        is_fast_falling = hasattr(self, 'is_fast_falling') and self.is_fast_falling
        
        # NOTE: We're no longer setting acceleration and velocity directly
        # Instead, we just update state flags that the main character class will use
        
        # Update dash/run state - just keep track of the state, don't modify position
        if not self.in_air:
            # In dash state
            if self.is_dashing:
                self.dash_frame_counter += 1
                if self.dash_frame_counter >= self.ground_physics['dash_to_run_transition_frames']:
                    # Transition to run after dash frames
                    self.is_dashing = False
                    self.is_running = True
                    self.dash_frame_counter = 0
            
            # Start dash when starting to move from standstill
            if (moving_left or moving_right) and abs(self.vel.x) < 0.1:
                self.is_dashing = True
                self.is_running = False
                self.dash_frame_counter = 0
                
            # Stop running/dashing when no directional input
            if not moving_left and not moving_right:
                self.is_dashing = False
                self.is_running = False
        else:
            # Reset ground movement states when in air
            self.is_dashing = False
            self.is_running = False
            
        # Update hitstun frames
        if self.hitstun_frames > 0:
            self.hitstun_frames -= 1
            if self.hitstun_frames == 0:
                # Exit tumble state and knockback when hitstun ends
                self.tumble_state = False
                if self.move == DAMAGED:
                    self.move = STAND
    
    def jump_with_melee_physics(self, is_short_hop=False):
        """Execute a jump with Melee physics"""
        # Only allow jump if not animation locked and not in air
        if self.animation_locked or self.in_air:
            return False
            
        if is_short_hop:
            # Short hop with lower Melee velocity
            self.vel.y = -self.air_physics['fall_speed'] * 0.8  # Lower multiplier for short hop
            print(f"{self.name} Melee short hop with velocity {self.vel.y}")
        else:
            # Regular jump with Melee velocity
            self.vel.y = -self.air_physics['fall_speed'] * 1.5
            print(f"{self.name} Melee full jump with velocity {self.vel.y}")
            
        self.in_air = True
        return True
    
    def take_damage_with_melee_physics(self, damage, kb_growth, base_kb, attacker_pos_x, angle_degrees=45):
        """
        Apply damage with Melee knockback physics
        
        Args:
            damage: Damage amount (percent)
            kb_growth: Knockback growth value
            base_kb: Base knockback value
            attacker_pos_x: X position of the attacker (for knockback direction)
            angle_degrees: Launch angle in degrees (default 45°)
        
        Returns:
            New damage percentage
        """
        try:
            print(f"DAMAGE DEBUG: {self.name} taking damage, starting position: ({self.pos.x}, {self.pos.y})")
            print(f"DAMAGE DEBUG: Pre-damage state: in_air={self.in_air}, dropping={getattr(self, 'is_dropping_through', False)}")
            
            # Calculate old damage percent for knockback formula
            old_percent = self.damage_percent
            
            # Increase damage percentage
            self.damage_percent += damage
            
            # Calculate knockback
            if 'calculate_knockback' in globals():
                # Use the imported function if available
                knockback = calculate_knockback(
                    defender_percent=self.damage_percent,
                    attack_damage=damage,
                    defender_weight=self.weight,
                    knockback_growth=kb_growth,
                    base_knockback=base_kb
                )
            else:
                # Fallback formula if function not available
                print("Warning: calculate_knockback not found, using basic formula")
                percent_factor = self.damage_percent / 100.0
                knockback = 20 + (percent_factor * kb_growth) + base_kb
            
            # Determine knockback direction (reverse horizontal component if hit from right)
            knockback_direction = 1 if attacker_pos_x < self.pos.x else -1
            
            # Calculate velocity components
            if 'knockback_to_velocity' in globals():
                # Use imported function if available
                vx, vy = knockback_to_velocity(knockback, angle_degrees)
            else:
                # Fallback velocity calculation
                print("Warning: knockback_to_velocity not found, using basic calculation")
                speed = 0.03 * knockback  # Same as in knockback_to_velocity
                angle_radians = math.radians(angle_degrees)
                vx = speed * math.cos(angle_radians)
                vy = -speed * math.sin(angle_radians)  # Negative because y is down in PyGame
            
            print(f"DAMAGE DEBUG: Raw knockback values: knockback={knockback}, vx={vx}, vy={vy}")
            
            # Apply direction to horizontal component
            vx *= knockback_direction
            
            # CRITICAL: Ensure vertical knockback is ALWAYS upward on hit
            # Force strong upward knockback to ensure no platform fall-through
            if vy > -2:  # If upward velocity is too low
                vy = -5  # Set to a substantial upward value
            
            print(f"DAMAGE DEBUG: Final knockback velocity: vx={vx}, vy={vy}")
            
            # IMPORTANT: Force position adjustment to ensure no clipping into platforms
            # Move character slightly upward to prevent platform clipping
            self.pos.y -= 5  # Move up slightly to avoid platform intersection
            
            # Apply to velocity
            self.vel.x = vx
            self.vel.y = vy
            
            # Calculate hitstun
            if 'calculate_hitstun' in globals():
                self.hitstun_frames = calculate_hitstun(knockback)
            else:
                # Fallback hitstun calculation
                print("Warning: calculate_hitstun not found, using basic calculation")
                self.hitstun_frames = int(knockback * 0.4)  # Same factor as in calculate_hitstun
            
            # Set tumble state if knockback exceeds threshold
            if 'LAUNCH_AND_STUN' in globals():
                self.tumble_state = knockback >= LAUNCH_AND_STUN['tumble_threshold']
            else:
                # Default threshold if not defined
                self.tumble_state = knockback >= 80
            
            # Enter damage state
            self.move = DAMAGED
            self.animation_locked = True
            self.animation_lock_timer = 0
            self.animation_lock_duration = self.hitstun_frames
            
            # Completely reset any platform drop-through state
            self.dropping_through_platforms = set()
            self.is_dropping_through = False
            
            # CRITICAL: Always set knockback air state
            self.in_air = True
            self.is_knockback_air = True
            
            # Debug output
            print(f"DAMAGE DEBUG: {self.name} took {damage}% damage (now at {self.damage_percent}%)")
            print(f"DAMAGE DEBUG: Knockback: {knockback:.2f}, Hitstun: {self.hitstun_frames} frames")
            print(f"DAMAGE DEBUG: New position: ({self.pos.x}, {self.pos.y}), velocity: ({self.vel.x:.2f}, {self.vel.y:.2f})")
            print(f"DAMAGE DEBUG: Post-hit state: in_air={self.in_air}, knockback_air={self.is_knockback_air}, dropping={self.is_dropping_through}")
            
            return self.damage_percent
        except Exception as e:
            print(f"ERROR in take_damage_with_melee_physics: {e}")
            import traceback
            traceback.print_exc()
            
            # Basic fallback implementation if something goes wrong
            self.damage_percent += damage
            
            # Basic knockback
            knockback_multiplier = 1.0 + (self.damage_percent / 100.0)
            self.vel.x = 5 * knockback_direction * knockback_multiplier
            self.vel.y = -8 * knockback_multiplier  # Stronger upward launch
            
            # Move up to prevent platform clipping
            self.pos.y -= 5
            
            # Set damage state
            self.move = DAMAGED
            self.animation_locked = True
            self.animation_lock_timer = 0
            self.animation_lock_duration = 20
            self.in_air = True
            self.is_dropping_through = False  # Ensure no drop-through
            self.is_knockback_air = True
            self.dropping_through_platforms = set()
            
            print(f"DAMAGE DEBUG: Fallback knockback applied. vel=({self.vel.x}, {self.vel.y})")
            
            return self.damage_percent
    
    def apply_landing_lag_with_melee_physics(self, was_aerial_attack=False):
        """
        Apply landing lag based on Melee rules
        
        Args:
            was_aerial_attack: Whether landing occurred during an aerial attack
        """
        try:
            # Determine base landing lag frames
            if was_aerial_attack:
                # Use aerial landing lag range
                min_lag, max_lag = LANDING_LAG['aerial_lag_frames_range']
                
                # Scale base lag based on move strength (example implementation)
                # In a real game this would be move-specific
                move_strength = 0.5  # Arbitrary value between 0-1 
                base_lag_frames = min_lag + (max_lag - min_lag) * move_strength
                
                # Apply L-cancel if within window
                if self.l_cancel_window > 0:
                    base_lag_frames *= LANDING_LAG['l_cancel_factor']
                    self.l_cancel_successful = True
                    print(f"{self.name} successfully L-canceled!")
                else:
                    self.l_cancel_successful = False
            else:
                # Normal landing
                base_lag_frames = LANDING_LAG['normal_landing_lag_frames']
                self.l_cancel_successful = False
            
            # Set landing lag and animation lock
            self.landing_lag = int(base_lag_frames)
            self.animation_locked = True
            self.animation_lock_timer = 0
            self.animation_lock_duration = self.landing_lag
            
            # Visual feedback - landing animation
            # Use DAMAGED state if LANDING is not defined
            if 'LANDING' in globals():
                self.move = LANDING
            else:
                # Fallback to DAMAGED animation
                self.move = DAMAGED
                print("Warning: LANDING state not defined, using DAMAGED animation instead")
            
            # Reset l-cancel window
            self.l_cancel_window = 0
            
            # Debug output
            print(f"{self.name} landing lag: {self.landing_lag} frames")
            
        except Exception as e:
            # If there's an error, just reset the character state
            print(f"Error in landing: {e}")
            self.animation_locked = False
            self.landing_lag = 0
    
    def try_l_cancel(self):
        """
        Attempt to L-cancel (sets window for successful L-cancel)
        Should be called when shield button is pressed while in air
        """
        if self.in_air:
            self.l_cancel_window = LANDING_LAG['l_cancel_window_frames']
            print(f"{self.name} attempting L-cancel")
            
    def update_l_cancel_window(self):
        """Update L-cancel window timer"""
        if self.l_cancel_window > 0:
            self.l_cancel_window -= 1 