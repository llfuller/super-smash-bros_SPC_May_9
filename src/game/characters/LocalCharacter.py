import sys
import pygame as pg

# move up one directory to be able to import the settings and images
sys.path.append("..")
from settings import *
from images import *
from characters.MeleePhysics import MeleePhysicsMixin  # Import the mixin
from melee_physics import KNOCKBACK_EXAMPLES, calculate_knockback  # Import needed constants

# Add new animation state
LANDING = 'landing'

# Character size scaling factor
CHARACTER_SCALE = 2.0

# Movement speed multiplier (horizontal only)
MOVEMENT_SPEED_MULTIPLIER = 2.0

# Jump height adjustment to compensate for larger character size
JUMP_HEIGHT_FACTOR = 1.0  # Adjust this to control jump height

# Knockback base values
BASE_KNOCKBACK_X = 3.0  # Base horizontal knockback
BASE_KNOCKBACK_Y = 2.0  # Base vertical knockback

vec = pg.math.Vector2

# This is a modified base character class that doesn't rely on hardcoded keyboard input
class LocalCharacter(pg.sprite.Sprite, MeleePhysicsMixin):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move, 
                 images_walk_r, images_walk_l, image_stand_r, image_stand_l,
                 image_weak_r, image_weak_l, image_heavy_r, image_heavy_l,
                 image_damaged_r, image_damaged_l, image_dead,
                 weak_damage, heavy_damage, acceleration):
        pg.sprite.Sprite.__init__(self)

        # Identity
        self.name = name
        self.status = status
        
        # Stats - convert health to damage percentage (starting at 0%)
        self.damage_percent = 0.0  # Damage percentage (Smash Bros style)
        self.weak = weak_damage
        self.heavy = heavy_damage
        # Keep the original acceleration value
        self.acce = acceleration
        
        # Position and movement
        self.pos = vec(pos[0], pos[1])  # Convert to Vector2 for consistency
        self.direc = direc
        self.walk_c = walk_c if walk_c is not None else 0
        self.move = move
        
        # Initialize last ground position tracker
        # This helps prevent characters from falling through platforms
        self.last_ground_y = pos[1]  # Start with spawn position as ground
        self.initialized_platform_check = False
        
        # Animation state variables
        self.animation_frame_counter = 0
        self.animation_locked = False
        self.animation_lock_timer = 0
        self.animation_lock_duration = 0
        self.in_air = False  # Start on the ground by default
        self.landing_lag = 0
        
        # Input state variables (for Melee physics)
        self.moving_left = False
        self.moving_right = False
        self.is_jumping = False
        self.is_fast_falling = False
        
        # Platform drop-through variables
        self.drop_through = False  # Flag set by controller when down is pressed
        self.dropping_through_platforms = set()  # Set of platforms being dropped through
        self.is_dropping_through = False  # State flag to track a drop-through in progress
        
        # Attack recovery timers (in frames)
        self.weak_attack_recovery = 20
        self.heavy_attack_recovery = 35
        self.landing_recovery = 10  # Base landing recovery
        self.damage_stun = 15  # Base stun from taking damage
        
        # Graphics - scale all images to 2x size
        self.walkR = [self.scale_image(img) for img in images_walk_r]
        self.walkL = [self.scale_image(img) for img in images_walk_l]
        self.standR = self.scale_image(image_stand_r)
        self.standL = self.scale_image(image_stand_l)
        self.weakR = self.scale_image(image_weak_r)
        self.weakL = self.scale_image(image_weak_l)
        self.heavyR = self.scale_image(image_heavy_r)
        self.heavyL = self.scale_image(image_heavy_l)
        self.damagedR = self.scale_image(image_damaged_r)
        self.damagedL = self.scale_image(image_damaged_l)
        self.dead_image = self.scale_image(image_dead)
        
        # Physics
        self.game = game
        
        # Set initial image based on direction
        if self.direc == LEFT:
            self.image = self.standL
        else:
            self.image = self.standR
            
        self.rect = self.image.get_rect()
        
        # Important: Set midbottom instead of center to ensure character stands on platforms
        self.rect.midbottom = self.pos
        
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        
        # Input flag - whether this character should be controlled by keyboard
        self.process_input = False
        
        # Initialize Melee physics based on character name
        character_type = 'generic'
        if 'mario' in name.lower():
            character_type = 'mario'
        elif 'luigi' in name.lower():
            character_type = 'luigi'
        
        self.init_melee_physics(character_type)
    
    def scale_image(self, image):
        """Scale an image to the desired size (2x)"""
        current_width = image.get_width()
        current_height = image.get_height()
        new_width = int(current_width * CHARACTER_SCALE)
        new_height = int(current_height * CHARACTER_SCALE)
        return pg.transform.scale(image, (new_width, new_height))

    def jump(self):
        # Debug info to see if this function is getting called
        print(f"{self.name} attempting to jump. Currently in_air: {self.in_air}, animation_locked: {self.animation_locked}")
        
        # Make sure we can actually jump
        if self.animation_locked:
            print(f"{self.name} can't jump because animation is locked")
            return False
            
        if self.in_air:
            print(f"{self.name} can't jump because already in air")
            return False
        
        # Apply a single upward impulse (don't change horizontal velocity)
        self.vel.y = -16  # Reduced from -20 for lower jumps
        self.in_air = True
        self.is_jumping = True
        
        # Clear any platform we were on
        self.last_ground_y = None
        
        print(f"{self.name} jumped with velocity {self.vel.y}")
        return True

    def take_damage(self, damage, attacker_pos_x):
        """
        Apply damage (increases percentage) and calculate knockback based on percentage
        Returns the new damage percentage
        """
        try:
            # Use Melee physics for damage and knockback
            # For weak attacks, use low knockback growth
            # For heavy attacks, use higher knockback growth and base knockback
            if damage <= self.weak:
                kb_growth = KNOCKBACK_EXAMPLES['weak']['knockback_growth'] 
                base_kb = KNOCKBACK_EXAMPLES['weak']['base_knockback']
            elif damage <= self.heavy:
                kb_growth = KNOCKBACK_EXAMPLES['medium']['knockback_growth']
                base_kb = KNOCKBACK_EXAMPLES['medium']['base_knockback']
            else:
                kb_growth = KNOCKBACK_EXAMPLES['strong']['knockback_growth']
                base_kb = KNOCKBACK_EXAMPLES['strong']['base_knockback']
            
            # Use 45 degree angle for all attacks for now
            angle = 45
            
            # Use Melee physics for damage calculation
            return self.take_damage_with_melee_physics(damage, kb_growth, base_kb, attacker_pos_x, angle)
        except Exception as e:
            # Fallback to a basic implementation if there's an error
            print(f"Error in take_damage: {e}, using fallback method")
            
            # Basic damage and knockback
            self.damage_percent += damage
            
            # Simple knockback based on damage percentage
            knockback_multiplier = 1.0 + (self.damage_percent / 100.0)
            
            # Determine horizontal knockback direction
            knockback_direction = 1 if attacker_pos_x < self.pos.x else -1
            
            # Apply simple knockback
            self.vel.x = 5 * knockback_multiplier * knockback_direction
            self.vel.y = -4 * knockback_multiplier  # Negative for upward
            
            # Set state
            self.in_air = True
            self.move = DAMAGED
            self.animation_locked = True
            self.animation_lock_timer = 0
            self.animation_lock_duration = 20  # Fixed stun duration
            
            print(f"{self.name} took {damage}% damage, now at {self.damage_percent}%")
            return self.damage_percent
    
    def weakAttack(self):
        # Only allow attack if not already in an attack animation or damaged
        if self.animation_locked or self.move in [WEAK_ATTACK, HEAVY_ATTACK, DAMAGED, LANDING] or self.damage_percent >= 999:
            return
            
        if not self.game.chatting:
            # Lock animation for weak attack duration
            self.animation_locked = True
            self.animation_lock_timer = 0
            self.animation_lock_duration = self.weak_attack_recovery
            self.move = WEAK_ATTACK
            
            # Check collision with enemies
            enemy_group = getattr(self, 'enemy_sprites', self.game.enemy_sprites)
            collided_enemies = pg.sprite.spritecollide(self, enemy_group, False)
            for enemy in collided_enemies:
                # Apply damage using percentage system
                enemy.take_damage(self.weak, self.pos.x)
                self.game.attackPlayer(enemy.name, self.weak, DAMAGED, self.pos.x)

    def heavyAttack(self):
        # Only allow attack if not already in an attack animation or damaged
        if self.animation_locked or self.move in [WEAK_ATTACK, HEAVY_ATTACK, DAMAGED, LANDING] or self.damage_percent >= 999:
            return
            
        if not self.game.chatting:
            # Lock animation for heavy attack duration
            self.animation_locked = True
            self.animation_lock_timer = 0
            self.animation_lock_duration = self.heavy_attack_recovery
            self.move = HEAVY_ATTACK
            
            # Check collision with enemies
            enemy_group = getattr(self, 'enemy_sprites', self.game.enemy_sprites)
            collided_enemies = pg.sprite.spritecollide(self, enemy_group, False)
            for enemy in collided_enemies:
                # Apply damage using percentage system
                enemy.take_damage(self.heavy, self.pos.x)
                self.game.attackPlayer(enemy.name, self.heavy, DAMAGED, self.pos.x)
    
    def update(self):
        # Disable emergency reset - we have a better solution now
        # Save previous position and state for collision checking
        previous_pos = vec(self.pos.x, self.pos.y)
        was_in_air = self.in_air
        was_knockback = getattr(self, 'is_knockback_air', False)
        
        # Add debug every ~60 frames if in knockback
        if hasattr(self, 'is_knockback_air') and self.is_knockback_air and hasattr(self.game, 'current_frame'):
            if self.game.current_frame % 60 == 0:
                print(f"KNOCKBACK DEBUG: {self.name} in knockback, pos=({self.pos.x}, {self.pos.y}), vel=({self.vel.x}, {self.vel.y})")
                print(f"KNOCKBACK DEBUG: hitstun={getattr(self, 'hitstun_frames', 0)}, in_air={self.in_air}, dropping={getattr(self, 'is_dropping_through', False)}")
        
        # First update Melee physics - but don't let it override our gravity
        was_gravity = self.acc.y
        self.update_melee_physics()
        self.update_l_cancel_window()
        
        # CRITICAL: Handle hitstun and knockback state correctly
        # Initialize the knockback flag if needed
        if not hasattr(self, 'is_knockback_air'):
            self.is_knockback_air = False
            
        # Handle animation lock timers
        if self.animation_locked:
            self.animation_lock_timer += 1
            if self.animation_lock_timer >= self.animation_lock_duration:
                self.animation_locked = False
                # After lock expires, return to standing if not moving
                if self.move in [WEAK_ATTACK, HEAVY_ATTACK, DAMAGED, LANDING]:
                    self.move = STAND
        
        # CRITICAL: Always check if we're actually on solid ground
        if not self.in_air:
            # Check if there's a platform directly under us
            self.check_ground_beneath()
            
            # PLATFORM DROP-THROUGH LOGIC: Check if we should initiate drop-through
            if self.drop_through:
                # Check for a platform directly under our feet
                current_platform = self.get_platform_at_position(self.pos.x, self.pos.y)
                if current_platform and current_platform.type == 'platform':
                    # This is a valid platform we can drop through
                    print(f"{self.name} initiating drop-through at y={self.pos.y}")
                    
                    # Force character into air state
                    self.in_air = True
                    self.is_dropping_through = True
                    self.dropping_through_platforms.add(current_platform)
                    
                    # Give slight downward velocity to start fall
                    self.vel.y = 1.5
                    
                    # Clear ground state
                    self.last_ground_y = None
                    if hasattr(self, 'last_platform'):
                        delattr(self, 'last_platform')
        
        # Special handling for knockback - NEVER allow drop-through in hitstun
        if self.is_knockback_air:
            # Reset any potential drop-through flags during knockback
            self.is_dropping_through = False
            self.dropping_through_platforms = set()
        
        # Apply horizontal movement - always allow this, but with different physics in air
        horizontal_update = self.vel.x + 0.5 * self.acc.x
        self.pos.x += horizontal_update
        
        # Apply vertical movement - gravity when in air
        if self.in_air:
            # Check if we are in hitstun
            in_hitstun = hasattr(self, 'hitstun_frames') and self.hitstun_frames > 0
            
            if in_hitstun:
                # Track initial hitstun duration if this is a new hitstun state
                if not hasattr(self, 'initial_hitstun'):
                    self.initial_hitstun = self.hitstun_frames
                
                # Calculate gravity scale based on hitstun progress
                # 0 = no gravity, 1 = full gravity
                hitstun_progress = 1.0 - (self.hitstun_frames / max(1, self.initial_hitstun))
                
                # Gradually turn on gravity starting from the middle of hitstun
                if hitstun_progress < 0.5:
                    # First half of hitstun - no gravity
                    gravity_scale = 0.0
                else:
                    # Second half - linearly interpolate from 0 to 1
                    # Map 0.5-1.0 to 0.0-1.0
                    gravity_scale = (hitstun_progress - 0.5) * 2.0
                
                # Apply scaled gravity
                if gravity_scale > 0:
                    scaled_gravity = 0.5 * gravity_scale  # Base gravity * scale
                    self.vel.y += scaled_gravity
                    
                    # Debug output occasionally
                    if self.game.current_frame % 20 == 0:
                        print(f"HITSTUN DEBUG: {self.name} hitstun progress: {hitstun_progress:.2f}, gravity scale: {gravity_scale:.2f}")
            else:
                # Normal gravity when not in hitstun
                # Reset initial hitstun tracking
                if hasattr(self, 'initial_hitstun'):
                    delattr(self, 'initial_hitstun')
                
                # Apply full gravity
                self.acc.y = 0.5  # Constant gravity
                self.vel.y += self.acc.y  # Accumulate gravity
            
            # Cap falling speed to prevent excessive velocity
            if self.vel.y > 10:
                self.vel.y = 10
                
            # Update vertical position
            self.pos.y += self.vel.y
        else:
            # Reset vertical velocity when on ground
            self.vel.y = 0
            self.acc.y = 0
            
            # Ensure position is at ground level if we have it
            if hasattr(self, 'last_ground_y') and self.last_ground_y is not None:
                self.pos.y = self.last_ground_y
        
        # Perform collision detection - first update the rect
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.pos
        
        # Always check for platform collisions
        # Check for platforms
        collision = pg.sprite.spritecollide(self, self.game.platforms, False)
        
        # Debug output for drop-through state
        if self.drop_through and not self.in_air:
            print(f"{self.name} wants to drop through, down key is pressed")
        
        # Update drop-through platform tracking
        if self.dropping_through_platforms:
            # Clear platforms that we're no longer in contact with
            platforms_to_remove = set()
            for platform in self.dropping_through_platforms:
                # Remove platform if we're below it or no longer colliding
                if self.pos.y > platform.rect.bottom + 10 or platform not in collision:
                    platforms_to_remove.add(platform)
            
            # Remove platforms we've fully dropped through
            self.dropping_through_platforms -= platforms_to_remove
            
            # If no more platforms being dropped through, reset state
            if not self.dropping_through_platforms:
                if self.is_dropping_through:
                    print(f"{self.name} finished drop-through")
                self.is_dropping_through = False
        
        # CRITICAL: Prevent infinite loop - clear collision if we just landed
        should_check_collision = True
        if not was_in_air and not self.in_air and hasattr(self, '_last_landing_frame'):
            if self.game.current_frame - self._last_landing_frame < 2:
                # Skip collision check if we just landed in the last frame
                should_check_collision = False
        
        if should_check_collision:
            # Filter platforms:
            # 1. Always collide with floors
            # 2. For regular platforms, handle drop-through logic
            # 3. Allow passing through from below
            filtered_collision = []
            for platform in collision:
                # Check if we're currently dropping through this platform
                if platform in self.dropping_through_platforms:
                    continue
                
                # CRITICAL: When in knockback (hitstun), don't drop through ANY platforms
                if hasattr(self, 'is_knockback_air') and self.is_knockback_air:
                    # During knockback, collide with ALL platforms
                    filtered_collision.append(platform)
                    continue
                    
                # Check if we're initiating a drop-through
                if self.can_drop_through(platform, previous_pos):
                    print(f"{self.name} will drop through platform at y={platform.rect.top}")
                    self.dropping_through_platforms.add(platform)
                    self.is_dropping_through = True
                    continue
                
                # Check if we're passing through from below
                if self.is_passing_through_from_below(platform, previous_pos):
                    self.dropping_through_platforms.add(platform)
                    self.is_dropping_through = True
                    continue
                
                # Can't pass through, handle normal collision
                filtered_collision.append(platform)
            
            if filtered_collision:
                # Sort platforms by y-position to find the highest one we're colliding with
                filtered_collision.sort(key=lambda p: p.rect.top)
                platform = filtered_collision[0]
                
                # Check if we need to handle landing/standing on platform
                if self.vel.y >= 0:  # Only land when moving downward or still
                    # Get position of character's feet
                    feet_y = self.pos.y
                    platform_top = platform.rect.top + 4  # Adjusted top with offset
                    
                    # Check if we're landing from above (with tolerance)
                    if previous_pos.y <= platform.rect.top:
                        # Apply landing lag if we were in the air
                        if was_in_air:
                            # Use Melee physics for landing lag
                            was_aerial_attack = self.move in [WEAK_ATTACK, HEAVY_ATTACK]
                            self.apply_landing_lag_with_melee_physics(was_aerial_attack)
                        
                        # Force position onto the platform with adjusted offset to make character visually on the platform
                        self.pos.y = platform_top  # Use the adjusted platform top
                        self.vel.y = 0
                        self.in_air = False
                        
                        # Store the ground y-position and platform reference
                        self.last_ground_y = self.pos.y
                        self.last_platform = platform
                        self._last_landing_frame = getattr(self.game, 'current_frame', 0)
                        
                        # Reset jumping and fast falling flags
                        self.is_jumping = False
                        self.is_fast_falling = False
                        
                        # Reset drop-through state
                        self.is_dropping_through = False
                        self.dropping_through_platforms.clear()
                        
                        # Reset knockback state if landing after knockback
                        if hasattr(self, 'is_knockback_air') and self.is_knockback_air:
                            self.is_knockback_air = False
                        
                        if was_in_air:
                            # Only log if actually landing from air
                            print(f"{self.name} landed on platform at y={self.pos.y}")
                elif self.vel.y < 0:  # Moving upward
                    # Hit platform from below, reset vertical velocity
                    self.vel.y = 0
            else:
                # No valid platforms to land on - double-check edge cases
                # Do an additional check for "walking off edge" cases
                if not self.in_air and self.vel.y >= 0:
                    # We should be in air but somehow aren't - verify with precise detection
                    feet_x = self.pos.x
                    feet_y = self.pos.y
                    feet_width = 5
                    
                    # Look for ANY platform below us that would prevent a fall
                    found_support = False
                    for platform in self.game.platforms:
                        # Check horizontal bounds
                        if platform.rect.left - feet_width/2 <= feet_x <= platform.rect.right + feet_width/2:
                            # Check if platform is at our feet or slightly below
                            platform_top = platform.rect.top
                            if abs(feet_y - platform_top) < 8:  # Within 8 pixels (slight tolerance)
                                found_support = True
                                break
                    
                    if not found_support:
                        # We're legitimately off an edge
                        print(f"{self.name} has no support below - setting to air state")
                        self.in_air = True
                        self.vel.y = 0.1  # Small initial velocity
                        self.last_ground_y = None
        
        # Update sprite image based on current state
        self.update_sprite_image()
        
        # Final update to collision rectangle
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.pos
    
    def check_ground_beneath(self):
        """Check if there's ground beneath the character"""
        # Only run this check for grounded characters
        if self.in_air:
            return
            
        # CRITICAL: Get the EXACT position of the character's feet
        feet_x = self.pos.x
        feet_y = self.pos.y  # This is already the bottom of the character
        
        # Create a more precise hitbox for ground detection
        feet_width = 5  # Narrow feet hitbox (pixels)
        
        # Check for platforms directly beneath the character's feet
        left_edge = feet_x - feet_width/2
        right_edge = feet_x + feet_width/2
        
        # Debug visualization - uncomment if needed
        # self.game.screen.fill((255, 0, 0), pg.Rect(left_edge, feet_y, feet_width, 5))
        
        # Check all platforms
        found_platform = False
        for platform in self.game.platforms:
            # Only check if feet are within horizontal bounds of the platform
            if (left_edge <= platform.rect.right and 
                right_edge >= platform.rect.left):
                
                # Check if the platform is at the right height (accounting for the 4-pixel offset)
                platform_top = platform.rect.top + 4
                if abs(feet_y - platform_top) < 5:  # Within 5 pixels of platform's adjusted top
                    found_platform = True
                    # We're on this platform
                    break
        
        # If no platform found beneath us, start falling
        if not found_platform:
            # Verify we're actually off the edge by doing a deeper check
            # Look for ANY platform below us 
            for platform in self.game.platforms:
                if (left_edge <= platform.rect.right and 
                    right_edge >= platform.rect.left and
                    platform.rect.top > feet_y and
                    platform.rect.top < feet_y + 100):  # Check up to 100 pixels below
                    # There's a platform below, don't trigger fall yet - the character is just transitioning between platforms
                    return
            
            # We're genuinely off an edge with nothing below
            print(f"{self.name} is off edge at ({feet_x}, {feet_y}) - will fall")
            self.in_air = True
            self.vel.y = 0.1  # Small initial downward velocity
    
    def get_platform_at_position(self, x, y):
        """Find a platform at the given position"""
        for platform in self.game.platforms:
            if (platform.rect.left <= x <= platform.rect.right and
                abs(y - platform.rect.top) < 5):
                return platform
        return None

    def apply_landing_lag(self):
        """Apply landing lag based on vertical velocity and other factors"""
        # This function is kept for compatibility but we use the Melee version instead
        was_aerial_attack = self.move in [WEAK_ATTACK, HEAVY_ATTACK]
        self.apply_landing_lag_with_melee_physics(was_aerial_attack)

    def update_sprite_image(self):
        """Update the sprite's image based on current movement state"""
        # Animation frame counter for controlling animation speed
        self.animation_frame_counter += 1
        
        # Update walk animations at a normal speed (every 5 frames - same as other animations)
        should_update = self.animation_frame_counter % 5 == 0
        
        if self.move == WALK:
            if self.direc == LEFT:
                # Only update walk_c when should_update is True
                if should_update:
                    max_walk = len(self.walkL) - 1
                    self.walk_c = (self.walk_c + 1) % max(1, max_walk)
                self.image = self.walkL[min(self.walk_c, len(self.walkL)-1)]
            elif self.direc == RIGHT:
                # Only update walk_c when should_update is True
                if should_update:
                    max_walk = len(self.walkR) - 1
                    self.walk_c = (self.walk_c + 1) % max(1, max_walk)
                self.image = self.walkR[min(self.walk_c, len(self.walkR)-1)]
        
        elif self.move == STAND:
            if self.direc == LEFT:
                self.image = self.standL
            elif self.direc == RIGHT:
                self.image = self.standR

        elif self.move == WEAK_ATTACK:
            if self.direc == LEFT:
                self.image = self.weakL
            elif self.direc == RIGHT:
                self.image = self.weakR

        elif self.move == HEAVY_ATTACK:
            if self.direc == LEFT:
                self.image = self.heavyL
            elif self.direc == RIGHT:
                self.image = self.heavyR
        
        elif self.move == DAMAGED or self.move == LANDING:
            # Both damaged and landing use the same animation for now
            if self.direc == LEFT:
                self.image = self.damagedL
            elif self.direc == RIGHT:
                self.image = self.damagedR

        if self.damage_percent >= 999:
            self.image = self.dead_image

    def can_move(self):
        """Check if character can be controlled by movement inputs"""
        return not self.animation_locked and self.damage_percent < 999 and self.hitstun_frames <= 0

    def is_defeated(self):
        """Check if character is defeated (999% damage)"""
        return self.damage_percent >= 999

    def can_drop_through(self, platform, previous_pos=None):
        """Check if the platform can be dropped through"""
        # Floor platforms cannot be dropped through
        if platform.type == 'floor':
            return False
        
        # If not a valid platform, cannot drop through
        if platform.type != 'platform':
            return False
        
        # If already dropping through this platform, allow it to continue
        if platform in self.dropping_through_platforms:
            return True
        
        # Only allow drop-through if down key is deliberately pressed
        # AND we're on top of the platform (not hitting from side/below)
        if self.drop_through and not self.in_air:
            # Check if we're actually on top of this platform
            # More precise check: are we standing on it?
            platform_top = platform.rect.top + 4  # Adjusted top with offset
            if (abs(self.pos.y - platform_top) < 5 and  # Within 5 pixels of platform top + offset
                self.pos.x >= platform.rect.left and 
                self.pos.x <= platform.rect.right):
                print(f"{self.name} can drop through platform at y={platform.rect.top}")
                return True
        
        # If in a drop-through state, allow it to continue
        if self.is_dropping_through:
            return True
        
        # Otherwise, cannot drop through
        return False

    def is_passing_through_from_below(self, platform, previous_pos):
        """Check if character is passing through a platform from below"""
        # Only apply to non-floor platforms
        if platform.type == 'floor':
            return False
            
        # Never pass through platforms during knockback
        if hasattr(self, 'is_knockback_air') and self.is_knockback_air:
            return False
            
        # Check if we're moving upward
        if self.vel.y < 0:
            # Check if we were below the platform in the previous frame
            if previous_pos.y > platform.rect.bottom:
                print(f"{self.name} passing through platform from below")
                return True
                
        return False

