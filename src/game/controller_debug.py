"""
Controller Debug Utility for Super Smash Bros

This is a specialized diagnostic tool to identify where controller processing
is failing in the game. It tests each component of the input pipeline separately.
"""

import pygame as pg
import sys
import os
import time

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import required modules
from config import PRO_CONTROLLER, DEFAULT_SETTINGS
from input_handler import input_handler, INTENTS
from settings import *

pg.init()
pg.joystick.init()

# Setup display
screen = pg.display.set_mode((800, 600))
pg.display.set_caption('Controller Debug Utility')
clock = pg.time.Clock()
font = pg.font.Font(None, 30)

def main():
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    
    # Controller detection
    joystick = None
    controller_name = "No controller detected"
    
    # Test results
    stage_results = {
        "controller_detection": False,
        "input_handler_connection": False,
        "intent_processing": False,
        "mapping_test": {}
    }
    
    # Initialize
    print("\n===== CONTROLLER DEBUG UTILITY =====")
    print("This utility will diagnose controller issues step by step")
    print("Press ESC to exit, Space to manually proceed to next test stage")
    
    # Wait for controller recognition
    time.sleep(0.5)
    
    # Stage 1: Basic Controller Detection
    print("\n[STAGE 1] Testing basic controller detection...")
    if pg.joystick.get_count() > 0:
        try:
            joystick = pg.joystick.Joystick(0)
            joystick.init()
            controller_name = joystick.get_name()
            num_axes = joystick.get_numaxes()
            num_buttons = joystick.get_numbuttons()
            num_hats = joystick.get_numhats()
            
            stage_results["controller_detection"] = True
            print(f"✓ SUCCESS: Controller detected: {controller_name}")
            print(f"  Axes: {num_axes}, Buttons: {num_buttons}, Hats: {num_hats}")
            
            # Detailed info
            for i in range(num_axes):
                print(f"  Axis {i}: {joystick.get_axis(i):.2f}")
            
            # Check for stick at rest values
            if num_axes >= 2:
                x_rest = joystick.get_axis(0)
                y_rest = joystick.get_axis(1)
                print(f"  Left stick rest values: X={x_rest:.4f}, Y={y_rest:.4f}")
                if abs(x_rest) > 0.2 or abs(y_rest) > 0.2:
                    print("  ⚠ WARNING: Stick rest values are not near zero - may need calibration")
            
        except Exception as e:
            print(f"✗ FAILURE: Error initializing controller: {e}")
    else:
        print("✗ FAILURE: No controllers detected")
    
    # Stage 2: Input Handler Connection
    print("\n[STAGE 2] Testing input handler connection...")
    
    # Ensure controller is enabled in the input handler
    input_handler.controller_enabled = True
    print(f"Controller enabled flag set: {input_handler.controller_enabled}")
    
    # Create a test player
    test_player = "TestPlayer"
    input_handler.add_player(test_player, is_player_one=True)
    print(f"Test player added: {test_player in input_handler.player_intents}")
    
    # Check if controller was initialized for the test player
    if test_player in input_handler.controllers:
        stage_results["input_handler_connection"] = True
        controller_info = input_handler.controllers[test_player]
        print(f"✓ SUCCESS: Controller connected to input handler")
        print(f"  Controller name: {controller_info['name']}")
        print(f"  Connected: {controller_info['connected']}")
    else:
        print(f"✗ FAILURE: Controller not connected to input handler")
        print(f"  Available controllers: {list(input_handler.controllers.keys())}")
        
        # Try manual connection
        print("  Attempting manual controller connection...")
        if stage_results["controller_detection"] and joystick:
            result = input_handler.init_controller(test_player, 0)
            print(f"  Manual connection result: {result}")
            if test_player in input_handler.controllers:
                stage_results["input_handler_connection"] = True
                print(f"  ✓ Manual connection succeeded")
            else:
                print(f"  ✗ Manual connection failed")
    
    # Stage 3: Intent Processing Test
    print("\n[STAGE 3] Testing intent processing...")
    print("Move stick/press buttons to see intents - watch the window and console output")
    
    # Main testing loop
    running = True
    auto_proceed = False
    test_stage = 3 if stage_results["input_handler_connection"] else 2
    start_time = time.time()
    button_pressed = [False] * 20  # Track which buttons have been pressed
    axes_moved = [False] * 10      # Track which axes have shown movement
    
    # Mapping test
    mapping_issues = {}
    expected_mappings = {
        "Move Left": ["LEFT on D-pad", "Left Stick LEFT"],
        "Move Right": ["RIGHT on D-pad", "Left Stick RIGHT"],
        "Move Up": ["UP on D-pad", "Left Stick UP"],
        "Move Down": ["DOWN on D-pad", "Left Stick DOWN"],
        "Weak Attack": ["B button", "A button (Xbox)", "X/Cross button (PS)"],
        "Heavy Attack": ["Y button", "Y button (Xbox)", "Triangle button (PS)"],
    }
    
    while running:
        # Event handling
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key == pg.K_SPACE:
                    test_stage += 1
                    print(f"\nMoving to stage {test_stage}...")
                    if test_stage > 4:
                        running = False
            
            # Special controller event debugging
            if event.type == pg.JOYBUTTONDOWN:
                print(f"Button pressed: {event.button}")
                if event.button < len(button_pressed):
                    button_pressed[event.button] = True
            elif event.type == pg.JOYAXISMOTION:
                if abs(event.value) > 0.5 and event.axis < len(axes_moved):
                    if not axes_moved[event.axis]:
                        print(f"Axis {event.axis} significant movement: {event.value:.2f}")
                        axes_moved[event.axis] = True
            elif event.type == pg.JOYHATMOTION:
                print(f"Hat {event.hat} motion: {event.value}")
        
        # Process inputs in input handler (similar to game loop)
        input_handler.update(pg.event.get(), pg.key.get_pressed())
        
        # Test intent processing
        if test_stage >= 3 and test_player in input_handler.player_intents:
            # Check which intents are active
            active_intents = []
            
            # Test each movement intent
            if input_handler.get_intent(test_player, INTENTS['MOVE_LEFT']):
                active_intents.append("MOVE_LEFT")
                stage_results["intent_processing"] = True
                stage_results["mapping_test"]["Move Left"] = True
            if input_handler.get_intent(test_player, INTENTS['MOVE_RIGHT']):
                active_intents.append("MOVE_RIGHT")
                stage_results["intent_processing"] = True
                stage_results["mapping_test"]["Move Right"] = True
            if input_handler.get_intent(test_player, INTENTS['MOVE_UP']):
                active_intents.append("MOVE_UP")
                stage_results["intent_processing"] = True
                stage_results["mapping_test"]["Move Up"] = True
            if input_handler.get_intent(test_player, INTENTS['MOVE_DOWN']):
                active_intents.append("MOVE_DOWN")
                stage_results["intent_processing"] = True
                stage_results["mapping_test"]["Move Down"] = True
            
            # Test attack intents
            if input_handler.get_intent(test_player, INTENTS['WEAK_ATTACK']):
                active_intents.append("WEAK_ATTACK")
                stage_results["intent_processing"] = True
                stage_results["mapping_test"]["Weak Attack"] = True
            if input_handler.get_intent(test_player, INTENTS['HEAVY_ATTACK']):
                active_intents.append("HEAVY_ATTACK")
                stage_results["intent_processing"] = True
                stage_results["mapping_test"]["Heavy Attack"] = True
                
            # Display active intents if any
            if active_intents and (time.time() - start_time) > 1.0:
                print(f"Active intents: {', '.join(active_intents)}")
                start_time = time.time()  # Reset timer to prevent spam
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw header
        title_text = font.render("Controller Debug Utility", True, WHITE)
        screen.blit(title_text, (20, 20))
        
        # Draw controller status
        status_color = GREEN if stage_results["controller_detection"] else RED
        controller_text = font.render(f"Controller: {controller_name}", True, status_color)
        screen.blit(controller_text, (20, 60))
        
        # Draw test stage results
        y_pos = 100
        for i, (stage, result) in enumerate([
            ("1. Controller Detection", stage_results["controller_detection"]),
            ("2. Input Handler Connection", stage_results["input_handler_connection"]),
            ("3. Intent Processing", stage_results["intent_processing"])
        ]):
            result_color = GREEN if result else RED
            result_text = "PASS" if result else "FAIL"
            test_text = font.render(f"{stage}: {result_text}", True, result_color)
            screen.blit(test_text, (20, y_pos))
            y_pos += 30
        
        # If in stage 3 or above, show intent detection
        if test_stage >= 3:
            y_pos += 20
            intent_header = font.render("Intent Detection Test:", True, WHITE)
            screen.blit(intent_header, (20, y_pos))
            y_pos += 30
            
            # Show intents for movement/actions
            for intent_name, detected in [
                ("Move Left", "Move Left" in stage_results["mapping_test"]),
                ("Move Right", "Move Right" in stage_results["mapping_test"]),
                ("Move Up", "Move Up" in stage_results["mapping_test"]),
                ("Move Down", "Move Down" in stage_results["mapping_test"]),
                ("Weak Attack", "Weak Attack" in stage_results["mapping_test"]),
                ("Heavy Attack", "Heavy Attack" in stage_results["mapping_test"])
            ]:
                text_color = GREEN if detected else WHITE
                intent_text = font.render(f"{intent_name}: {'✓' if detected else 'Not detected yet'}", True, text_color)
                screen.blit(intent_text, (40, y_pos))
                
                # Show hint for expected inputs
                if not detected and intent_name in expected_mappings:
                    hint_text = ", ".join(expected_mappings[intent_name][:1])  # Show first hint only
                    hint_render = font.render(f"Try: {hint_text}", True, BLUE)
                    screen.blit(hint_render, (300, y_pos))
                
                y_pos += 25
        
        # Show active joystick values if controller is detected
        if stage_results["controller_detection"] and joystick:
            y_pos += 20
            joystick_header = font.render("Current Controller State:", True, WHITE)
            screen.blit(joystick_header, (20, y_pos))
            y_pos += 30
            
            # Show axis values
            for i in range(min(joystick.get_numaxes(), 6)):  # Limit to 6 axes
                axis_val = joystick.get_axis(i)
                color = WHITE
                if abs(axis_val) > 0.5:
                    color = GREEN
                axis_text = font.render(f"Axis {i}: {axis_val:+.2f}", True, color)
                screen.blit(axis_text, (40, y_pos))
                y_pos += 25
            
            # Show active button states
            active_buttons = []
            for i in range(joystick.get_numbuttons()):
                if joystick.get_button(i):
                    active_buttons.append(str(i))
            
            if active_buttons:
                button_text = font.render(f"Active Buttons: {', '.join(active_buttons)}", True, GREEN)
            else:
                button_text = font.render("No buttons pressed", True, WHITE)
            screen.blit(button_text, (40, y_pos))
            y_pos += 25
            
            # Show hat (D-pad) values
            for i in range(joystick.get_numhats()):
                hat_val = joystick.get_hat(i)
                hat_text = font.render(f"D-pad: {hat_val}", True, 
                                      GREEN if hat_val != (0, 0) else WHITE)
                screen.blit(hat_text, (40, y_pos))
        
        # Instructions
        instructions = [
            "Press SPACE to manually proceed to next test",
            "Press ESC to exit",
            "",
            "Test your controller by pressing buttons and moving sticks",
            "Watch for intent detection in the game window"
        ]
        
        y_pos = 500
        for instruction in instructions:
            instr_text = font.render(instruction, True, WHITE)
            screen.blit(instr_text, (20, y_pos))
            y_pos += 25
        
        # Update display
        pg.display.flip()
        clock.tick(30)
    
    # Final report
    print("\n===== TEST RESULTS =====")
    print(f"1. Controller Detection: {'PASS' if stage_results['controller_detection'] else 'FAIL'}")
    print(f"2. Input Handler Connection: {'PASS' if stage_results['input_handler_connection'] else 'FAIL'}")
    print(f"3. Intent Processing: {'PASS' if stage_results['intent_processing'] else 'FAIL'}")
    
    # Intent mapping details
    print("\nIntent Mapping Results:")
    for intent in ["Move Left", "Move Right", "Move Up", "Move Down", "Weak Attack", "Heavy Attack"]:
        result = "Detected" if intent in stage_results["mapping_test"] else "Not detected"
        print(f"  {intent}: {result}")
    
    # Provide specific advice based on test results
    print("\n===== DIAGNOSTICS AND FIXES =====")
    
    if not stage_results["controller_detection"]:
        print("ISSUE: Controller not detected by Pygame")
        print("FIXES:")
        print("1. Ensure controller is properly connected before starting the game")
        print("2. Try a different USB port")
        print("3. Install required drivers for your controller")
        print("4. On some systems, you might need to use a controller mapping utility")
    
    elif not stage_results["input_handler_connection"]:
        print("ISSUE: Controller detected but not properly connected to input handler")
        print("FIXES:")
        print("1. Edit input_handler.py to update controller detection logic")
        print("2. Make sure controller_enabled flag is properly set")
        print("3. Debug the input_handler.add_player method when is_player_one=True")
    
    elif not stage_results["intent_processing"]:
        print("ISSUE: Controller connected but intents not being registered")
        print("FIXES:")
        print("1. Check button mappings in config.py - they may not match your controller")
        print("2. Debug _process_controller method in input_handler.py")
        print("3. Make sure analog stick axis values are being read correctly")
    
    else:
        # Check incomplete mappings
        missing_mappings = [intent for intent in ["Move Left", "Move Right", "Move Up", "Move Down", 
                                                 "Weak Attack", "Heavy Attack"] 
                           if intent not in stage_results["mapping_test"]]
        
        if missing_mappings:
            print("ISSUE: Some controller mappings not detected")
            print(f"Missing mappings: {', '.join(missing_mappings)}")
            print("FIXES:")
            print("1. Update button mappings in config.py to match your controller")
            print("2. Check input_handler._process_controller method for correct mapping")
        else:
            print("All tests PASSED! Controller should be working correctly in the game.")
            print("If you're still having issues, check:")
            print("1. Player_controller.py to ensure it's using the intent system correctly")
            print("2. Verify that LocalGame.py is calling input_handler.update() in its event loop")
    
    # Clean up
    pg.quit()

if __name__ == "__main__":
    main() 