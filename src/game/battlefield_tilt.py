'''
Battlefield Tilt Feature

This module implements a special event where the entire battlefield tilts,
causing all characters to slide off the screen.
'''

import pygame as pg
import math
import random
from settings import TILT_MODE_ENABLED, TILT_OSCILLATION_SPEED, TILT_MAX_ANGLE, TILT_MIN_ANGLE

class BattlefieldTilt:
    def __init__(self, game):
        self.game = game
        self.is_active = False
        self.tilt_angle = 0  # Current tilt angle in degrees
        self.max_tilt_angle = 20  # Maximum tilt angle
        self.tilt_speed = 0.5  # How fast the battlefield tilts (degrees per frame)
        self.tilt_direction = 1  # 1 for right tilt, -1 for left tilt
        self.tilt_duration = 0  # Counter for how long the tilt has been active
        self.max_tilt_duration = 180  # Maximum duration (3 seconds at 60 FPS)
        
        # Visual effect properties
        self.original_platform_positions = {}  # Store original positions
        self.original_platform_rects = {}  # Store original rects for collision
        self.original_background_rect = None
        self.background_surface = None
        
        # Tilt mode properties
        self.tilt_mode_active = TILT_MODE_ENABLED
        self.oscillation_speed = TILT_OSCILLATION_SPEED
        self.oscillation_max_angle = TILT_MAX_ANGLE
        self.oscillation_min_angle = TILT_MIN_ANGLE
        self.continuous_tilt = False
        
        # Stage center point (for rotation)
        self.center_x = self.game.screen.get_width() // 2
        self.center_y = self.game.screen.get_height() // 2
        
    def toggle_tilt_mode(self):
        """Toggle the continuous tilt mode on or off"""
        self.tilt_mode_active = not self.tilt_mode_active
        
        if self.tilt_mode_active:
            # Store original platform positions if not already stored
            if not self.original_platform_positions:
                self._store_original_positions()
            self.continuous_tilt = True
            self.is_active = True
            
            # Record event in game's event system if available
            if hasattr(self.game, 'record_event'):
                self.game.record_event("TILT_MODE_ENABLED", 
                                      "Tilt Mode activated! The stage will continuously rotate.", 
                                      "Critical")
        else:
            self.continuous_tilt = False
            self.is_active = False
            self.reset()
            
            # Record event
            if hasattr(self.game, 'record_event'):
                self.game.record_event("TILT_MODE_DISABLED", 
                                      "Tilt Mode deactivated. The stage has returned to normal.", 
                                      "Medium")
            
        return self.tilt_mode_active
    
    def _store_original_positions(self):
        """Store the original positions of all platforms and other elements"""
        # Store original platform positions and rects
        self.original_platform_positions = {}
        self.original_platform_rects = {}
        
        for platform in self.game.platforms:
            # Store original position
            self.original_platform_positions[platform] = {
                'x': platform.rect.x,
                'y': platform.rect.y
            }
            
            # Store original rect for collision detection
            self.original_platform_rects[platform] = platform.rect.copy()
            
        # Store background information if available
        if hasattr(self.game, 'background'):
            self.original_background_rect = self.game.background.get_rect().copy()
            self.background_surface = self.game.background
        
    def trigger_tilt(self, direction=None):
        """Trigger the battlefield tilt effect"""
        if self.is_active and not self.continuous_tilt:
            return False
            
        # Set tilt direction (random if not specified)
        if direction is None:
            self.tilt_direction = random.choice([-1, 1])
        else:
            self.tilt_direction = direction
            
        # Store original platform positions
        self._store_original_positions()
            
        # Reset tilt parameters
        self.tilt_angle = 0
        self.tilt_duration = 0
        self.is_active = True
        
        # Record event in game's event system if available
        if hasattr(self.game, 'record_event') and not self.continuous_tilt:
            self.game.record_event("BATTLEFIELD_TILT", 
                                  f"The battlefield is tilting {'right' if self.tilt_direction > 0 else 'left'}!", 
                                  "Critical")
            
        return True
        
    def update(self):
        """Update the tilt effect each frame"""
        if not self.is_active:
            return
            
        if self.continuous_tilt:
            # Continuous oscillation mode
            self._update_oscillation()
        else:
            # Single tilt event mode
            self._update_single_tilt()
            
        # Additional check to ensure characters don't fall through platforms
        self._prevent_platform_clipping()
    
    def _update_oscillation(self):
        """Update the continuous oscillating tilt effect"""
        # Store previous angle before update for direction change detection
        previous_angle = self.tilt_angle
        previous_direction = self.tilt_direction
        
        # Update the tilt angle based on the oscillation speed and direction
        self.tilt_angle += self.oscillation_speed * self.tilt_direction
        
        # Check if we've reached the maximum or minimum angle to change direction
        direction_changed = False
        if self.tilt_angle >= self.oscillation_max_angle:
            self.tilt_angle = self.oscillation_max_angle
            if self.tilt_direction > 0:  # Only change direction if we're not already going in the other direction
                self.tilt_direction = -1  # Start tilting in the other direction
                direction_changed = True
        elif self.tilt_angle <= self.oscillation_min_angle:
            self.tilt_angle = self.oscillation_min_angle
            if self.tilt_direction < 0:  # Only change direction if we're not already going in the other direction
                self.tilt_direction = 1  # Start tilting in the other direction
                direction_changed = True
            
        # Apply side force based on tilt angle (but keep gravity pointing down)
        self._apply_tilt_physics()
        
        # Apply visual tilt to platforms AND update collision rects
        self._apply_visual_tilt()
        
        # Apply screen rotation effect
        self._apply_screen_rotation()
        
        # Force an extra platform clipping prevention check on direction change
        if direction_changed:
            # Log the direction change for debugging
            print(f"Tilt direction changed at angle {self.tilt_angle}°")
            
            # Special handling when direction changes to prevent characters from falling through
            self._prevent_platform_clipping_on_direction_change()
    
    def _update_single_tilt(self):
        """Update a single tilt event"""
        # Increment duration counter
        self.tilt_duration += 1
        
        # Increase tilt angle
        self.tilt_angle += self.tilt_speed * self.tilt_direction
        
        # Cap the tilt angle at the maximum
        if abs(self.tilt_angle) > self.max_tilt_angle:
            self.tilt_angle = self.max_tilt_angle * self.tilt_direction
            
        # Apply side force based on tilt angle (but keep gravity pointing down)
        self._apply_tilt_physics()
        
        # Apply visual tilt to platforms AND update collision rects
        self._apply_visual_tilt()
        
        # Apply screen rotation effect
        self._apply_screen_rotation()
        
        # Check if tilt duration has exceeded maximum
        if self.tilt_duration >= self.max_tilt_duration:
            self.reset()
            
    def _apply_tilt_physics(self):
        """Apply side force based on tilt angle ONLY to players that are on the ground"""
        # Apply horizontal force only to grounded player sprites
        for player_data in self.game.players.values():
            if 'sprite' in player_data:
                sprite = player_data['sprite']
                
                # Check if the player is on the ground (not in the air)
                if hasattr(sprite, 'in_air') and not sprite.in_air:
                    # Apply a side force proportional to the tilt angle (ONLY horizontal force)
                    angle_rad = math.radians(self.tilt_angle)
                    slide_force = 0.3 * math.sin(angle_rad)  # Adjust strength as needed
                    
                    # ONLY modify horizontal acceleration (x component) for grounded players
                    sprite.acc.x += slide_force
                    
                # DO NOT modify sprite.acc.y - leave gravity completely unchanged
                # DO NOT apply any force to airborne players
                    
    def _apply_visual_tilt(self):
        """Apply visual AND collision tilting to platforms"""
        # Skip if no original positions stored
        if not self.original_platform_positions:
            return
            
        # Calculate rotation point (center of screen)
        center_x = self.center_x
        center_y = self.center_y
        
        # Track platforms that have moved upward to push characters up
        platforms_moved_up = []
        
        # Apply rotation to each platform
        for platform, original_pos in self.original_platform_positions.items():
            # Get original rect dimensions
            orig_rect = self.original_platform_rects[platform]
            orig_width = orig_rect.width
            orig_height = orig_rect.height
            
            # Calculate platform center point relative to stage center
            platform_center_x = original_pos['x'] + orig_width / 2
            platform_center_y = original_pos['y'] + orig_height / 2
            
            x_diff = platform_center_x - center_x
            y_diff = platform_center_y - center_y
            
            # Rotate the center point
            angle_rad = math.radians(self.tilt_angle)
            rotated_x = center_x + (x_diff * math.cos(angle_rad) - y_diff * math.sin(angle_rad))
            rotated_y = center_y + (x_diff * math.sin(angle_rad) + y_diff * math.cos(angle_rad))
            
            # Store the original top position before rotation
            original_top = platform.get_rotated_top() if hasattr(platform, 'get_rotated_top') else platform.rect.top
            
            # Create a new Surface for the rotated platform - use platform's original image
            rotated_surface = pg.transform.rotate(platform.original_image, -self.tilt_angle)
            
            # Get the rect of the rotated surface and position it
            rotated_rect = rotated_surface.get_rect(center=(rotated_x, rotated_y))
            
            # Update platform's rect for drawing AND collision detection
            platform.rect = rotated_rect
            platform.rotated_surface = rotated_surface
            
            # Store additional rendering info
            platform.is_rotated = True
            platform.rotation_angle = self.tilt_angle
            
            # Update the corner points for collision detection
            if hasattr(platform, 'update_rotation'):
                platform.update_rotation(self.tilt_angle, center_x, center_y)
            
            # Check if the platform has moved upward
            new_top = platform.get_rotated_top() if hasattr(platform, 'get_rotated_top') else platform.rect.top
            
            # Only track significant upward movement (more than 2 pixels)
            # This avoids excessive bumping from minor movements
            if new_top < original_top - 2:
                platforms_moved_up.append((platform, original_top, new_top))
            # We don't need to track slight downward movements anymore
        
        # After updating all platforms, check for characters that need to be pushed up
        for player_data in self.game.players.values():
            if 'sprite' in player_data:
                sprite = player_data['sprite']
                
                # ONLY update characters that are firmly grounded (not just leaving a platform)
                # and only if they've been grounded for a few frames
                if not sprite.in_air and not getattr(sprite, 'just_jumped', False):
                    # Store whether the character was actually on a platform that moved
                    on_moving_platform = False
                    
                    for platform, original_top, new_top in platforms_moved_up:
                        # Check horizontal overlap
                        platform_left = platform.get_rotated_left() if hasattr(platform, 'get_rotated_left') else platform.rect.left
                        platform_right = platform.get_rotated_right() if hasattr(platform, 'get_rotated_right') else platform.rect.right
                        
                        # More strict horizontal check - character must be mostly on platform
                        character_center = sprite.rect.centerx
                        if character_center > platform_left and character_center < platform_right:
                            # Also check that character is VERY close to platform top (max 3 pixels)
                            platform_top = new_top  # Use the new top position
                            if abs(sprite.rect.bottom - original_top) <= 3:
                                on_moving_platform = True
                                
                                # Don't push if player is intentionally dropping through platform
                                is_dropping_through = False
                                if hasattr(sprite, 'drop_through') and sprite.drop_through:
                                    is_dropping_through = True
                                
                                # Check for down input which allows dropping through
                                if hasattr(sprite, 'controller'):
                                    if getattr(sprite.controller, 'down_pressed', False):
                                        is_dropping_through = True
                                
                                if not is_dropping_through:
                                    # Calculate exact push amount (only the amount the platform moved up)
                                    upward_delta = original_top - new_top
                                    
                                    # Push character up by exactly the amount the platform moved
                                    sprite.pos.y -= upward_delta
                                    sprite.rect.bottom = sprite.pos.y
                                    
                                    # No need to check other platforms
                                    break
                    
                    # If character wasn't on any moving platform, don't mess with their position
                    if not on_moving_platform:
                        # Let regular physics handle their movement
                        pass
    
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
        if self.continuous_tilt:
            # If in continuous mode, don't reset completely
            return
            
        self.is_active = False
        self.tilt_angle = 0
        
        # Restore original platform positions and rects
        for platform, original_pos in self.original_platform_positions.items():
            platform.rect.x = original_pos['x']
            platform.rect.y = original_pos['y']
            
            # Restore original rect for collision
            if platform in self.original_platform_rects:
                platform.rect = self.original_platform_rects[platform].copy()
            
            # Clear rotation flags
            if hasattr(platform, 'is_rotated'):
                platform.is_rotated = False
                platform.rotation_angle = 0
            
        # Record event in game's event system if available
        if hasattr(self.game, 'record_event'):
            self.game.record_event("BATTLEFIELD_RESET", 
                                  "The battlefield has returned to normal!", 
                                  "Medium")
                    
        # Clear stored positions if not in continuous mode
        if not self.continuous_tilt:
            self.original_platform_positions = {}
            self.original_platform_rects = {}

    def _prevent_platform_clipping(self):
        """Additional check to ensure characters don't fall through platforms"""
        # For each character in the game
        for player_data in self.game.players.values():
            if 'sprite' in player_data:
                sprite = player_data['sprite']
                
                # Skip if the character is already in the air and clearly falling
                # This avoids unnecessary checks for characters in mid-air
                if sprite.in_air and sprite.vel.y > 3:
                    continue
                    
                # Skip if the player is intentionally dropping through platform
                is_dropping_through = False
                if hasattr(sprite, 'drop_through') and sprite.drop_through:
                    is_dropping_through = True
                
                # Check for down input which allows dropping through
                if hasattr(sprite, 'controller'):
                    if getattr(sprite.controller, 'down_pressed', False):
                        is_dropping_through = True
                
                if is_dropping_through:
                    continue
                
                # Get the character's feet position
                feet_x = sprite.rect.centerx
                feet_y = sprite.rect.bottom
                
                # Check all platforms for potential collisions
                for platform in self.game.platforms:
                    # Skip if not rotated - regular collision will handle those
                    if not platform.is_rotated:
                        continue
                        
                    # Quick check if character is horizontally over the platform
                    # Only check with the center point of the character
                    platform_left = platform.get_rotated_left() if hasattr(platform, 'get_rotated_left') else platform.rect.left
                    platform_right = platform.get_rotated_right() if hasattr(platform, 'get_rotated_right') else platform.rect.right
                    
                    if not (feet_x >= platform_left and feet_x <= platform_right):
                        continue
                    
                    # Get platform top
                    platform_top = platform.get_rotated_top() if hasattr(platform, 'get_rotated_top') else platform.rect.top
                    
                    # Only trigger if character is REALLY close to platform (5 pixels max)
                    # and only if the character was previously grounded
                    # This prevents constant bumping during regular gameplay
                    if platform_top <= feet_y <= platform_top + 5 and not sprite.in_air:
                        # Character is actually clipping through the platform
                        # Reposition them, but very carefully
                        sprite.pos.y = platform_top
                        sprite.rect.bottom = platform_top
                        
                        # Reset vertical velocity - but only if they're falling
                        if sprite.vel.y > 0:
                            sprite.vel.y = 0
                            
                        # Ensure they're considered grounded
                        sprite.in_air = False
                        
                        # Set last_ground_y for proper physics
                        if hasattr(sprite, 'last_ground_y'):
                            sprite.last_ground_y = platform_top
                            
                        # We don't need to check other platforms
                        break
    
    def _prevent_platform_clipping_on_direction_change(self):
        """Additional check to ensure characters don't fall through platforms when direction changes"""
        # For each character in the game
        for player_data in self.game.players.values():
            if 'sprite' in player_data:
                sprite = player_data['sprite']
                
                # Only handle characters that are close to a platform
                # Don't include airborne characters that are clearly not near a platform
                if sprite.in_air and sprite.vel.y > 2:  # If falling fast, leave them alone
                    continue
                
                # Skip if player is intentionally dropping through platform
                is_dropping_through = False
                if hasattr(sprite, 'drop_through') and sprite.drop_through:
                    is_dropping_through = True
                
                # Check for down input which allows dropping through
                if hasattr(sprite, 'controller'):
                    if getattr(sprite.controller, 'down_pressed', False):
                        is_dropping_through = True
                
                if is_dropping_through:
                    continue
                
                # Get the character's feet position and body bounds
                feet_x = sprite.rect.centerx
                feet_y = sprite.rect.bottom
                
                # Use a more reasonable collision box (no extra buffer)
                character_left = sprite.rect.left
                character_right = sprite.rect.right
                
                # Track if we've found a platform for this character
                platform_found = False
                
                # Check all platforms for potential collisions
                for platform in self.game.platforms:
                    # Skip if not rotated 
                    if not platform.is_rotated:
                        continue
                        
                    # Standard horizontal check - character must overlap with platform
                    platform_left = platform.get_rotated_left() if hasattr(platform, 'get_rotated_left') else platform.rect.left
                    platform_right = platform.get_rotated_right() if hasattr(platform, 'get_rotated_right') else platform.rect.right
                    
                    # Check for horizontal overlap between character and platform
                    if not (character_right > platform_left and character_left < platform_right):
                        continue
                    
                    # For direction changes, use a smaller check range (10 pixels instead of 20)
                    platform_top = platform.get_rotated_top() if hasattr(platform, 'get_rotated_top') else platform.rect.top
                    
                    # Only check if the character is very close to the platform (within 7 pixels)
                    if platform_top - 2 <= feet_y <= platform_top + 7:
                        # Character is close to platform - push them up to stand on it
                        sprite.pos.y = platform_top
                        sprite.rect.bottom = platform_top
                        
                        # Reset vertical velocity and set grounded state
                        sprite.vel.y = 0
                        sprite.in_air = False
                        if hasattr(sprite, 'is_grounded'):
                            sprite.is_grounded = True
                        
                        # Set last_ground_y for proper physics
                        if hasattr(sprite, 'last_ground_y'):
                            sprite.last_ground_y = platform_top
                            
                        # Debug logging but make it less verbose
                        # print(f"Direction change: Repositioned character {player_data.get('name', 'unknown')} onto platform")
                        
                        platform_found = True
                        break  # No need to check more platforms
                
                # Only log if we actually did something (reduce spam)
                if platform_found and sprite.in_air:
                    sprite.in_air = False
                    # print(f"Direction change: Grounded airborne character {player_data.get('name', 'unknown')}")