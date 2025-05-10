import sys
import pygame as pg

# move up one directory to be able to import the settings and images
sys.path.append("..")
from settings import *
from images import *

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
        
        # Stats
        self.health = health
        self.weak = weak_damage
        self.heavy = heavy_damage
        self.acce = acceleration
        
        # Position and movement
        self.pos = pos
        self.direc = direc
        self.walk_c = walk_c if walk_c is not None else 0
        self.move = move
        
        # Graphics
        self.walkR = images_walk_r
        self.walkL = images_walk_l
        self.standR = image_stand_r
        self.standL = image_stand_l
        self.weakR = image_weak_r
        self.weakL = image_weak_l
        self.heavyR = image_heavy_r
        self.heavyL = image_heavy_l
        self.damagedR = image_damaged_r
        self.damagedL = image_damaged_l
        self.dead_image = image_dead
        
        # Physics
        self.game = game
        self.image = self.standR
        self.rect = self.image.get_rect()
        self.rect.center = (GAME_WIDTH / 2, HEIGHT / 2)
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        
        # Input flag - whether this character should be controlled by keyboard
        self.process_input = False
        
    def jump(self):
        self.rect.x += 1
        collision = pg.sprite.spritecollide(self, self.game.platforms, False)
        self.rect.x -= 1
        if collision:
            self.vel.y = -VEL

    def weakAttack(self):
        if self.health > 0 and not self.game.chatting:
            collided_enemies = pg.sprite.spritecollide(self, self.game.enemy_sprites, False)
            for enemy in collided_enemies:
                enemy.health -= self.weak
                enemy.move = DAMAGED
                self.game.attackPlayer(enemy.name, self.weak, DAMAGED)
                if enemy.health < 0:
                    enemy.health = 0

    def heavyAttack(self):
        if self.health > 0 and not self.game.chatting:
            collided_enemies = pg.sprite.spritecollide(self, self.game.enemy_sprites, False)
            for enemy in collided_enemies:
                enemy.health -= self.heavy
                enemy.move = DAMAGED
                self.game.attackPlayer(enemy.name, self.heavy, DAMAGED)
                if enemy.health < 0:
                    enemy.health = 0
    
    def update(self):
        self.acc = vec(0, 0.5)
        
        # Update physics
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        # Update sprite image based on current state
        self.update_sprite_image()
        
        # Update collision rectangle
        self.rect = self.image.get_rect()
        self.rect.midbottom = self.pos

        # Handle platform collisions
        if self.vel.y > 0:
            collision = pg.sprite.spritecollide(self, self.game.platforms, False)
            if collision:
                self.pos[1] = collision[0].rect.top + 1
                self.vel[1] = 0

    def update_sprite_image(self):
        """Update the sprite's image based on current movement state"""
        if self.move == WALK:
            if self.direc == LEFT:
                self.image = self.walkL[min(self.walk_c, len(self.walkL)-1)]
            elif self.direc == RIGHT:
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
        
        elif self.move == DAMAGED:
            if self.direc == LEFT:
                self.image = self.damagedL
            elif self.direc == RIGHT:
                self.image = self.damagedR

        if self.health <= 0:
            self.image = self.dead_image

# Create local character versions of each character

# Mario
class LocalMario(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        walkR = [maS1, maM1, maM2, maM3, maM4, maM5, maM6, maM7]
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

# Luigi
class LocalLuigi(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        walkR = [luS1, luM1, luM2, luM3, luM4, luM5, luM6, luM7]
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

# Yoshi
class LocalYoshi(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        walkR = [yoS1, yoM1, yoM2, yoM3, yoM4, yoM5, yoM6, yoM7]
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
        walkR = [poS1, poM1, poM2, poM3, poM4, poM5, poM6, poM7]
        walkL = [pg.transform.flip(image, True, False) for image in walkR]
        standR = poS1
        standL = pg.transform.flip(standR, True, False)
        weakR = poW1
        weakL = pg.transform.flip(weakR, True, False)
        heavyR = poH1
        heavyL = pg.transform.flip(heavyR, True, False)
        damagedR = poD1
        damagedL = pg.transform.flip(damagedR, True, False)
        
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
        walkR = [naS1, naM1, naM2, naM3, naM4, naM5, naM6, naM7]
        walkL = [pg.transform.flip(image, True, False) for image in walkR]
        standR = naS1
        standL = pg.transform.flip(standR, True, False)
        weakR = naW1
        weakL = pg.transform.flip(weakR, True, False)
        heavyR = naH1
        heavyL = pg.transform.flip(heavyR, True, False)
        damagedR = naD1
        damagedL = pg.transform.flip(damagedR, True, False)
        
        super().__init__(
            game, name, status, health, pos, direc, walk_c, move,
            walkR, walkL, standR, standL, 
            weakR, weakL, heavyR, heavyL,
            damagedR, damagedL, dead,
            5.7, 11, 0.22  # weak damage, heavy damage, acceleration
        )

# Link
class LocalLink(LocalCharacter):
    def __init__(self, game, name, status, health, pos, direc, walk_c, move):
        walkR = [liS1, liM1, liM2, liM3, liM4, liM5, liM6, liM7]
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