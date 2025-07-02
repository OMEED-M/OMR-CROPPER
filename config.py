"""
Configuration settings for OMR Sheet Marker Detection & Cropping System

This module contains all configuration parameters organized by pipeline step.
Only variables actually used in the codebase are included.
"""

# =============================================================================
# CORE PROCESSING SETTINGS
# =============================================================================

# Step 1: Image preprocessing
GAUSSIAN_BLUR_KERNEL = (5, 5)
THRESHOLD_VALUE = 150
MARGIN_CROP_RATIO = 0.02

# Step 2: Corner detection and grid analysis
CORNER_REGION_RATIO_X = 5
CORNER_REGION_RATIO_Y = 5
CELL_SIZE_RATIO = 0.005
WHITE_CELL_THRESHOLD = 70
SYNTHETIC_MARKER_SIZE_RATIO = 0.004

# Step 3: Corner verification
CORNER_VERIFICATION_TOLERANCE_RATIO = 0.02  # Relative to image diagonal
CORNER_VERIFICATION_MIN_LINES = 1
CORNER_VERIFICATION_CIRCLE_RADIUS_RATIO = 0.015  # Relative to image diagonal

# Step 4: Output cropping
OUTPUT_WIDTH = 800
OUTPUT_HEIGHT = 1200

# =============================================================================
# VISUALIZATION SETTINGS
# =============================================================================

# Scalable visualization ratios (used by actual pipeline)
DASH_LENGTH_RATIO = 0.008
CORNER_BOUNDARY_THICKNESS_RATIO = 0.001
BEST_CELL_CIRCLE_RADIUS_RATIO = 0.006
BEST_CELL_CIRCLE_THICKNESS_RATIO = 0.0015

# Fixed visualization settings (used by step 1 preprocessing)
VISUALIZATION_HEIGHT = 600

# Grid and cell display
CELL_GRID_THICKNESS = 1

# =============================================================================
# COLORS (BGR FORMAT)
# =============================================================================

# Primary colors for corners
COLOR_RED = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (255, 0, 0)
COLOR_CYAN = (255, 255, 0)

# Additional colors for visualization
COLOR_PINK = (255, 192, 203)
COLOR_ORANGE = (255, 165, 0)
COLOR_LIGHT_BLUE = (0, 165, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_CYAN_ARROWS = (0, 255, 255)

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

# Operation modes
DEBUG_MODE = True

# File handling
SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

# Directory structure
tmp_dir = "tmp"
steps_dir = "steps"

# Missing corner testing (modified by CLI and tests)
ENABLE_MISSING_CORNER_CALCULATION = False
FORCE_MISSING_CORNER = None
