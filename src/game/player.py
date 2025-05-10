'''
Player class to encapsulate player data and logic
'''

class Player:
    def __init__(self, name, character="none"):
        self.name = name
        self.character = character
        self.status = "unready"
        self.health = 100.0
        self.x_pos = 0.0
        self.y_pos = 0.0
        self.direction = "right"
        self.walk_count = 0
        self.move = "stand"
        self.sprite = None
    
    def set_position(self, x, y):
        """Set the player's position"""
        self.x_pos = float(x)
        self.y_pos = float(y)
        
        # Update sprite position if it exists
        if self.sprite:
            self.sprite.pos[0] = self.x_pos
            self.sprite.pos[1] = self.y_pos
    
    def set_character(self, character):
        """Set the player's character"""
        self.character = character
    
    def set_status(self, status):
        """Set the player's ready status"""
        self.status = status
    
    def set_direction(self, direction):
        """Set the player's facing direction"""
        self.direction = direction
        
        # Update sprite direction if it exists
        if self.sprite:
            self.sprite.direc = direction
    
    def set_move(self, move):
        """Set the player's movement state"""
        self.move = move
        
        # Update sprite movement if it exists
        if self.sprite:
            self.sprite.move = move
    
    def set_walk_count(self, count):
        """Set the player's walk animation frame count"""
        self.walk_count = int(count)
        
        # Update sprite walk count if it exists
        if self.sprite:
            self.sprite.walk_c = self.walk_count
    
    def take_damage(self, damage):
        """Reduce player health by the given damage amount"""
        self.health = max(0.0, self.health - float(damage))
        
        # Update sprite health if it exists
        if self.sprite:
            self.sprite.health = self.health
        
        return self.health
    
    def is_alive(self):
        """Check if the player is still alive"""
        return self.health > 0
    
    def is_ready(self):
        """Check if the player is ready to play"""
        return self.status == "ready"
    
    def update_from_sprite(self):
        """Update player data from the sprite"""
        if self.sprite:
            self.x_pos = self.sprite.pos[0]
            self.y_pos = self.sprite.pos[1]
            self.direction = self.sprite.direc
            self.walk_count = self.sprite.walk_c
            self.move = self.sprite.move
    
    def to_dict(self):
        """Convert player to a dictionary (for compatibility with existing code)"""
        return {
            'name': self.name,
            'character': self.character,
            'status': self.status,
            'health': str(self.health),
            'xPos': str(self.x_pos),
            'yPos': str(self.y_pos),
            'direc': self.direction,
            'walk_c': str(self.walk_count),
            'move': self.move,
            'sprite': self.sprite
        }
    
    @staticmethod
    def from_dict(player_dict):
        """Create a Player instance from a dictionary"""
        player = Player(player_dict['name'], player_dict['character'])
        player.status = player_dict['status']
        player.health = float(player_dict['health'])
        player.x_pos = float(player_dict['xPos'])
        player.y_pos = float(player_dict['yPos'])
        player.direction = player_dict['direc']
        player.walk_count = int(player_dict['walk_c'])
        player.move = player_dict['move']
        if 'sprite' in player_dict:
            player.sprite = player_dict['sprite']
        
        return player 