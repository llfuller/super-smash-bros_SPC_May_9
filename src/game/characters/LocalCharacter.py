import sys
import pygame as pg
import math

# move up one directory to be able to import the settings and images
sys.path.append("..")
from settings import *  # Import all settings including GIANT_MODE_ENABLED and GIANT_MODE_SCALE_FACTOR
from images import *
from characters.MeleePhysics import MeleePhysicsMixin  # Import the mixin
from melee_physics import KNOCKBACK_EXAMPLES, calculate_knockback, calculate_hitstun, knockback_to_velocity  # Import needed constants
# Import sound manager
from sound_manager import sound_manager

# Add new animation state
LANDING = 'landing'

# Character size scaling factor - now we use the settings from settings.py
# CHARACTER_SCALE = 2.0

# GIANT MODE scaling - we'll use the settings from settings.py
# GIANT_MODE_ENABLED = False  # Set to True to enable GIANT MODE
# GIANT_MODE_SCALE_FACTOR = 1.75  # This will make characters 1.75x bigger than normal

# Movement speed multiplier (horizontal only)
MOVEMENT_SPEED_MULTIPLIER = 2.0

# Jump height adjustment to compensate for larger character size
JUMP_HEIGHT_FACTOR = 1.0  # Adjust this to control jump height

# Knockback base values
BASE_KNOCKBACK_X = 3.0  # Base horizontal knockback
BASE_KNOCKBACK_Y = 2.0  # Base vertical knockback

# Shield properties
SHIELD_ALPHA = 190  # Transparency of shield
# Default shield colors by character
SHIELD_COLORS = {
    'Mario': (255, 0, 0),       # Red
    'Luigi': (0, 255, 0),       # Green
    'Yoshi': (0, 255, 0),       # Green
    'Popo': (0, 0, 255),        # Blue
    'Nana': (255, 0, 255),      # Pink
    'Link': (0, 255, 255),      # Cyan
    'default': (255, 255, 255)  # White for any other character
}
SHIELD_SIZE = 80                 # Base shield size
SHIELD_DURATION = 300           # Max shield frames before breaking (5 seconds at 60 FPS)

