'''
Unified Input Handler for Super Smash Bros

This module implements a unified input handling system that processes inputs
from both keyboard and controllers, mapping them to player intents regardless of input source.
'''

import pygame as pg
from config import PRO_CONTROLLER, DEFAULT_SETTINGS

# Define player intents (actions)
INTENTS = {
    # Movement intents
    'MOVE_LEFT': 'move_left',
    'MOVE_RIGHT': 'move_right',
    'MOVE_UP': 'move_up',       # Jump
    'MOVE_DOWN': 'move_down',   # Fast-fall or platform drop-through
    
    # Attack intents
    'WEAK_ATTACK': 'weak_attack',
    'HEAVY_ATTACK': 'heavy_attack',
    
    # Defensive intent
    'SHIELD': 'shield',         # Create a shield to block damage
    
    # Game control intents
    'MENU': 'menu',
    'RESTART': 'restart',
    'QUIT': 'quit',
}

class InputHandler:
    """
    Central input handler that processes inputs from all sources
    and maps them to player intents regardless of input device.
    """
    def __init__(self):
        # Input device status
        self.keyboard_enabled = True
        self.controller_enabled = False
        self.controller_priority = True  # When True, controller input takes precedence over keyboard
        self.controllers = {}  # Maps player names to controller objects
        
        # Player intent state
        self.player_intents = {}  # Maps player names to their current intents
        self.prev_player_intents = {}  # Previous frame intents for edge detection
        
        # Analog input values (for analog stick values)
        self.analog_values = {}  # Maps player_name+axis to values
        
        # Jump button tracking for short hop detection
        self.jump_press_frame = {}  # Tracks when jump button was pressed for each player
        self.jump_release_frame = {}  # Tracks when jump button was released
        self.current_frame = 0  # Current frame count for timing
        
        # Controller settings
        self.deadzone = DEFAULT_SETTINGS['controller_deadzone']
        
        # Debug mode
        self.debug = False
    
    def add_player(self, player_name, is_player_one=False):
        """
        Add a player to the input handler
        
        Args:
            player_name: Name of the player
            is_player_one: True if this is player one (using controller)
        """
        # Initialize intent state dictionaries for this player
        self.player_intents[player_name] = {intent: False for intent in INTENTS.values()}
        self.prev_player_intents[player_name] = {intent: False for intent in INTENTS.values()}
        
        # Initialize analog values for this player
        self.analog_values[f"{player_name}_horizontal"] = 0.0
        self.analog_values[f"{player_name}_vertical"] = 0.0
        
        # If this is player one and controllers are available, try to use controller
        if is_player_one and self.controller_enabled and pg.joystick.get_count() > 0:
            print(f"Initializing controller for {player_name} (Player One)")
            self.init_controller(player_name, 0)
    
    def init_controller(self, player_name, controller_id=0):
        """Initialize controller for a specific player"""
        if not pg.joystick.get_init():
            pg.joystick.init()
        
        # Check if controller is available
        if pg.joystick.get_count() > controller_id:
            try:
                joystick = pg.joystick.Joystick(controller_id)
                joystick.init()
                controller_name = joystick.get_name()
                
                print(f"Initializing controller: {controller_name}")
                print(f"Number of axes: {joystick.get_numaxes()}")
                print(f"Number of buttons: {joystick.get_numbuttons()}")
                print(f"Number of hats: {joystick.get_numhats()}")
                
                # Create a controller object
                controller = {
                    'joystick': joystick,
                    'name': controller_name,
                    'id': controller_id,
                    'mapping': self._get_mapping_for_controller(controller_name),
                    'connected': True
                }
                
                # Print the button mapping that was selected
                print(f"Using button mapping: {controller['mapping']}")
                
                # Store controller for this player
                self.controllers[player_name] = controller
                self.controller_enabled = True
                
                print(f"Controller '{controller_name}' initialized for {player_name}")
                return True
            except Exception as e:
                print(f"Failed to initialize controller: {e}")
                # Get more detailed error information
                import traceback
                traceback.print_exc()
                return False
        else:
            print(f"No controller found for {player_name}: {pg.joystick.get_count()} controllers available")
            return False
    
    def _get_mapping_for_controller(self, controller_name):
        """Determine button mapping based on controller type"""
        controller_name_lower = controller_name.lower()
        print(f"Determining mapping for controller: {controller_name}")
        
        # Nintendo Switch Pro Controller - check multiple possible names
        if ("switch" in controller_name_lower and "pro" in controller_name_lower) or \
           "pro controller" in controller_name_lower or \
           "nintendo" in controller_name_lower:
            print("Detected as Nintendo Switch Pro Controller")
            return {
                INTENTS['WEAK_ATTACK']: PRO_CONTROLLER['y_button'],    # Y button (Right button) - Weak attack
                INTENTS['HEAVY_ATTACK']: PRO_CONTROLLER['x_button'],   # X button (Bottom button) - Strong attack
                INTENTS['MENU']: PRO_CONTROLLER['minus'],              # Minus button
                INTENTS['RESTART']: PRO_CONTROLLER['plus'],            # Plus button
                INTENTS['QUIT']: PRO_CONTROLLER['home'],               # Home button
                # B and A buttons for jump are handled in _process_controller_state
                # Movement is handled through stick and hat
            }
        elif "xbox" in controller_name_lower:
            # Xbox controller
            print("Detected as Xbox controller")
            return {
                INTENTS['WEAK_ATTACK']: 0,    # A button
                INTENTS['HEAVY_ATTACK']: 3,   # Y button
                INTENTS['MENU']: 6,           # Back/View button
                INTENTS['RESTART']: 7,        # Start/Menu button
                INTENTS['QUIT']: 8,           # Xbox button
            }
        elif "playstation" in controller_name_lower or "ps4" in controller_name_lower or "ps5" in controller_name_lower:
            # PlayStation controller
            print("Detected as PlayStation controller")
            return {
                INTENTS['WEAK_ATTACK']: 0,    # Cross/X button
                INTENTS['HEAVY_ATTACK']: 3,   # Triangle/Y button
                INTENTS['MENU']: 8,           # Share/Create button
                INTENTS['RESTART']: 9,        # Options button
                INTENTS['QUIT']: 10,          # PS button
            }
        else:
            # Generic controller - use default mapping
            print("Detected as generic controller - using default mapping")
            return {
                INTENTS['WEAK_ATTACK']: 0,    # Usually primary action button
                INTENTS['HEAVY_ATTACK']: 1,   # Usually secondary action button
                INTENTS['MENU']: 6,           # Option/Menu button
                INTENTS['RESTART']: 7,        # Start button
                INTENTS['QUIT']: 10,          # Home button
            }
    
    def update(self, events):
        """
        Process all inputs and update player intent states
        
        Args:
            events: List of pygame events
        """
        # Increment the current frame
        self.current_frame += 1
        
        # Store previous frame's intents first for jump tracking
        prev_intents = {}
        for player_name in self.player_intents:
            prev_intents[player_name] = self.player_intents[player_name].copy()
        
        # Collect ALL input states at the same time to ensure consistent timing
        keys_pressed = pg.key.get_pressed()
        
        # Collect controller state information upfront for all connected controllers
        controller_states = {}
        if self.controller_enabled:
            for player_name, controller in self.controllers.items():
                if controller['connected']:
                    try:
                        joystick = controller['joystick']
                        
                        # Create a snapshot of all controller data
                        state = {
                            'buttons': [joystick.get_button(i) for i in range(joystick.get_numbuttons())],
                            'axes': [joystick.get_axis(i) for i in range(joystick.get_numaxes())],
                            'hats': [joystick.get_hat(i) for i in range(joystick.get_numhats())]
                        }
                        controller_states[player_name] = state
                        
                        # Store axes values directly in analog_values
                        if joystick.get_numaxes() > 0:
                            x_axis = state['axes'][min(PRO_CONTROLLER['l_stick_x'], joystick.get_numaxes()-1)]
                            self.analog_values[f"{player_name}_horizontal"] = x_axis
                        
                        if joystick.get_numaxes() > 1:
                            y_axis = state['axes'][min(PRO_CONTROLLER['l_stick_y'], joystick.get_numaxes()-1)]
                            self.analog_values[f"{player_name}_vertical"] = y_axis
                            
                    except Exception as e:
                        print(f"Error reading controller state for {player_name}: {e}")
        
        # Store previous intent states for edge detection
        for player_name in self.player_intents:
            self.prev_player_intents[player_name] = prev_intents[player_name]
            # Reset all intents to False
            for intent in INTENTS.values():
                self.player_intents[player_name][intent] = False
        
        # Process controller inputs FIRST (they have priority)
        if self.controller_enabled:
            for player_name, controller in self.controllers.items():
                if controller['connected'] and player_name in controller_states:
                    # Process controller input using the snapshot we already took
                    self._process_controller_state(player_name, controller, controller_states[player_name])
                    
                    # Debug output for controller state
                    if self.debug and hasattr(self, 'debug_frame_counter') and self.debug_frame_counter % 60 == 0:
                        state = controller_states[player_name]
                        print(f"\nController snapshot for {player_name}:")
                        
                        # Print axis values
                        active_axes = []
                        for i, value in enumerate(state['axes'][:4]):  # Show first 4 axes
                            if abs(value) > 0.1:  # Only show active axes
                                active_axes.append(f"{i}:{value:.2f}")
                        if active_axes:
                            print(f"  Active axes: {', '.join(active_axes)}")
                        
                        # Print button states
                        active_buttons = []
                        for i, pressed in enumerate(state['buttons'][:12]):  # Show first 12 buttons
                            if pressed:
                                active_buttons.append(str(i))
                        if active_buttons:
                            print(f"  Active buttons: {', '.join(active_buttons)}")
                        
                        # Print hat states
                        active_hats = []
                        for i, value in enumerate(state['hats']):
                            if value != (0, 0):
                                active_hats.append(f"{i}:{value}")
                        if active_hats:
                            print(f"  Active hats: {', '.join(active_hats)}")
        
        # Process keyboard inputs AFTER controllers (they only apply if no controller for that player)
        # Only use keyboard for players that don't have a controller connected
        if self.keyboard_enabled:
            player_names = list(self.player_intents.keys())
            for i, player_name in enumerate(player_names):
                # Skip if this player already has controller input
                if player_name in self.controllers and self.controllers[player_name]['connected']:
                    # Log that we're skipping keyboard for this player
                    if self.debug and hasattr(self, 'debug_frame_counter') and self.debug_frame_counter % 300 == 0:
                        print(f"Skipping keyboard input for {player_name} - controller is primary input")
                    continue
                
                # Process keyboard for this player based on index (player 1 = arrows, player 2 = WASD)
                self._process_keyboard_for_player(player_name, keys_pressed, i)
        
        # Process connection/disconnection events
        for event in events:
            if event.type == pg.JOYDEVICEADDED:
                print(f"Controller connected: {event.device_index}")
                self._reinitialize_controllers()
            
            elif event.type == pg.JOYDEVICEREMOVED:
                print(f"Controller disconnected: {event.device_index}")
                for player_name, controller in self.controllers.items():
                    if controller['id'] == event.device_index:
                        controller['connected'] = False
                        print(f"Controller for {player_name} disconnected")
                self._reinitialize_controllers()
        
        # Update debug counter
        if not hasattr(self, 'debug_frame_counter'):
            self.debug_frame_counter = 0
        self.debug_frame_counter += 1
        
        # Track jump button press and release for short hop detection
        self._update_jump_tracking()
        
        # Log current jump tracking state occasionally for debugging
        if self.debug_frame_counter % 60 == 0:
            for player_name in self.player_intents:
                press_frame = self.jump_press_frame.get(player_name, 0)
                release_frame = self.jump_release_frame.get(player_name, 0)
                if press_frame > 0:
                    print(f"DEBUG: {player_name} jump tracking state - press_frame: {press_frame}, held for {self.current_frame - press_frame} frames")
        
        # Debug output
        if self.debug and self.debug_frame_counter % 60 == 0:
            for player_name, intents in self.player_intents.items():
                active_intents = [intent for intent, active in intents.items() if active]
                if active_intents:
                    print(f"{player_name} intents: {', '.join(active_intents)}")
    
    def _process_keyboard_for_player(self, player_name, keys_pressed, player_index):
        """Process keyboard inputs for a specific player"""
        # Get player intents
        intents = self.player_intents[player_name]
        
        # Default key assignments
        # Player 1 uses arrow keys + Left Alt/Shift/Ctrl
        # Player 2 uses WASD + E/Q/R keys
        
        # Create a list of keys to check based on player index
        keys_to_check = [
            # Player 1 keys (arrows + alt/shift/ctrl)
            {
                'left': pg.K_LEFT,
                'right': pg.K_RIGHT,
                'up': pg.K_UP,              # Jump
                'down': pg.K_DOWN,
                'weak_attack': pg.K_z,
                'heavy_attack': pg.K_x,
                'shield': pg.K_LSHIFT,
                'menu': pg.K_ESCAPE,
                'restart': pg.K_r,
                'quit': pg.K_q
            },
            # Player 2 keys (WASD + E/Q/R)
            {
                'left': pg.K_a,
                'right': pg.K_d,
                'up': pg.K_w,               # Jump
                'down': pg.K_s,
                'weak_attack': pg.K_g,
                'heavy_attack': pg.K_h,
                'shield': pg.K_e,
                'menu': pg.K_ESCAPE,
                'restart': pg.K_r,
                'quit': pg.K_q
            }
        ]
        
        # Get key assignments for this player
        keys = keys_to_check[min(player_index, len(keys_to_check) - 1)]
        
        # Process movement intents
        intents[INTENTS['MOVE_LEFT']] = keys_pressed[keys['left']]
        intents[INTENTS['MOVE_RIGHT']] = keys_pressed[keys['right']]
        intents[INTENTS['MOVE_UP']] = keys_pressed[keys['up']]
        intents[INTENTS['MOVE_DOWN']] = keys_pressed[keys['down']]
        
        # Process attack intents
        intents[INTENTS['WEAK_ATTACK']] = keys_pressed[keys['weak_attack']]
        intents[INTENTS['HEAVY_ATTACK']] = keys_pressed[keys['heavy_attack']]
        
        # Process shield intent
        intents[INTENTS['SHIELD']] = keys_pressed[keys['shield']]
        
        # Process game control intents
        intents[INTENTS['MENU']] = keys_pressed[keys['menu']]
        intents[INTENTS['RESTART']] = keys_pressed[keys['restart']]
        intents[INTENTS['QUIT']] = keys_pressed[keys['quit']]
    
    def _process_keyboard(self, keys_pressed):
        """
        DEPRECATED: Use _process_keyboard_for_player instead
        This method is kept for backwards compatibility.
        
        Process keyboard inputs and map them to player intents for all players
        
        Args:
            keys_pressed: Pygame key state dictionary
        """
        # Map keyboard inputs to each player in order
        player_names = list(self.player_intents.keys())
        for i, player_name in enumerate(player_names):
            # Only process keyboard for players without connected controllers
            if player_name not in self.controllers or not self.controllers[player_name]['connected']:
                self._process_keyboard_for_player(player_name, keys_pressed, i)
    
    def _process_controller_state(self, player_name, controller, state):
        """
        Process controller inputs from a snapshot of controller state
        
        Args:
            player_name: Name of the player
            controller: Controller object
            state: Snapshot of controller state with buttons, axes, and hats
        """
        try:
            mapping = controller['mapping']
            intents = self.player_intents[player_name]
            
            # Process button inputs based on mapping
            for intent, button in mapping.items():
                if button is not None and button < len(state['buttons']) and state['buttons'][button]:
                    intents[intent] = True
                    if self.debug and self.debug_frame_counter % 30 == 0:
                        print(f"{player_name} button {button} -> {intent}")
            
            # Check for B button to work as jump (Switch Pro Controller)
            b_button = min(PRO_CONTROLLER['b_button'], len(state['buttons'])-1)
            if b_button >= 0 and state['buttons'][b_button]:
                intents[INTENTS['MOVE_UP']] = True
                if self.debug and self.debug_frame_counter % 30 == 0:
                    print(f"{player_name} B button ({b_button}) -> MOVE_UP (jump)")
            
            # A button as jump (Switch Pro Controller)
            a_button = min(PRO_CONTROLLER['a_button'], len(state['buttons'])-1)
            if a_button >= 0 and state['buttons'][a_button]:
                intents[INTENTS['MOVE_UP']] = True
                if self.debug and self.debug_frame_counter % 30 == 0:
                    print(f"{player_name} A button ({a_button}) -> MOVE_UP (jump)")
            
            # Y button as weak attack
            y_button = min(PRO_CONTROLLER['y_button'], len(state['buttons'])-1)
            if y_button >= 0 and state['buttons'][y_button]:
                intents[INTENTS['WEAK_ATTACK']] = True
                if self.debug and self.debug_frame_counter % 30 == 0:
                    print(f"{player_name} Y button ({y_button}) -> WEAK_ATTACK")
                    
            # X button as strong attack
            x_button = min(PRO_CONTROLLER['x_button'], len(state['buttons'])-1)
            if x_button >= 0 and state['buttons'][x_button]:
                intents[INTENTS['HEAVY_ATTACK']] = True
                if self.debug and self.debug_frame_counter % 30 == 0:
                    print(f"{player_name} X button ({x_button}) -> HEAVY_ATTACK")
            
            # Debug all button states to find which ones are pressed
            if self.debug and self.debug_frame_counter % 10 == 0:
                # Print active buttons for debugging
                active_buttons = []
                for i, pressed in enumerate(state['buttons']):
                    if pressed:
                        active_buttons.append(str(i))
                if active_buttons:
                    print(f"DEBUG: {player_name} active buttons: [{', '.join(active_buttons)}]")

            # Check the main shield buttons (L, R, ZL, ZR)
            shield_active = False
            if (PRO_CONTROLLER['l_button'] < len(state['buttons']) and state['buttons'][PRO_CONTROLLER['l_button']]):
                shield_active = True
                if self.debug:
                    print(f"DEBUG: {player_name} L button ({PRO_CONTROLLER['l_button']}) pressed for shield")
            elif (PRO_CONTROLLER['r_button'] < len(state['buttons']) and state['buttons'][PRO_CONTROLLER['r_button']]):
                shield_active = True
                if self.debug:
                    print(f"DEBUG: {player_name} R button ({PRO_CONTROLLER['r_button']}) pressed for shield")
            elif (PRO_CONTROLLER['zl_button'] < len(state['buttons']) and state['buttons'][PRO_CONTROLLER['zl_button']]):
                shield_active = True
                if self.debug:
                    print(f"DEBUG: {player_name} ZL button ({PRO_CONTROLLER['zl_button']}) pressed for shield")
            elif (PRO_CONTROLLER['zr_button'] < len(state['buttons']) and state['buttons'][PRO_CONTROLLER['zr_button']]):
                shield_active = True
                if self.debug:
                    print(f"DEBUG: {player_name} ZR button ({PRO_CONTROLLER['zr_button']}) pressed for shield")

            # If that didn't work, try the generic shield_buttons array as fallback
            if not shield_active and 'shield_buttons' in PRO_CONTROLLER:
                for btn_idx in PRO_CONTROLLER['shield_buttons']:
                    if btn_idx < len(state['buttons']) and state['buttons'][btn_idx]:
                        shield_active = True
                        if self.debug:
                            print(f"DEBUG: {player_name} shield button {btn_idx} pressed via fallback array")
                        break
            
            # Set the shield intent if any shield button is active
            if shield_active:
                intents[INTENTS['SHIELD']] = True
                # Always print shield activation in debug mode (regardless of frame)
                if self.debug:
                    print(f"DEBUG: {player_name} SHIELD intent activated - shield button pressed")
            
            # Get analog stick values
            x_axis = 0.0
            y_axis = 0.0
            
            if state['axes']:
                try:
                    # Try configured axes first
                    l_stick_x = min(PRO_CONTROLLER['l_stick_x'], len(state['axes']) - 1)
                    l_stick_y = min(PRO_CONTROLLER['l_stick_y'], len(state['axes']) - 1)
                    
                    x_axis = state['axes'][l_stick_x]
                    y_axis = state['axes'][l_stick_y]
                except Exception as e:
                    # Fall back to default axes if there was an issue
                    print(f"Error accessing specified axes: {e}, using defaults")
                    if len(state['axes']) > 0:
                        x_axis = state['axes'][0]  # Most controllers use 0 for left stick X
                    if len(state['axes']) > 1:
                        y_axis = state['axes'][1]  # Most controllers use 1 for left stick Y
            
            # Apply deadzone
            if abs(x_axis) < self.deadzone:
                x_axis = 0
            if abs(y_axis) < self.deadzone:
                y_axis = 0
            
            # Check for D-pad input from hat
            hat_input = (0, 0)
            if state['hats']:
                hat_input = state['hats'][0]  # D-pad is typically hat 0
                if self.debug and hat_input != (0, 0) and self.debug_frame_counter % 30 == 0:
                    print(f"{player_name} D-pad: {hat_input}")
            
            # Map analog and hat inputs to movement intents
            # Note: For stick, up is negative Y, down is positive Y
            if hat_input[1] == 1 or y_axis < -0.5:  # Up
                intents[INTENTS['MOVE_UP']] = True
                if self.debug and self.debug_frame_counter % 30 == 0:
                    print(f"{player_name} MOVE_UP intent: hat={hat_input[1]}, y_axis={y_axis:.2f}")
            
            if hat_input[1] == -1 or y_axis > 0.5:  # Down
                intents[INTENTS['MOVE_DOWN']] = True
                if self.debug and self.debug_frame_counter % 30 == 0:
                    print(f"{player_name} MOVE_DOWN intent: hat={hat_input[1]}, y_axis={y_axis:.2f}")
            
            if hat_input[0] == -1 or x_axis < -0.5:  # Left
                intents[INTENTS['MOVE_LEFT']] = True
                if self.debug and self.debug_frame_counter % 30 == 0:
                    print(f"{player_name} MOVE_LEFT intent: hat={hat_input[0]}, x_axis={x_axis:.2f}")
            
            if hat_input[0] == 1 or x_axis > 0.5:  # Right
                intents[INTENTS['MOVE_RIGHT']] = True
                if self.debug and self.debug_frame_counter % 30 == 0:
                    print(f"{player_name} MOVE_RIGHT intent: hat={hat_input[0]}, x_axis={x_axis:.2f}")
                
        except Exception as e:
            print(f"Error processing controller state for {player_name}: {e}")
            import traceback
            traceback.print_exc()
    
    def _reinitialize_controllers(self):
        """Reinitialize all controllers"""
        if not pg.joystick.get_init():
            pg.joystick.init()
        
        # Reinitialize all controllers
        for player_name, controller in self.controllers.items():
            if not controller['connected']:
                self.init_controller(player_name, controller['id'])
    
    def get_intent(self, player_name, intent):
        """
        Check if a player has a specific intent active
        
        Args:
            player_name: Name of the player
            intent: The intent to check
            
        Returns:
            bool: True if the intent is active, False otherwise
        """
        if player_name in self.player_intents:
            return self.player_intents[player_name].get(intent, False)
        return False
    
    def is_intent_just_activated(self, player_name, intent):
        """
        Check if a player intent was just activated (rising edge)
        
        Args:
            player_name: Name of the player
            intent: The intent to check
            
        Returns:
            bool: True if the intent was just activated, False otherwise
        """
        if player_name in self.player_intents and player_name in self.prev_player_intents:
            current = self.player_intents[player_name].get(intent, False)
            previous = self.prev_player_intents[player_name].get(intent, False)
            return current and not previous
        return False
    
    def is_intent_just_deactivated(self, player_name, intent):
        """
        Check if a player intent was just deactivated (falling edge)
        
        Args:
            player_name: Name of the player
            intent: The intent to check
            
        Returns:
            bool: True if the intent was just deactivated, False otherwise
        """
        if player_name in self.player_intents and player_name in self.prev_player_intents:
            current = self.player_intents[player_name].get(intent, False)
            previous = self.prev_player_intents[player_name].get(intent, False)
            return not current and previous
        return False
    
    def get_analog_value(self, player_name, axis):
        """
        Get analog input value for a player's axis
        
        Args:
            player_name: Name of the player
            axis: 'horizontal' or 'vertical'
            
        Returns:
            float: Analog value between -1.0 and 1.0
        """
        key = f"{player_name}_{axis}"
        return self.analog_values.get(key, 0.0)
    
    def set_debug(self, debug):
        """
        Enable or disable debug output
        
        Args:
            debug: True to enable debug output, False to disable
        """
        self.debug = debug

    def _process_controller(self, player_name, controller):
        """
        DEPRECATED: This method is kept for backwards compatibility.
        Use _process_controller_state with a snapshot of controller state instead.
        
        Args:
            player_name: Name of the player
            controller: Controller object
        """
        try:
            joystick = controller['joystick']
            
            # Create a snapshot of controller state
            state = {
                'buttons': [joystick.get_button(i) for i in range(joystick.get_numbuttons())],
                'axes': [joystick.get_axis(i) for i in range(joystick.get_numaxes())],
                'hats': [joystick.get_hat(i) for i in range(joystick.get_numhats())]
            }
            
            # Process using the snapshot method
            self._process_controller_state(player_name, controller, state)
                
        except Exception as e:
            print(f"Error reading controller for {player_name}: {e}")
            import traceback
            traceback.print_exc()
            controller['connected'] = False

    def _update_jump_tracking(self):
        """Update jump button press and release tracking for short hop detection"""
        for player_name in self.player_intents:
            # Get the current and previous jump button state
            current_jump_pressed = self.get_intent(player_name, INTENTS['MOVE_UP'])
            previous_jump_pressed = self.prev_player_intents[player_name].get(INTENTS['MOVE_UP'], False)
            
            # Check for button press (rising edge)
            if current_jump_pressed and not previous_jump_pressed:
                # Reset any previous release frame
                self.jump_release_frame[player_name] = 0
                
                # Record the press frame if not already set
                if self.jump_press_frame.get(player_name, 0) == 0:
                    self.jump_press_frame[player_name] = self.current_frame
                    print(f"DEBUG: {player_name} jump button PRESSED at frame {self.current_frame}")
            
            # Check for button release (falling edge)
            elif not current_jump_pressed and previous_jump_pressed:
                press_frame = self.jump_press_frame.get(player_name, 0)
                
                # Only record release if we have a valid press
                if press_frame > 0:
                    self.jump_release_frame[player_name] = self.current_frame
                    frames_held = self.current_frame - press_frame
                    print(f"DEBUG: {player_name} jump button RELEASED at frame {self.current_frame} (held for {frames_held} frames)")
            
            # Reset stale jump presses
            press_frame = self.jump_press_frame.get(player_name, 0)
            if press_frame > 0 and self.current_frame - press_frame > 20:  # Reduced from 60 to 20 frames
                print(f"DEBUG: Clearing stale jump press for {player_name} (held for too long without release)")
                self.jump_press_frame[player_name] = 0
                self.jump_release_frame[player_name] = 0
    
    def is_short_hop(self, player_name):
        """Check if player performed a short hop (quick press and release of jump button)"""
        # Get the frame numbers for this player
        press_frame = self.jump_press_frame.get(player_name, 0)
        release_frame = self.jump_release_frame.get(player_name, 0)
        
        # Check if we have valid press and release data
        if press_frame > 0 and release_frame > press_frame:
            # Check if button was released quickly enough for short hop
            frames_held = release_frame - press_frame
            is_short_hop = frames_held <= 7  # Melee-accurate timing (typically 3-7 frames)
            
            if is_short_hop:
                print(f"DEBUG: {player_name} performed short hop (held for {frames_held} frames)")
            else:
                print(f"DEBUG: {player_name} pressed jump too long for short hop (held for {frames_held} frames)")
            
            # Reset tracking after checking
            self.jump_press_frame[player_name] = 0
            self.jump_release_frame[player_name] = 0
            
            return is_short_hop
        
        return False

