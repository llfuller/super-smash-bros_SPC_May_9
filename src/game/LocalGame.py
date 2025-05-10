'''

This is a local version of the Super Smash Bros game that supports two players
on a single computer without requiring network connectivity.

The game maintains the same gameplay mechanics and features as the original
but eliminates the need for a separate server.

'''

import sys
import pygame as pg
import json
import copy
import random

# Fix import paths to use direct imports since we're in the game directory
from characters.LocalCharacter import (
    LocalMario, LocalLuigi, LocalYoshi, 
    LocalPopo, LocalNana, LocalLink
)

# menus
from menus.Intro import Intro
from menus.Other import Other
from menus.Start import Start

# others
from objects.Platform import Platform
from settings import *
from images import *
from platform_layouts import get_layout  # Import the platform layouts

# Add missing color
YELLOW = (255, 255, 0)

# Vector utility
vec = pg.math.Vector2

print()
print('========== SUPER SMASH BROS - Local Two-Player Edition ==========')
print('Happy playing! This is the current version and limitations:')
print('- Once you create a game and enter, you must reset for a new one.')
print('- No option to recreate a game or to return to the main menu.')
print('- Game is just an endless loop that detects winner of each round.')
print()
print('Player 1 Controls:                Player 2 Controls:')
print('- Arrow keys: Move                - WASD keys: Move')
print('- Z: Weak attack                  - G: Weak attack')
print('- X: Heavy attack                 - H: Heavy attack')
print()
print('UPDATES (errors will show up here if ever):')

