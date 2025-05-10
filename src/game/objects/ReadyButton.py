'''

This is similar to Button.py but when clicked - the old image stays.

'''

import os
import pygame as pg

# add the path to the folder with the button images
img_path = os.path.abspath(os.curdir) + '/images/buttons/'

class ReadyButton:
    def __init__(self, label, x, y, w, h):
        self.label = label
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image = pg.image.load(img_path+label+'a.png')
        self.clicked = False
        self.is_highlighted = False

    # returns True and changes image if mouse is inside button
    # else returns False and retains original image
    def isOver(self, pos):
        # pos is the mouse position or a tuple of (x,y) coordinates
        if pos[0] > self.x and pos[0] < self.x + self.w:
            if pos[1] > self.y and pos[1] < self.y + self.h:
                was_highlighted = self.is_highlighted
                self.is_highlighted = True
                if self.clicked:
                    self.image = pg.image.load(img_path+self.label+'a.png')
                else:
                    self.image = pg.image.load(img_path+self.label+'b.png')
                return True

        self.is_highlighted = False
        if self.clicked:
            self.image = pg.image.load(img_path+self.label+'b.png')
        else:
            self.image = pg.image.load(img_path+self.label+'a.png')
        return False

    # toggle clicked attribute
    def click(self):
        if not self.clicked:
            self.clicked = True
        else:
            self.clicked = False
    