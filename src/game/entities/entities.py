# ================================================================
#  entities.py  (engine‑agnostic reference classes)
# ================================================================
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Sequence
import pygame
import random
import os

# ----------------------------------------------------------------
#  ENUMS (expressed as str literals to avoid importing Enum class)
# ----------------------------------------------------------------
EVENTS        = {"OnStart","EveryFrame","OnTimer","OnCollision",
                 "OnVoiceCommand","OnHealthBelow","OnDestroyed"}
ENTITY_TYPES  = {"character","projectile","hazard","powerup","effect"}
COMPONENTS    = {"Transform","Sprite","Collider","RigidBody","Health",
                 "Damage","AI_Brain","Lifespan","ParticleEmitter",
                 "AudioCue","CustomVar"}

# ----------------------------------------------------------------
#  ACTION BASE ‑‑ each subclass must implement do(engine_ctx, self_ent, target)
# ----------------------------------------------------------------
class Action:
    def do(self, eng, self_ent:'Entity', target:Any|None): ...

# Pure‑data subclasses ---------------------------------------------------------
@dataclass
class SpawnAction(Action):
    prefab:str; x:Any; y:Any; properties:Dict[str,Any]|None=None
@dataclass
class ApplyForceAction(Action):
    vector:Dict[str,Any]           # {"x":expr,"y":expr}
@dataclass
class ModifyStatAction(Action):
    field:str; value:Any; target:str|None="self"
@dataclass
class PlayAnimationAction(Action):
    name:str
@dataclass
class PlaySoundAction(Action):
    cue:str
@dataclass
class DestroyAction(Action):
    pass
@dataclass
class SetTimerAction(Action):
    id:str; duration:float; repeat:int=0
@dataclass
class CommentaryAction(Action):
    text:str

ACTION_MAP:Dict[str,type[Action]] = {
    "Spawn":SpawnAction,
    "ApplyForce":ApplyForceAction,
    "ModifyStat":ModifyStatAction,
    "PlayAnimation":PlayAnimationAction,
    "PlaySound":PlaySoundAction,
    "Destroy":DestroyAction,
    "SetTimer":SetTimerAction,
    "Commentary":CommentaryAction,
}

# ----------------------------------------------------------------
#  BEHAVIOR
# ----------------------------------------------------------------
@dataclass
class Behavior:
    event:str                       # must be in EVENTS
    actions:Sequence[Action]

# ----------------------------------------------------------------
#  ENTITY (engine‑agnostic)
# ----------------------------------------------------------------
@dataclass
class Entity:
    id:str
    prefab:str                      # must be in ENTITY_TYPES
    components:Dict[str,Any] = field(default_factory=dict)
    behaviors:List[Behavior] = field(default_factory=list)
    engine_obj:Any=None             # opaque handle set by adapter

    # Adapter hook -------------------------------------------------
    def build(self, engine_ctx, prefab_factory:Callable[...,Any]):
        """Instantiate engine object via prefab_factory then let the
           adapter apply components and wire events."""
        self.engine_obj = prefab_factory(self.prefab, self.components)

# ----------------------------------------------------------------
#  TIMER
# ----------------------------------------------------------------
@dataclass
class Timer:
    id:str
    duration:float
    repeat:int
    on_complete:Sequence[Action]

# ----------------------------------------------------------------
#  PACKET  (the top‑level MOD packet)
# ----------------------------------------------------------------
@dataclass
class ModPacket:
    entities:List[Entity]
    timers:List[Timer]

    @classmethod
    def from_dict(cls, d:Dict[str,Any]) -> 'ModPacket':
        ents=[]
        for e in d.get("entities",[]):
            beh=[]
            for b in e.get("behaviors",[]):
                acts=[ACTION_MAP[a["type"]](**{k:v for k,v in a.items() if k!="type"})
                      for a in b["actions"]]
                beh.append(Behavior(event=b["event"], actions=acts))
            ents.append(Entity(id=e["id"], prefab=e["prefab"],
                               components=e.get("components",{}),
                               behaviors=beh))
        timers=[]
        for t in d.get("timers",[]):
            acts=[ACTION_MAP[a["type"]](**{k:v for k,v in a.items() if k!="type"})
                  for a in t["on_complete"]]
            timers.append(Timer(id=t["id"], duration=t["duration"],
                                repeat=t.get("repeat",0), on_complete=acts))
        return cls(entities=ents, timers=timers)
    
