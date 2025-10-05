"""
Configuration module for the Chess Game

This module contains all constants, settings, and configuration values
used throughout the application.
"""

class GameConfig:
    """Main game configuration settings"""

    # Window and display settings
    SCREEN_SIZE_PERCENTAGE = 0.75  # 75% of screen dimensions
    WINDOW_ASPECT_RATIO = 1.4      # Wider to accommodate help panel
    MIN_WINDOW_WIDTH = 600         # Minimum window width in pixels
    MIN_WINDOW_HEIGHT = 429        # Minimum window height (calculated from width/aspect ratio)

    # Board sizing and positioning
    BOARD_SIZE_PERCENTAGE = 0.85   # 85% of smaller window dimension
    BOARD_VERTICAL_MULTIPLIER = 0.9 # Multiplier for available vertical space
    BOARD_MARGIN_PERCENTAGE = 0.07 # 7% margin from edges

    # Help panel
    HELP_PANEL_WIDTH_PERCENTAGE = 0.35  # 35% of window width for help panel
    HELP_PANEL_MARGIN_PERCENTAGE = 0.02 # 2% margin between board and help panel
    HELP_PANEL_TOP_PADDING = 0.015      # 1.5% of window height for top padding
    HELP_PANEL_TABLE_MARGIN = 0.03      # 3% of panel width for table margins
    HELP_PANEL_TABLE_PADDING = 0.015    # 1.5% of panel width for table padding

    # VCR buttons
    VCR_BUTTON_SIZE_PERCENTAGE = 0.04   # 4% of window width
    VCR_BUTTON_SPACING_PERCENTAGE = 0.008 # 0.8% of window width
    VCR_BUTTON_BOTTOM_MARGIN = 0.015    # 1.5% of window height from bottom

    # Flip Board and Help buttons
    FLIP_HELP_BUTTON_HEIGHT = 0.019     # 1.9% of window height
    FLIP_HELP_BUTTON_SPACING = 0.008    # 0.8% of window width
    FLIP_HELP_BUTTON_PADDING = 0.015    # 1.5% of window width for text padding
    FLIP_HELP_BUTTON_MARGIN_RIGHT = 0.008 # 0.8% of window width from panel edge
    FLIP_HELP_BUTTON_Y_OFFSET = 0.008   # 0.8% of window height below stats panel

    # Checkbox settings
    CHECKBOX_SIZE_PERCENTAGE = 0.025    # 2.5% of window width for checkbox size
    CHECKBOX_SPACING_PERCENTAGE = 0.05  # 5% of window height between checkboxes
    CHECKBOX_LABEL_SPACING = 0.01       # 1% of window width between checkbox and label
    CHECKBOX_SHADOW_OFFSET = 0.002      # 0.2% of window width for shadow
    CHECKBOX_CORNER_RADIUS = 0.003      # 0.3% of window width for rounded corners

    # Captured pieces display
    CAPTURED_PIECE_SIZE_RATIO = 0.33    # Captured piece size relative to square size
    CAPTURED_PIECE_Y_OFFSET = 0.008     # 0.8% of window height above/below board
    CAPTURED_PIECE_SPACING = 0.004      # 0.4% of window width between pieces
    CAPTURED_PAWN_SCALE = 0.7           # Pawns are 70% of other captured pieces
    CAPTURED_ADVANTAGE_SPACING = 0.004  # 0.4% of window width before advantage text

    # Board border and elements
    BOARD_BORDER_THICKNESS = 0.002      # 0.2% of window width
    COORDINATE_OFFSET = 0.008           # 0.8% of window height for coordinate text

    # Statistics table
    STATS_ROW_PADDING = 0.004           # 0.4% of window height for row padding
    STATS_TABLE_ROWS = 9                # Number of rows in stats table
    STATS_CELL_PADDING = 0.004          # 0.4% of window width for cell padding

    # Help overlay (modal window)
    HELP_OVERLAY_WIDTH = 0.8            # 80% of window width
    HELP_OVERLAY_HEIGHT = 0.8           # 80% of window height
    HELP_OVERLAY_BORDER = 0.003         # 0.3% of window width
    HELP_OVERLAY_PADDING = 0.02         # 2% of overlay width
    HELP_OVERLAY_LINE_SPACING = 0.006   # 0.6% of overlay height
    HELP_OVERLAY_COLUMN_SPACING = 0.04  # 4% of overlay width

    # Font sizes (as percentage of board size)
    FONT_LARGE_PERCENTAGE = 0.09   # 9% of board size
    FONT_MEDIUM_PERCENTAGE = 0.06  # 6% of board size
    FONT_SMALL_PERCENTAGE = 0.045  # 4.5% of board size
    FONT_BUTTON_PERCENTAGE = 0.035  # 3.5% of window width (smaller button font)

