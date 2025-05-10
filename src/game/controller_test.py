'''
Switch Pro Controller Test Utility

This script helps diagnose controller issues with PyGame by showing real-time
button presses and axis values.

Run this standalone to test your controller before playing the game.
'''

import pygame as pg
import sys
import os
import time

# Initialize pygame
pg.init()
pg.joystick.init()

# Setup display
screen = pg.display.set_mode((800, 600))
pg.display.set_caption('Controller Test Utility')
clock = pg.time.Clock()
font = pg.font.Font(None, 30)

def main():
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    
    # Controller state
    controller_found = False
    joystick = None
    controller_name = "No controller detected"
    axes_values = []
    button_states = []
    hat_states = []
    
    # Initialize
    print("=== Controller Test Utility ===")
    print("This utility will help diagnose controller issues")
    print("Press any controller button to see its index")
    print("Press ESC or close the window to exit")
    print()
    
    # Wait for controller recognition
    time.sleep(0.5)
    
    # Try to initialize joystick
    if pg.joystick.get_count() > 0:
        try:
            joystick = pg.joystick.Joystick(0)
            joystick.init()
            controller_name = joystick.get_name()
            num_axes = joystick.get_numaxes()
            num_buttons = joystick.get_numbuttons()
            num_hats = joystick.get_numhats()
            
            # Initialize state arrays
            axes_values = [0.0] * num_axes
            button_states = [False] * num_buttons
            hat_states = [(0, 0)] * num_hats
            
            controller_found = True
            print(f"Controller detected: {controller_name}")
            print(f"Axes: {num_axes}, Buttons: {num_buttons}, Hats: {num_hats}")
        except Exception as e:
            print(f"Error initializing controller: {e}")
    else:
        print("No controllers detected.")
        print("Please connect a controller and restart this utility.")
    
    # Main loop
    running = True
    
    # For reinitialization if controller is connected mid-session
    last_check = time.time()
    
    while running:
        # Handle events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
            
            # Log controller events
            if event.type == pg.JOYBUTTONDOWN:
                print(f"Button pressed: {event.button}")
            elif event.type == pg.JOYHATMOTION:
                print(f"Hat {event.hat} value: {event.value}")
            elif event.type == pg.JOYAXISMOTION:
                # Only log significant axis changes to avoid spam
                if abs(event.value) > 0.5:
                    print(f"Axis {event.axis} value: {event.value:.2f}")
        
        # Periodically check for controller connection
        current_time = time.time()
        if current_time - last_check > 2.0:  # Check every 2 seconds
            last_check = current_time
            
            # If no controller, try to find one
            if not controller_found and pg.joystick.get_count() > 0:
                try:
                    pg.joystick.quit()
                    pg.joystick.init()
                    joystick = pg.joystick.Joystick(0)
                    joystick.init()
                    controller_name = joystick.get_name()
                    num_axes = joystick.get_numaxes()
                    num_buttons = joystick.get_numbuttons()
                    num_hats = joystick.get_numhats()
                    
                    # Initialize state arrays
                    axes_values = [0.0] * num_axes
                    button_states = [False] * num_buttons
                    hat_states = [(0, 0)] * num_hats
                    
                    controller_found = True
                    print(f"Controller connected: {controller_name}")
                except Exception as e:
                    print(f"Error detecting new controller: {e}")
            
            # If controller was disconnected, log it
            elif controller_found and pg.joystick.get_count() == 0:
                print("Controller disconnected")
                controller_found = False
                joystick = None
        
        # Update controller state if connected
        if controller_found and joystick:
            try:
                # Read axis values
                for i in range(joystick.get_numaxes()):
                    axes_values[i] = joystick.get_axis(i)
                
                # Read button states
                for i in range(joystick.get_numbuttons()):
                    button_states[i] = joystick.get_button(i)
                
                # Read hat states
                for i in range(joystick.get_numhats()):
                    hat_states[i] = joystick.get_hat(i)
            except Exception as e:
                print(f"Error reading controller: {e}")
                controller_found = False
                joystick = None
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw controller info
        title_text = font.render("Controller Test Utility", True, WHITE)
        screen.blit(title_text, (20, 20))
        
        controller_text = font.render(f"Controller: {controller_name}", True, 
                                     GREEN if controller_found else RED)
        screen.blit(controller_text, (20, 60))
        
        instruction_text = font.render("Press buttons, move sticks, or D-pad to see values", True, WHITE)
        screen.blit(instruction_text, (20, 100))
        
        # Draw button states
        if controller_found:
            # Draw button states
            button_title = font.render("Button States:", True, WHITE)
            screen.blit(button_title, (20, 150))
            
            for i, state in enumerate(button_states):
                color = GREEN if state else WHITE
                button_text = font.render(f"Button {i}: {'PRESSED' if state else 'Released'}", True, color)
                screen.blit(button_text, (20, 180 + i * 30))
            
            # Draw axis values
            axis_title = font.render("Axis Values:", True, WHITE)
            screen.blit(axis_title, (300, 150))
            
            for i, value in enumerate(axes_values):
                # Determine color based on value for visual feedback
                if abs(value) < 0.1:
                    color = WHITE  # Neutral
                elif value > 0:
                    color = GREEN  # Positive
                else:
                    color = RED    # Negative
                
                axis_text = font.render(f"Axis {i}: {value:+.2f}", True, color)
                screen.blit(axis_text, (300, 180 + i * 30))
            
            # Draw hat (D-pad) states
            hat_title = font.render("Hat (D-pad) Values:", True, WHITE)
            screen.blit(hat_title, (550, 150))
            
            for i, value in enumerate(hat_states):
                hat_text = font.render(f"Hat {i}: {value}", True, 
                                      BLUE if value != (0, 0) else WHITE)
                screen.blit(hat_text, (550, 180 + i * 30))
        else:
            not_found = font.render("No controller detected", True, RED)
            screen.blit(not_found, (20, 180))
            
            help_text1 = font.render("1. Make sure controller is connected", True, WHITE)
            help_text2 = font.render("2. Try unplugging and reconnecting", True, WHITE)
            help_text3 = font.render("3. Some controllers need special drivers", True, WHITE)
            help_text4 = font.render("4. Press buttons to test if detected", True, WHITE)
            
            screen.blit(help_text1, (20, 230))
            screen.blit(help_text2, (20, 260))
            screen.blit(help_text3, (20, 290))
            screen.blit(help_text4, (20, 320))
        
        # Draw exit instruction
        exit_text = font.render("Press ESC to exit", True, WHITE)
        screen.blit(exit_text, (20, 550))
        
        # Update display
        pg.display.flip()
        clock.tick(30)
    
    # Clean up
    pg.quit()
    sys.exit()

if __name__ == "__main__":
    main() 