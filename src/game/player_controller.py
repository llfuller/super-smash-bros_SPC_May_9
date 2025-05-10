'''
Player Controller for Super Smash Bros

This module implements player controllers that use the unified intent-based input system 
to convert player intents into character actions.
'''

import pygame as pg
from settings import LEFT, RIGHT, WALK, STAND, GAME_WIDTH
from input_handler import input_handler, INTENTS

class PlayerController:
    """
    Controller class for a player character that translates input intents
    to character behavior regardless of input source.
    """
    def __init__(self, player_name, player_data, sprite=None):
        self.player_name = player_name
        self.player_data = player_data
        self.sprite = sprite
        
    def set_sprite(self, sprite):
        """Update the sprite reference"""
        self.sprite = sprite
    
    def check_attack_key(self, event, game):
        """
        Check for attack intents and apply them to the character.
        This method doesn't need the event parameter anymore, but kept for compatibility.
        
        Args:
            event: Pygame event (not used, kept for compatibility)
            game: The game object
            
        Returns:
            bool: True if an attack was performed, False otherwise
        """
        if not self.sprite or self.player_name not in game.players:
            return False
        
        # Check for weak attack intent
        if input_handler.is_intent_just_activated(self.player_name, INTENTS['WEAK_ATTACK']):
            if self.sprite.can_move():
                self.sprite.weakAttack()
                print(f"DEBUG: {self.player_name} performing weak attack via intent")
                return True
        
        # Check for heavy attack intent
        elif input_handler.is_intent_just_activated(self.player_name, INTENTS['HEAVY_ATTACK']):
            if self.sprite.can_move():
                self.sprite.heavyAttack()
                print(f"DEBUG: {self.player_name} performing heavy attack via intent")
                return True
        
        return False
    
    def handle_movement(self, keys, game):
        """
        Process movement intents and apply them to the character
        
        Args:
            keys: Pygame key state (ignored in favor of intent system)
            game: The game object
        """
        # Debug print for every 120 frames to verify this method is being called
        if hasattr(game, 'current_frame') and game.current_frame % 120 == 0 and game.controller_debug:
            print(f"DEBUG: handle_movement called for {self.player_name} (frame {game.current_frame})")
        
        if not self.sprite or self.player_name not in game.players:
            return
        
        # Get player data and sprite
        player_data = game.players[self.player_name]
        sprite = self.sprite
        
        # Don't process movement if player is dead or game is not in play
        if sprite.damage_percent >= 999 or not game.playing:
            return
        
        # Ensure sprite has correct attributes
        if not hasattr(sprite, 'vel'):
            sprite.vel = pg.math.Vector2(0, 0)
        if not hasattr(sprite, 'acc'):
            sprite.acc = pg.math.Vector2(0, 0)
        
        # Reset movement flags
        sprite.moving_left = False
        sprite.moving_right = False
        
        # Debug output to periodically check intent status
        if hasattr(game, 'current_frame') and game.current_frame % 60 == 0 and game.controller_debug:
            move_left = input_handler.get_intent(self.player_name, INTENTS['MOVE_LEFT'])
            move_right = input_handler.get_intent(self.player_name, INTENTS['MOVE_RIGHT'])
            move_up = input_handler.get_intent(self.player_name, INTENTS['MOVE_UP'])
            move_down = input_handler.get_intent(self.player_name, INTENTS['MOVE_DOWN'])
            print(f"{self.player_name} intents: LEFT={move_left}, RIGHT={move_right}, UP={move_up}, DOWN={move_down}")
        
        # Process drop-through and fast fall (MOVE_DOWN intent)
        if input_handler.get_intent(self.player_name, INTENTS['MOVE_DOWN']):
            # Set flag on sprite for dropping through platforms
            sprite.drop_through = True
            
            # Check for fast fall (only in air and after apex of jump)
            if sprite.in_air and sprite.vel.y > 0:
                sprite.is_fast_falling = True
        else:
            # Clear the flag when input is released
            sprite.drop_through = False
            sprite.is_fast_falling = False
        
        # Process jump (MOVE_UP intent)
        if input_handler.get_intent(self.player_name, INTENTS['MOVE_UP']) and not sprite.is_jumping and not sprite.in_air and not sprite.animation_locked:
            sprite.jump()
        
        # Check if character can be controlled (not in middle of animation)
        if not hasattr(sprite, 'can_move') or not sprite.can_move():
            # Still update player data from sprite to ensure synchronized state
            self._update_player_data_from_sprite(player_data, sprite)
            return
        
        # Track if we're moving horizontally this frame
        is_moving_horizontally = False
        
        # Get analog stick value for horizontal movement
        x_axis = input_handler.get_analog_value(self.player_name, 'horizontal')
        
        # Process horizontal movement - Move left
        # CRITICAL: Test for intent first, THEN check analog value only for magnitude
        if input_handler.get_intent(self.player_name, INTENTS['MOVE_LEFT']) and float(player_data['xPos']) > 40:
            is_moving_horizontally = True
            
            # Set direction for animations
            sprite.direc = LEFT
            
            if sprite.in_air:
                # Air control is more limited
                sprite.vel.x = max(sprite.vel.x - 0.2, -2)  # Slower horizontal air movement
            else:
                # Ground movement is faster - use analog value for speed if available
                if abs(x_axis) > 0.3:  # Only use analog value if significant movement detected
                    sprite.vel.x = -3 * min(1.0, abs(x_axis))  # Scale speed by stick intensity
                else:
                    sprite.vel.x = -3  # Default speed for non-analog input
                sprite.move = WALK
            
            # Update flags for animation and physics
            sprite.moving_left = True
            sprite.moving_right = False
            
            # Update player data
            player_data['direc'] = LEFT
            if not sprite.in_air:
                player_data['move'] = WALK
            
            player_data['walk_c'] = str(sprite.walk_c)
        
        # Move right - same pattern as left movement
        elif input_handler.get_intent(self.player_name, INTENTS['MOVE_RIGHT']) and float(player_data['xPos']) < GAME_WIDTH-40:
            is_moving_horizontally = True
            
            # Set direction for animations
            sprite.direc = RIGHT
            
            if sprite.in_air:
                # Air control is more limited
                sprite.vel.x = min(sprite.vel.x + 0.2, 2)  # Slower horizontal air movement
            else:
                # Ground movement is faster - use analog value for speed if available
                if abs(x_axis) > 0.3:  # Only use analog value if significant movement detected
                    sprite.vel.x = 3 * min(1.0, abs(x_axis))  # Scale speed by stick intensity
                else:
                    sprite.vel.x = 3  # Default speed for non-analog input
                sprite.move = WALK
            
            # Update flags for animation and physics
            sprite.moving_right = True
            sprite.moving_left = False
            
            # Update player data
            player_data['direc'] = RIGHT
            if not sprite.in_air:
                player_data['move'] = WALK
            
            player_data['walk_c'] = str(sprite.walk_c)
        else:
            # No horizontal input, slow down (apply friction)
            sprite.vel.x *= 0.8  # Apply friction to gradually stop
            if abs(sprite.vel.x) < 0.1:
                sprite.vel.x = 0  # Stop completely when very slow
        
        # If not moving horizontally and not in air, reset to standing
        if not is_moving_horizontally and not sprite.in_air:
            sprite.walk_c = 0
            
            # Only transition to STAND if not in another animation
            if sprite.move == WALK:
                sprite.move = STAND
                player_data['move'] = STAND
                
            player_data['walk_c'] = '0'
        
        # Update player data from sprite position
        self._update_player_data_from_sprite(player_data, sprite)
    
    def _update_player_data_from_sprite(self, player_data, sprite):
        """
        Update player data dictionary from sprite state
        
        Args:
            player_data: Player data dictionary
            sprite: Player sprite
        """
        player_data['xPos'] = str(sprite.pos.x)
        player_data['yPos'] = str(sprite.pos.y)
        player_data['direc'] = sprite.direc
        player_data['walk_c'] = str(sprite.walk_c)
        player_data['move'] = sprite.move 