# Controller class to abstract keyboard input
class KeyboardController:
    def __init__(self, up_key, left_key, right_key, down_key, weak_key, heavy_key, player_name):
        self.up_key = up_key
        self.left_key = left_key
        self.right_key = right_key
        self.down_key = down_key  # Add down key for platform drop-through and fast fall
        self.weak_key = weak_key
        self.heavy_key = heavy_key
        self.player_name = player_name
    
    def check_attack_key(self, event, game):
        """Check if attack keys were pressed and perform the corresponding action"""
        if event.type == pg.KEYDOWN:
            # Weak attack
            if event.key == self.weak_key:
                if self.player_name in game.players and 'sprite' in game.players[self.player_name]:
                    game.players[self.player_name]['sprite'].weakAttack()
                    return True
            
            # Heavy attack
            elif event.key == self.heavy_key:
                if self.player_name in game.players and 'sprite' in game.players[self.player_name]:
                    game.players[self.player_name]['sprite'].heavyAttack()
                    return True
        
        return False
    
    def handle_movement(self, keys, game):
        """Handle movement controls for the player"""
        if self.player_name not in game.players or 'sprite' not in game.players[self.player_name]:
            return
            
        player_data = game.players[self.player_name]
        sprite = player_data['sprite']
        
        # Don't process movement if player is dead or game is not in play
        if sprite.damage_percent >= 999 or not game.playing:
            return
            
        # EMERGENCY FIX: Reset any problematic state
        # Ensure sprite has correct attributes
        if not hasattr(sprite, 'vel'):
            sprite.vel = vec(0, 0)
        if not hasattr(sprite, 'acc'):
            sprite.acc = vec(0, 0)
        
        # Reset movement flags (these will be updated based on input)
        sprite.moving_left = False
        sprite.moving_right = False
        
        # Optional debug output
        if hasattr(game, 'current_frame') and game.current_frame % 60 == 0:
            # Print state once per second
            print(f"{self.player_name} state: in_air={sprite.in_air}, pos=({sprite.pos.x:.1f}, {sprite.pos.y:.1f}), vel=({sprite.vel.x:.1f}, {sprite.vel.y:.1f})")
        
        # Check for drop-through platform input
        if keys[self.down_key]:
            # Set flag on sprite for dropping through platforms
            sprite.drop_through = True
            
            # Check for fast fall (only in air and after apex of jump)
            if sprite.in_air and sprite.vel.y > 0:
                sprite.is_fast_falling = True
        else:
            # Clear the flag when key is released
            sprite.drop_through = False
            sprite.is_fast_falling = False
        
        # Check for jump input - use key down to allow one jump at a time
        if keys[self.up_key] and not sprite.is_jumping and not sprite.in_air and not sprite.animation_locked:
            sprite.jump()
            
            # After jumping, temporarily prevent re-jumping until key is released
            # This is handled by the sprite's in_air flag
        
        # Check if character can be controlled (not in middle of animation)
        if not hasattr(sprite, 'can_move') or not sprite.can_move():
            # Still update player data from sprite to ensure synchronized state
            player_data['xPos'] = str(sprite.pos.x)
            player_data['yPos'] = str(sprite.pos.y)
            player_data['direc'] = sprite.direc
            player_data['walk_c'] = str(sprite.walk_c)
            player_data['move'] = sprite.move
            return
        
        # Track if we're moving horizontally this frame
        is_moving_horizontally = False
        
        # HORIZONTAL MOVEMENT - with different behavior in air vs ground
        # Move left
        if keys[self.left_key] and float(player_data['xPos']) > 40:
            is_moving_horizontally = True
            
            # Set direction for animations
            sprite.direc = LEFT
            
            if sprite.in_air:
                # Air control is more limited
                sprite.vel.x = max(sprite.vel.x - 0.2, -2)  # Slower horizontal air movement
            else:
                # Ground movement is faster
                sprite.vel.x = -3  # Normal ground speed
                sprite.move = WALK
            
            # Update flags for animation and physics
            sprite.moving_left = True
            sprite.moving_right = False
            
            # Update player data
            player_data['direc'] = LEFT
            if not sprite.in_air:
                player_data['move'] = WALK
            
            # Make sure walk_c doesn't go out of bounds (only update on ground)
            if not sprite.in_air:
                walk_count = getattr(sprite, 'walk_c', 0)
                if hasattr(sprite, 'walkL'):
                    max_walk = len(sprite.walkL) - 1
                    sprite.walk_c = (walk_count + 1) % max(1, max_walk)
                else:
                    sprite.walk_c = (walk_count + 1) % 8
                    
                player_data['walk_c'] = str(sprite.walk_c)
        
        # Move right
        elif keys[self.right_key] and float(player_data['xPos']) < GAME_WIDTH-40:
            is_moving_horizontally = True
            
            # Set direction for animations
            sprite.direc = RIGHT
            
            if sprite.in_air:
                # Air control is more limited
                sprite.vel.x = min(sprite.vel.x + 0.2, 2)  # Slower horizontal air movement
            else:
                # Ground movement is faster
                sprite.vel.x = 3  # Normal ground speed
                sprite.move = WALK
            
            # Update flags for animation and physics
            sprite.moving_right = True
            sprite.moving_left = False
            
            # Update player data
            player_data['direc'] = RIGHT
            if not sprite.in_air:
                player_data['move'] = WALK
            
            # Make sure walk_c doesn't go out of bounds (only update on ground)
            if not sprite.in_air:
                walk_count = getattr(sprite, 'walk_c', 0)
                if hasattr(sprite, 'walkR'):
                    max_walk = len(sprite.walkR) - 1
                    sprite.walk_c = (walk_count + 1) % max(1, max_walk)
                else:
                    sprite.walk_c = (walk_count + 1) % 8
                    
                player_data['walk_c'] = str(sprite.walk_c)
        else:
            # No horizontal input, slow down (apply friction)
            sprite.vel.x *= 0.8  # Apply friction to gradually stop
            if abs(sprite.vel.x) < 0.1:
                sprite.vel.x = 0  # Stop completely when very slow
        
        # If not moving horizontally and not in air, reset to standing
        if not is_moving_horizontally and not sprite.in_air:
            sprite.walk_c = 0
            
            # Only transition to STAND if not in another animation
            if sprite.move == WALK:
                sprite.move = STAND
                player_data['move'] = STAND
                
            player_data['walk_c'] = '0'
        
        # Update player data from sprite position
        player_data['xPos'] = str(sprite.pos.x)
        player_data['yPos'] = str(sprite.pos.y)
        
        # Update collision rectangle - let sprite's update handle platform collision