# ----------------------------------------------------------------
# Adapter methods for connecting the above to the rest of the codebase
# ----------------------------------------------------------------

# Class to manage entity registry and DSL execution context
class EntitySystem:
    def __init__(self, game):
        self.game = game
        self.entities = {}  # id -> Entity
        self.entity_map = {}  # engine_obj -> Entity
        self.timers = {}  # id -> Timer
    
    def register_entity(self, entity):
        """Register an entity in the system for tracking."""
        self.entities[entity.id] = entity
        if entity.engine_obj:
            self.entity_map[entity.engine_obj] = entity

    def sprite_to_entity(self, sprite):
        """Convert sprite to entity reference."""
        return self.entity_map.get(sprite)
    
    def process_event(self, event_type, target=None, ctx=None):
        """Process an event for all registered entities."""
        if ctx is None:
            ctx = {}
        
        for entity in self.entities.values():
            for behavior in entity.behaviors:
                if behavior.event == event_type:
                    for action in behavior.actions:
                        self.execute_action(action, entity, target, ctx)
    
    def execute_action(self, action, self_entity, target=None, ctx=None):
        """Execute a single action."""
        return action_runner(action, self, self_entity, target)

    def evaluate(self, expr, self_entity, target):
        """Evaluate an expression in the context of entities."""
        if isinstance(expr, (int, float)):
            return expr
        if isinstance(expr, str) and expr.isdigit():
            return float(expr)
        if expr == "self.x" and self_entity and self_entity.engine_obj:
            return self_entity.engine_obj.pos.x
        if expr == "self.y" and self_entity and self_entity.engine_obj:
            return self_entity.engine_obj.pos.y
        if expr == "target.x" and target:
            return target.pos.x
        if expr == "target.y" and target:
            return target.pos.y
        return 0
    
    def spawn_entity(self, prefab, x, y, properties=None):
        """Spawn a new entity at the given position."""
        from uuid import uuid4
        
        if properties is None:
            properties = {}
        
        # Create a new entity with a unique ID
        entity_id = f"{prefab}_{uuid4().hex[:8]}"
        
        # Set up position in components
        components = {"xPos": x, "yPos": y}
        components.update(properties)
        
        # Create entity
        entity = Entity(id=entity_id, prefab=prefab, components=components)
        
        # Build the entity using our factory
        entity.build(self, prefab_factory)
        
        # Register the entity
        self.register_entity(entity)
        
        return entity.engine_obj
    
    def load_from_json(self, json_file):
        """Load entities and timers from a JSON file."""
        import json
        import os
        
        try:
            # Make sure the path is correct relative to the game directory
            if not os.path.isabs(json_file):
                # Try a couple of common relative paths
                if os.path.exists(json_file):
                    pass  # Use as is
                elif os.path.exists(f"src/game/{json_file}"):
                    json_file = f"src/game/{json_file}"
                elif os.path.exists(f"src/game/entities/{json_file}"):
                    json_file = f"src/game/entities/{json_file}"
            
            print(f"Loading entity definitions from {json_file}")
            with open(json_file, "r") as f:
                data = json.load(f)
            
            # Use the ModPacket.from_dict to parse the data
            packet = ModPacket.from_dict(data)
            
            # Process entities
            for entity in packet.entities:
                # Register the entity
                self.register_entity(entity)
                
                # Build it if needed
                if not entity.engine_obj:
                    # Get position from components
                    x = float(entity.components.get("xPos", 0))
                    y = float(entity.components.get("yPos", 0))
                    entity.build(self, prefab_factory)
            
            # Process timers
            for timer in packet.timers:
                self.timers[timer.id] = {
                    "duration": timer.duration,
                    "repeat": timer.repeat,
                    "actions": timer.on_complete,
                    "remaining": timer.duration,
                    "repeats_left": timer.repeat
                }
            
            return len(packet.entities), len(packet.timers)
            
        except Exception as e:
            print(f"Error loading entity definitions: {e}")
            import traceback
            traceback.print_exc()
            return 0, 0
    
    def update_timers(self, dt=1/60):
        """Update all timers, triggering any that have elapsed."""
        timers_to_remove = []
        
        for timer_id, timer in self.timers.items():
            # Decrement timer
            timer["remaining"] -= dt
            
            # Check if timer has elapsed
            if timer["remaining"] <= 0:
                # Execute actions
                for action in timer["actions"]:
                    self.execute_action(action, None)
                
                # Handle repeats
                if timer["repeats_left"] > 0:
                    timer["repeats_left"] -= 1
                    timer["remaining"] = timer["duration"]
                elif timer["repeats_left"] == 0:
                    # Remove this timer
                    timers_to_remove.append(timer_id)
        
        # Remove expired timers
        for timer_id in timers_to_remove:
            del self.timers[timer_id]

