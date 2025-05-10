'''
GameState class to manage different game states
'''

from settings import INTRO, START, GUIDE, ABOUT, GAME

class GameState:
    """
    Class to manage game state transitions and handle state-specific logic
    """
    
    def __init__(self, game):
        self.game = game
        self.current_state = INTRO
    
    def change_state(self, new_state):
        """Change to a new game state"""
        self.current_state = new_state
        
        # Reset state-specific variables when changing states
        if new_state == GAME:
            self.game.winner = ''
            self.game.chat_init = False
            
        elif new_state == INTRO:
            # Reset player data when returning to main menu
            self.game.reset_player_data()
        
        return self.current_state
    
    def get_current_state(self):
        """Get the current game state"""
        return self.current_state
    
    def is_in_menu(self):
        """Check if the game is in any menu state (not in gameplay)"""
        return self.current_state in (INTRO, START, GUIDE, ABOUT)
    
    def is_in_game(self):
        """Check if the game is in the gameplay state"""
        return self.current_state == GAME
    
    def is_in_main_menu(self):
        """Check if the game is in the main menu"""
        return self.current_state == INTRO
    
    def handle_state_transition(self, event_key):
        """Handle state transitions based on key presses"""
        
        # Only certain transitions are allowed depending on current state
        if self.current_state == GAME and self.game.showed_end:
            # After game ends
            if event_key == 'r':
                # Restart game
                self.game.restartGame()
                return True
                
            elif event_key == 'm':
                # Return to main menu
                self.change_state(INTRO)
                return True
                
            elif event_key == 'q':
                # Quit game
                return False  # Game loop should stop
        
        # Default - continue game loop
        return True 