# Create a global instance
input_handler = InputHandler() 

# Test function for when this file is run directly
if __name__ == "__main__":
    print("Input Handler Test Mode")
    print("Press keys to see intents or connect a controller")
    print("Press ESC to exit, R to reinitialize controller")
    
    # Initialize pygame
    pg.init()
    pg.joystick.init()
    
    # Create test window
    screen = pg.display.set_mode((800, 600))
    pg.display.set_caption("Input Handler Test")
    
    # Font for display
    font = pg.font.Font(None, 30)
    small_font = pg.font.Font(None, 24)
    
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 50, 50)
    BLUE = (50, 150, 255)
    YELLOW = (255, 255, 0)
    
    # Function to display raw controller input data
    def display_raw_controller_data(joystick, screen, start_y):
        y_pos = start_y
        
        # Header for raw data section
        title = font.render("RAW CONTROLLER DATA", True, YELLOW)
        screen.blit(title, (400, y_pos))
        y_pos += 40
        
        # Button states
        for i in range(joystick.get_numbuttons()):
            state = joystick.get_button(i)
            color = GREEN if state else WHITE
            text = small_font.render(f"Button {i}: {'PRESSED' if state else 'Released'}", True, color)
            screen.blit(text, (400, y_pos))
            y_pos += 20
            
            # Only show 10 buttons at a time to avoid overflow
            if i >= 9 and i < joystick.get_numbuttons() - 1:
                text = small_font.render(f"... {joystick.get_numbuttons() - 10} more buttons ...", True, WHITE)
                screen.blit(text, (400, y_pos))
                y_pos += 20
                break
        
        y_pos += 10
        
        # Axis values
        for i in range(min(joystick.get_numaxes(), 6)):  # Show up to 6 axes
            value = joystick.get_axis(i)
            color = GREEN if abs(value) > 0.5 else WHITE
            text = small_font.render(f"Axis {i}: {value:+.2f}", True, color)
            screen.blit(text, (400, y_pos))
            y_pos += 20
        
        # Hat values
        y_pos += 10
        for i in range(joystick.get_numhats()):
            value = joystick.get_hat(i)
            color = GREEN if value != (0, 0) else WHITE
            text = small_font.render(f"Hat {i}: {value}", True, color)
            screen.blit(text, (400, y_pos))
            y_pos += 20
        
        return y_pos
    
    # Check for controllers immediately
    print("\nDetecting controllers...")
    num_joysticks = pg.joystick.get_count()
    print(f"Found {num_joysticks} controllers")
    
    for i in range(num_joysticks):
        try:
            joystick = pg.joystick.Joystick(i)
            joystick.init()
            print(f"Controller {i}: {joystick.get_name()}")
            print(f"  Axes: {joystick.get_numaxes()}")
            print(f"  Buttons: {joystick.get_numbuttons()}")
            print(f"  Hats: {joystick.get_numhats()}")
        except Exception as e:
            print(f"Error initializing controller {i}: {e}")
    
    # Setup test player
    test_player = "TestPlayer"
    print(f"\nSetting up test player: {test_player}")
    input_handler.add_player(test_player, is_player_one=True)
    input_handler.controller_enabled = True  # Enable controller support
    input_handler.set_debug(True)  # Enable debug output
    
    # Force controller initialization if one was detected
    if num_joysticks > 0 and test_player not in input_handler.controllers:
        print("Controller was found but not initialized by add_player. Trying manual initialization...")
        success = input_handler.init_controller(test_player, 0)
        print(f"Manual controller initialization: {'Successful' if success else 'Failed'}")
    
    # Main test loop
    running = True
    clock = pg.time.Clock()
    last_check_time = 0
    show_raw_data = True  # Toggle for raw controller data display
    
    while running:
        current_time = pg.time.get_ticks()
        
        # Handle events
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                if event.key == pg.K_r:
                    # Force reinitialize controller
                    print("\nManually reinitializing controllers...")
                    
                    # First refresh pygame's joystick system
                    pg.joystick.quit()
                    pg.joystick.init()
                    
                    num_joysticks = pg.joystick.get_count()
                    print(f"Found {num_joysticks} controllers")
                    
                    if num_joysticks > 0:
                        if test_player in input_handler.controllers:
                            del input_handler.controllers[test_player]
                        success = input_handler.init_controller(test_player, 0)
                        print(f"Manual controller initialization: {'Successful' if success else 'Failed'}")
                    else:
                        print("No controllers found during reinitialization")
                if event.key == pg.K_d:
                    # Toggle raw data display
                    show_raw_data = not show_raw_data
                    print(f"Raw controller data display: {'Enabled' if show_raw_data else 'Disabled'}")
        
        # Update input handler with events
        input_handler.update(events)
        
        # Periodically check controller connection
        if current_time - last_check_time > 3000:  # Every 3 seconds
            last_check_time = current_time
            joystick_count = pg.joystick.get_count()
            
            if joystick_count > 0 and test_player not in input_handler.controllers:
                print(f"Controller detected but not initialized. Attempting initialization...")
                success = input_handler.init_controller(test_player, 0)
                print(f"Periodic controller initialization: {'Successful' if success else 'Failed'}")
        
        # Clear screen
        screen.fill(BLACK)
        
        # Display active intents
        y_pos = 30
        text = font.render("Active Intents:", True, WHITE)
        screen.blit(text, (20, y_pos))
        y_pos += 40
        
        active_intents = []
        for intent_name, intent_value in INTENTS.items():
            if input_handler.get_intent(test_player, intent_value):
                active_intents.append(intent_name)
                intent_text = font.render(f"- {intent_name}", True, GREEN)
                screen.blit(intent_text, (40, y_pos))
                y_pos += 30
        
        if not active_intents:
            text = font.render("None (Press keys or use controller)", True, WHITE)
            screen.blit(text, (40, y_pos))
        
        # Display controller info
        y_pos = 200
        if test_player in input_handler.controllers and input_handler.controllers[test_player]['connected']:
            controller = input_handler.controllers[test_player]
            text = font.render(f"Controller: {controller['name']}", True, GREEN)
            screen.blit(text, (20, y_pos))
            
            # Show analog values
            y_pos += 40
            h_val = input_handler.get_analog_value(test_player, "horizontal")
            v_val = input_handler.get_analog_value(test_player, "vertical")
            text = font.render(f"Left Stick: X={h_val:.2f}, Y={v_val:.2f}", True, WHITE)
            screen.blit(text, (40, y_pos))
            
            # Show controller button mapping
            y_pos += 40
            text = font.render("Button Mapping:", True, WHITE)
            screen.blit(text, (40, y_pos))
            
            # Show mapped buttons
            y_pos += 30
            for intent, button in controller['mapping'].items():
                if button is not None:
                    mapping_text = small_font.render(f"{intent}: Button {button}", True, BLUE)
                    screen.blit(mapping_text, (60, y_pos))
                    y_pos += 25
            
            # Show raw controller data if enabled 
            if show_raw_data:
                try:
                    display_raw_controller_data(controller['joystick'], screen, 200)
                except Exception as e:
                    print(f"Error displaying raw controller data: {e}")
        else:
            # Show detailed controller detection state
            text = font.render("No controller connected to input handler", True, RED)
            screen.blit(text, (20, y_pos))
            
            y_pos += 40
            joystick_count = pg.joystick.get_count()
            
            if joystick_count == 0:
                text = font.render("No physical controllers detected by pygame", True, WHITE)
                screen.blit(text, (40, y_pos))
                
                y_pos += 30
                text = small_font.render("Please connect controller and press R to reinitialize", True, WHITE)
                screen.blit(text, (40, y_pos))
            else:
                text = font.render(f"{joystick_count} controller(s) detected but not properly initialized", True, WHITE)
                screen.blit(text, (40, y_pos))
                
                y_pos += 30
                for i in range(joystick_count):
                    try:
                        joystick = pg.joystick.Joystick(i)
                        joystick.init()
                        controller_name = joystick.get_name()
                        text = small_font.render(f"Controller {i}: {controller_name}", True, BLUE)
                        screen.blit(text, (60, y_pos))
                        y_pos += 25
                        
                        # Show raw data for the first controller even if not in input handler
                        if show_raw_data and i == 0:
                            display_raw_controller_data(joystick, screen, 350)
                    except Exception as e:
                        text = small_font.render(f"Error with controller {i}: {str(e)}", True, RED)
                        screen.blit(text, (60, y_pos))
                        y_pos += 25
                
                y_pos += 10
                text = small_font.render("Press R to reinitialize controller connection", True, WHITE)
                screen.blit(text, (40, y_pos))
        
        # Display input handler state
        y_pos = 350
        text = font.render("Input Handler State:", True, WHITE)
        screen.blit(text, (20, y_pos))
        
        y_pos += 30
        text = small_font.render(f"Controller Enabled: {input_handler.controller_enabled}", True, 
                              GREEN if input_handler.controller_enabled else RED)
        screen.blit(text, (40, y_pos))
        
        y_pos += 25
        text = small_font.render(f"Debug Mode: {input_handler.debug}", True, WHITE)
        screen.blit(text, (40, y_pos))
        
        y_pos += 25
        text = small_font.render(f"Deadzone: {input_handler.deadzone}", True, WHITE)
        screen.blit(text, (40, y_pos))
        
        # Display key controls
        y_pos = 500
        text = font.render("Controls:", True, WHITE)
        screen.blit(text, (20, y_pos))
        
        y_pos += 30
        text = small_font.render("Arrows: Move, Z: Weak Attack, X: Heavy Attack", True, WHITE)
        screen.blit(text, (40, y_pos))
        
        y_pos += 25
        text = small_font.render("R: Reinitialize Controller, D: Toggle Raw Data", True, WHITE)
        screen.blit(text, (40, y_pos))
        
        y_pos += 25
        text = small_font.render("ESC: Exit Test", True, WHITE)
        screen.blit(text, (40, y_pos))
        
        # Update display
        pg.display.flip()
        clock.tick(60)
    
    # Clean up
    pg.quit()
    print("Input Handler Test finished") 