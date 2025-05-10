'''
UI components for rendering game UI elements
'''

import pygame as pg
from settings import *

class StatsBoard:
    """
    Display player health and other stats
    """
    def __init__(self, screen):
        self.screen = screen
        self.font = pg.font.Font(None, 22)
    
    def draw(self, players):
        """Draw the stats board with player information"""
        # Draw header
        text = self.font.render('Player - Life', True, WHITE)
        pg.draw.rect(self.screen, BLACK, (10, 10, 140, 20))
        pg.draw.rect(self.screen, GRAY, (10, 30, 140, 30*len(players)))
        self.screen.blit(text, (37, 12))
        
        # Draw player stats
        i = 0
        for player_data in players.values():
            name = player_data.get('name', 'Unknown')
            health = float(player_data.get('health', 0))
            stats = name + ' - ' + str(int(health))
            diff = 10 - len(name)
            
            # Color text according to player's health
            if health > 60:
                color = GREEN
            elif health <= 60 and health > 20:
                color = ORANGE
            elif health <= 20 and health > 0:
                color = RED
            else:
                color = BLACK
            
            text = self.font.render(stats, True, color)
            self.screen.blit(text, (12+(diff*5), 40+(i*30)))
            i += 1


class ChatBox:
    """
    Display game messages and chat
    """
    def __init__(self, screen):
        self.screen = screen
        self.message_font = pg.font.Font(None, 30)
        self.chat_font = pg.font.Font(None, 24)
    
    def draw_message(self, message):
        """Draw the current message at the bottom of the chat area"""
        text_surface = self.message_font.render(message, True, WHITE)
        self.screen.blit(text_surface, (760, 644))
    
    def draw_messages(self, messages):
        """Draw all chat messages"""
        for i, message in enumerate(messages):
            text_surface = self.chat_font.render(message, True, BLACK)
            self.screen.blit(text_surface, (730, 95+(i*25)))
    
    def show_game_end(self, winner):
        """Return a list of messages to display when the game ends"""
        messages = []
        messages.append(f'===== {winner} won this round! =====')
        messages.append("-> Press R to restart the game")
        messages.append('')
        messages.append('-> Press M to go back to the main menu')
        messages.append('')
        messages.append('-> Press Q to exit the game')
        messages.append('   * We hope you enjoyed playing!')
        messages.append('======================================')
        return messages


class PlayerNameTag:
    """
    Display player names above their sprites
    """
    def __init__(self, screen):
        self.screen = screen
        self.font = pg.font.Font(None, 20)
    
    def draw(self, sprite, name):
        """Draw the player's name above their sprite"""
        coords = (sprite.rect.left, sprite.rect.top-15)
        text_surface = self.font.render(name, True, WHITE)
        self.screen.blit(text_surface, coords) 