# Create a bob-omb sprite class
class BobOmbSprite(pygame.sprite.Sprite):
    def __init__(self, game, x, y, properties=None):
        super().__init__()
        
        self.game = game
        self.name = "Bob-omb"
        self.type = "hazard"
        
        # Load the bob-omb image instead of drawing it
        try:
            # Use the utility function to find the image
            image_path = find_resource("SSF2_Bob-omb.png", "items")
            
            if image_path:
                self.original_image = pygame.image.load(image_path).convert_alpha()
                print(f"Successfully loaded Bob-omb image from {image_path}")
                
                # Scale the image to an appropriate size
                self.size = 32
                self.original_image = pygame.transform.scale(self.original_image, (self.size, self.size))
                self.image = self.original_image.copy()
            else:
                raise pygame.error("Could not find Bob-omb image in any common location")
                
        except pygame.error as e:
            # Fallback if image can't be loaded
            print(f"Warning: Could not load Bob-omb image: {e}")
            print("Using fallback drawn sprite instead")
            self.size = 28
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            
            # Define colors as instance variables
            self.BLACK = (0, 0, 0)
            self.WHITE = (255, 255, 255)
            self.DARK_GRAY = (50, 50, 50)
            self.GRAY = (100, 100, 100)
            self.METAL = (180, 180, 180)
            self.RED = (255, 60, 60)
            self.YELLOW = (255, 255, 0)
            
            # Create visual components
            # Main body (slightly oval)
            pygame.draw.ellipse(self.image, self.BLACK, (2, 4, 24, 22))
            
            # Metal parts (wind-up key)
            pygame.draw.rect(self.image, self.METAL, (10, 22, 8, 4))  # Base
            
            # Eyes
            eye_size = 3
            pygame.draw.circle(self.image, self.WHITE, (8, 12), eye_size)
            pygame.draw.circle(self.image, self.WHITE, (20, 12), eye_size)
            pygame.draw.circle(self.image, self.BLACK, (8, 12), 1)  # Pupils
            pygame.draw.circle(self.image, self.BLACK, (20, 12), 1)
            
            # Fuse
            pygame.draw.rect(self.image, self.GRAY, (13, 1, 2, 6))
            
            # Draw initial fuse glow
            pygame.draw.circle(self.image, self.RED, (14, 2), 3)
            
            # Feet
            pygame.draw.ellipse(self.image, self.DARK_GRAY, (6, 23, 6, 4))
            pygame.draw.ellipse(self.image, self.DARK_GRAY, (16, 23, 6, 4))
            
            self.original_image = self.image.copy()
        
        self.rect = self.image.get_rect()
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0.5)  # Gravity
        
        # Store original image for flipping when walking
        self.facing_right = True
        
        # Timer until explosion
        self.fuse_time = properties.get("fuse_time", 180)  # 3 seconds at 60fps
        self.explosion_radius = properties.get("explosion_radius", 100)
        self.damage = properties.get("damage", 25)
        
        # Fuse animation variables
        self.frame_counter = 0
        self.fuse_flash = False
        
        # Walking animation
        self.walking = False
        self.walk_dir = 1  # 1 = right, -1 = left
        self.walk_timer = 0
        self.walk_speed = 1
        self.walk_counter = 0
        
    def update(self):
        # Apply physics
        self.vel += self.acc
        self.pos += self.vel
        self.rect.midbottom = self.pos
        
        # Handle platform collisions
        self.handle_platform_collisions()
        
        # Count down fuse
        self.fuse_time -= 1
        
        # Update fuse animation
        self.frame_counter += 1
        if self.frame_counter >= 10 - max(0, int(8 * (1 - self.fuse_time / 180))):
            self.frame_counter = 0
            self.fuse_flash = not self.fuse_flash
        
        # Update walking behavior
        if not self.walking and random.random() < 0.01:  # 1% chance to start walking
            self.walking = True
            self.walk_dir = random.choice([-1, 1])  # Random direction
            self.walk_timer = random.randint(30, 90)  # Walk for 0.5-1.5 seconds
            
            # Flip image based on direction
            if (self.walk_dir > 0 and not self.facing_right) or (self.walk_dir < 0 and self.facing_right):
                self.facing_right = self.walk_dir > 0
                self.image = pygame.transform.flip(self.original_image, not self.facing_right, False)
        
        if self.walking:
            # Move in walking direction
            self.pos.x += self.walk_dir * self.walk_speed
            
            # Walking animation handled by slight movement
            self.walk_counter += 1
            if self.walk_counter % 10 == 0:
                # Add a slight bobbing effect
                if (self.walk_counter // 10) % 2 == 0:
                    self.pos.y -= 1
                else:
                    self.pos.y += 1
            
            # Decrement walk timer
            self.walk_timer -= 1
            if self.walk_timer <= 0:
                self.walking = False
        
        # Flash red when about to explode
        if self.fuse_time < 60:  # Last second
            # Create a copy of the original image
            self.image = self.original_image.copy()
            if self.walk_dir < 0 and self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
                
            if self.frame_counter % 5 == 0:  # Flash every few frames
                # Create a red overlay
                overlay = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
                flash_intensity = 100 + int(155 * (1 - self.fuse_time / 60))  # Increasing intensity
                overlay.fill((255, 0, 0, flash_intensity))
                self.image.blit(overlay, (0, 0))
                
        # Check for explosion
        if self.fuse_time <= 0:
            self.explode()
            
    def apply_force(self, force_x, force_y):
        """Apply a force to the bob-omb"""
        self.vel.x += force_x
        self.vel.y += force_y
        
        # Limit velocity for stability
        max_vel = 20
        if abs(self.vel.x) > max_vel:
            self.vel.x = max_vel if self.vel.x > 0 else -max_vel
        if abs(self.vel.y) > max_vel:
            self.vel.y = max_vel if self.vel.y > 0 else -max_vel
        
        # If force applied, reduce fuse time (make it more sensitive)
        if abs(force_x) > 5 or abs(force_y) > 5:
            print("Force applied to bob-omb, reducing fuse time!")
            self.fuse_time = max(self.fuse_time - 30, 10)  # Reduce by half second but keep minimum
    
    def handle_platform_collisions(self):
        # Check collisions with platforms
        for platform in self.game.platforms:
            if self.rect.colliderect(platform.rect):
                # If falling onto platform
                if self.vel.y > 0 and self.rect.bottom >= platform.rect.top and self.rect.bottom <= platform.rect.top + 15:
                    self.pos.y = platform.rect.top
                    self.vel.y = -self.vel.y * 0.5  # Bounce with damping
                    if abs(self.vel.y) < 1:
                        self.vel.y = 0
                
                # Side collisions
                elif self.rect.right >= platform.rect.left and self.rect.left <= platform.rect.right:
                    if self.vel.x > 0:
                        self.pos.x = platform.rect.left - self.rect.width / 2
                        self.vel.x *= -0.7  # Bounce off walls with damping
                    elif self.vel.x < 0:
                        self.pos.x = platform.rect.right + self.rect.width / 2
                        self.vel.x *= -0.7  # Bounce off walls with damping
    
    def explode(self):
        """Create an explosion and apply damage to nearby players"""
        # Create explosion particle effect
        try:
            # Try to create a more visually impressive explosion
            explosion_size = self.explosion_radius * 1.5
            explosion = pygame.Surface((int(explosion_size), int(explosion_size)), pygame.SRCALPHA)
            
            # Draw explosion rings
            center = (int(explosion_size/2), int(explosion_size/2))
            colors = [
                (255, 255, 200, 255),  # White-yellow core
                (255, 165, 0, 200),    # Orange mid
                (255, 0, 0, 150),      # Red outer
                (100, 0, 0, 100)       # Dark red edge
            ]
            
            # Draw concentric circles for explosion
            for i, color in enumerate(colors):
                radius = int(explosion_size/2 * (1 - i/len(colors)/2))
                pygame.draw.circle(explosion, color, center, radius)
            
            # Add explosion to the game at the bob-omb's position
            explosion_rect = explosion.get_rect()
            explosion_rect.center = self.rect.center
            self.game.screen.blit(explosion, explosion_rect)
            pygame.display.update(explosion_rect)  # Immediate visual feedback
            
            # Add message
            print(f"Bob-omb exploded at {self.pos}")
            
        except Exception as e:
            print(f"Error creating explosion effect: {e}")
        
        # Check for players in blast radius
        for name, player_data in self.game.players.items():
            if 'sprite' in player_data:
                player_sprite = player_data['sprite']
                # Calculate distance
                player_pos = pygame.math.Vector2(player_sprite.rect.center)
                bomb_pos = pygame.math.Vector2(self.rect.center)
                distance = player_pos.distance_to(bomb_pos)
                
                # If in blast radius, damage player
                if distance < self.explosion_radius:
                    # Scale damage based on distance
                    distance_factor = 1 - (distance / self.explosion_radius)
                    scaled_damage = self.damage * distance_factor
                    
                    # Apply knockback direction based on relative position
                    direction = 1 if player_pos.x > bomb_pos.x else -1
                    
                    # Attack the player
                    self.game.attackPlayer(name, scaled_damage, "hit", self.pos.x)
                    
                    # Apply additional explosion force
                    if hasattr(player_sprite, 'apply_force'):
                        # Calculate directional force
                        force_x = direction * 15 * distance_factor
                        force_y = -10 * distance_factor
                        player_sprite.apply_force(force_x, force_y)
        
        # Remove the bob-omb
        self.kill()

# Global entity system instance (will be initialized when game is created)
DSL = None

# 1. convert prefab → actual Sprite / Fighter / Projectile
def prefab_factory(prefab_name, components):
    # Ensure we have a reference to the game
    game = DSL.game if DSL else None
    if not game:
        print("Warning: Cannot create prefab without game reference")
        return None
    
    # Extract position info
    x = float(components.get("xPos", 0))
    y = float(components.get("yPos", 0))
    
    # Create appropriate sprite based on prefab type
    if prefab_name == "bobomb":
        sprite = BobOmbSprite(game, x, y, components)
        game.all_sprites.add(sprite)
        return sprite
    
    # Placeholder for other entity types
    print(f"Prefab '{prefab_name}' not implemented")
    return None

# 2. execute actions
def action_runner(action, engine_ctx, self_ent, target):
    if isinstance(action, SpawnAction):
        return engine_ctx.spawn_entity(
            action.prefab,
            engine_ctx.evaluate(action.x, self_ent, target),
            engine_ctx.evaluate(action.y, self_ent, target),
            action.properties or {}
        )
    elif isinstance(action, ApplyForceAction):
        vec = action.vector
        if self_ent and self_ent.engine_obj and hasattr(self_ent.engine_obj, "apply_force"):
            self_ent.engine_obj.apply_force(
                engine_ctx.evaluate(vec["x"], self_ent, target),
                engine_ctx.evaluate(vec["y"], self_ent, target)
            )
    elif isinstance(action, PlaySoundAction):
        # Simply log for now
        print(f"Playing sound: {action.cue}")
    elif isinstance(action, DestroyAction):
        if self_ent and self_ent.engine_obj:
            self_ent.engine_obj.kill()
    
    # Add other action types as needed
    return None

# 3. wire events to entity system
def on_collision(self_sprite, other_sprite):
    if DSL:
        target_entity = DSL.sprite_to_entity(other_sprite)
        self_entity = DSL.sprite_to_entity(self_sprite)
        if self_entity:
            DSL.process_event("OnCollision", target_entity, {"target": target_entity})

# Initialize pygame for the BobOmbSprite class
# import pygame  # Moved to the top of the file

# Utility function to find game resources
def find_resource(filename, subdirectory=None):
    """
    Find a game resource by trying multiple common paths.
    
    Args:
        filename: The name of the file to find
        subdirectory: Optional subdirectory within the resources directory
        
    Returns:
        The path to the resource if found, or None if not found
    """
    # Possible base directories relative to different working directories
    base_dirs = [
        "./",                      # Running from src/
        "../",                     # Running from src/game/
        "../../",                  # Running from src/game/entities/
        "src/",                    # Running from project root
        "game/",                   # Alternative
        "src/game/"                # Another alternative
    ]
    
    # If subdirectory is provided, add it to the resource path
    resource_path = os.path.join("images", subdirectory, filename) if subdirectory else os.path.join("images", filename)
    
    # Try each base directory
    for base_dir in base_dirs:
        full_path = os.path.join(base_dir, resource_path)
        if os.path.exists(full_path):
            return full_path
    
    # If we get here, the resource wasn't found
    return None