# Create local character versions of each character

# Mario - has maM1 through maM7
class LocalMario(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        # Remove standing sprite from walk animation
        walkR = [maM1, maM2, maM3, maM4, maM5, maM6, maM7]
        walkL = [pg.transform.flip(image, True, False) for image in walkR]
        standR = maS1
        standL = pg.transform.flip(standR, True, False)
        weakR = maW1
        weakL = pg.transform.flip(weakR, True, False)
        heavyR = maH1
        heavyL = pg.transform.flip(heavyR, True, False)
        damagedR = maD1
        damagedL = pg.transform.flip(damagedR, True, False)
        
        super().__init__(
            game, name, status, health, pos, direc, walk_c, move,
            walkR, walkL, standR, standL, 
            weakR, weakL, heavyR, heavyL,
            damagedR, damagedL, dead,
            3, 6, 0.5  # weak damage, heavy damage, acceleration
        )
        # Ensure Mario uses mario physics
        self.init_melee_physics('mario')

# Luigi - has luM1 through luM8
class LocalLuigi(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        # Remove standing sprite from walk animation
        walkR = [luM1, luM2, luM3, luM4, luM5, luM6, luM7, luM8]
        walkL = [pg.transform.flip(image, True, False) for image in walkR]
        standR = luS1
        standL = pg.transform.flip(standR, True, False)
        weakR = luW1
        weakL = pg.transform.flip(weakR, True, False)
        heavyR = luH1
        heavyL = pg.transform.flip(heavyR, True, False)
        damagedR = luD1
        damagedL = pg.transform.flip(damagedR, True, False)
        
        super().__init__(
            game, name, status, health, pos, direc, walk_c, move,
            walkR, walkL, standR, standL, 
            weakR, weakL, heavyR, heavyL,
            damagedR, damagedL, dead,
            4, 8, 0.4  # weak damage, heavy damage, acceleration
        )
        # Ensure Luigi uses luigi physics
        self.init_melee_physics('luigi')

# Yoshi - has yoM1 through yoM8
class LocalYoshi(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        # Remove standing sprite from walk animation
        walkR = [yoM1, yoM2, yoM3, yoM4, yoM5, yoM6, yoM7, yoM8]
        walkL = [pg.transform.flip(image, True, False) for image in walkR]
        standR = yoS1
        standL = pg.transform.flip(standR, True, False)
        weakR = yoW1
        weakL = pg.transform.flip(weakR, True, False)
        heavyR = yoH1
        heavyL = pg.transform.flip(heavyR, True, False)
        damagedR = yoD1
        damagedL = pg.transform.flip(damagedR, True, False)
        
        super().__init__(
            game, name, status, health, pos, direc, walk_c, move,
            walkR, walkL, standR, standL, 
            weakR, weakL, heavyR, heavyL,
            damagedR, damagedL, dead,
            5, 10, 0.3  # weak damage, heavy damage, acceleration
        )

# Popo
class LocalPopo(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        # Popo only has 3 movement sprites - remove standing sprite
        walkL = [poM1, poM2, poM3]
        walkR = [pg.transform.flip(image, True, False) for image in walkL]
        standL = poS1
        standR = pg.transform.flip(standL, True, False)
        weakL = poW1
        weakR = pg.transform.flip(weakL, True, False)
        heavyL = poH1
        heavyR = pg.transform.flip(heavyL, True, False)
        damagedL = poD1
        damagedR = pg.transform.flip(damagedL, True, False)
        
        super().__init__(
            game, name, status, health, pos, direc, walk_c, move,
            walkR, walkL, standR, standL, 
            weakR, weakL, heavyR, heavyL,
            damagedR, damagedL, dead,
            5.5, 11, 0.25  # weak damage, heavy damage, acceleration
        )

# Nana
class LocalNana(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        # Nana only has 3 movement sprites - remove standing sprite
        walkL = [naM1, naM2, naM3]
        walkR = [pg.transform.flip(image, True, False) for image in walkL]
        standL = naS1
        standR = pg.transform.flip(standL, True, False)
        weakL = naW1
        weakR = pg.transform.flip(weakL, True, False)
        heavyL = naH1
        heavyR = pg.transform.flip(heavyL, True, False)
        damagedL = naD1
        damagedR = pg.transform.flip(damagedL, True, False)
        
        super().__init__(
            game, name, status, health, pos, direc, walk_c, move,
            walkR, walkL, standR, standL, 
            weakR, weakL, heavyR, heavyL,
            damagedR, damagedL, dead,
            5, 10, 0.3  # weak damage, heavy damage, acceleration
        )

# Link
class LocalLink(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        # Remove standing sprite from walk animation
        walkR = [liM1, liM2, liM3, liM4, liM5, liM6, liM7, liM8]
        walkL = [pg.transform.flip(image, True, False) for image in walkR]
        standR = liS1
        standL = pg.transform.flip(standR, True, False)
        weakR = liW1
        weakL = pg.transform.flip(weakR, True, False)
        heavyR = liH1
        heavyL = pg.transform.flip(heavyR, True, False)
        damagedR = liD1
        damagedL = pg.transform.flip(damagedR, True, False)
        
        super().__init__(
            game, name, status, health, pos, direc, walk_c, move,
            walkR, walkL, standR, standL, 
            weakR, weakL, heavyR, heavyL,
            damagedR, damagedL, dead,
            5, 10, 0.3  # weak damage, heavy damage, acceleration
        ) 