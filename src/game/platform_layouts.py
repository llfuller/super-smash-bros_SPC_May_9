'''
Platform layout configurations for different levels/arenas.
This allows for easy modification or addition of new layouts.
'''

# Standard layout - the default one used in the game
STANDARD_LAYOUT = [
    # format: (platform_type, x, y, width, height)
    ('floor', 0, 670, 700, 30),      # Base floor
    ('platform', 60, 460, 200, 50),  # Left platform
    ('platform', 435, 460, 200, 50), # Right platform
    ('platform', 250, 260, 200, 50)  # Middle platform
]

# A more complex layout with additional platforms
ADVANCED_LAYOUT = [
    ('floor', 0, 670, 700, 30),      # Base floor
    ('platform', 60, 520, 150, 40),  # Bottom left
    ('platform', 490, 520, 150, 40), # Bottom right
    ('platform', 275, 400, 150, 40), # Middle
    ('platform', 100, 300, 150, 40), # Top left
    ('platform', 450, 300, 150, 40)  # Top right
]

# Simple layout with minimal platforms
SIMPLE_LAYOUT = [
    ('floor', 0, 670, 700, 30),      # Base floor
    ('platform', 250, 400, 200, 50)  # Single middle platform
]

# Dictionary mapping layout names to their configurations
LAYOUTS = {
    'standard': STANDARD_LAYOUT,
    'advanced': ADVANCED_LAYOUT,
    'simple': SIMPLE_LAYOUT
}

def get_layout(name='standard'):
    """Get a platform layout by name"""
    return LAYOUTS.get(name, STANDARD_LAYOUT) 