# Get shield size accounting for GIANT MODE scaling
def get_shield_size():
    """Get shield size based on GIANT MODE settings"""
    shield_size = SHIELD_SIZE
    
    # Apply GIANT MODE scaling if enabled in settings
    if getattr(sys.modules['settings'], 'GIANT_MODE_ENABLED', False):
        giant_scale = getattr(sys.modules['settings'], 'GIANT_MODE_SCALE_FACTOR', 1.75)
        shield_size = int(shield_size * giant_scale)
        
    return shield_size

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
        
        # Store original position
        self.original_pos = vec(pos[0], pos[1])
        
        # Initialize position vector - we'll update this after scaling
        self.pos = vec(pos[0], pos[1])
        
        # Movement state initialization
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
        
        # Get character type for shield color
        character_type = 'default'
        for char_name in SHIELD_COLORS.keys():
            if char_name in self.__class__.__name__:
                character_type = char_name
                break
        
        # Shield properties
        self.shield_active = False
        self.shield_health = SHIELD_DURATION
        self.shield_surface = None
        self.shield_color = SHIELD_COLORS.get(character_type, SHIELD_COLORS['default'])
        self.shield_radius = SHIELD_SIZE // 2
        self.shield_broken = False
        self.shield_cooldown = 0  # Cooldown after shield break
        
        # Graphics - scale all images to appropriate size
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
        
        # CRITICAL FIX: When in GIANT_MODE, we need to adjust the midbottom position directly
        # to account for the larger sprite size
        self.giant_mode = getattr(sys.modules['settings'], 'GIANT_MODE_ENABLED', False)
        if self.giant_mode:
            # In giant mode, position the feet at the original position
            print(f"GIANT FIX: Adjusting position for {name}")
            print(f"Original position: {self.pos}, Rect: {self.rect}")
            
            # Set position directly
            self.rect.midbottom = (self.pos.x, self.pos.y)
            # Now update pos to match the rect's midbottom
            self.pos.x, self.pos.y = self.rect.midbottom
            
            print(f"Adjusted position: {self.pos}, Rect midbottom: {self.rect.midbottom}")
        else:
            # Standard positioning - use midbottom
            self.rect.midbottom = (self.pos.x, self.pos.y)
        
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
        
        # Create shield surface
        self.create_shield_surface()
    
    def scale_image(self, image):
        """Scale an image to the desired size (accounting for GIANT MODE)"""
        current_width = image.get_width()
        current_height = image.get_height()
        
        # Calculate the effective scale based on whether GIANT MODE is enabled
        # Default scale is 2.0 if not specified in settings
        scale_factor = getattr(sys.modules['settings'], 'CHARACTER_SCALE', 2.0)
        
        # Apply GIANT MODE scaling if enabled in settings
        if getattr(sys.modules['settings'], 'GIANT_MODE_ENABLED', False):
            giant_scale = getattr(sys.modules['settings'], 'GIANT_MODE_SCALE_FACTOR', 1.75)
            scale_factor *= giant_scale
            print(f"GIANT MODE scale factor: {scale_factor}")
        
        new_width = int(current_width * scale_factor)
        new_height = int(current_height * scale_factor)
        
        # Debug output for scaling
        if getattr(sys.modules['settings'], 'GIANT_MODE_ENABLED', False):
            print(f"Scaling image from {current_width}x{current_height} to {new_width}x{new_height}")
            
        return pg.transform.scale(image, (new_width, new_height))

    def create_shield_surface(self):
        """Create the shield surface with the character's color"""
        # Get scaled shield size based on GIANT MODE setting
        shield_size = SHIELD_SIZE
        
        # Apply GIANT MODE scaling if enabled in settings
        if getattr(sys.modules['settings'], 'GIANT_MODE_ENABLED', False):
            giant_scale = getattr(sys.modules['settings'], 'GIANT_MODE_SCALE_FACTOR', 1.75)
            shield_size = int(shield_size * giant_scale)
            print(f"Giant mode shield size: {shield_size}")
        
        # Create transparent surface for shield
        self.shield_surface = pg.Surface((shield_size, shield_size), pg.SRCALPHA)
        shield_radius = shield_size // 2
        
        # Draw the shield as a circle
        pg.draw.circle(
            self.shield_surface, 
            (*self.shield_color, SHIELD_ALPHA), 
            (shield_radius, shield_radius), 
            shield_radius
        )
        
        # Debug info
        if getattr(self.game, 'shield_debug', False):
            print(f"Created shield for {self.name}: size={shield_size}, color={self.shield_color}")

    def jump(self, is_short_hop=False):
        # Debug info to see if this function is getting called
        print(f"{self.name} attempting to jump. Currently in_air: {self.in_air}, animation_locked: {self.animation_locked}, short_hop: {is_short_hop}")
        
        # Make sure we can actually jump
        if self.animation_locked:
            print(f"{self.name} can't jump because animation is locked")
            return False
            
        if self.in_air:
            print(f"{self.name} can't jump because already in air")
            return False
        
        # Character type detection for playing the right sound
        character_type = self.__class__.__name__.replace('Local', '')
        
        # Apply different upward impulse based on jump type
        if is_short_hop:
            self.vel.y = -10  # Reduced velocity for short hop
            print(f"{self.name} short hopped with velocity {self.vel.y}")
            
            # Play short hop sound
            sound_manager.play_jump_sound(character=character_type, jump_type='short_hop')
        else:
            self.vel.y = -16  # Full jump velocity
            print(f"{self.name} full jumped with velocity {self.vel.y}")
            
            # Play jump sound based on character type
            if 'Samus' in self.__class__.__name__:
                # Samus has a special high jump sound
                sound_manager.play_jump_sound(character='Samus', jump_type='high_jump')
            else:
                # Standard jump sound
                sound_manager.play_jump_sound(character=character_type, jump_type='standard')
            
        self.in_air = True
        self.is_jumping = True
        
        # Clear any platform we were on
        self.last_ground_y = None
        
        return True
        
    def take_damage(self, damage, attacker_pos_x):
        """
        Apply damage (increases percentage) and calculate knockback based on percentage
        Returns the new damage percentage
        """
        try:
            # If shield is active, don't take damage
            if self.shield_active and not self.shield_broken:
                # Reduce shield health based on damage
                self.shield_health -= damage * 2  # Shield depletes faster
                
                # Play shield hit sound
                sound_manager.play_shield_sound('hit')
                
                # Check if shield broke
                if self.shield_health <= 0:
                    self.shield_health = 0
                    self.shield_broken = True
                    self.shield_active = False
                    self.shield_cooldown = 120  # 2 seconds cooldown (60 FPS)
                    # Add shield break effect/animation here if desired
                    print(f"{self.name}'s shield broke!")
                    
                    # Play shield break sound
                    sound_manager.play_shield_sound('break')
                
                # No damage taken, return current damage
                return self.damage_percent
            
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
            
            # If shield is active, don't take damage
            if self.shield_active and not self.shield_broken:
                return self.damage_percent
            
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
            
            # Get character type for sound effects
            character_type = self.__class__.__name__.replace('Local', '')
            
            # Play weak attack sound with character voice
            sound_manager.play_attack_sound('weak', character_type)
            
            # Try to play character-specific attack sound if available
            sound_manager.play_character_sound(character_type, 'attack_weak')
            
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
            
            # Get character type for sound effects
            character_type = self.__class__.__name__.replace('Local', '')
            
            # Play heavy attack sound with character voice
            sound_manager.play_attack_sound('heavy', character_type)
            
            # Try to play character-specific attack sound if available
            sound_manager.play_character_sound(character_type, 'attack_heavy')
            
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
        
        # Update shield cooldown if broken
        if self.shield_broken and self.shield_cooldown > 0:
            self.shield_cooldown -= 1
            if self.shield_cooldown <= 0:
                self.shield_broken = False
                self.shield_health = SHIELD_DURATION  # Reset shield health
        
        # Regenerate shield health slowly when not in use
        if not self.shield_active and not self.shield_broken and self.shield_health < SHIELD_DURATION:
            self.shield_health += 0.5  # Slow regeneration rate
            if self.shield_health > SHIELD_DURATION:
                self.shield_health = SHIELD_DURATION
        
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
        
        # Stop movement if shield is active
        if self.shield_active:
            self.vel.x = 0
            self.acc.x = 0
            
            # Check if shield should break due to timeout
            self.shield_health -= 1
            if self.shield_health <= 0:
                self.shield_health = 0
                self.shield_broken = True
                self.shield_active = False
                self.shield_cooldown = 120  # 2 seconds cooldown
                self.move = STAND
                print(f"{self.name}'s shield broke from extended use!")
        
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
        """Check if there's actually ground beneath us when we think we're grounded"""
        # If we already know we're in the air, no need to check
        if self.in_air:
            return
            
        # Get all platform collisions
        ground_found = False
        
        # Check if we're on any platform - we need to be very slightly above or touching
        # Use a small downward ray cast (1-2 pixels) to check for platform collision
        test_rect = pg.Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height + 2)
        
        for platform in self.game.platforms:
            if platform.rect.colliderect(test_rect):
                # We're on a platform
                ground_found = True
                
                # Remember last ground height
                self.last_ground_y = self.pos.y
                
                # Store platform for collision checks
                if not hasattr(self, 'last_platform'):
                    self.last_platform = platform
                    
                # Once we've confirmed we're on a platform, we can stop checking
                break
                
        # If no ground was found, we're actually in the air!
        if not ground_found:
            self.in_air = True
            print(f"{self.name} detected no ground beneath them while grounded! y={self.pos.y}")
            
            # Track this as a potentially high-impact event
            if hasattr(self.game, 'record_event'):
                if self.vel.y >= 0 and abs(self.vel.x) > 5:
                    # Character is moving fast horizontally and falling - this could be a ledge dash
                    self.game.record_event("LEDGE_DASH", f"{self.name} dashed off a ledge at high speed!")
                else:
                    # Just a regular falling off ledge
                    self.game.record_event("LEDGE_FALL", f"{self.name} fell off a platform!")

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
        
        if self.damage_percent >= 999:
            self.image = self.dead_image
            return

        # First check shield state
        if self.shield_active:
            # Use standing sprite when shielding
            if self.direc == LEFT:
                self.image = self.standL
            else:
                self.image = self.standR
        elif self.move == WALK:
            # Handle normal animation states
            walk_frame = min(self.walk_c, len(self.walkL) - 1)  # Prevents index errors
            if self.direc == LEFT:
                self.image = self.walkL[walk_frame]
            else:
                self.image = self.walkR[walk_frame]
        elif self.move == STAND:
            if self.direc == LEFT:
                self.image = self.standL
            else:
                self.image = self.standR
        elif self.move == WEAK_ATTACK:
            if self.direc == LEFT:
                self.image = self.weakL
            else:
                self.image = self.weakR
        elif self.move == HEAVY_ATTACK:
            if self.direc == LEFT:
                self.image = self.heavyL
            else:
                self.image = self.heavyR
        elif self.move == DAMAGED:
            if self.direc == LEFT:
                self.image = self.damagedL
            else:
                self.image = self.damagedR
        elif self.move == LANDING:
            # Use standing sprite for landing
            if self.direc == LEFT:
                self.image = self.standL
            else:
                self.image = self.standR
                
    def draw(self, surface):
        """Draw the character and shield"""
        # Draw the character
        surface.blit(self.image, self.rect)
        
        # Draw shield if active
        if self.shield_active and not self.shield_broken:
            # Position shield at center of character
            shield_pos = self.rect.center
            
            # Create shield surface
            if getattr(sys.modules['settings'], 'GIANT_MODE_ENABLED', False):
                # Adjust shield size and position for giant mode
                giant_scale = getattr(sys.modules['settings'], 'GIANT_MODE_SCALE_FACTOR', 1.75)
                shield_size = int(SHIELD_SIZE * giant_scale)
                shield_surface = pg.Surface((shield_size, shield_size), pg.SRCALPHA)
                shield_radius = shield_size // 2
            else:
                # Regular shield
                shield_surface = pg.Surface((SHIELD_SIZE, SHIELD_SIZE), pg.SRCALPHA)
                shield_radius = SHIELD_SIZE // 2
            
            # Draw shield circle
            pg.draw.circle(
                shield_surface, 
                (*self.shield_color, SHIELD_ALPHA), 
                (shield_radius, shield_radius), 
                shield_radius
            )
            
            # Position shield centered on character
            shield_rect = shield_surface.get_rect(center=shield_pos)
            surface.blit(shield_surface, shield_rect)
            
            # Debug output for shield positioning
            if self.game.shield_debug:
                # Draw edge rectangle around shield
                pg.draw.rect(surface, (255, 0, 0), shield_rect, 1)
                # Print shield info if this is player 1
                if self.name == self.game.player_names[0]:
                    shield_info = f"Shield: {shield_pos}, size: {SHIELD_SIZE}"
                    font = pg.font.SysFont('Arial', 12)
                    text = font.render(shield_info, True, (255, 255, 255))
                    surface.blit(text, (10, 10))
        
        # Draw debug info if needed (bounding box)
        if self.game.controller_debug:
            # Draw the rectangle outline for collision debugging
            pg.draw.rect(surface, (255, 0, 0), self.rect, 2)
            
            # Draw position dot
            pg.draw.circle(surface, (0, 255, 0), (int(self.pos.x), int(self.pos.y)), 3)
            
            # Draw damage percentage
            font = pg.font.SysFont('Arial', 14)
            damage_text = font.render(f"{self.damage_percent:.1f}%", True, (255, 0, 0))
            surface.blit(damage_text, (self.rect.x, self.rect.y - 20))
            
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

    def activate_shield(self):
        """Activate shield if it's not broken"""
        if not self.shield_broken and self.shield_cooldown <= 0:
            if not self.shield_active:
                # Print debug message when shield activates
                print(f"{self.name}'s shield activated")
                
                # Play shield on sound
                sound_manager.play_shield_sound('on')
                
            self.shield_active = True
            self.move = SHIELD
            
            # Make sure shield surface is created
            if self.shield_surface is None:
                print(f"DEBUG: Creating shield surface for {self.name} in activate_shield")
                self.create_shield_surface()
            
            # Return True if successful
            return True
        else:
            # Return False if shield can't be activated
            if self.shield_broken:
                print(f"DEBUG: Can't activate shield for {self.name} - shield is broken")
            elif self.shield_cooldown > 0:
                print(f"DEBUG: Can't activate shield for {self.name} - shield on cooldown ({self.shield_cooldown})")
            return False

    def deactivate_shield(self):
        """Deactivate shield"""
        if self.shield_active:
            # Print debug message when shield deactivates
            print(f"{self.name}'s shield deactivated")
            
            # Play shield off sound
            sound_manager.play_shield_sound('off')
            
        self.shield_active = False
        if self.move == SHIELD:
            self.move = STAND

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
            
            # Get character type for sound effects
            character_type = self.__class__.__name__.replace('Local', '')
            
            # Play damage sound with character voice
            sound_manager.play_damage_sound(damage, character_type)
            
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
            
            # Record extreme knockback events in game
            if hasattr(self.game, 'record_event'):
                if knockback > 150:
                    # This is an extremely powerful hit
                    self.game.record_event("MASSIVE_KNOCKBACK", f"{self.name} was hit with massive knockback power ({knockback:.1f})!")
                elif knockback > 100:
                    # This is a very powerful hit
                    self.game.record_event("POWERFUL_KNOCKBACK", f"{self.name} was hit with powerful knockback ({knockback:.1f})!")
                    
                # Record tumble state if it happens
                if self.tumble_state:
                    self.game.record_event("TUMBLE", f"{self.name} was knocked into a tumbling state!")
            
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
            
            # If shield is active, don't take damage
            if self.shield_active and not self.shield_broken:
                return self.damage_percent
            
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

    def apply_landing_lag_with_melee_physics(self, was_aerial_attack=False):
        """Apply landing lag with Melee physics rules"""
        try:
            # Make sure melee settings are available
            if 'LANDING_LAG' not in globals():
                print("Warning: LANDING_LAG settings not found, using defaults")
                normal_landing_lag = 4
                aerial_landing_lag = 12 if was_aerial_attack else 4
                l_cancel_factor = 0.5
            else:
                normal_landing_lag = LANDING_LAG['normal_landing_lag_frames']
                aerial_landing_lag = was_aerial_attack and 12 or normal_landing_lag
                l_cancel_factor = LANDING_LAG['l_cancel_factor']
                
            # Determine base landing lag
            landing_lag_frames = normal_landing_lag
            
            # Check for L-cancel success
            if was_aerial_attack:
                landing_lag_frames = aerial_landing_lag
                
                if self.l_cancel_successful:
                    # L-cancel reduces landing lag
                    landing_lag_frames = int(landing_lag_frames * l_cancel_factor)
                    print(f"{self.name} successfully L-canceled! Landing lag reduced to {landing_lag_frames} frames")
                    
                    # Record L-cancel event
                    if hasattr(self.game, 'record_event'):
                        self.game.record_event("L_CANCEL", f"{self.name} executed a perfect L-cancel!")
            
            # Apply landing lag
            self.move = LANDING
            self.animation_locked = True
            self.animation_lock_timer = 0
            self.animation_lock_duration = landing_lag_frames
            
            # Reset L-cancel flags
            self.l_cancel_window = 0
            self.l_cancel_successful = False
            
            return landing_lag_frames
        except Exception as e:
            print(f"Error in apply_landing_lag_with_melee_physics: {e}")
            import traceback
            traceback.print_exc()
            return 4  # Default fallback

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