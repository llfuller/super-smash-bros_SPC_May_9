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

# characters
from characters.Mario import Mario
from characters.Luigi import Luigi
from characters.Yoshi import Yoshi
from characters.Popo import Popo
from characters.Nana import Nana
from characters.Link import Link

# menus
from menus.Intro import Intro
from menus.Other import Other
from menus.Start import Start

# others
from objects.Platform import Platform
from settings import *
from images import *

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
        
        # player variables
        self.player_names = ["", ""]  # player1, player2
        self.player_characters = ["none", "none"]  # character selections
        self.player_statuses = ["unready", "unready"]  # ready status
        self.current_player_index = 0  # which player is currently selecting (0 or 1)
        self.player_count = 0  # number of ready players
        self.name_available = True  # for compatibility with menu code

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
                    self.updateAllPlayers()
                    
                self.clock.tick(FPS)
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

    def loadPlatforms(self):
        base = Platform('floor', 0, HEIGHT-30, GAME_WIDTH, 30)
        self.all_sprites.add(base)
        self.platforms.add(base)

        plat1 = Platform('platform', 60, 460, 200, 50)
        self.all_sprites.add(plat1)
        self.platforms.add(plat1)

        plat2 = Platform('platform', 435, 460, 200, 50)
        self.all_sprites.add(plat2)
        self.platforms.add(plat2)

        plat3 = Platform('platform', 250, 260, 200, 50)
        self.all_sprites.add(plat3)
        self.platforms.add(plat3)

    def events(self):
        try:
            keys = pg.key.get_pressed()

            # once player enters game screen - show initial chat
            if not self.chat_init:
                self.chat_text = 'Game started! Good luck!'
                self.chat_init = True

            for event in pg.event.get():
                # check for closing window
                if event.type == pg.QUIT:                    
                    print("You quit in the middle of the game!")
                    self.running = False
                    pg.quit()
                    quit()

                # attacks for player 1 (arrow keys + Z/X)
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_z:
                        if self.player_names[0] in self.players:
                            self.players[self.player_names[0]]['sprite'].weakAttack()
                    
                    elif event.key == pg.K_x:
                        if self.player_names[0] in self.players:
                            self.players[self.player_names[0]]['sprite'].heavyAttack()
                    
                    # attacks for player 2 (WASD + G/H)
                    elif event.key == pg.K_g:
                        if self.player_names[1] in self.players:
                            self.players[self.player_names[1]]['sprite'].weakAttack()
                    
                    elif event.key == pg.K_h:
                        if self.player_names[1] in self.players:
                            self.players[self.player_names[1]]['sprite'].heavyAttack()
                    
                    # restart game after match ends
                    elif event.key == pg.K_r:
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

            # Handle player 1 movement (arrow keys)
            if self.player_names[0] in self.players and self.players[self.player_names[0]]['health'] > 0 and self.playing:
                player1 = self.players[self.player_names[0]]
                sprite1 = player1['sprite']
                
                # Reset movement state
                sprite1.move = STAND
                
                if keys[pg.K_UP]:
                    sprite1.jump()
                    sprite1.walk_c = 0

                if keys[pg.K_LEFT] and float(player1['xPos']) > 40:
                    sprite1.acc.x = -sprite1.acce
                    sprite1.walk_c = (sprite1.walk_c + 1) % 8
                    sprite1.direc = LEFT
                    sprite1.move = WALK
                    player1['direc'] = LEFT
                    player1['move'] = WALK
                    player1['walk_c'] = str(sprite1.walk_c)

                elif keys[pg.K_RIGHT] and float(player1['xPos']) < GAME_WIDTH-40:
                    sprite1.acc.x = sprite1.acce
                    sprite1.walk_c = (sprite1.walk_c + 1) % 8
                    sprite1.direc = RIGHT
                    sprite1.move = WALK
                    player1['direc'] = RIGHT
                    player1['move'] = WALK
                    player1['walk_c'] = str(sprite1.walk_c)
                
                else:
                    sprite1.walk_c = 0
                    sprite1.move = STAND
                    player1['move'] = STAND
                    player1['walk_c'] = '0'
            
            # Handle player 2 movement (WASD)
            if self.player_names[1] in self.players and self.players[self.player_names[1]]['health'] > 0 and self.playing:
                player2 = self.players[self.player_names[1]]
                sprite2 = player2['sprite']
                
                # Reset movement state
                sprite2.move = STAND
                
                if keys[pg.K_w]:
                    sprite2.jump()
                    sprite2.walk_c = 0

                if keys[pg.K_a] and float(player2['xPos']) > 40:
                    sprite2.acc.x = -sprite2.acce
                    sprite2.walk_c = (sprite2.walk_c + 1) % 8
                    sprite2.direc = LEFT
                    sprite2.move = WALK
                    player2['direc'] = LEFT
                    player2['move'] = WALK
                    player2['walk_c'] = str(sprite2.walk_c)

                elif keys[pg.K_d] and float(player2['xPos']) < GAME_WIDTH-40:
                    sprite2.acc.x = sprite2.acce
                    sprite2.walk_c = (sprite2.walk_c + 1) % 8
                    sprite2.direc = RIGHT
                    sprite2.move = WALK
                    player2['direc'] = RIGHT
                    player2['move'] = WALK
                    player2['walk_c'] = str(sprite2.walk_c)
                
                else:
                    sprite2.walk_c = 0
                    sprite2.move = STAND
                    player2['move'] = STAND
                    player2['walk_c'] = '0'
        except Exception as e:
            print(f"Error: {e}")
            quit()

    def update(self):
        try:
            self.all_sprites.update()
            
            # Update player positions in the local server state
            for name, player_data in self.players.items():
                if 'sprite' in player_data:
                    sprite = player_data['sprite']
                    player_data['xPos'] = str(sprite.pos[0])
                    player_data['yPos'] = str(sprite.pos[1])
                    
                    # Ensure player doesn't fall off the bottom
                    if float(player_data['yPos']) > 700:
                        player_data['yPos'] = '30'
                        sprite.pos[1] = 30
        except Exception as e:
            print(f"Error in update: {e}")
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
        text = font.render('Player - Life', True, WHITE)
        pg.draw.rect(self.screen, BLACK, (10, 10, 140, 20))
        pg.draw.rect(self.screen, GRAY, (10, 30, 140, 30*len(self.players)))
        self.screen.blit(text, (37,12))

        i = 0        
        for player_data in self.players.values():
            name = player_data.get('name', 'Unknown')
            health = float(player_data.get('health', 0))
            stats = name + ' - ' + str(int(health))
            diff = 10 - len(name)

            # color text according to player's health
            if health > 60:
                text = font.render(stats, True, GREEN)
            elif health <= 60 and health > 20:
                text = font.render(stats, True, ORANGE) 
            elif health <= 20 and health > 0:
                text = font.render(stats, True, RED)
            elif health == 0:
                text = font.render(stats, True, BLACK)

            self.screen.blit(text, (12+(diff*5),40+(i*30)))
            i += 1

    # ========================= LOCAL SERVER METHODS =========================
    
    # Menu interface compatibility methods
    def connectPlayer(self, name):
        if self.current_player_index < 2:
            self.player_names[self.current_player_index] = name
            
            # Add to players dict (emulating server behavior)
            self.players[name] = {
                'name': name,
                'character': 'none',
                'status': 'unready',
                'health': '100',
                'xPos': '0',
                'yPos': '0',
                'direc': 'right',
                'walk_c': '0',
                'move': 'stand'
            }
            
            # Move to next player if first player is set
            if self.current_player_index == 0:
                self.current_player_index = 1
    
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
            elif name == self.player_names[1]:
                self.player_statuses[1] = status
            
            # Count ready players
            self.player_count = 0
            for player_status in self.player_statuses:
                if player_status == 'ready':
                    self.player_count += 1
    
    def startGame(self):
        # Only start if both players are ready
        if self.player_statuses[0] == 'ready' and self.player_statuses[1] == 'ready':
            print("====== Started Game! ======")
            
            # Position players
            # Player 1
            self.players[self.player_names[0]]['xPos'] = '157'
            self.players[self.player_names[0]]['yPos'] = '480'
            self.players[self.player_names[0]]['direc'] = 'right'
            
            # Player 2
            self.players[self.player_names[1]]['xPos'] = '534'
            self.players[self.player_names[1]]['yPos'] = '480'
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
        for name, player_data in self.players.items():
            char = player_data['character']
            x = float(player_data['xPos'])
            y = float(player_data['yPos'])
            d = player_data['direc']
            h = float(player_data['health'])
            w = int(player_data['walk_c'])
            m = player_data['move']
            pos = [x, y]
            
            # Set as current player for character creation (compatibility with character classes)
            self.curr_player = name
            
            # Create the appropriate character
            if char == MARIO:
                player = Mario(self, self.curr_player, name, 'alive', h, pos, d, w, m)
            elif char == LUIGI:
                player = Luigi(self, self.curr_player, name, 'alive', h, pos, d, w, m)
            elif char == YOSHI:
                player = Yoshi(self, self.curr_player, name, 'alive', h, pos, d, w, m)
            elif char == POPO:
                player = Popo(self, self.curr_player, name, 'alive', h, pos, d, w, m)
            elif char == NANA:
                player = Nana(self, self.curr_player, name, 'alive', h, pos, d, w, m)
            elif char == LINK:
                player = Link(self, self.curr_player, name, 'alive', h, pos, d, w, m)
            
            # Store the sprite reference
            player_data['sprite'] = player
            
            # Add to sprite groups
            self.all_sprites.add(player)
            
            # Set as enemy for the other player
            for other_name in self.players:
                if other_name != name:
                    self.enemy_sprites.add(player)
    
    def updatePlayer(self):
        # This is called by character sprites - we need it for compatibility
        # For the local game, we directly update the player data in the update() method
        pass
    
    def updateAllPlayers(self):
        # In the network version, this fetches updates from the server
        # For our local version, we're already updating player states in the update() method
        pass
    
    def checkWinner(self):
        # Check if there's a winner (one player with health > 0)
        alive_count = len(self.players)
        alive = ''
        
        for name, player_data in self.players.items():
            if float(player_data['health']) == 0:
                alive_count -= 1
            else:
                alive = name
        
        # If only one player is alive, they win
        if alive_count <= 1 and alive:
            self.winner = alive
    
    def attackPlayer(self, player_name, damage, move):
        # Process attack on a player
        if player_name in self.players:
            target = self.players[player_name]
            current_health = float(target['health'])
            new_health = max(0, current_health - float(damage))
            target['health'] = str(new_health)
            target['move'] = move
            
            # Update sprite state if it exists
            if 'sprite' in target:
                target['sprite'].health = new_health
                target['sprite'].move = move
    
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