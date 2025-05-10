import sys
import pygame as pg

# move up one directory to be able to import the settings and images
sys.path.append("..")
from settings import *
from images import *

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
class LocalCharacter(pg.sprite.Sprite):
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
        # Double the horizontal acceleration for faster movement
        self.acce = acceleration * MOVEMENT_SPEED_MULTIPLIER
        
        # Position and movement
        self.pos = vec(pos[0], pos[1])  # Convert to Vector2 for consistency
        self.direc = direc
        self.walk_c = walk_c if walk_c is not None else 0
        self.move = move
        
        # Animation state variables
        self.animation_frame_counter = 0
        self.animation_locked = False
        self.animation_lock_timer = 0
        self.animation_lock_duration = 0
        self.in_air = False
        self.landing_lag = 0
        
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
    
    def scale_image(self, image):
        """Scale an image to the desired size (2x)"""
        current_width = image.get_width()
        current_height = image.get_height()
        new_width = int(current_width * CHARACTER_SCALE)
        new_height = int(current_height * CHARACTER_SCALE)
        return pg.transform.scale(image, (new_width, new_height))

    def jump(self):
        # Only allow jump if not animation locked
        if self.animation_locked:
            # Cannot jump during landing lag or other locked animations
            return
            
        # Only allow jumping if on the ground (not in air)
        if self.in_air:
            return
            
        self.rect.x += 1
        collision = pg.sprite.spritecollide(self, self.game.platforms, False)
        self.rect.x -= 1
        if collision:
            # Use normal jump velocity × jump height factor for proper jump height
            self.vel.y = -VEL * JUMP_HEIGHT_FACTOR
            self.in_air = True

    def take_damage(self, damage, attacker_pos_x):
        """
        Apply damage (increases percentage) and calculate knockback based on percentage
        Returns the new damage percentage
        """
        # Increase damage percentage
        self.damage_percent += damage
        
        # Calculate knockback based on damage percentage
        # Higher percentage = more knockback
        knockback_multiplier = 1.0 + (self.damage_percent / 100.0)
        
        # Determine horizontal knockback direction
        knockback_direction = 1 if attacker_pos_x < self.pos.x else -1
        
        # Apply knockback
        knockback_x = BASE_KNOCKBACK_X * knockback_multiplier * knockback_direction
        knockback_y = -BASE_KNOCKBACK_Y * knockback_multiplier  # Negative for upward
        
        # Apply to velocity
        self.vel.x = knockback_x
        self.vel.y = knockback_y
        
        # Enter damage state
        self.move = DAMAGED
        
        # Apply animation lock based on percentage (higher = longer stun)
        stun_duration = int(self.damage_stun * knockback_multiplier)
        self.animation_locked = True
        self.animation_lock_timer = 0
        self.animation_lock_duration = stun_duration
        
        # Set in_air since knockback will launch the player
        self.in_air = True
        
        print(f"{self.name} took {damage}%, now at {self.damage_percent}% with knockback {knockback_x:.2f}, {knockback_y:.2f}")
        
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
        # Handle animation lock timers
        if self.animation_locked:
            self.animation_lock_timer += 1
            if self.animation_lock_timer >= self.animation_lock_duration:
                self.animation_locked = False
                # After lock expires, return to standing if not moving
                if self.move in [WEAK_ATTACK, HEAVY_ATTACK, DAMAGED, LANDING]:
                    self.move = STAND
        
        # Update physics
        self.acc = vec(0, 0.5)  # Gravity
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        # Update collision rectangle for collision detection
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.pos

        # Detect landing from air
        was_in_air = self.in_air
        if self.vel.y > 0:  # Falling
            # Check for platforms
            collision = pg.sprite.spritecollide(self, self.game.platforms, False)
            
            # Clear drop-through for platforms that are no longer in collision
            if self.dropping_through_platforms:
                platforms_to_remove = set()
                for platform in self.dropping_through_platforms:
                    if platform not in collision:
                        platforms_to_remove.add(platform)
                
                self.dropping_through_platforms -= platforms_to_remove
                
                # If no platforms are being dropped through anymore, reset the state
                if not self.dropping_through_platforms:
                    self.is_dropping_through = False
            
            # Filter platforms:
            # 1. Always collide with floors
            # 2. For regular platforms, handle drop-through logic
            filtered_collision = []
            for platform in collision:
                # Check if we can drop through this platform
                if self.can_drop_through(platform):
                    # Add the platform to the set being dropped through
                    self.dropping_through_platforms.add(platform)
                    # Set the drop-through state to active
                    self.is_dropping_through = True
                    # Skip collision with this platform
                    print(f"Player {self.name} dropping through platform while falling")
                else:
                    # Can't drop through, handle normal collision
                    filtered_collision.append(platform)
            
            if filtered_collision:
                # Landing on a platform or floor
                if was_in_air:
                    self.apply_landing_lag()
                
                self.pos[1] = filtered_collision[0].rect.top + 1
                self.vel[1] = 0
                self.in_air = False
                
                # Reset drop-through state when landing
                self.is_dropping_through = False
                self.dropping_through_platforms.clear()
            else:
                # No valid platforms to land on, remain in the air
                self.in_air = True
        else:
            # In the air if velocity is upward
            self.in_air = True
            
            # Also check if we need to clear drop-through state
            # This handles the case where the player jumps through a platform
            collision = pg.sprite.spritecollide(self, self.game.platforms, False)
            if not collision:
                # No collision with any platform, clear the drop-through state
                self.is_dropping_through = False
                self.dropping_through_platforms.clear()
        
        # Update sprite image based on current state
        self.update_sprite_image()
        
        # Final update to collision rectangle
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.pos
        
    def apply_landing_lag(self):
        """Apply landing lag based on vertical velocity and other factors"""
        # Calculate landing lag based on fall speed (higher fall = more lag)
        fall_intensity = abs(self.vel.y) / 15.0  # Normalize
        
        # Landing lag of 10 frames as requested
        base_lag_frames = 10
        
        # No additional velocity-based lag 
        velocity_lag = 0
        
        # Set landing lag and animation lock
        self.landing_lag = int(base_lag_frames + velocity_lag)
        self.animation_locked = True
        self.animation_lock_timer = 0
        self.animation_lock_duration = self.landing_lag
        
        # Visual feedback - special landing animation
        self.move = LANDING
        
        # Debug output
        print(f"Landing lag: {self.landing_lag} frames (vel.y: {self.vel.y:.2f})")

    def update_sprite_image(self):
        """Update the sprite's image based on current movement state"""
        # Animation frame counter for controlling animation speed
        self.animation_frame_counter += 1
        
        # Slow down walk animations by 4x (update every 20 frames instead of 5)
        # For other animations, keep the normal speed (every 5 frames)
        should_update_walk = self.animation_frame_counter % 20 == 0
        should_update_other = self.animation_frame_counter % 5 == 0
        
        if self.move == WALK:
            if self.direc == LEFT:
                # Only update walk_c when should_update_walk is True (4x slower)
                if should_update_walk:
                    max_walk = len(self.walkL) - 1
                    self.walk_c = (self.walk_c + 1) % max(1, max_walk)
                self.image = self.walkL[min(self.walk_c, len(self.walkL)-1)]
            elif self.direc == RIGHT:
                # Only update walk_c when should_update_walk is True (4x slower)
                if should_update_walk:
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
        return not self.animation_locked and self.damage_percent < 999

    def is_defeated(self):
        """Check if character is defeated (999% damage)"""
        return self.damage_percent >= 999

    def can_drop_through(self, platform):
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
        
        # If drop-through initiated (down key pressed), allow it
        if self.drop_through:
            return True
        
        # If in a drop-through state, allow it to continue
        if self.is_dropping_through:
            return True
        
        # Otherwise, cannot drop through
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
            5.7, 11, 0.22  # weak damage, heavy damage, acceleration
        )

# Link - has liM1 through liM10
class LocalLink(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        # Remove standing sprite from walk animation
        walkR = [liM1, liM2, liM3, liM4, liM5, liM6, liM7, liM8, liM9, liM10]
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
            6, 12, 0.2  # weak damage, heavy damage, acceleration
        ) 