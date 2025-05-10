import os
import pygame as pg

# add the path to the folder with the button images
img_path = os.path.abspath(os.curdir) + '/images/buttons/'

class Button:
    def __init__(self, label, x, y, w, h):
        self.label = label
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image = pg.image.load(img_path+label+'a.png')
        self.is_highlighted = False

    # returns True and changes image if mouse is inside button
    # else returns False and retains original image
    def isOver(self, pos):
        # pos is the mouse position or a tuple of (x,y) coordinates
        if pos[0] > self.x and pos[0] < self.x + self.w:
            if pos[1] > self.y and pos[1] < self.y + self.h:
                self.image = pg.image.load(img_path+self.label+'b.png')
                was_highlighted = self.is_highlighted
                self.is_highlighted = True
                return True

        self.image = pg.image.load(img_path+self.label+'a.png')
        self.is_highlighted = False
        return False