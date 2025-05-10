import sys
import pygame as pg

# move up one directory to be able to import the settings and images
sys.path.append("..")
from objects.Button import Button
from settings import *
from images import *
from sound_manager import sound_manager

class Intro:
    def __init__(self, game):
        self.game = game

        start = Button('start', 400, 275, 300, 100)
        guide = Button('guide', 400, 400, 300, 100)
        about = Button('about', 400, 525, 300, 100)

        while self.game.status == INTRO:
            self.game.screen.blit(INTRO_BG, ORIGIN)

            for event in pg.event.get():
                pos = pg.mouse.get_pos()

                if event.type == pg.QUIT:
                    print("You quit in the middle of the game!")
                    self.game.running = False
                    quit()
                
                # mouse click
                if event.type == pg.MOUSEBUTTONDOWN:
                    if start.isOver(pos):
                        # Play start sound
                        sound_manager.play_ui_sound('select')
                        self.game.status = START
                    elif guide.isOver(pos):
                        # Play guide sound
                        sound_manager.play_ui_sound('select')
                        self.game.status = GUIDE
                    elif about.isOver(pos):
                        # Play about sound
                        sound_manager.play_ui_sound('select')
                        self.game.status = ABOUT

                # mouse hover
                if event.type == pg.MOUSEMOTION:
                    # Check for new hover state and play sound if needed
                    if start.isOver(pos) and not start.is_highlighted:
                        sound_manager.play_ui_sound('select')
                    if guide.isOver(pos) and not guide.is_highlighted:
                        sound_manager.play_ui_sound('select')
                    if about.isOver(pos) and not about.is_highlighted:
                        sound_manager.play_ui_sound('select')

            self.game.screen.blit(start.image, (start.x, start.y))
            self.game.screen.blit(guide.image, (guide.x, guide.y))
            self.game.screen.blit(about.image, (about.x, about.y))

            pg.display.flip()