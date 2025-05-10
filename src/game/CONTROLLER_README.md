# Controller Support for Super Smash Bros

This guide helps you set up and troubleshoot controller support for the game, with specific focus on Switch Pro Controllers.

## Controller Types Supported

The game has been designed to work with several popular controller types:

1. **Nintendo Switch Pro Controller** - Primary testing was done with this controller
2. **Xbox Controllers** (Xbox One, Xbox Series X/S) - Should work with standard Windows drivers
3. **PlayStation Controllers** (DualShock 4, DualSense) - May require additional drivers
4. **Generic USB/Bluetooth Controllers** - Basic support, button mappings may need adjustment

## Setup Guide

1. **Connect your controller** to your PC:
   - **Wired Connection**: Connect using USB cable
   - **Bluetooth**: Pair your controller through Windows Bluetooth settings
   
2. **Start the game**: 
   ```
   python LocalGameLauncher.py
   ```
   The game should automatically detect your controller.

3. **Enable Debug Mode**:
   - Press `F1` during gameplay to toggle debug mode
   - This displays controller input values in the console

## Button Mappings

Default button mappings are:

### Switch Pro Controller
- **Movement**: Left Stick or D-pad
- **Jump**: Up on Left Stick or D-pad
- **Fast Fall**: Down on Left Stick or D-pad
- **Weak Attack**: B button
- **Heavy Attack**: Y button
- **Restart Game**: Plus button
- **Menu**: Minus button
- **Quit**: Home button

### Xbox Controller
- **Movement**: Left Stick or D-pad
- **Jump**: Up on Left Stick or D-pad
- **Fast Fall**: Down on Left Stick or D-pad  
- **Weak Attack**: A button
- **Heavy Attack**: Y button
- **Restart Game**: Start/Menu button
- **Menu**: Back/View button
- **Quit**: Xbox button

### PlayStation Controller
- **Movement**: Left Stick or D-pad
- **Jump**: Up on Left Stick or D-pad
- **Fast Fall**: Down on Left Stick or D-pad
- **Weak Attack**: Cross (X) button
- **Heavy Attack**: Triangle button
- **Restart Game**: Options button
- **Menu**: Share/Create button
- **Quit**: PS button

## Troubleshooting

### Controller Not Detected

1. **Run the controller test utility**:
   ```
   python controller_test.py
   ```
   This utility shows real-time information about your controller.

2. **Check if the controller is properly connected**:
   - Try disconnecting and reconnecting
   - Check battery level if using Bluetooth
   - Try using a USB connection instead of Bluetooth

3. **Windows recognition**:
   - Make sure Windows recognizes the controller in Control Panel > Devices and Printers
   - You should see the controller listed when connected

4. **Restart the game** after connecting the controller

### Controller Detected But Not Working

1. **Debug Mode**:
   - Press `F1` to enable debug mode
   - Look at the console output when pressing buttons to see if inputs are registered

2. **Check Button Mappings**:
   - Run `controller_test.py` to see the actual button indices
   - Press each button and note its index number
   - Update button mappings in `config.py` to match your controller

3. **Check for Conflicts**:
   - Other programs might be capturing controller inputs
   - Close Steam or other game launchers that might be interfering

### Common Issues for Switch Pro Controllers

1. **Controller connects but no inputs detected**:
   - This is often caused by Windows using generic HID drivers
   - Try installing special Pro Controller drivers or use a tool like BetterJoy

2. **Button mappings are incorrect**:
   - Update the PRO_CONTROLLER settings in `config.py`:
   ```python
   PRO_CONTROLLER = {
       'b_button': X,     # Replace X with correct button index
       'y_button': Y,     # Replace Y with correct button index
       # etc.
   }
   ```

3. **Controller disconnects frequently**:
   - Try using a USB connection
   - Check for Bluetooth interference
   - Update your Bluetooth drivers

### Controller Stick Problems

1. **Deadzone issues** (character moves when stick is neutral):
   - Adjust the 'controller_deadzone' value in DEFAULT_SETTINGS in `config.py`
   - Increase if character drifts, decrease if stick feels unresponsive
   ```python
   DEFAULT_SETTINGS = {
       # Other settings...
       'controller_deadzone': 0.15,  # Try values between 0.1 and 0.25
   }
   ```

2. **Inverted axes** (up/down or left/right reversed):
   - Use the controller_test.py to see axis behavior
   - Update the controller logic in `input_handler.py` if needed

## How Controller Support Works

The game uses a unified input handling system that:

1. Detects and initializes controllers automatically
2. Maps controller inputs to game actions consistently
3. Handles both digital (button) and analog (stick) inputs
4. Supports hot-plugging (connect/disconnect during gameplay)
5. Provides debug tools to diagnose issues

## Still Having Issues?

If you continue to have problems:

1. Check the console for error messages
2. Make sure your controller is working with other applications
3. Try updating your controller's firmware if applicable
4. As a last resort, use keyboard controls (always supported) 