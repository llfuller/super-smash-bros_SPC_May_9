"""
Controller Information Utility

This simple utility displays detailed information about any connected controllers.
It helps identify button mappings and axis values for your specific controller.
"""

import pygame as pg
import sys
import time

def main():
    pg.init()
    pg.joystick.init()
    
    print("\n=== Controller Information Utility ===")
    print("This utility shows detailed information about your controller")
    print("Press buttons and move sticks to see their IDs and values")
    print("\nDetecting controllers...")
    
    # Wait a moment for controller detection
    time.sleep(0.5)
    
    # Check for controllers
    joystick_count = pg.joystick.get_count()
    print(f"Found {joystick_count} controller(s)\n")
    
    if joystick_count == 0:
        print("No controllers detected. Please connect a controller and try again.")
        return
    
    # Create a window to display controller info
    screen = pg.display.set_mode((800, 600))
    pg.display.set_caption("Controller Information Utility")
    clock = pg.time.Clock()
    font = pg.font.Font(None, 30)
    small_font = pg.font.Font(None, 24)
    
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 100, 255)
    YELLOW = (255, 255, 0)
    
    # Tracks the last pressed buttons
    last_pressed = {}
    button_pressed_time = {}
    
    # Initialize all joysticks
    joysticks = []
    for i in range(joystick_count):
        try:
            joystick = pg.joystick.Joystick(i)
            joystick.init()
            joysticks.append(joystick)
            
            print(f"Controller {i+1}: {joystick.get_name()}")
            print(f"  Axes: {joystick.get_numaxes()}")
            print(f"  Buttons: {joystick.get_numbuttons()}")
            print(f"  Hats: {joystick.get_numhats()}")
            print()
        except Exception as e:
            print(f"Error initializing controller {i}: {e}")
    
    print("Press buttons to see their IDs in the window")
    print("Press ESC to exit")
    
    # Main loop
    running = True
    current_joy = 0  # Current joystick to display
    
    while running:
        # Handle events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key == pg.K_n and joystick_count > 1:
                    # Switch to next controller
                    current_joy = (current_joy + 1) % joystick_count
            
            # Track button presses
            elif event.type == pg.JOYBUTTONDOWN:
                if event.joy == current_joy:
                    last_pressed[event.button] = time.time()
                    button_pressed_time[event.button] = 0
                    print(f"Button pressed: {event.button}")
            
            # Track significant axis movement
            elif event.type == pg.JOYAXISMOTION:
                if event.joy == current_joy and abs(event.value) > 0.5:
                    print(f"Axis {event.axis} value: {event.value:.2f}")
            
            # Track hat movement
            elif event.type == pg.JOYHATMOTION:
                if event.joy == current_joy and event.value != (0, 0):
                    print(f"Hat {event.hat} value: {event.value}")
        
        # Clear screen
        screen.fill(BLACK)
        
        # Get current joystick
        if joysticks and current_joy < len(joysticks):
            joystick = joysticks[current_joy]
            
            # Display controller info header
            title = font.render(f"Controller {current_joy+1}: {joystick.get_name()}", True, WHITE)
            screen.blit(title, (20, 20))
            
            # Instructions
            if joystick_count > 1:
                instr = small_font.render("Press N to switch controllers, ESC to exit", True, WHITE)
            else:
                instr = small_font.render("Press ESC to exit", True, WHITE)
            screen.blit(instr, (20, 60))
            
            # Display button states
            btn_title = font.render("Button States:", True, WHITE)
            screen.blit(btn_title, (20, 100))
            
            # Update button highlight timers
            current_time = time.time()
            for btn in list(last_pressed.keys()):
                button_pressed_time[btn] = int((current_time - last_pressed[btn]) * 10)
                # Remove highlight after 3 seconds
                if button_pressed_time[btn] > 30:
                    del last_pressed[btn]
                    del button_pressed_time[btn]
            
            # Draw button states in a grid
            cols = 4
            btn_width = 150
            btn_height = 30
            max_buttons = joystick.get_numbuttons()
            
            for i in range(max_buttons):
                col = i % cols
                row = i // cols
                x = 20 + col * btn_width
                y = 130 + row * btn_height
                
                state = joystick.get_button(i)
                
                # Determine color based on state and recent press
                if state:
                    color = GREEN
                elif i in last_pressed:
                    # Fade from yellow to white
                    fade = min(255, 100 + button_pressed_time[i] * 5)
                    color = (255, 255, 255 - fade)
                else:
                    color = WHITE
                
                btn_text = small_font.render(f"Button {i}: {'ON' if state else 'off'}", True, color)
                screen.blit(btn_text, (x, y))
            
            # Display axis values
            axis_title = font.render("Axis Values:", True, WHITE)
            screen.blit(axis_title, (20, 300))
            
            # Draw axis values with bars
            max_axes = joystick.get_numaxes()
            for i in range(max_axes):
                value = joystick.get_axis(i)
                
                # Determine color based on value
                if abs(value) < 0.1:
                    color = WHITE
                elif value > 0:
                    color = GREEN
                else:
                    color = RED
                
                axis_text = small_font.render(f"Axis {i}: {value:+.2f}", True, color)
                screen.blit(axis_text, (20, 330 + i * 25))
                
                # Draw a bar to visualize the value
                bar_x = 180
                bar_width = 200
                bar_height = 15
                
                # Background bar
                pg.draw.rect(screen, (50, 50, 50), (bar_x, 335 + i * 25, bar_width, bar_height))
                
                # Value bar
                value_width = int((value + 1) * bar_width / 2)
                if value > 0:
                    pg.draw.rect(screen, GREEN, (bar_x + bar_width//2, 335 + i * 25, value_width, bar_height))
                else:
                    pg.draw.rect(screen, RED, (bar_x + bar_width//2 + value_width, 335 + i * 25, -value_width, bar_height))
                
                # Center line
                pg.draw.line(screen, YELLOW, (bar_x + bar_width//2, 335 + i * 25), 
                            (bar_x + bar_width//2, 335 + i * 25 + bar_height), 2)
            
            # Display hat (D-pad) values
            hat_title = font.render("Hat (D-pad) Values:", True, WHITE)
            screen.blit(hat_title, (500, 100))
            
            # Draw hat values
            max_hats = joystick.get_numhats()
            for i in range(max_hats):
                value = joystick.get_hat(i)
                color = BLUE if value != (0, 0) else WHITE
                hat_text = small_font.render(f"Hat {i}: {value}", True, color)
                screen.blit(hat_text, (500, 130 + i * 30))
                
                # Draw a visual representation of the hat
                center_x = 650
                center_y = 138 + i * 30
                radius = 25
                
                # Draw outer circle
                pg.draw.circle(screen, WHITE, (center_x, center_y), radius, 1)
                
                # Draw center point or position based on value
                if value == (0, 0):
                    pg.draw.circle(screen, WHITE, (center_x, center_y), 3)
                else:
                    pos_x = center_x + value[0] * radius * 0.7
                    pos_y = center_y - value[1] * radius * 0.7  # Inverted Y for screen coords
                    pg.draw.circle(screen, BLUE, (int(pos_x), int(pos_y)), 5)
            
            # Show mapping recommendations based on controller type
            name_lower = joystick.get_name().lower()
            mapping_title = font.render("Recommended Button Mapping:", True, WHITE)
            screen.blit(mapping_title, (500, 300))
            
            if "switch" in name_lower or "nintendo" in name_lower or "pro" in name_lower:
                mapping = [
                    "B button: Button 2",
                    "Y button: Button 0",
                    "Minus: Button 8",
                    "Plus: Button 9",
                    "Home: Button 12",
                    "Left stick: Axes 0,1"
                ]
            elif "xbox" in name_lower:
                mapping = [
                    "A button: Button 0",
                    "Y button: Button 3",
                    "Back/View: Button 6",
                    "Start/Menu: Button 7",
                    "Xbox: Button 8",
                    "Left stick: Axes 0,1"
                ]
            elif "playstation" in name_lower or "ps4" in name_lower or "ps5" in name_lower:
                mapping = [
                    "Cross/X: Button 0",
                    "Triangle: Button 3",
                    "Share/Create: Button 8",
                    "Options: Button 9",
                    "PS: Button 10",
                    "Left stick: Axes 0,1"
                ]
            else:
                mapping = [
                    "Primary action: Button 0",
                    "Secondary action: Button 1",
                    "Menu: Button 6-7",
                    "Left stick: Usually Axes 0,1",
                    "Check button presses to identify"
                ]
            
            # Draw mapping recommendations
            for i, line in enumerate(mapping):
                map_text = small_font.render(line, True, YELLOW)
                screen.blit(map_text, (500, 330 + i * 25))
            
            # Display instructions for config.py
            config_title = font.render("For config.py:", True, WHITE)
            screen.blit(config_title, (20, 500))
            
            if "switch" in name_lower or "nintendo" in name_lower or "pro" in name_lower:
                config_text = [
                    "PRO_CONTROLLER = {",
                    "    'y_button': 0,    # Y button (Heavy attack)",
                    "    'b_button': 2,    # B button (Weak attack)",
                    "    'minus': 8,       # Minus button (Menu)",
                    "    'plus': 9,        # Plus button (Restart)",
                    "    'l_stick_x': 0,   # Left stick X axis",
                    "    'l_stick_y': 1,   # Left stick Y axis",
                    "}"
                ]
            else:
                config_text = [
                    "# Modify config.py based on your controller values",
                    "# Use the button numbers shown above"
                ]
            
            for i, line in enumerate(config_text):
                text = small_font.render(line, True, BLUE)
                screen.blit(text, (20, 530 + i * 20))
        
        # Update display and limit framerate
        pg.display.flip()
        clock.tick(30)
    
    # Clean up
    pg.quit()
    print("Controller Information Utility exited")

if __name__ == "__main__":
    main() 