class LocalGame:
    # ========================= IMPORTANT METHODS =========================
    def __init__(self):
        # initialize
        pg.init()
        pg.mixer.init()
        pg.display.set_caption(TITLE)
        pg.display.set_icon(ICON)

        # game variables
        self.screen = pg.display.set_mode(BG_SIZE)
        self.clock = pg.time.Clock()
        self.status = INTRO
        self.running = True  # game is running
        self.playing = False  # player is inside the arena
        self.showed_end = False  # checks if end game results have been showed
        self.initialized = False  # initialized game in arena (with players)
        self.restart_request = False  # checks if player requested for a restart
        self.current_frame = 0  # Track frames for debugging and timing
        
        # Emergency recovery counter for movement issues
        self.emergency_fix_applied = False
        
        # player variables
        self.player_names = ["", ""]  # player1, player2
        self.player_characters = ["none", "none"]  # character selections
        self.player_statuses = ["unready", "unready"]  # ready status
        self.current_player_index = 0  # which player is currently selecting (0 or 1)
        self.player_count = 0  # number of ready players
        self.name_available = True  # for compatibility with menu code
        
        # Character options for auto-selection of Player 2
        self.character_options = [MARIO, LUIGI, YOSHI, POPO, NANA, LINK]

        # converted background images for optimized game loop
        self.arena_bg = ARENA_BG.convert()
        self.chat_bg = CHAT_BG.convert()

        # chat-like message system (no actual networking)
        self.chat_text = ''
        self.chatting = False
        self.chat_once = False
        self.chat_init = False
        self.chat_messages = []

        # local server state
        self.players = {}  # equivalent to server's player dictionary
        self.init_players = {}  # for game restart
        self.winner = ""
        
        # Required for menu compatibility
        self.curr_player = ""  # updated during character selection
        
        # Auto player 2 setup
        self.auto_player2 = True  # Flag to enable/disable auto-setup of player 2
        
        # Setup controllers
        self.controllers = {}
        # Controllers will be fully initialized after player names are set

    def _setup_controllers(self):
        """Initialize controllers with player names after they are defined"""
        if self.player_names[0]:
            # Player 1: Arrow keys and Z/X for attacks
            self.controllers[self.player_names[0]] = KeyboardController(
                pg.K_UP, pg.K_LEFT, pg.K_RIGHT, pg.K_DOWN, pg.K_z, pg.K_x, self.player_names[0]
            )
        
        if self.player_names[1]:
            # Player 2: WASD and G/H for attacks
            self.controllers[self.player_names[1]] = KeyboardController(
                pg.K_w, pg.K_a, pg.K_d, pg.K_s, pg.K_g, pg.K_h, self.player_names[1]
            )

    def run(self):
        # check for the current menu depending on the status
        while True:
            if self.status == INTRO:
                Intro(self)

            elif self.status == START:
                Start(self)

            elif self.status == GUIDE:
                Other(self, GUIDE, GUIDE_BG)

            elif self.status == ABOUT:
                Other(self, ABOUT, ABOUT_BG)

            elif self.status == GAME:
                self.winner = ''

                if self.initialized and self.playing:
                    self.checkWinner()
                    
                self.clock.tick(FPS)
                self.current_frame += 1
                self.events()
                self.update()
                self.draw()
            
    def new(self):
        # the players will be added after starting the game
        self.enemy_sprites = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group()
        self.platforms = pg.sprite.Group()

        self.loadPlatforms()
        self.run()

    def loadPlatforms(self, layout_name='standard'):
        """Load platforms based on a named layout configuration"""
        # Get the platform layout configuration
        platform_layout = get_layout(layout_name)
        
        # Clear existing platforms if any
        for sprite in self.platforms:
            sprite.kill()
        
        # Create platforms from the layout
        for platform_config in platform_layout:
            platform_type, x, y, width, height = platform_config
            platform = Platform(platform_type, x, y, width, height)
            self.all_sprites.add(platform)
            self.platforms.add(platform)

    def events(self):
        try:
            keys = pg.key.get_pressed()

            # once player enters game screen - show initial chat
            if not self.chat_init:
                self.chat_text = 'Game started! Good luck!'
                self.chat_init = True
                
            # EMERGENCY FIX: Add periodic stability check
            if not self.emergency_fix_applied and self.current_frame > 60:
                self.emergency_fix_applied = True
                print("Applying emergency movement stabilization...")
                for name, player_data in self.players.items():
                    if 'sprite' in player_data:
                        sprite = player_data['sprite']
                        # Reset physics to safe state
                        sprite.in_air = False
                        sprite.vel = vec(0, 0)
                        sprite.acc = vec(0, 0)
                        
                        # Find a safe platform to position on
                        for platform in self.platforms:
                            if platform.type == 'floor':
                                sprite.pos.y = platform.rect.top + 4
                                sprite.last_ground_y = sprite.pos.y
                                break

            for event in pg.event.get():
                # check for closing window
                if event.type == pg.QUIT:                    
                    print("You quit in the middle of the game!")
                    self.running = False
                    pg.quit()
                    quit()

                # Handle all controllers for attack inputs
                handled_attack = False
                for controller in self.controllers.values():
                    if controller.check_attack_key(event, self):
                        handled_attack = True
                        break
                
                # If the event wasn't handled as an attack, check other game controls
                if not handled_attack and event.type == pg.KEYDOWN:
                    # restart game after match ends
                    if event.key == pg.K_r:
                        if self.showed_end:
                            if not self.restart_request:
                                self.restartGame()
                                self.restart_request = True
                                self.chat_messages.append('Game restarted!')
                    
                    # return to main menu
                    elif event.key == pg.K_m:
                        if self.showed_end:
                            self.quitToMainMenu()
                    
                    # quit game
                    elif event.key == pg.K_q:
                        if self.showed_end:
                            print("Thank you for playing!")
                            self.running = False
                            pg.quit()
                            quit()

            # Handle movement for all players using their respective controllers
            for controller in self.controllers.values():
                controller.handle_movement(keys, self)
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()  # Print full stack trace for better debugging
            quit()

    def update(self):
        try:
            # Increment frame counter
            self.current_frame += 1
            
            # Update all non-player sprites
            for sprite in self.all_sprites:
                if not any(sprite == player_data.get('sprite') for player_data in self.players.values() if 'sprite' in player_data):
                    sprite.update()
                    
            # First update sprite physics and state for all player sprites
            for name, player_data in self.players.items():
                if 'sprite' in player_data:
                    sprite = player_data['sprite']
                    # Let the sprite's update method handle physics
                    sprite.update()
                    
                    # Update player data from sprite position after physics
                    player_data['xPos'] = str(sprite.pos.x)
                    player_data['yPos'] = str(sprite.pos.y)
                    
                    # Ensure player doesn't fall off the bottom of the screen
                    if float(player_data['yPos']) > 700:
                        print(f"Player {name} fell off bottom, respawning...")
                        # Respawn at top center with no velocity
                        sprite.pos.x = GAME_WIDTH / 2
                        sprite.pos.y = 100
                        sprite.vel.x = 0
                        sprite.vel.y = 0
                        
                        # Ensure we clear any saved ground position
                        if hasattr(sprite, 'last_ground_y'):
                            sprite.last_ground_y = None
                            
                        # Set in_air flag to ensure physics work correctly
                        sprite.in_air = True
                        
                        # Update player data to match sprite position
                        player_data['xPos'] = str(sprite.pos.x)
                        player_data['yPos'] = str(sprite.pos.y)
                        
                        # Add damage when falling off
                        sprite.damage_percent += 10  # 10% damage for falling
                        player_data['damage_percent'] = str(sprite.damage_percent)
                    
                    # Check if we need to initialize the character on a platform
                    # This helps prevent the initial falling through platforms issue
                    elif not hasattr(sprite, 'initialized_platform_check'):
                        # Do an initial platform check to ensure characters start on platforms
                        for platform in self.platforms:
                            # Check if character is standing on this platform
                            if (sprite.pos.y >= platform.rect.top and
                                sprite.pos.y <= platform.rect.top + 10 and
                                sprite.pos.x >= platform.rect.left and
                                sprite.pos.x <= platform.rect.right):
                                # Character is on a platform, set ground state
                                sprite.in_air = False
                                sprite.last_ground_y = platform.rect.top + 1
                                sprite.pos.y = sprite.last_ground_y
                                sprite.vel.y = 0
                                print(f"Initialized {name} on platform at y={sprite.last_ground_y}")
                                break
                        
                        # Mark character as checked
                        sprite.initialized_platform_check = True
                    
            # Check winner after all updates
            if self.initialized and self.playing:
                self.checkWinner()
                
        except Exception as e:
            print(f"Error in update: {e}")
            import traceback
            traceback.print_exc()
            quit()

    # for consistently drawing the background and the sprites
    def draw(self):
        try:
            # show the background
            self.screen.blit(self.arena_bg, ORIGIN)
            self.screen.blit(self.chat_bg, (700,0))
            
            # check method below
            self.drawStatsBoard()
            
            # show all the sprites
            self.all_sprites.draw(self.screen)

            # write the player's name on top of the sprite
            font = pg.font.Font(None, 20)
            for player_data in self.players.values():
                if 'sprite' in player_data:
                    sprite = player_data['sprite']
                    coors = (sprite.rect.left, sprite.rect.top-15)
                    text_surface = font.render(sprite.name, True, WHITE)
                    self.screen.blit(text_surface, coors)

            # show end game results
            if len(self.winner) > 0 and not self.showed_end:
                self.initialized = False
                self.playing = False

                self.chat_messages = []
                self.chat_messages.append('===== {} won this round! ====='.format(self.winner))
                self.chat_messages.append("-> Press R to restart the game")
                self.chat_messages.append('')
                self.chat_messages.append('-> Press M to go back to the main menu')
                self.chat_messages.append('')
                self.chat_messages.append('-> Press Q to exit the game')
                self.chat_messages.append('   * We hope you enjoyed playing!')
                self.chat_messages.append('======================================')

                self.showed_end = True

            # show the message area
            font = pg.font.Font(None, 30)
            text_surface = font.render(self.chat_text, True, WHITE)
            self.screen.blit(text_surface, (760,644))

            # show all the messages
            font2 = pg.font.Font(None, 24)
            for i in range(0,len(self.chat_messages)):
                text_surface2 = font2.render(self.chat_messages[i], True, BLACK)
                self.screen.blit(text_surface2, (730,95+(i*25)))

            pg.display.flip()
            
        except Exception as e:
            print(f"Error in draw: {e}")
            quit()

    # board with the players' name and life
    def drawStatsBoard(self):
        font = pg.font.Font(None, 22)
        text = font.render('Player - Damage %', True, WHITE)
        pg.draw.rect(self.screen, BLACK, (10, 10, 140, 20))
        pg.draw.rect(self.screen, GRAY, (10, 30, 140, 30*len(self.players)))
        self.screen.blit(text, (37,12))

        i = 0        
        for player_data in self.players.values():
            name = player_data.get('name', 'Unknown')
            
            # Get damage percentage from sprite or player data
            if 'sprite' in player_data:
                damage_percent = player_data['sprite'].damage_percent
            else:
                damage_percent = float(player_data.get('damage_percent', 0))
                
            stats = name + ' - ' + str(int(damage_percent)) + '%'
            diff = 10 - len(name)

            # Color text according to player's damage percentage
            if damage_percent < 50:
                text = font.render(stats, True, GREEN)
            elif damage_percent < 100:
                text = font.render(stats, True, YELLOW) 
            elif damage_percent < 150:
                text = font.render(stats, True, ORANGE)
            elif damage_percent < 999:
                text = font.render(stats, True, RED)
            else:  # 999% (defeated)
                text = font.render(stats, True, BLACK)

            self.screen.blit(text, (12+(diff*5),40+(i*30)))
            i += 1

    # ========================= LOCAL SERVER METHODS =========================
    
    # Automatically set up player 2 after player 1 selects their character
    def setupPlayer2(self):
        if not self.auto_player2:
            return
            
        # Create a name for Player 2 that's different from Player 1
        player2_name = "Player 2"
        if player2_name == self.player_names[0]:
            player2_name = "Player Two"
            
        # Choose a random character that's different from Player 1's character
        available_chars = [char for char in self.character_options if char != self.player_characters[0]]
        if not available_chars:  # Just in case
            available_chars = self.character_options
        player2_char = random.choice(available_chars)
        
        # Connect player 2
        self.player_names[1] = player2_name
        self.players[player2_name] = {
            'name': player2_name,
            'character': player2_char,
            'status': 'ready',  # Auto-ready
            'damage_percent': '0',  # Start with 0% damage
            'xPos': '0',
            'yPos': '0',
            'direc': 'left',
            'walk_c': '0',
            'move': 'stand'
        }
        
        # Set player 2's character and status
        self.player_characters[1] = player2_char
        self.player_statuses[1] = 'ready'
        
        # Update player count
        self.player_count = 2
        
        # Set up the controller for player 2
        self._setup_controllers()
        
        print(f"Auto-setup Player 2: {player2_name} with character {player2_char}")
        
        # Return so the startGame can be called
        return True
    
    # Menu interface compatibility methods
    def connectPlayer(self, name):
        if self.current_player_index < 2:
            self.player_names[self.current_player_index] = name
            
            # Add to players dict (emulating server behavior)
            self.players[name] = {
                'name': name,
                'character': 'none',
                'status': 'unready',
                'damage_percent': '0',  # Start with 0% damage
                'xPos': '0',
                'yPos': '0',
                'direc': 'right',
                'walk_c': '0',
                'move': 'stand'
            }
            
            # Move to next player if first player is set
            if self.current_player_index == 0:
                self.current_player_index = 1
                
            # Setup controller for this player
            self._setup_controllers()
    
    def checkName(self, name):
        # In local mode, just check if the name is already used by the other player
        if self.current_player_index == 1 and name == self.player_names[0]:
            self.name_available = False
        else:
            self.name_available = True
    
    def editPlayerName(self, old_name, new_name):
        # Update name in player list
        if old_name in self.player_names:
            index = self.player_names.index(old_name)
            self.player_names[index] = new_name
        
        # Update in players dict
        if old_name in self.players:
            self.players[new_name] = self.players.pop(old_name)
            self.players[new_name]['name'] = new_name
            
            # Update in controllers if needed
            if old_name in self.controllers:
                controller = self.controllers.pop(old_name)
                controller.player_name = new_name
                self.controllers[new_name] = controller
    
    def editPlayerCharacter(self, name, character):
        # Set character in players dict
        if name in self.players:
            self.players[name]['character'] = character
            
            # For tracking in our local player state
            if name == self.player_names[0]:
                self.player_characters[0] = character
            elif name == self.player_names[1]:
                self.player_characters[1] = character
    
    def editPlayerStatus(self, name, status):
        # Update status in players dict
        if name in self.players:
            self.players[name]['status'] = status
            
            # For tracking in our local player state
            if name == self.player_names[0]:
                self.player_statuses[0] = status
                
                # If we're player 1 and we just got ready, set up player 2 automatically
                if status == 'ready' and self.auto_player2:
                    self.setupPlayer2()
                    
            elif name == self.player_names[1]:
                self.player_statuses[1] = status
            
            # Count ready players
            self.player_count = 0
            for player_status in self.player_statuses:
                if player_status == 'ready':
                    self.player_count += 1
                    
            # Start game if both players are ready
            if self.player_count == 2:
                self.startGame()
    
    def startGame(self):
        # Only start if both players are ready
        if self.player_statuses[0] == 'ready' and self.player_statuses[1] == 'ready':
            print("====== Started Game! ======")
            
            # Position players
            # Player 1 
            self.players[self.player_names[0]]['xPos'] = '157'
            self.players[self.player_names[0]]['yPos'] = '460'  # Match platform heights
            self.players[self.player_names[0]]['direc'] = 'right'
            
            # Player 2
            self.players[self.player_names[1]]['xPos'] = '534'
            self.players[self.player_names[1]]['yPos'] = '460'  # Match platform heights
            self.players[self.player_names[1]]['direc'] = 'left'
            
            # Create copy for restart
            self.init_players = copy.deepcopy(self.players)
            
            # Create the actual character sprites
            self.createCharacterSprites()
            
            # Set game state
            self.status = GAME
            self.playing = True
            self.initialized = True
            
            # Game start message
            self.chat_messages.append('============ GAME START ============')
            self.chat_messages.append('Best of luck - may the best player win!')
            self.chat_messages.append('======================================')
    
    def createCharacterSprites(self):
        # Create sprites for both players
        try:
            # Create a dictionary to store the sprites by player name for easier reference
            player_sprites = {}
            
            # Character factory dictionary
            character_classes = {
                MARIO: LocalMario,
                LUIGI: LocalLuigi,
                YOSHI: LocalYoshi,
                POPO: LocalPopo,
                NANA: LocalNana,
                LINK: LocalLink
            }
            
            for name, player_data in self.players.items():
                char = player_data['character']
                x = float(player_data['xPos'])
                y = float(player_data['yPos'])
                d = player_data['direc']
                
                # Use damage_percent or default to 0 if not present (for compatibility)
                damage_percent = 0.0
                if 'damage_percent' in player_data:
                    damage_percent = float(player_data['damage_percent'])
                elif 'health' in player_data:
                    # Legacy support - convert health to 0 damage
                    damage_percent = 0.0
                
                w = int(player_data['walk_c'])
                m = player_data['move']
                pos = [x, y]
                
                player = None
                # Create the appropriate character using our local character classes
                try:
                    # Use factory pattern to get the right character class
                    character_class = character_classes.get(char, LocalMario)
                    
                    # Create the player with the appropriate parameters
                    player = character_class(self, name, 'alive', damage_percent, pos, d, w, m)
                    
                    # Initialize specific physics properties to ensure proper starting state
                    player.vel = vec(0, 0)  # Start with no velocity
                    player.acc = vec(0, 0)  # Start with no acceleration
                    player.in_air = False   # Start on the ground
                    player.is_jumping = False
                    player.is_fast_falling = False
                    
                    # Adjust positioning - make sure feet are exactly on the platform
                    # Look for platforms at the character's position
                    platform_at_pos = None
                    for platform in self.platforms:
                        if (pos[0] >= platform.rect.left and 
                            pos[0] <= platform.rect.right and
                            abs(pos[1] - platform.rect.top) < 20):  # Within 20 pixels of platform top
                            platform_at_pos = platform
                            break
                    
                    if platform_at_pos:
                        # Position character precisely on platform
                        player.pos.y = platform_at_pos.rect.top + 4  # Adjusted to +4 to visually stand on platform
                        player.last_ground_y = player.pos.y
                        print(f"Adjusted {name} to platform at y={player.pos.y}")
                    else:
                        # Default ground position
                        player.last_ground_y = pos[1]
                    
                    # Debug output
                    print(f"Created {char} for {name} at position {pos[0]}, {player.pos.y}")
                    
                    if char not in character_classes:
                        print(f"Character {char} not found, defaulting to Mario")
                
                except Exception as char_error:
                    print(f"Error creating character {char}: {char_error}")
                    print("Defaulting to Mario")
                    # If creating a specific character fails, default to Mario
                    player = LocalMario(self, name, 'alive', damage_percent, pos, d, w, m)
                
                if player:
                    # Store the sprite reference
                    player_data['sprite'] = player
                    player_sprites[name] = player
                    
                    # Add to sprite groups
                    self.all_sprites.add(player)
            
            # Clear the existing enemy_sprites group
            self.enemy_sprites.empty()
            
            # Create a dedicated enemy_sprites group for each player
            # This ensures that a player doesn't attack themselves
            for player_name, player_sprite in player_sprites.items():
                # Create a list of enemies for this player
                enemies = []
                
                # Add all other players as enemies
                for other_name, other_sprite in player_sprites.items():
                    if other_name != player_name:
                        enemies.append(other_sprite)
                
                # Set the player's enemy sprites
                # Note: We need a custom enemy sprites group for each character
                # But the API only has one self.enemy_sprites group
                # We'll need to modify the weakAttack and heavyAttack methods
                # to use this custom group instead
                player_sprite.enemy_sprites = pg.sprite.Group()
                for enemy in enemies:
                    player_sprite.enemy_sprites.add(enemy)
            
            # For backward compatibility with the original game code,
            # set up the main enemy_sprites group (for debugging only)
            for player_name, player_sprite in player_sprites.items():
                for other_name, other_sprite in player_sprites.items():
                    if player_name != other_name:
                        self.enemy_sprites.add(other_sprite)
                    
        except Exception as e:
            print(f"Error in createCharacterSprites: {e}")
            import traceback
            traceback.print_exc()  # Print full stack trace for better debugging
    
    def updatePlayer(self):
        # This method exists for compatibility with the character classes
        # It's not needed in our local implementation
        pass
    
    def checkWinner(self):
        # Check if there's a winner (one player with damage < 999%)
        alive_count = len(self.players)
        alive = ''
        
        for name, player_data in self.players.items():
            if 'sprite' in player_data:
                sprite = player_data['sprite']
                if sprite.is_defeated():
                    alive_count -= 1
                else:
                    alive = name
            else:
                # Use player data if sprite not available
                if float(player_data.get('damage_percent', 0)) >= 999:
                    alive_count -= 1
                else:
                    alive = name
        
        # If only one player is alive, they win
        if alive_count <= 1 and alive:
            self.winner = alive
    
    def attackPlayer(self, player_name, damage, move, attacker_pos_x):
        # Process attack on a player
        try:
            # Find attacker
            attacker_pos_x = float(attacker_pos_x)
            
            # Update damage in player data
            if player_name in self.players:
                player_data = self.players[player_name]
                
                # If player has a sprite, use its take_damage method
                if 'sprite' in player_data:
                    sprite = player_data['sprite']
                    
                    # Determine knockback values based on damage amount from attacker
                    # (This is handled inside the sprite's take_damage method)
                    new_damage = sprite.take_damage(damage, attacker_pos_x)
                    
                    # Update player data to match sprite state
                    player_data['damage_percent'] = str(sprite.damage_percent)
                    player_data['move'] = move
                    
                    # Debug output
                    print(f"Player {player_name} took {damage}% damage, now at {new_damage}%")
                    
                    # Check for a winner
                    self.checkWinner()
                else:
                    print(f"Warning: Player {player_name} has no sprite to attack")
        except Exception as e:
            print(f"Error in attackPlayer: {e}")
            import traceback
            traceback.print_exc()
    
    def restartGame(self):
        # Reset player states from initial state
        self.players = copy.deepcopy(self.init_players)
        
        # Reset sprite groups
        self.enemy_sprites = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group()
        self.platforms = pg.sprite.Group()
        self.loadPlatforms()
        
        # Create character sprites with reset values
        self.createCharacterSprites()
        
        # Reset game state
        self.showed_end = False
        self.restart_request = False
        self.status = GAME
        self.playing = True
        self.initialized = True
        
        # Game restart message
        self.chat_messages = []
        self.chat_messages.append('=========== GAME RESTART ===========')
        self.chat_messages.append('Best of luck - may the best player win!')
        self.chat_messages.append('======================================')
    
    def quitToMainMenu(self):
        # Reset game state
        self.status = INTRO
        self.playing = False
        self.showed_end = False
        self.initialized = False
        self.restart_request = False
        
        # Reset player variables
        self.player_names = ["", ""]
        self.player_characters = ["none", "none"]
        self.player_statuses = ["unready", "unready"]
        self.current_player_index = 0
        self.player_count = 0
        self.curr_player = ""
        
        # Reset controllers
        self.controllers = {}
        
        # Reset chat area
        self.chat_text = ''
        self.chatting = False
        self.chat_once = False
        self.chat_init = False
        self.chat_messages = []
        
        # Reset player state
        self.players = {}
        self.init_players = {}
        
        # Reset sprite groups
        self.enemy_sprites = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group()
        self.platforms = pg.sprite.Group()
        self.loadPlatforms()

# main start of the program
game = LocalGame()

while game.running:
    game.new()