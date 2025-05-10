import os
import pygame as pg
import math

# add the path to the folder with the other images
img_path = os.path.abspath(os.curdir) + '/images/others/'

# platform may either be a floating one or the base
class Platform(pg.sprite.Sprite):
    def __init__(self, label, x, y, w, h):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.image.load(img_path+label+'.png').convert()
        self.original_image = self.image.copy()  # Store original image for rotation
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.x = x
        self.y = y
        self.w = w 
        self.h = h
        # Store platform type for drop-through logic
        self.type = label  # 'floor' or 'platform'
        
        # Rotation properties
        self.is_rotated = False
        self.rotation_angle = 0
        self.rotated_surface = None
        self.color = (101, 67, 33)  # Default brown color for platforms
        
        # Original corner points for collision detection
        self.corners = self._calculate_corners()
        self.rotated_corners = self.corners.copy()  # Will be updated during rotation
        
        # Collision detection properties
        self.collision_poly = None  # Will store polygon for collision detection
    
    def _calculate_corners(self):
        """Calculate the corner points of the platform"""
        # Store corner points relative to center
        center_x = self.rect.centerx
        center_y = self.rect.centery
        half_width = self.rect.width / 2
        half_height = self.rect.height / 2
        
        # Top-left, top-right, bottom-right, bottom-left
        corners = [
            (center_x - half_width, center_y - half_height),  # Top-left
            (center_x + half_width, center_y - half_height),  # Top-right
            (center_x + half_width, center_y + half_height),  # Bottom-right
            (center_x - half_width, center_y + half_height)   # Bottom-left
        ]
        return corners
    
    def update(self):
        """Update the platform if needed"""
        # If the platform is rotated, we need to use the rotated surface for rendering
        if self.is_rotated and self.rotated_surface is not None:
            self.image = self.rotated_surface
        else:
            self.image = self.original_image
    
    def draw(self, surface):
        """Custom draw method used during rotation"""
        # Only blit the appropriate surface - either rotated or original
        surface.blit(self.image, self.rect)
        
        # Debug: draw collision polygon
        # if self.is_rotated and self.collision_poly:
        #     pg.draw.polygon(surface, (255, 0, 0), self.rotated_corners, 2)
    
    def update_rotation(self, angle, center_x, center_y):
        """Update the platform's rotation and collision geometry"""
        self.rotation_angle = angle
        self.is_rotated = True
        
        # Calculate the rotated corners for collision detection
        self.rotated_corners = []
        angle_rad = math.radians(angle)
        
        # Always recalculate corners from original points to avoid error accumulation
        original_corners = self._calculate_corners()
        
        for corner_x, corner_y in original_corners:
            # Calculate vector from center to corner
            rel_x = corner_x - center_x
            rel_y = corner_y - center_y
            
            # Rotate vector
            rot_x = rel_x * math.cos(angle_rad) - rel_y * math.sin(angle_rad)
            rot_y = rel_x * math.sin(angle_rad) + rel_y * math.cos(angle_rad)
            
            # Calculate new absolute position
            new_x = center_x + rot_x
            new_y = center_y + rot_y
            
            # Add to rotated corners
            self.rotated_corners.append((new_x, new_y))
        
        # Update collision polygon
        self.collision_poly = pg.Rect.clip(self.rect, pg.Rect(0, 0, 10000, 10000))
    
    def point_inside(self, x, y):
        """Check if a point is inside the rotated platform using ray casting algorithm"""
        if not self.is_rotated:
            # Fast check for non-rotated platforms
            return self.rect.collidepoint(x, y)
        
        # Ray casting algorithm for rotated platforms
        inside = False
        for i in range(len(self.rotated_corners)):
            j = (i + 1) % len(self.rotated_corners)
            p1x, p1y = self.rotated_corners[i]
            p2x, p2y = self.rotated_corners[j]
            
            # Check if point is on the same side as all edges
            if ((p1y > y) != (p2y > y)) and (x < (p2x - p1x) * (y - p1y) / (p2y - p1y) + p1x):
                inside = not inside
        
        return inside
    
    def get_rotated_top(self):
        """Get the top edge of the rotated platform"""
        if not self.is_rotated:
            return self.rect.top
        
        # Find the minimum y value among the rotated corners
        return min(corner[1] for corner in self.rotated_corners)
    
    def get_rotated_bottom(self):
        """Get the bottom edge of the rotated platform"""
        if not self.is_rotated:
            return self.rect.bottom
        
        # Find the maximum y value among the rotated corners
        return max(corner[1] for corner in self.rotated_corners)
    
    def get_rotated_left(self):
        """Get the left edge of the rotated platform"""
        if not self.is_rotated:
            return self.rect.left
        
        # Find the minimum x value among the rotated corners
        return min(corner[0] for corner in self.rotated_corners)
    
    def get_rotated_right(self):
        """Get the right edge of the rotated platform"""
        if not self.is_rotated:
            return self.rect.right
        
        # Find the maximum x value among the rotated corners
        return max(corner[0] for corner in self.rotated_corners)
    
    def collide_with_rect(self, other_rect):
        """Check if this rotated platform collides with a rectangle"""
        if not self.is_rotated:
            # Fast check for non-rotated platforms
            return self.rect.colliderect(other_rect)
        
        # Check if any corner of the rect is inside the rotated platform
        rect_corners = [
            (other_rect.left, other_rect.top),
            (other_rect.right, other_rect.top),
            (other_rect.right, other_rect.bottom),
            (other_rect.left, other_rect.bottom)
        ]
        
        for corner in rect_corners:
            if self.point_inside(*corner):
                return True
        
        # Check if any corner of the platform is inside the rect
        for corner in self.rotated_corners:
            if other_rect.collidepoint(corner):
                return True
        
        # Check for edge intersections (simplified - may miss some edge cases)
        return False