class Colors:
    """Color constants for the game"""

    # Basic RGB colors
    RGB_WHITE = (255, 255, 255)
    RGB_BLACK = (0, 0, 0)

    # Chess board colors
    LIGHT_SQUARE = (240, 217, 181)  # Light brown
    DARK_SQUARE = (181, 136, 99)    # Dark brown

    # Last move highlighting colors (lichess-style)
    LIGHT_SQUARE_LAST_MOVE = (205, 210, 106)  # Light green overlay on light squares
    DARK_SQUARE_LAST_MOVE = (170, 162, 58)    # Dark green overlay on dark squares

    # UI highlight colors
    HIGHLIGHT = (255, 255, 0)       # Yellow for highlights
    SELECTED = (160, 160, 160)      # Neutral grey for selected square

    # Button colors
    BUTTON_BACKGROUND_COLOR = (100, 100, 100)
    BUTTON_HOVER_COLOR = (150, 150, 150)
    BUTTON_TEXT_COLOR = (255, 255, 255)

    # Text colors
    BLACK_TEXT = (0, 0, 0)

    # Board annotation colors (neutral, warning, caution, positive)
    ANNOTATION_NEUTRAL = (128, 128, 128)     # Light grey for neutral/informational
    ANNOTATION_WARNING = (255, 0, 0)        # Red for strong warnings
    ANNOTATION_CAUTION = (255, 255, 0)      # Yellow for awareness/caution
    ANNOTATION_POSITIVE = (0, 255, 0)       # Green for good/positive

    # UI Panel colors
    HELP_PANEL_BACKGROUND = (250, 250, 250) # Light grey panel background
    CHECKBOX_SHADOW = (200, 200, 200)       # Checkbox shadow
    CHECKBOX_UNCHECKED_BG = (248, 248, 248) # Checkbox unchecked background
    CHECKBOX_BORDER_UNCHECKED = (180, 180, 180) # Border when unchecked
    LABEL_TEXT_COLOR = (60, 60, 60)         # Dark grey for labels

    # Table colors for statistics
    TABLE_BORDER = (220, 220, 220)          # Faint gray for cell borders
    TABLE_FAVORABLE_BG = (230, 255, 230)    # More pronounced green background
    TABLE_UNFAVORABLE_BG = (255, 230, 230)  # More pronounced red background
    TABLE_NEUTRAL_BG = (250, 250, 250)      # Light gray for neutral rows

    # Game status colors
    STATUS_CHECK = (255, 0, 0)              # Red for check
    STATUS_CHECKMATE = (255, 0, 0)          # Red for checkmate
    STATUS_NORMAL = (0, 128, 0)             # Green for normal moves
    STALEMATE_TEXT = (255, 0, 0)            # Red for stalemate text
    STALEMATE_OUTLINE = (0, 0, 0)           # Black outline for stalemate

    # Piece placeholder colors
    PIECE_BORDER = (100, 100, 100)          # Grey border for piece placeholders

    # Fork visualization colors
    FORK_ORIGIN = (0, 255, 255)             # Cyan for fork origin (very bright)
    FORK_DESTINATION = (0, 128, 255)        # Bright blue for fork destination
    FORK_TARGET = (255, 0, 255)             # Magenta for forked pieces (very visible)

class AnimationConfig:
    """Animation timing and settings"""

    # Move animation
    MOVE_INDICATOR_RADIUS_FACTOR = 0.25  # Radius as factor of square size

class GameConstants:
    """Chess game constants"""

    BOARD_SIZE = 8
    UNDO_HISTORY_LIMIT = 50  # Maximum moves to keep for undo

    # File paths
    PIECE_IMAGE_DIRECTORY = "images/2x/"

    # Piece size factors
    PAWN_SIZE_FACTOR = 0.65     # Pawns are 65% of square size
    PIECE_SIZE_FACTOR = 0.75    # Other pieces are 75% of square size

    # Standard chess piece values for material evaluation
    # Uses python-chess piece type constants (integers 1-6)
    PIECE_VALUES = {
        1: 1,    # PAWN
        2: 3,    # KNIGHT
        3: 3,    # BISHOP
        4: 5,    # ROOK
        5: 9,    # QUEEN
        6: 0     # KING (invaluable/special case)
    }