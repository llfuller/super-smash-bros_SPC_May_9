'''
Battlefield Tilt Feature

This module implements a special event where the entire battlefield tilts,
causing all characters to slide off the screen.
'''

import pygame as pg
import math
import random

class BattlefieldTilt:
    def __init__(self, game):
        self.game = game
        self.is_active = False
        self.tilt_angle = 0  # Current tilt angle in degrees
        self.max_tilt_angle = 45  # Maximum tilt angle
        self.tilt_speed = 0.5  # How fast the battlefield tilts (degrees per frame)
        self.tilt_direction = 1  # 1 for right tilt, -1 for left tilt
        self.tilt_duration = 0  # Counter for how long the tilt has been active
        self.max_tilt_duration = 180  # Maximum duration (3 seconds at 60 FPS)
        
        # Visual effect properties
        self.original_platform_positions = {}  # Store original positions
        self.original_background_rect = None
        self.background_surface = None
        
    def trigger_tilt(self, direction=None):
        """Trigger the battlefield tilt effect"""
        if self.is_active:
            return False
            
        # Set tilt direction (random if not specified)
        if direction is None:
            self.tilt_direction = random.choice([-1, 1])
        else:
            self.tilt_direction = direction
            
        # Store original platform positions
        self.original_platform_positions = {}
        for platform in self.game.platforms:
            self.original_platform_positions[platform] = {
                'x': platform.rect.x,
                'y': platform.rect.y
            }
            
        # Store background information if available
        if hasattr(self.game, 'background'):
            self.original_background_rect = self.game.background.get_rect().copy()
            self.background_surface = self.game.background
            
        # Reset tilt parameters
        self.tilt_angle = 0
        self.tilt_duration = 0
        self.is_active = True
        
        # Record event in game's event system if available
        if hasattr(self.game, 'record_event'):
            self.game.record_event("BATTLEFIELD_TILT", 
                                  f"The battlefield is tilting {'right' if self.tilt_direction > 0 else 'left'}!", 
                                  "Critical")
            
        return True
        
    def update(self):
        """Update the tilt effect each frame"""
        if not self.is_active:
            return
            
        # Increment duration counter
        self.tilt_duration += 1
        
        # Increase tilt angle
        self.tilt_angle += self.tilt_speed * self.tilt_direction
        
        # Cap the tilt angle at the maximum
        if abs(self.tilt_angle) > self.max_tilt_angle:
            self.tilt_angle = self.max_tilt_angle * self.tilt_direction
            
        # Apply physics effects to all characters
        self._apply_tilt_physics()
        
        # Apply visual tilt to platforms
        self._apply_visual_tilt()
        
        # Apply screen rotation effect
        self._apply_screen_rotation()
        
        # Check if tilt duration has exceeded maximum
        if self.tilt_duration >= self.max_tilt_duration:
            self.reset()
            
    def _apply_tilt_physics(self):
        """Apply tilting physics to all characters"""
        # Apply to all player sprites using the MeleePhysics method
        for player_data in self.game.players.values():
            if 'sprite' in player_data:
                sprite = player_data['sprite']
                
                # Use the apply_tilt_physics method if available
                if hasattr(sprite, 'apply_tilt_physics'):
                    sprite.apply_tilt_physics(self.tilt_angle, self.tilt_direction)
                else:
                    # Fallback for sprites without the method
                    angle_rad = math.radians(self.tilt_angle)
                    slide_force = 0.5 * math.sin(angle_rad) * self.tilt_direction
                    sprite.acc.x += slide_force
                    
                    # Force character into air state if angle is steep enough
                    if abs(self.tilt_angle) > 20 and not sprite.in_air:
                        sprite.in_air = True
                        sprite.vel.y = 2  # Small initial downward velocity
                    
    def _apply_visual_tilt(self):
        """Apply visual tilting effect to platforms"""
        # Skip if no original positions stored
        if not self.original_platform_positions:
            return
            
        # Calculate rotation point (center of screen)
        center_x = self.game.screen.get_width() // 2
        center_y = self.game.screen.get_height() // 2
        
        # Apply rotation to each platform
        for platform, original_pos in self.original_platform_positions.items():
            # Calculate rotated position
            x_diff = original_pos['x'] - center_x
            y_diff = original_pos['y'] - center_y
            
            angle_rad = math.radians(self.tilt_angle)
            rotated_x = x_diff * math.cos(angle_rad) - y_diff * math.sin(angle_rad)
            rotated_y = x_diff * math.sin(angle_rad) + y_diff * math.cos(angle_rad)
            
            # Update platform position
            platform.rect.x = center_x + rotated_x
            platform.rect.y = center_y + rotated_y
            
    def _apply_screen_rotation(self):
        """Apply a rotation effect to the entire game screen"""
        # Store the original screen if we haven't already
        if not hasattr(self, 'original_screen'):
            self.original_screen = self.game.screen.copy()
            
        # Create a new surface for the rotated screen
        if not hasattr(self, 'rotated_screen'):
            self.rotated_screen = pg.Surface(self.game.screen.get_size(), pg.SRCALPHA)
            
        # Clear the rotated screen
        self.rotated_screen.fill((0, 0, 0, 0))
        
        # Get the original screen content
        original = self.game.screen.copy()
        
        # Rotate the screen (use a smaller angle for subtle effect)
        visual_angle = self.tilt_angle * 0.5  # Use half the physics angle for visual effect
        rotated = pg.transform.rotate(original, -visual_angle)  # Negative for correct rotation direction
        
        # Calculate position to blit the rotated surface
        rect = rotated.get_rect(center=self.game.screen.get_rect().center)
        
        # Draw a background color to fill any gaps
        self.game.screen.fill((0, 0, 0))
        
        # Blit the rotated surface onto the screen
        self.game.screen.blit(rotated, rect.topleft)
            
    def reset(self):
        """Reset the battlefield to its original state"""
        self.is_active = False
        self.tilt_angle = 0
        
        # Restore original platform positions
        for platform, original_pos in self.original_platform_positions.items():
            platform.rect.x = original_pos['x']
            platform.rect.y = original_pos['y']
            
        # Reset any modified physics parameters
        for player_data in self.game.players.values():
            if 'sprite' in player_data:
                sprite = player_data['sprite']
                
                # Restore original friction if it was modified
                if hasattr(sprite, 'original_friction') and hasattr(sprite, 'ground_physics'):
                    sprite.ground_physics['friction'] = sprite.original_friction
                    delattr(sprite, 'original_friction')
                
                # Reset can_jump flag
                if hasattr(sprite, 'can_jump'):
                    sprite.can_jump = True
                    
                # Reset any other modified physics parameters
                if hasattr(sprite, 'init_melee_physics'):
                    sprite.init_melee_physics(sprite.character_type)
                    
        # Record event in game's event system if available
        if hasattr(self.game, 'record_event'):
            self.game.record_event("BATTLEFIELD_RESET", 
                                  "The battlefield has returned to normal!", 
                                  "Medium")
                    
        # Clear stored positions
        self.original_platform_positions = {}