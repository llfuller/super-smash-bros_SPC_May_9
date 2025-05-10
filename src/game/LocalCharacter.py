    def update_sprite_image(self):
        """Update the sprite's image based on current movement state"""
        # Animation frame counter for controlling animation speed
        self.animation_frame_counter = getattr(self, 'animation_frame_counter', 0)
        self.animation_frame_counter += 1
        
        # Only update animation every 5 frames for smoother animation
        should_update_animation = self.animation_frame_counter % 5 == 0
        
        if self.move == WALK:
            if self.direc == LEFT:
                # Only update walk_c when should_update_animation is True
                if should_update_animation:
                    max_walk = len(self.walkL) - 1
                    self.walk_c = (self.walk_c + 1) % max(1, max_walk)
                self.image = self.walkL[min(self.walk_c, len(self.walkL)-1)]
            elif self.direc == RIGHT:
                # Only update walk_c when should_update_animation is True
                if should_update_animation:
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
        
        elif self.move == DAMAGED:
            if self.direc == LEFT:
                self.image = self.damagedL
            elif self.direc == RIGHT:
                self.image = self.damagedR

        if self.health <= 0:
            self.image = self.dead_image 