# Add test code that runs when this file is executed directly
if __name__ == "__main__":
    print("PlayerController module - not meant to be run directly.")
    print("To start the game, run LocalGameLauncher.py instead.")
    print("\nRunning controller test utility...")
    
    try:
        # Try to import and run the controller test utility
        import os
        import sys
        
        # Get the current directory and add it to path if needed
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
            
        print(f"Looking for controller_test.py in: {current_dir}")
        
        # Check if controller_test.py exists
        test_path = os.path.join(current_dir, "controller_test.py")
        if os.path.exists(test_path):
            print(f"Found controller_test.py, launching...")
            
            # Use exec to run the controller test
            with open(test_path, 'r') as f:
                exec(f.read())
        else:
            print("controller_test.py not found.")
            
            # Create a very simple controller test
            print("Creating simple controller test...")
            pg.init()
            pg.joystick.init()
            
            # Check for controllers
            joystick_count = pg.joystick.get_count()
            print(f"Found {joystick_count} controllers")
            
            if joystick_count > 0:
                # Initialize the first joystick
                joystick = pg.joystick.Joystick(0)
                joystick.init()
                
                # Show controller info
                print(f"Controller name: {joystick.get_name()}")
                print(f"Axes: {joystick.get_numaxes()}")
                print(f"Buttons: {joystick.get_numbuttons()}")
                print(f"Hats: {joystick.get_numhats()}")
                
                # Create a window to visualize controller input
                screen = pg.display.set_mode((640, 480))
                pg.display.set_caption("Controller Test")
                
                # Main loop for controller test
                running = True
                clock = pg.time.Clock()
                font = pg.font.Font(None, 36)
                
                while running:
                    # Handle events
                    for event in pg.event.get():
                        if event.type == pg.QUIT:
                            running = False
                        elif event.type == pg.KEYDOWN:
                            if event.key == pg.K_ESCAPE:
                                running = False
                    
                    # Clear screen
                    screen.fill((0, 0, 0))
                    
                    # Draw controller info
                    screen.blit(font.render(f"Controller: {joystick.get_name()}", True, (255, 255, 255)), (20, 20))
                    
                    # Draw axes
                    y_pos = 70
                    for i in range(joystick.get_numaxes()):
                        axis_val = joystick.get_axis(i)
                        bar_width = int((axis_val + 1) * 150)
                        pg.draw.rect(screen, (0, 255, 0), (200, y_pos, bar_width, 20))
                        screen.blit(font.render(f"Axis {i}: {axis_val:.2f}", True, (255, 255, 255)), (20, y_pos))
                        y_pos += 30
                    
                    # Draw buttons
                    y_pos += 20
                    for i in range(joystick.get_numbuttons()):
                        button_val = joystick.get_button(i)
                        button_color = (255, 0, 0) if button_val else (70, 70, 70)
                        pg.draw.circle(screen, button_color, (30, y_pos), 10)
                        screen.blit(font.render(f"Button {i}: {button_val}", True, (255, 255, 255)), (50, y_pos - 10))
                        y_pos += 30
                    
                    # Draw hats
                    y_pos += 20
                    for i in range(joystick.get_numhats()):
                        hat_val = joystick.get_hat(i)
                        screen.blit(font.render(f"Hat {i}: {hat_val}", True, (255, 255, 255)), (20, y_pos))
                        y_pos += 30
                    
                    # Update screen
                    pg.display.flip()
                    clock.tick(30)
                
                # Clean up
                pg.quit()
            else:
                print("No controller detected. Connect a controller and try again.")
    except Exception as e:
        print(f"Error running controller test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTo start the game, run LocalGameLauncher.py instead.") 