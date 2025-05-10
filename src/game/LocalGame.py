'''
Local Multiplayer Super Smash Bros Clone

This is a modified version of the original game that supports local multiplayer
with two controllers on a single instance without requiring a server.

Controls:
Player 1 (Keyboard):
- Arrow keys: Movement
- Z: Weak attack
- X: Heavy attack

Player 2 (Controller):
- D-pad/Left stick: Movement
- Button 0/A: Weak attack 
- Button 1/B: Heavy attack
'''

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

# others
from objects.Platform import Platform
from settings import *
from images import *

# dependencies
import pygame as pg
import sys
import json
import random

class LocalPlayer:
    def __init__(self, name, character=None, is_ready=False):
        self.name = name
        self.character = character
        self.is_ready = is_ready
        self.status = 'alive'
        self.health = 100
        self.xPos = 0
        self.yPos = 0
        self.direc = 'right'
        self.walk_c = 0
        self.move = 'stand'

class LocalGame:
    def __init__(self):
        # initialize pygame
        pg.init()
        pg.mixer.init()
        pg.display.set_caption(TITLE)
        pg.display.set_icon(ICON)
        
        # initialize joystick subsystem for controller support
        pg.joystick.init()
        self.joysticks = []
        for i in range(pg.joystick.get_count()):
            joystick = pg.joystick.Joystick(i)
            joystick.init()
            self.joysticks.append(joystick)
            print(f"Found controller: {joystick.get_name()}")
        
        # game variables
        self.screen = pg.display.set_mode(BG_SIZE)
        self.clock = pg.time.Clock()
        self.status = INTRO
        self.running = True
        self.playing = False
        self.showed_end = False
        self.initialized = False
        self.winner = ''
        
        # converted background images for optimized game loop
        self.arena_bg = ARENA_BG.convert()
        self.chat_bg = CHAT_BG.convert()
        
        # local players
        self.players = {}
        self.char_selection_index = 0
        self.player_setup_state = 0  # 0: player 1 selection, 1: player 2 selection, 2: ready
        self.player_characters = [MARIO, LUIGI, YOSHI, POPO, NANA, LINK]
        self.player1 = LocalPlayer("Player 1")
        self.player2 = LocalPlayer("Player 2")

        # sprite groups
        self.enemy_sprites = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group()
        self.platforms = pg.sprite.Group()
        
        # messages
        self.messages = []

    def run(self):
        while self.running:
            if self.status == INTRO:
                self.handle_intro()
            elif self.status == GUIDE:
                Other(self, GUIDE, GUIDE_BG)
            elif self.status == ABOUT:
                Other(self, ABOUT, ABOUT_BG)
            elif self.status == START:
                self.handle_character_selection()
            elif self.status == GAME:
                self.game_loop()
    
    def handle_intro(self):
        # Simple intro screen
        running = True
        while running and self.running:
            self.clock.tick(FPS)
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                    running = False
                    pg.quit()
                    sys.exit()
                
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        self.status = START
                        running = False
                    elif event.key == pg.K_g:
                        self.status = GUIDE
                        running = False
                    elif event.key == pg.K_a:
                        self.status = ABOUT
                        running = False
                    elif event.key == pg.K_ESCAPE:
                        self.running = False
                        running = False
                        pg.quit()
                        sys.exit()
            
            # Draw intro screen
            self.screen.blit(INTRO_BG, (0, 0))
            font = pg.font.Font(None, 40)
            title = font.render("SUPER SMASH BROS - LOCAL", True, WHITE)
            start = font.render("Press ENTER to Start", True, WHITE)
            guide = font.render("Press G for Guide", True, WHITE)
            about = font.render("Press A for About", True, WHITE)
            quit_text = font.render("Press ESC to Quit", True, WHITE)
            
            self.screen.blit(title, (FULL_WIDTH//2 - title.get_width()//2, 100))
            self.screen.blit(start, (FULL_WIDTH//2 - start.get_width()//2, 300))
            self.screen.blit(guide, (FULL_WIDTH//2 - guide.get_width()//2, 350))
            self.screen.blit(about, (FULL_WIDTH//2 - about.get_width()//2, 400))
            self.screen.blit(quit_text, (FULL_WIDTH//2 - quit_text.get_width()//2, 450))
            
            pg.display.flip()
    
    def handle_character_selection(self):
        running = True
        
        # Character images for selection screen
        char_images = {
            MARIO: maS1,
            LUIGI: luS1, 
            YOSHI: yoS1,
            POPO: poS1,
            NANA: naS1,
            LINK: liS1
        }
        
        current_player = self.player1 if self.player_setup_state == 0 else self.player2
        selection_index = 0
        
        while running and self.running:
            self.clock.tick(FPS)
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                    running = False
                    pg.quit()
                    sys.exit()
                
                # Keyboard controls for selection
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_LEFT:
                        selection_index = (selection_index - 1) % len(self.player_characters)
                    elif event.key == pg.K_RIGHT:
                        selection_index = (selection_index + 1) % len(self.player_characters)
                    elif event.key == pg.K_RETURN:
                        selected_char = self.player_characters[selection_index]
                        current_player.character = selected_char
                        current_player.is_ready = True
                        
                        if self.player_setup_state == 0:
                            self.player_setup_state = 1
                            current_player = self.player2
                            selection_index = 0
                        else:
                            # Both players have selected their characters
                            self.start_game()
                            running = False
                
                # Controller input for player 2
                if self.player_setup_state == 1 and len(self.joysticks) > 0:
                    if event.type == pg.JOYBUTTONDOWN:
                        if event.button == 0:  # A button
                            selected_char = self.player_characters[selection_index]
                            current_player.character = selected_char
                            current_player.is_ready = True
                            self.start_game()
                            running = False
                    
                    # Handle joystick axis for d-pad/analog movement
                    if event.type == pg.JOYAXISMOTION:
                        if event.axis == 0:  # X axis
                            if event.value > 0.5:  # Right
                                selection_index = (selection_index + 1) % len(self.player_characters)
                            elif event.value < -0.5:  # Left
                                selection_index = (selection_index - 1) % len(self.player_characters)
                    
                    # Handle hat (d-pad) movement for selection
                    if event.type == pg.JOYHATMOTION:
                        hat_x, hat_y = event.value
                        if hat_x == 1:  # Right
                            selection_index = (selection_index + 1) % len(self.player_characters)
                        elif hat_x == -1:  # Left
                            selection_index = (selection_index - 1) % len(self.player_characters)
            
            # Draw character selection screen
            self.screen.fill(BLACK)
            
            # Draw title
            font = pg.font.Font(None, 40)
            if self.player_setup_state == 0:
                title = font.render("Player 1 - Choose your character", True, WHITE)
            else:
                title = font.render("Player 2 - Choose your character", True, WHITE)
            
            self.screen.blit(title, (FULL_WIDTH//2 - title.get_width()//2, 100))
            
            # Draw character options
            char_name = self.player_characters[selection_index]
            char_img = char_images[char_name]
            
            # Make larger display
            scaled_img = pg.transform.scale(char_img, (200, 200))
            self.screen.blit(scaled_img, (FULL_WIDTH//2 - 100, 200))
            
            char_name_text = font.render(char_name, True, WHITE)
            self.screen.blit(char_name_text, (FULL_WIDTH//2 - char_name_text.get_width()//2, 420))
            
            # Navigation instructions
            nav_font = pg.font.Font(None, 30)
            if self.player_setup_state == 0:
                nav_text = nav_font.render("Use LEFT/RIGHT arrows to select, ENTER to confirm", True, WHITE)
            else:
                if len(self.joysticks) > 0:
                    nav_text = nav_font.render("Use D-pad/Left stick to select, A to confirm", True, WHITE)
                else:
                    nav_text = nav_font.render("Use LEFT/RIGHT arrows to select, ENTER to confirm", True, WHITE)
            
            self.screen.blit(nav_text, (FULL_WIDTH//2 - nav_text.get_width()//2, 500))
            
            pg.display.flip()
    
    def start_game(self):
        self.loadPlatforms()
        
        # Set player positions
        self.player1.xPos = 200
        self.player1.yPos = HEIGHT - 100
        self.player2.xPos = 500
        self.player2.yPos = HEIGHT - 100
        
        # Create player characters
        self.create_player_character(self.player1, "p1")
        self.create_player_character(self.player2, "p2")
        
        self.status = GAME
        self.initialized = True
        self.playing = True
        self.messages.append("============ GAME START ============")
        self.messages.append("Best of luck - may the best player win!")
    
    def create_player_character(self, player_data, player_id):
        pos = [player_data.xPos, player_data.yPos]
        char = player_data.character
        
        if char == MARIO:
            player = Mario(self, player_id, player_data.name, 'alive', 100, pos, 'right', 0, 'stand')
        elif char == LUIGI:
            player = Luigi(self, player_id, player_data.name, 'alive', 100, pos, 'right', 0, 'stand')
        elif char == YOSHI:
            player = Yoshi(self, player_id, player_data.name, 'alive', 100, pos, 'right', 0, 'stand')
        elif char == POPO:
            player = Popo(self, player_id, player_data.name, 'alive', 100, pos, 'right', 0, 'stand')
        elif char == NANA:
            player = Nana(self, player_id, player_data.name, 'alive', 100, pos, 'right', 0, 'stand')
        elif char == LINK:
            player = Link(self, player_id, player_data.name, 'alive', 100, pos, 'right', 0, 'stand')
        
        self.players[player_id] = player
        self.all_sprites.add(player)
        
        # Add to enemy sprite group for collision detection
        if player_id == "p1":
            self.enemy_sprites.add(self.players["p2"])
        else:
            self.enemy_sprites.add(self.players["p1"])
    
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
    
    def game_loop(self):
        while self.running and self.playing:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
            self.check_winner()
    
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.playing = False
                self.running = False
                pg.quit()
                sys.exit()
            
            # Key presses for player 1 attacks
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_z:
                    if "p1" in self.players:
                        self.players["p1"].weakAttack()
                elif event.key == pg.K_x:
                    if "p1" in self.players:
                        self.players["p1"].heavyAttack()
                elif event.key == pg.K_r:
                    if self.showed_end:
                        self.restart_game()
                elif event.key == pg.K_ESCAPE:
                    self.playing = False
                    self.status = INTRO
            
            # Controller inputs for player 2 attacks
            if len(self.joysticks) > 0 and event.type == pg.JOYBUTTONDOWN:
                if event.button == 0:  # A button (weak attack)
                    if "p2" in self.players:
                        self.players["p2"].weakAttack()
                elif event.button == 1:  # B button (heavy attack)
                    if "p2" in self.players:
                        self.players["p2"].heavyAttack()
        
        # Keyboard controls for player 1 movement
        keys = pg.key.get_pressed()
        player1 = self.players.get("p1")
        
        if player1 and player1.health > 0:
            # Jump
            if keys[pg.K_UP]:
                player1.jump()
            
            # Left movement
            if keys[pg.K_LEFT] and player1.pos[0] > 40:
                player1.acc.x = -player1.acce
                player1.walk_c += 1
                if player1.walk_c >= 8:
                    player1.walk_c = 0
                player1.direc = LEFT
                player1.move = WALK
            
            # Right movement
            elif keys[pg.K_RIGHT] and player1.pos[0] < GAME_WIDTH-40:
                player1.acc.x = player1.acce
                player1.walk_c += 1
                if player1.walk_c >= 8:
                    player1.walk_c = 0
                player1.direc = RIGHT
                player1.move = WALK
            
            # Standing
            else:
                player1.walk_c = 0
                player1.move = STAND
        
        # Controller input for player 2 movement
        if len(self.joysticks) > 0:
            joystick = self.joysticks[0]
            player2 = self.players.get("p2")
            
            if player2 and player2.health > 0:
                # Check hat (d-pad) for movement
                hat_x, hat_y = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0, 0)
                
                # Jump (up on d-pad or left stick)
                if hat_y == 1 or joystick.get_axis(1) < -0.5:
                    player2.jump()
                
                # Left movement
                if (hat_x == -1 or joystick.get_axis(0) < -0.5) and player2.pos[0] > 40:
                    player2.acc.x = -player2.acce
                    player2.walk_c += 1
                    if player2.walk_c >= 8:
                        player2.walk_c = 0
                    player2.direc = LEFT
                    player2.move = WALK
                
                # Right movement
                elif (hat_x == 1 or joystick.get_axis(0) > 0.5) and player2.pos[0] < GAME_WIDTH-40:
                    player2.acc.x = player2.acce
                    player2.walk_c += 1
                    if player2.walk_c >= 8:
                        player2.walk_c = 0
                    player2.direc = RIGHT
                    player2.move = WALK
                
                # Standing
                else:
                    player2.walk_c = 0
                    player2.move = STAND
    
    def update(self):
        self.all_sprites.update()
    
    def draw(self):
        # Draw the background and screen elements
        self.screen.blit(self.arena_bg, ORIGIN)
        self.screen.blit(self.chat_bg, (700,0))
        
        # Draw stats board
        self.draw_stats_board()
        
        # Draw all sprites
        self.all_sprites.draw(self.screen)
        
        # Draw player names
        font = pg.font.Font(None, 20)
        for player in self.players.values():
            coors = (player.rect.left, player.rect.top-15)
            text_surface = font.render((player.name), True, WHITE)
            self.screen.blit(text_surface, coors)
        
        # Draw messages
        font2 = pg.font.Font(None, 24)
        for i in range(min(len(self.messages), 10)):
            text_surface2 = font2.render(self.messages[i], True, BLACK)
            self.screen.blit(text_surface2, (730, 95+(i*25)))
        
        # Draw end game results
        if self.winner and not self.showed_end:
            self.messages = []
            self.messages.append(f"===== {self.winner} won this round! =====")
            self.messages.append("-> Press R to restart the game")
            self.messages.append("-> Press ESC to return to the main menu")
            self.showed_end = True
        
        pg.display.flip()
    
    def draw_stats_board(self):
        font = pg.font.Font(None, 22)
        text = font.render('Player - Life', True, WHITE)
        pg.draw.rect(self.screen, BLACK, (10, 10, 140, 20))
        pg.draw.rect(self.screen, GRAY, (10, 30, 140, 30*len(self.players)))
        self.screen.blit(text, (37,12))

        i = 0        
        for player in self.players.values():
            name = player.name
            stats = name + ' - ' + str(int(player.health))
            diff = 10 - len(player.name)

            # color text according to player's health
            if player.health > 60:
                text = font.render(stats, True, GREEN)
            elif player.health <= 60 and player.health > 20:
                text = font.render(stats, True, ORANGE) 
            elif player.health <= 20 and player.health > 0:
                text = font.render(stats, True, RED)
            elif player.health == 0:
                text = font.render(stats, True, BLACK)

            self.screen.blit(text, (12+(diff*5),40+(i*30)))
            i += 1
    
    def check_winner(self):
        if not self.playing:
            return
            
        # Check if any player has 0 health
        p1 = self.players.get("p1")
        p2 = self.players.get("p2")
        
        if p1 and p2:
            if p1.health <= 0:
                self.winner = p2.name
                self.playing = False
            elif p2.health <= 0:
                self.winner = p1.name
                self.playing = False
    
    def restart_game(self):
        # Reset player health and positions
        self.player1.health = 100
        self.player1.xPos = 200
        self.player1.yPos = HEIGHT - 100
        
        self.player2.health = 100
        self.player2.xPos = 500
        self.player2.yPos = HEIGHT - 100
        
        # Clear sprite groups
        self.enemy_sprites.empty()
        self.all_sprites.empty()
        self.platforms.empty()
        
        # Reload platforms and players
        self.loadPlatforms()
        self.create_player_character(self.player1, "p1")
        self.create_player_character(self.player2, "p2")
        
        # Reset game state
        self.showed_end = False
        self.winner = ''
        self.playing = True
        self.messages = []
        self.messages.append("=========== GAME RESTART ===========")
        self.messages.append("Best of luck - may the best player win!")
    
    # Required by character classes for compatibility
    def updatePlayer(self):
        pass
    
    def attackPlayer(self, player_name, damage, move):
        # Handle attack locally
        if player_name == "p1":
            self.players["p1"].health -= damage
            self.players["p1"].move = move
            if self.players["p1"].health < 0:
                self.players["p1"].health = 0
        elif player_name == "p2":
            self.players["p2"].health -= damage
            self.players["p2"].move = move
            if self.players["p2"].health < 0:
                self.players["p2"].health = 0

# Main entry point
if __name__ == "__main__":
    game = LocalGame()
    game.run() 