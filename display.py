"""
Chess Display Module

This module handles the visual representation of the chess board and game state.
It provides functionality to display the board, pieces, and game information.
"""

from typing import Optional, Tuple, List
import pygame
import json
import os
import sys
import math
import time
import chess
from chess_board import BoardState, square_from_coords, coords_from_square
from config import GameConfig, Colors, AnimationConfig, GameConstants

# Get the correct path for bundled resources (PyInstaller compatibility)
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Running in normal Python environment
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ChessDisplay:
    """Handles the visual display of the chess game"""
    
    def __init__(self, window_width: int = 800, window_height: int = 600):
        """Initialize the display with window dimensions"""
        self.window_width = window_width
        self.window_height = window_height
        
        # Colors from config
        self.RGB_WHITE = Colors.RGB_WHITE
        self.RGB_BLACK = Colors.RGB_BLACK
        self.LIGHT_SQUARE = Colors.LIGHT_SQUARE
        self.DARK_SQUARE = Colors.DARK_SQUARE
        self.HIGHLIGHT = Colors.HIGHLIGHT
        self.SELECTED = Colors.SELECTED
        
        # Board dimensions using config values (restored to normal)
        self.board_size = int(min(window_width, window_height * 0.9) * GameConfig.BOARD_SIZE_PERCENTAGE)
        self.square_size = self.board_size // GameConstants.BOARD_SIZE

        # Position board - horizontally with margin, vertically centered
        self.board_margin_x = int(window_width * GameConfig.BOARD_MARGIN_PERCENTAGE)
        # Vertically center the board (accounting for legend space)
        legend_space = self.square_size  # Space for coordinate legends
        total_board_height = self.board_size + legend_space
        self.board_margin_y = (window_height - total_board_height) // 2
        
        # Ensure pygame is initialized before creating fonts
        if not pygame.get_init():
            pygame.init()
        
        # Font setup using config values - modern sans-serif fonts
        try:
            # Try to use modern system fonts (Inter, SF Pro, Roboto, etc.)
            font_list = 'inter,sfprodisplay,roboto,notosans,opensans,lato,calibri,segoeui,helvetica,arial,sans-serif'
            self.font_large = pygame.font.SysFont(font_list, int(self.board_size * GameConfig.FONT_LARGE_PERCENTAGE), bold=True)
            self.font_medium = pygame.font.SysFont(font_list, int(self.board_size * GameConfig.FONT_MEDIUM_PERCENTAGE), bold=False)
            self.font_medium_bold = pygame.font.SysFont(font_list, int(self.board_size * GameConfig.FONT_MEDIUM_PERCENTAGE), bold=True)
            self.font_small = pygame.font.SysFont(font_list, int(self.board_size * GameConfig.FONT_SMALL_PERCENTAGE), bold=False)
            self.font_small_bold = pygame.font.SysFont(font_list, int(self.board_size * GameConfig.FONT_SMALL_PERCENTAGE), bold=True)
        except:
            # Fallback to default if system fonts aren't available
            self.font_large = pygame.font.Font(None, int(self.board_size * GameConfig.FONT_LARGE_PERCENTAGE))
            self.font_medium = pygame.font.Font(None, int(self.board_size * GameConfig.FONT_MEDIUM_PERCENTAGE))
            self.font_medium_bold = pygame.font.Font(None, int(self.board_size * GameConfig.FONT_MEDIUM_PERCENTAGE))
            self.font_small = pygame.font.Font(None, int(self.board_size * GameConfig.FONT_SMALL_PERCENTAGE))
            self.font_small_bold = pygame.font.Font(None, int(self.board_size * GameConfig.FONT_SMALL_PERCENTAGE))
        
        # Load piece images (placeholder - you'd load actual piece images here)
        self.piece_images = self._load_piece_images()

        # Create move indicator circle surface once
        self.move_indicator = self._create_move_indicator()

        # Help panel dimensions and positioning
        self.help_panel_width = int(window_width * GameConfig.HELP_PANEL_WIDTH_PERCENTAGE)
        self.help_panel_x = self.board_margin_x + self.board_size + int(window_width * GameConfig.HELP_PANEL_MARGIN_PERCENTAGE)
        self.help_panel_y = self.board_margin_y

        # Checkbox dimensions
        self.checkbox_size = int(window_width * GameConfig.CHECKBOX_SIZE_PERCENTAGE)
        self.checkbox_spacing = int(window_height * GameConfig.CHECKBOX_SPACING_PERCENTAGE)

        # Help options - load from settings file if available
        self.settings_file = ".capablanca"
        self.help_options = [
            {"name": "Flip Board", "key": "flip_board", "enabled": False}
        ]
        self._load_settings()

        # Checkmate animation variables
        self.checkmate_animation_start_time = None
        self.checkmate_king_position = None

        # Move animation variables (for navigation)
        self.move_animation_start_time = None
        self.move_animation_from_square = None
        self.move_animation_to_square = None
        self.move_animation_piece = None
        self.move_animation_duration = 0.1  # 100ms in seconds (1/10 second)

        # Cache activity scores to avoid constant recalculation
        self.cached_activity_white = 0
        self.cached_activity_black = 0
        self.activity_cache_valid = False

        # Statistics hover feedback system
        self.hovered_statistic = None  # (stat_type, player_or_opponent) e.g., ("activity", "player")
        self.statistic_cell_rects = {}  # Track clickable areas for each statistic

        # Cached gradient surfaces for piece glows
        self.hanging_glow_surface = None
        self.hanging_glow_size = None
        self.attacked_glow_surface = None
        self.attacked_glow_size = None

        # VCR control buttons
        self.vcr_button_rects = {}  # Store button rectangles for click detection
        self.vcr_button_size = int(window_width * 0.04)  # 4% of window width

    def invalidate_activity_cache(self):
        """Invalidate activity cache when board state changes"""
        self.activity_cache_valid = False

    def draw_vcr_button(self, screen, x: int, y: int, button_type: str, enabled: bool = True) -> pygame.Rect:
        """Draw a VCR control button and return its rectangle"""
        size = self.vcr_button_size
        button_rect = pygame.Rect(x, y, size, size)

        # Symbol color (black if enabled, light grey if disabled)
        symbol_color = (0, 0, 0) if enabled else (200, 200, 200)

        # Draw symbol based on button type
        padding = size // 6
        if button_type == "rewind":
            # Double left arrow (|<<)
            # Draw bar
            bar_x = x + padding
            pygame.draw.rect(screen, symbol_color, (bar_x, y + padding, 2, size - 2*padding))
            # Draw double triangles
            tri1_x = bar_x + 4
            tri2_x = tri1_x + (size - 2*padding) // 2
            for tri_x in [tri1_x, tri2_x]:
                points = [
                    (tri_x + (size - 2*padding) // 2, y + padding),
                    (tri_x, y + size // 2),
                    (tri_x + (size - 2*padding) // 2, y + size - padding)
                ]
                pygame.draw.polygon(screen, symbol_color, points)

        elif button_type == "back":
            # Single left arrow (<)
            mid_x = x + size // 2
            points = [
                (mid_x + padding, y + padding),
                (mid_x - padding, y + size // 2),
                (mid_x + padding, y + size - padding)
            ]
            pygame.draw.polygon(screen, symbol_color, points)

        elif button_type == "forward":
            # Single right arrow (>)
            mid_x = x + size // 2
            points = [
                (mid_x - padding, y + padding),
                (mid_x + padding, y + size // 2),
                (mid_x - padding, y + size - padding)
            ]
            pygame.draw.polygon(screen, symbol_color, points)

        elif button_type == "fast_forward":
            # Double right arrow (>>|)
            # Draw double triangles
            tri1_x = x + padding
            tri2_x = tri1_x + (size - 2*padding) // 2
            for tri_x in [tri1_x, tri2_x]:
                points = [
                    (tri_x, y + padding),
                    (tri_x + (size - 2*padding) // 2, y + size // 2),
                    (tri_x, y + size - padding)
                ]
                pygame.draw.polygon(screen, symbol_color, points)
            # Draw bar
            bar_x = x + size - padding - 2
            pygame.draw.rect(screen, symbol_color, (bar_x, y + padding, 2, size - 2*padding))

        return button_rect
    
    def _load_piece_images(self) -> dict:
        """Load and scale piece images from PNG files"""
        images = {}

        # Map piece types to their string representations for filenames
        piece_symbols = {
            chess.PAWN: 'P',
            chess.KNIGHT: 'N',
            chess.BISHOP: 'B',
            chess.ROOK: 'R',
            chess.QUEEN: 'Q',
            chess.KING: 'K'
        }

        for color in [chess.WHITE, chess.BLACK]:
            for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
                # Calculate piece size based on type (pawns smaller than other pieces)
                if piece_type == chess.PAWN:
                    piece_size = int(self.square_size * 0.65)
                else:
                    piece_size = int(self.square_size * 0.75)

                # Create filename based on naming convention: {color}{piece}.png
                color_prefix = "w" if color == chess.WHITE else "b"
                piece_symbol = piece_symbols[piece_type]
                relative_filename = f"images/2x/{color_prefix}{piece_symbol}.png"
                filename = get_resource_path(relative_filename)

                try:
                    # Load the original image
                    original_image = pygame.image.load(filename)

                    # Scale once using smooth scaling and cache it
                    scaled_image = pygame.transform.smoothscale(original_image, (piece_size, piece_size))

                    # Store with the key format: "w1" for white pawn, "b6" for black king, etc.
                    color_str = "w" if color == chess.WHITE else "b"
                    key = f"{color_str}{piece_type}"
                    images[key] = scaled_image

                except pygame.error as e:
                    pass  # Could not load piece image
                    # Create a fallback colored rectangle if image loading fails
                    surface = pygame.Surface((piece_size, piece_size))
                    if color == chess.WHITE:
                        surface.fill(self.RGB_WHITE)
                    else:
                        surface.fill(self.RGB_BLACK)
                    pygame.draw.rect(surface, Colors.PIECE_BORDER, surface.get_rect(), 2)

                    color_str = "w" if color == chess.WHITE else "b"
                    key = f"{color_str}{piece_type}"
                    images[key] = surface

        return images

    def _create_move_indicator(self) -> pygame.Surface:
        """Create a translucent circle surface for move indicators"""
        # Create a surface with per-pixel alpha
        circle_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)

        # Circle size is 1/4 of the square
        circle_radius = self.square_size // 4
        center_x = self.square_size // 2
        center_y = self.square_size // 2

        # Draw translucent circle (light grey with alpha for subtle visibility)
        circle_color = (*Colors.ANNOTATION_NEUTRAL, 100)  # Light grey with transparency
        pygame.draw.circle(circle_surface, circle_color, (center_x, center_y), circle_radius)

        return circle_surface

    def draw_help_panel(self, screen, board_state=None, is_board_flipped=False) -> None:
        """Draw the help panel with checkboxes on the right side of the board and statistics below"""
        # Draw panel background (optional - subtle background)
        panel_rect = pygame.Rect(self.help_panel_x, self.help_panel_y,
                               self.help_panel_width, self.board_size)
        pygame.draw.rect(screen, Colors.HELP_PANEL_BACKGROUND, panel_rect)
        pygame.draw.rect(screen, Colors.RGB_BLACK, panel_rect, 1)

        # Draw checkboxes
        current_y = self.help_panel_y + 20
        for i, option in enumerate(self.help_options):
            self._draw_checkbox(screen, self.help_panel_x + 10, current_y, option)
            current_y += self.checkbox_spacing

        # Draw statistics below checkboxes if board_state is provided
        if board_state:
            # Calculate vertical centering for statistics table
            # 9 rows in the table, calculate total height needed
            stats_row_height = self.font_medium.get_height() + 6
            total_table_height = 9 * stats_row_height

            # Calculate space for VCR controls at bottom
            vcr_controls_height = self.vcr_button_size + 40  # Button height + padding

            # Center the table in the remaining vertical space (excluding VCR controls)
            remaining_vertical_space = self.board_size - (current_y - self.help_panel_y) - vcr_controls_height
            centered_start_y = current_y + (remaining_vertical_space - total_table_height) // 2

            self._draw_panel_statistics(screen, board_state, is_board_flipped, centered_start_y)

            # Draw VCR controls at the bottom
            self._draw_vcr_controls(screen, board_state)

    def _draw_panel_statistics(self, screen, board_state, is_board_flipped: bool, start_y: int) -> None:
        """Draw activity and pawn statistics in spreadsheet-style table format"""
        # Clear previous cell rectangles
        self.statistic_cell_rects = {}

        # Table dimensions - reduced size
        table_width = self.help_panel_width - 40  # Increased margin for smaller box
        table_x = self.help_panel_x + 20
        row_height = self.font_medium.get_height() + 6  # Moderate padding for readable rows

        # Column widths (proportional to table width)
        col1_width = int(table_width * 0.5)   # Statistic name (left)
        col2_width = int(table_width * 0.25)  # Player score (center)
        col3_width = int(table_width * 0.25)  # Opponent score (center)

        # Gather all statistics data
        white_activity, black_activity = board_state.get_activity_scores()
        white_pawns, black_pawns = board_state.get_pawn_counts()
        (white_stats, black_stats) = board_state.get_pawn_statistics()

        if is_board_flipped:
            player_activity, opponent_activity = black_activity, white_activity
            player_pawns, opponent_pawns = black_pawns, white_pawns
            player_stats, opponent_stats = black_stats, white_stats
        else:
            player_activity, opponent_activity = white_activity, black_activity
            player_pawns, opponent_pawns = white_pawns, black_pawns
            player_stats, opponent_stats = white_stats, black_stats

        player_backward, player_isolated, player_doubled, player_passed = player_stats
        opponent_backward, opponent_isolated, opponent_doubled, opponent_passed = opponent_stats

        # Get development statistics
        white_development, black_development = board_state.get_development_scores()
        if is_board_flipped:
            player_development, opponent_development = black_development, white_development
        else:
            player_development, opponent_development = white_development, black_development

        # Get attacked piece statistics
        white_attacked, black_attacked = board_state.get_attacked_scores()
        if is_board_flipped:
            player_attacked, opponent_attacked = black_attacked, white_attacked
        else:
            player_attacked, opponent_attacked = white_attacked, black_attacked

        # Get hanging piece statistics
        white_hanging, black_hanging = board_state.get_hanging_scores()
        if is_board_flipped:
            player_hanging, opponent_hanging = black_hanging, white_hanging
        else:
            player_hanging, opponent_hanging = white_hanging, black_hanging

        # Table data: (name, player_value, opponent_value, higher_is_better)
        table_data = [
            ("Hanging", player_hanging, opponent_hanging, False),  # Lower is better
            ("Attacked", player_attacked, opponent_attacked, False),  # Lower is better
            ("Developed", player_development, opponent_development, True),
            ("Passed", player_passed, opponent_passed, True),         # Higher is better
            ("Backward", player_backward, opponent_backward, False),  # Lower is better
            ("Isolated", player_isolated, opponent_isolated, False),  # Lower is better
            ("Doubled", player_doubled, opponent_doubled, False),     # Lower is better
            ("Pawns", player_pawns, opponent_pawns, True),
            ("Activity", player_activity, opponent_activity, True)
        ]

        current_y = start_y

        # Draw each row
        for row_name, player_val, opponent_val, higher_is_better in table_data:
            # Determine row background color based on favorability
            if player_val == opponent_val:
                row_bg_color = Colors.TABLE_NEUTRAL_BG
            elif higher_is_better:
                # For Activity and Pawns: higher is better
                if player_val > opponent_val:
                    row_bg_color = Colors.TABLE_FAVORABLE_BG
                else:
                    row_bg_color = Colors.TABLE_UNFAVORABLE_BG
            else:
                # For Backward, Isolated, Doubled: lower is better
                if player_val < opponent_val:
                    row_bg_color = Colors.TABLE_FAVORABLE_BG
                else:
                    row_bg_color = Colors.TABLE_UNFAVORABLE_BG

            # Draw row background
            row_rect = pygame.Rect(table_x, current_y, table_width, row_height)
            pygame.draw.rect(screen, row_bg_color, row_rect)

            # Draw cell borders (faint gray)
            # Top border
            pygame.draw.line(screen, Colors.TABLE_BORDER,
                           (table_x, current_y), (table_x + table_width, current_y))
            # Left border
            pygame.draw.line(screen, Colors.TABLE_BORDER,
                           (table_x, current_y), (table_x, current_y + row_height))
            # Vertical separators
            pygame.draw.line(screen, Colors.TABLE_BORDER,
                           (table_x + col1_width, current_y), (table_x + col1_width, current_y + row_height))
            pygame.draw.line(screen, Colors.TABLE_BORDER,
                           (table_x + col1_width + col2_width, current_y),
                           (table_x + col1_width + col2_width, current_y + row_height))
            # Right border
            pygame.draw.line(screen, Colors.TABLE_BORDER,
                           (table_x + table_width, current_y), (table_x + table_width, current_y + row_height))

            # Column 1: Statistic name (left-aligned)
            name_surface = self.font_medium.render(row_name, True, Colors.RGB_BLACK)
            name_x = table_x + 5  # 5px padding from left
            name_y = current_y + (row_height - name_surface.get_height()) // 2
            screen.blit(name_surface, (name_x, name_y))

            # Column 2: Player value (center-aligned)
            # Use red bold font if this is Hanging row and value > 0
            if row_name == "Hanging" and player_val > 0:
                player_surface = self.font_medium_bold.render(str(player_val), True, (255, 0, 0))
            else:
                player_surface = self.font_medium.render(str(player_val), True, Colors.RGB_BLACK)
            player_x = table_x + col1_width + (col2_width - player_surface.get_width()) // 2
            player_y = current_y + (row_height - player_surface.get_height()) // 2
            screen.blit(player_surface, (player_x, player_y))

            # Column 3: Opponent value (center-aligned)
            # Use red bold font if this is Hanging row and value > 0
            if row_name == "Hanging" and opponent_val > 0:
                opponent_surface = self.font_medium_bold.render(str(opponent_val), True, (255, 0, 0))
            else:
                opponent_surface = self.font_medium.render(str(opponent_val), True, Colors.RGB_BLACK)
            opponent_x = table_x + col1_width + col2_width + (col3_width - opponent_surface.get_width()) // 2
            opponent_y = current_y + (row_height - opponent_surface.get_height()) // 2
            screen.blit(opponent_surface, (opponent_x, opponent_y))

            # Store cell rectangles for hover detection
            player_cell_rect = pygame.Rect(table_x + col1_width, current_y, col2_width, row_height)
            opponent_cell_rect = pygame.Rect(table_x + col1_width + col2_width, current_y, col3_width, row_height)

            # Use lowercase for consistent key names
            stat_key = row_name.lower()
            self.statistic_cell_rects[f"{stat_key}_player"] = player_cell_rect
            self.statistic_cell_rects[f"{stat_key}_opponent"] = opponent_cell_rect

            current_y += row_height

        # Draw bottom border of the table
        pygame.draw.line(screen, Colors.TABLE_BORDER,
                       (table_x, current_y), (table_x + table_width, current_y))

    def _draw_vcr_controls(self, screen, board_state) -> None:
        """Draw VCR control buttons at the bottom of the help panel"""
        # Clear previous button rectangles
        self.vcr_button_rects = {}

        # Position buttons at the bottom of the panel, centered
        button_spacing = 10
        total_width = 4 * self.vcr_button_size + 3 * button_spacing
        start_x = self.help_panel_x + (self.help_panel_width - total_width) // 2
        button_y = self.help_panel_y + self.board_size - self.vcr_button_size - 20

        # Determine button states
        can_undo = board_state.can_undo()
        can_redo = board_state.can_redo()

        # Check if we can rewind to beginning (more than one undo available)
        can_rewind = len(board_state.undo_stack) > 0
        # Check if we can fast forward to end (redo stack has items)
        can_fast_forward = len(board_state.redo_stack) > 0

        # Draw buttons
        buttons = [
            ("rewind", can_rewind),
            ("back", can_undo),
            ("forward", can_redo),
            ("fast_forward", can_fast_forward)
        ]

        current_x = start_x
        for button_type, enabled in buttons:
            rect = self.draw_vcr_button(screen, current_x, button_y, button_type, enabled)
            self.vcr_button_rects[button_type] = rect
            current_x += self.vcr_button_size + button_spacing

    def update_statistics_hover(self, mouse_pos: tuple) -> None:
        """Update which statistic cell is being hovered"""
        self.hovered_statistic = None

        for cell_key, cell_rect in self.statistic_cell_rects.items():
            if cell_rect.collidepoint(mouse_pos):
                # Parse the cell key (e.g., "activity_player" -> ("activity", "player"))
                parts = cell_key.split('_')
                if len(parts) >= 2:
                    stat_type = parts[0]
                    player_side = parts[1]
                    self.hovered_statistic = (stat_type, player_side)
                break

    def get_highlighted_pieces_for_statistic(self, board_state, stat_type: str, player_side: str, is_board_flipped: bool):
        """Get pieces or squares to highlight based on the hovered statistic"""
        if not stat_type or not player_side:
            return []

        # Determine which color we're showing (player vs opponent)
        if is_board_flipped:
            player_color = chess.BLACK
            opponent_color = chess.WHITE
        else:
            player_color = chess.WHITE
            opponent_color = chess.BLACK

        target_color = player_color if player_side == "player" else opponent_color

        if stat_type == "activity":
            return self._get_activity_squares(board_state, target_color)
        elif stat_type == "developed":
            return self._get_developed_pieces(board_state, target_color)
        elif stat_type == "attacked":
            return self._get_attacked_pieces(board_state, target_color)
        elif stat_type == "hanging":
            return self._get_hanging_pieces(board_state, target_color)
        elif stat_type == "pawns":
            return self._get_pawn_pieces(board_state, target_color)
        elif stat_type == "backward":
            return self._get_backward_pawn_pieces(board_state, target_color)
        elif stat_type == "isolated":
            return self._get_isolated_pawn_pieces(board_state, target_color)
        elif stat_type == "doubled":
            return self._get_doubled_pawn_pieces(board_state, target_color)
        elif stat_type == "passed":
            return self._get_passed_pawn_pieces(board_state, target_color)

        return []

    def _get_activity_squares(self, board_state, color: bool):
        """Get all squares that pieces of this color can legally reach"""
        reachable_squares = set()

        # Save current turn
        original_turn = board_state.board.turn

        # Set turn to the color we're checking
        board_state.board.turn = color

        # Only count squares that pieces can legally reach
        for move in board_state.board.legal_moves:
            piece = board_state.board.piece_at(move.from_square)
            if piece and piece.color == color and piece.piece_type != chess.PAWN:
                reachable_squares.add(coords_from_square(move.to_square))

        # Restore original turn
        board_state.board.turn = original_turn

        return list(reachable_squares)

    def _get_developed_pieces(self, board_state, color: bool):
        """Get all developed pieces of this color"""
        developed_pieces = []

        if color == chess.WHITE:
            starting_rank = 0  # rank 1
            king_start = chess.E1
        else:
            starting_rank = 7  # rank 8
            king_start = chess.E8

        # Knights, bishops, queen: off back rank = developed
        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.QUEEN]:
            for square in chess.SQUARES:
                piece = board_state.board.piece_at(square)
                if piece and piece.color == color and piece.piece_type == piece_type:
                    if chess.square_rank(square) != starting_rank:
                        developed_pieces.append(coords_from_square(square))

        # King: developed if castled (not on starting square)
        king_square = board_state.board.king(color)
        if king_square != king_start:
            developed_pieces.append(coords_from_square(king_square))

        # Rooks: developed if moved OR if rooks are connected
        rook_squares = []
        for square in chess.SQUARES:
            piece = board_state.board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.ROOK:
                rook_squares.append(square)

        # Check if rooks are connected
        rooks_connected = False
        if len(rook_squares) == 2:
            r1, r2 = rook_squares
            if chess.square_rank(r1) == starting_rank and chess.square_rank(r2) == starting_rank:
                file1, file2 = chess.square_file(r1), chess.square_file(r2)
                min_file, max_file = min(file1, file2), max(file1, file2)
                pieces_between = False
                for file in range(min_file + 1, max_file):
                    check_square = chess.square(file, starting_rank)
                    if board_state.board.piece_at(check_square):
                        pieces_between = True
                        break
                if not pieces_between:
                    rooks_connected = True

        # Add developed rooks to list
        for rook_square in rook_squares:
            if chess.square_rank(rook_square) != starting_rank:
                developed_pieces.append(coords_from_square(rook_square))
            elif rooks_connected:
                developed_pieces.append(coords_from_square(rook_square))

        return developed_pieces

    def _get_attacked_pieces(self, board_state, color: bool):
        """Get all pieces of this color that are attacked by the enemy"""
        attacked_pieces = []
        enemy_color = not color

        for square in chess.SQUARES:
            piece = board_state.board.piece_at(square)
            if piece and piece.color == color:
                if board_state.board.is_attacked_by(enemy_color, square):
                    attacked_pieces.append(coords_from_square(square))

        return attacked_pieces

    def _get_hanging_pieces(self, board_state, color: bool):
        """Get all hanging pieces of this color"""
        hanging_squares = board_state.get_hanging_pieces(color)
        return [coords_from_square(sq) for sq in hanging_squares]

    def _get_pawn_pieces(self, board_state, color: bool):
        """Get all pawn pieces of this color"""
        pawn_pieces = []
        for square in chess.SQUARES:
            piece = board_state.board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.PAWN:
                pawn_pieces.append(coords_from_square(square))
        return pawn_pieces

    def _get_backward_pawn_pieces(self, board_state, color: bool):
        """Get backward pawn pieces of this color"""
        backward_pawns = []
        enemy_color = not color
        pawn_direction = 1 if color == chess.WHITE else -1

        for square in chess.SQUARES:
            piece = board_state.board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.PAWN:
                # Check if this is a backward pawn (simplified version of the main logic)
                rank = chess.square_rank(square)
                file = chess.square_file(square)

                # Check if pawn can be defended
                can_be_defended = False
                defend_rank = rank - pawn_direction
                if 0 <= defend_rank < 8:
                    for defend_file in [file - 1, file + 1]:
                        if 0 <= defend_file < 8:
                            defend_square = chess.square(defend_file, defend_rank)
                            defender = board_state.board.piece_at(defend_square)
                            if defender and defender.color == color and defender.piece_type == chess.PAWN:
                                can_be_defended = True
                                break

                # Check if pawn can safely advance
                can_safely_advance = True
                advance_rank = rank + pawn_direction
                if 0 <= advance_rank < 8:
                    for enemy_file in [file - 1, file + 1]:
                        if 0 <= enemy_file < 8:
                            enemy_attack_rank = advance_rank + pawn_direction
                            if 0 <= enemy_attack_rank < 8:
                                enemy_square = chess.square(enemy_file, enemy_attack_rank)
                                enemy_piece = board_state.board.piece_at(enemy_square)
                                if enemy_piece and enemy_piece.color == enemy_color and enemy_piece.piece_type == chess.PAWN:
                                    can_safely_advance = False
                                    break

                if not can_be_defended and not can_safely_advance:
                    backward_pawns.append(coords_from_square(square))

        return backward_pawns

    def _get_isolated_pawn_pieces(self, board_state, color: bool):
        """Get isolated pawn pieces of this color"""
        isolated_pawns = []
        for square in chess.SQUARES:
            piece = board_state.board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.PAWN:
                # Check if there are friendly pawns on adjacent files
                file = chess.square_file(square)
                has_adjacent_pawn = False
                for adjacent_file in [file - 1, file + 1]:
                    if 0 <= adjacent_file < 8:
                        for check_rank in range(8):
                            check_square = chess.square(adjacent_file, check_rank)
                            adjacent_piece = board_state.board.piece_at(check_square)
                            if adjacent_piece and adjacent_piece.color == color and adjacent_piece.piece_type == chess.PAWN:
                                has_adjacent_pawn = True
                                break
                        if has_adjacent_pawn:
                            break

                if not has_adjacent_pawn:
                    isolated_pawns.append(coords_from_square(square))

        return isolated_pawns

    def _get_doubled_pawn_pieces(self, board_state, color: bool):
        """Get doubled pawn pieces of this color"""
        doubled_pawns = []
        # Count pawns per file and identify doubled ones
        for file in range(8):
            pawns_on_file = []
            for rank in range(8):
                square = chess.square(file, rank)
                piece = board_state.board.piece_at(square)
                if piece and piece.color == color and piece.piece_type == chess.PAWN:
                    pawns_on_file.append(coords_from_square(square))

            # If more than one pawn on this file, highlight ALL of them
            if len(pawns_on_file) > 1:
                doubled_pawns.extend(pawns_on_file)  # Add all pawns on doubled files

        return doubled_pawns

    def _get_passed_pawn_pieces(self, board_state, color: bool):
        """Get passed pawn pieces of this color"""
        passed_pawns = []
        enemy_color = not color
        promotion_direction = 1 if color == chess.WHITE else -1

        # Check each pawn
        for square in chess.SQUARES:
            piece = board_state.board.piece_at(square)
            if piece and piece.color == color and piece.piece_type == chess.PAWN:
                rank = chess.square_rank(square)
                file = chess.square_file(square)

                # Check if this pawn is passed
                is_passed = True

                # Check the path to promotion on this file and adjacent files
                for check_file in [file - 1, file, file + 1]:
                    if 0 <= check_file <= 7:  # Valid file
                        # Check all squares from current position to promotion rank
                        check_rank = rank + promotion_direction
                        while 0 <= check_rank <= 7:
                            check_square = chess.square(check_file, check_rank)
                            enemy_piece = board_state.board.piece_at(check_square)
                            if enemy_piece and enemy_piece.color == enemy_color and enemy_piece.piece_type == chess.PAWN:
                                is_passed = False
                                break
                            check_rank += promotion_direction

                        if not is_passed:
                            break

                if is_passed:
                    passed_pawns.append(coords_from_square(square))

        return passed_pawns

    def _draw_checkbox(self, screen, x: int, y: int, option: dict) -> None:
        """Draw a single stylish checkbox with label"""
        # Create rounded rectangle effect with layered rectangles
        corner_radius = 4

        # Draw shadow (slightly offset)
        shadow_rect = pygame.Rect(x + 2, y + 2, self.checkbox_size, self.checkbox_size)
        pygame.draw.rect(screen, Colors.CHECKBOX_SHADOW, shadow_rect, border_radius=corner_radius)

        # Main checkbox background
        checkbox_rect = pygame.Rect(x, y, self.checkbox_size, self.checkbox_size)
        if option["enabled"]:
            # Filled background when checked
            pygame.draw.rect(screen, Colors.ANNOTATION_POSITIVE, checkbox_rect, border_radius=corner_radius)
        else:
            # Light background when unchecked
            pygame.draw.rect(screen, Colors.CHECKBOX_UNCHECKED_BG, checkbox_rect, border_radius=corner_radius)

        # Border
        border_color = Colors.ANNOTATION_POSITIVE if option["enabled"] else Colors.CHECKBOX_BORDER_UNCHECKED
        pygame.draw.rect(screen, border_color, checkbox_rect, width=2, border_radius=corner_radius)

        # Draw checkmark if enabled
        if option["enabled"]:
            # Draw a more refined checkmark
            check_color = Colors.RGB_WHITE
            check_thickness = 3
            # Smoother checkmark coordinates
            check_x1 = x + self.checkbox_size * 0.25
            check_y1 = y + self.checkbox_size * 0.55
            check_x2 = x + self.checkbox_size * 0.45
            check_y2 = y + self.checkbox_size * 0.7
            check_x3 = x + self.checkbox_size * 0.75
            check_y3 = y + self.checkbox_size * 0.35

            pygame.draw.line(screen, check_color, (check_x1, check_y1), (check_x2, check_y2), check_thickness)
            pygame.draw.line(screen, check_color, (check_x2, check_y2), (check_x3, check_y3), check_thickness)

        # Draw label with better styling
        label_text = self.font_small.render(option["name"], True, Colors.LABEL_TEXT_COLOR)
        label_x = x + self.checkbox_size + 12
        label_y = y + (self.checkbox_size - label_text.get_height()) // 2
        screen.blit(label_text, (label_x, label_y))

    def get_checkbox_at_pos(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """Get the key of the checkbox at the given mouse position, if any"""
        mouse_x, mouse_y = mouse_pos

        current_y = self.help_panel_y + 20  # Starting y position for checkboxes (matches drawing)
        for option in self.help_options:
            # Create expanded clickable area that includes both checkbox and text label
            label_text = self.font_small.render(option["name"], True, Colors.LABEL_TEXT_COLOR)
            label_width = label_text.get_width()

            # Clickable area extends from checkbox to end of text label
            clickable_rect = pygame.Rect(self.help_panel_x + 10, current_y,
                                       self.checkbox_size + 12 + label_width, self.checkbox_size)
            if clickable_rect.collidepoint(mouse_x, mouse_y):
                return option["key"]
            current_y += self.checkbox_spacing

        return None

    def get_vcr_button_at_pos(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """Get the VCR button type at the given mouse position, if any"""
        for button_type, rect in self.vcr_button_rects.items():
            if rect.collidepoint(mouse_pos):
                return button_type
        return None

    def toggle_help_option(self, key: str) -> bool:
        """Toggle a help option and return its new state"""
        for option in self.help_options:
            if option["key"] == key:
                option["enabled"] = not option["enabled"]
                self._save_settings()  # Save settings when changed
                return option["enabled"]
        return False

    def is_help_option_enabled(self, key: str) -> bool:
        """Check if a help option is enabled"""
        for option in self.help_options:
            if option["key"] == key:
                return option["enabled"]
        return False

    def draw_move_indicator(self, screen, x: int, y: int) -> None:
        """Draw the pre-created move indicator at specified position"""
        screen.blit(self.move_indicator, (x, y))

    def draw_hanging_piece_indicator(self, screen, x: int, y: int, is_player_piece: bool) -> None:
        """Draw a hanging piece indicator with consistent border thickness"""

        # Simple, clear colors
        if is_player_piece:
            indicator_color = Colors.ANNOTATION_WARNING  # Red for player's hanging pieces (danger)
        else:
            indicator_color = Colors.ANNOTATION_POSITIVE  # Green for opponent's hanging pieces (opportunity)

        # Use same border thickness as blue highlights for consistency
        border_thickness = 4

        # Draw border on all four edges
        border_rect = pygame.Rect(x, y, self.square_size, self.square_size)
        pygame.draw.rect(screen, indicator_color, border_rect, border_thickness)

    def is_animation_active(self) -> bool:
        """Check if any animations are currently running"""
        return (self.checkmate_animation_start_time is not None or
                self.move_animation_start_time is not None)

    def start_move_animation(self, from_square: chess.Square, to_square: chess.Square, piece: chess.Piece) -> None:
        """Start animating a move for navigation (undo/redo)"""
        import time
        self.move_animation_start_time = time.time()
        self.move_animation_from_square = from_square
        self.move_animation_to_square = to_square
        self.move_animation_piece = piece

    def stop_move_animation(self) -> None:
        """Stop the move animation and invalidate caches"""
        self.move_animation_start_time = None
        self.move_animation_from_square = None
        self.move_animation_to_square = None
        self.move_animation_piece = None
        # Invalidate activity cache so statistics are recalculated
        self.invalidate_activity_cache()

    def start_checkmate_animation(self, board_state: BoardState) -> None:
        """Start the checkmate animation for the losing king"""
        import time
        self.checkmate_animation_start_time = time.time()

        # Find the checkmated king position
        losing_color = board_state.board.turn
        self.checkmate_king_position = board_state.board.king(losing_color)

    def draw_move_animation(self, screen, is_board_flipped: bool) -> bool:
        """Draw the animated move. Returns True if animation is complete."""
        if self.move_animation_start_time is None:
            return True

        import time
        elapsed_time = time.time() - self.move_animation_start_time

        # Check if animation is complete
        if elapsed_time >= self.move_animation_duration:
            self.stop_move_animation()
            return True

        # Calculate animation progress (0.0 to 1.0)
        progress = elapsed_time / self.move_animation_duration

        # Get from/to coordinates
        from_row, from_col = coords_from_square(self.move_animation_from_square)
        to_row, to_col = coords_from_square(self.move_animation_to_square)

        # Apply board flip if needed
        if is_board_flipped:
            from_row, from_col = 7 - from_row, 7 - from_col
            to_row, to_col = 7 - to_row, 7 - to_col

        # Interpolate position
        current_row = from_row + (to_row - from_row) * progress
        current_col = from_col + (to_col - from_col) * progress

        # Convert to screen coordinates (center of square)
        screen_x = self.board_margin_x + int((current_col + 0.5) * self.square_size)
        screen_y = self.board_margin_y + int((current_row + 0.5) * self.square_size)

        # Draw the piece at the interpolated position
        color_str = "w" if self.move_animation_piece.color == chess.WHITE else "b"
        piece_key = f"{color_str}{self.move_animation_piece.piece_type}"

        if piece_key in self.piece_images:
            piece_image = self.piece_images[piece_key]
            # Center the piece image
            piece_rect = piece_image.get_rect(center=(screen_x, screen_y))
            screen.blit(piece_image, piece_rect)

        return False

    def draw_rotating_king(self, screen, piece: chess.Piece, x: int, y: int, elapsed_time: float) -> None:
        """Draw a king rotating on its head"""
        # Animation duration is 0.5 seconds for 360 degree rotation
        animation_duration = 0.5

        if elapsed_time > animation_duration:
            # Animation finished, draw normally but upside down
            angle = 180
        else:
            # Calculate rotation angle (0 to 180 degrees over 0.5 seconds)
            progress = elapsed_time / animation_duration
            angle = progress * 180

        # Get the original piece image
        color_str = "w" if piece.color == chess.WHITE else "b"
        key = f"{color_str}{piece.piece_type}"
        if key in self.piece_images:
            original_surface = self.piece_images[key]

            # Rotate the image
            rotated_surface = pygame.transform.rotate(original_surface, angle)

            # Center the rotated image in the square
            rotated_rect = rotated_surface.get_rect()
            center_x = x + self.square_size // 2
            center_y = y + self.square_size // 2
            rotated_rect.center = (center_x, center_y)

            screen.blit(rotated_surface, rotated_rect)
        else:
            # Fallback to text
            piece_text = chess.piece_symbol(piece.piece_type).upper() if piece.color == chess.WHITE else chess.piece_symbol(piece.piece_type)
            text_surface = self.font_large.render(piece_text, True, self.RGB_BLACK)
            text_rect = text_surface.get_rect(center=(x + self.square_size//2, y + self.square_size//2))
            screen.blit(text_surface, text_rect)

    def draw_board(self, screen, board_state: BoardState, selected_square_coords: Optional[Tuple[int, int]] = None,
                   highlighted_moves: List[Tuple[int, int]] = None, is_board_flipped: bool = False,
                   preview_board_state: Optional[BoardState] = None, dragging_piece=None, drag_origin=None,
                   mouse_pos: Optional[Tuple[int, int]] = None, show_forks: bool = False) -> None:
        """Draw the chess board with pieces"""
        if highlighted_moves is None:
            highlighted_moves = []

        # Check if move animation is active (skip tactical calculations if so)
        is_animating_move = (self.move_animation_start_time is not None)

        # Check if any highlighting is active (exchange or statistics)
        has_exchange_highlights = False
        has_statistics_highlights = False

        if mouse_pos and not self.hovered_statistic and not is_animating_move:
            evaluation_board = preview_board_state if preview_board_state else board_state
            highlight_positions = self.get_exchange_highlights(mouse_pos, evaluation_board, is_board_flipped)
            if highlight_positions:
                has_exchange_highlights = True

        if self.hovered_statistic and not is_animating_move:
            has_statistics_highlights = True

        any_highlights_active = has_exchange_highlights or has_statistics_highlights

        # Draw the board squares
        for row in range(8):
            for col in range(8):
                # Apply flipping transformation
                display_row = (7 - row) if is_board_flipped else row
                display_col = (7 - col) if is_board_flipped else col
                x = self.board_margin_x + display_col * self.square_size
                y = self.board_margin_y + display_row * self.square_size

                # Determine square color (use original coordinates for coloring)
                is_light = (row + col) % 2 == 0
                color = self.LIGHT_SQUARE if is_light else self.DARK_SQUARE

                # Apply last move highlighting (lichess-style green overlay) only if NO highlights are active
                if board_state.last_move and not any_highlights_active:
                    from_coords = coords_from_square(board_state.last_move.from_square)
                    to_coords = coords_from_square(board_state.last_move.to_square)
                    if (row, col) == from_coords or (row, col) == to_coords:
                        color = Colors.LIGHT_SQUARE_LAST_MOVE if is_light else Colors.DARK_SQUARE_LAST_MOVE

                # Highlight selected square only
                if selected_square_coords and selected_square_coords == (row, col):
                    color = self.SELECTED

                # Draw the square
                pygame.draw.rect(screen, color,
                               (x, y, self.square_size, self.square_size))

                # Draw piece glow BEFORE piece (so piece appears on top) - skip during move animation
                square = square_from_coords(row, col)
                evaluation_board = preview_board_state if preview_board_state else board_state

                if not is_animating_move:
                    # Check if piece is hanging (red glow)
                    white_hanging = set(evaluation_board.get_hanging_pieces(chess.WHITE))
                    black_hanging = set(evaluation_board.get_hanging_pieces(chess.BLACK))
                    all_hanging = white_hanging | black_hanging

                    if square in all_hanging:
                        self.draw_hanging_indicator(screen, x, y)
                    else:
                        # Check if piece is attacked but not hanging (magenta glow)
                        piece_at_square = evaluation_board.board.piece_at(square)
                        if piece_at_square:
                            enemy_color = not piece_at_square.color
                            if evaluation_board.board.is_attacked_by(enemy_color, square):
                                self.draw_attacked_indicator(screen, x, y)

                # Draw piece if present (skip if being dragged or if being animated)
                piece = board_state.board.piece_at(square)
                skip_piece = (dragging_piece and drag_origin and (row, col) == drag_origin)

                # Also skip piece if it's at the from or to square of the animation
                if is_animating_move:
                    from_coords = coords_from_square(self.move_animation_from_square)
                    to_coords = coords_from_square(self.move_animation_to_square)
                    if (row, col) == from_coords or (row, col) == to_coords:
                        skip_piece = True

                if piece and not skip_piece:
                    self.draw_piece(screen, piece, x, y, row, col)

                # Draw pin/skewer indicators AFTER piece (so they appear on top) - skip during move animation
                if piece and not is_animating_move:
                    white_pinned = set(evaluation_board.get_pinned_pieces(chess.WHITE))
                    black_pinned = set(evaluation_board.get_pinned_pieces(chess.BLACK))
                    all_pinned = white_pinned | black_pinned

                    white_skewered = set(evaluation_board.get_skewered_pieces(chess.WHITE))
                    black_skewered = set(evaluation_board.get_skewered_pieces(chess.BLACK))
                    all_skewered = white_skewered | black_skewered

                    if square in all_pinned:
                        self.draw_pin_indicator(screen, x, y)
                    elif square in all_skewered:
                        self.draw_skewer_indicator(screen, x, y)

                # Draw move indicator circle for possible moves
                if (row, col) in highlighted_moves:
                    self.draw_move_indicator(screen, x, y)

                # Exchange evaluation triangles removed

        # Draw fork indicators if enabled - skip during move animation
        if show_forks and not is_animating_move:
            evaluation_board = preview_board_state if preview_board_state else board_state

            # Get fork opportunities for both colors
            white_forks = evaluation_board.get_fork_opportunities(chess.WHITE)
            black_forks = evaluation_board.get_fork_opportunities(chess.BLACK)
            all_forks = white_forks + black_forks

            # Draw arrows for each fork
            for fork in all_forks:
                origin_coords = coords_from_square(fork['origin'])
                dest_coords = coords_from_square(fork['destination'])
                self.draw_fork_arrow(screen, origin_coords, dest_coords, is_board_flipped)

        # Draw exchange evaluation piece highlights (gray out non-highlighted) if hovering
        # Only run if NOT hovering over statistics (to avoid conflict)
        if mouse_pos and not self.hovered_statistic:
            evaluation_board = preview_board_state if preview_board_state else board_state
            highlight_positions = self.get_exchange_highlights(mouse_pos, evaluation_board, is_board_flipped)

            if highlight_positions:
                # Convert to set for fast lookup
                highlight_set = set(highlight_positions)

                # Draw gray overlay on ALL squares NOT in highlight set (both empty and occupied)
                for row in range(8):
                    for col in range(8):
                        if (row, col) not in highlight_set:
                            display_pos = self.get_square_display_position(row, col, is_board_flipped)
                            if display_pos:
                                x, y = display_pos
                                self.draw_gray_overlay(screen, x, y)

                # Draw thin white border around highlighted squares
                for row, col in highlight_set:
                    display_pos = self.get_square_display_position(row, col, is_board_flipped)
                    if display_pos:
                        x, y = display_pos
                        pygame.draw.rect(screen, (255, 255, 255), (x, y, self.square_size, self.square_size), 2)

        # Draw statistics highlighting if hovering over spreadsheet (gray out non-highlighted)
        if self.hovered_statistic:
            stat_type, player_side = self.hovered_statistic
            evaluation_board = preview_board_state if preview_board_state else board_state
            highlight_items = self.get_highlighted_pieces_for_statistic(evaluation_board, stat_type, player_side, is_board_flipped)

            if highlight_items:
                # Convert to set for fast lookup
                highlight_set = set(highlight_items)

                # Draw gray overlay on ALL squares NOT in highlight set (both empty and occupied)
                for row in range(8):
                    for col in range(8):
                        if (row, col) not in highlight_set:
                            display_pos = self.get_square_display_position(row, col, is_board_flipped)
                            if display_pos:
                                x, y = display_pos
                                self.draw_gray_overlay(screen, x, y)

                # Draw thin white border around highlighted squares
                for row, col in highlight_set:
                    display_pos = self.get_square_display_position(row, col, is_board_flipped)
                    if display_pos:
                        x, y = display_pos
                        pygame.draw.rect(screen, (255, 255, 255), (x, y, self.square_size, self.square_size), 2)

        # Draw board border (use actual board size based on squares)
        actual_board_size = self.square_size * 8
        border_rect = pygame.Rect(self.board_margin_x - 2, self.board_margin_y - 2,
                                actual_board_size + 4, actual_board_size + 4)
        pygame.draw.rect(screen, self.RGB_BLACK, border_rect, 2)

        # Draw coordinates
        self.draw_coordinates(screen, is_board_flipped)

        # Draw captured pieces
        self.draw_captured_pieces(screen, board_state, is_board_flipped)

        # Draw animated move if active
        if is_animating_move:
            self.draw_move_animation(screen, is_board_flipped)

    def draw_captured_pieces(self, screen, board_state: BoardState, is_board_flipped: bool) -> None:
        """Draw captured pieces above or below the board"""
        # Miniature piece size (smaller than board pieces)
        piece_size = self.square_size // 3

        # Get captured pieces dynamically from board state
        captured_white, captured_black = board_state.get_captured_pieces()

        # Determine which pieces go above and which go below
        # Captured pieces appear on the side of the player who captured them
        if is_board_flipped:
            # White on bottom, so white's captures (black pieces) go below
            pieces_above = captured_black  # Black's captures (white pieces) go above (black's side)
            pieces_below = captured_white  # White's captures (black pieces) go below (white's side)
        else:
            # White on bottom (normal orientation), so white's captures (black pieces) go below
            pieces_above = captured_white  # Black's captures (white pieces) go above (black's side)
            pieces_below = captured_black  # White's captures (black pieces) go below (white's side)

        # Calculate material advantage
        from config import GameConstants
        white_value = sum(GameConstants.PIECE_VALUES[p] for p in captured_black)  # Black captured = white's advantage
        black_value = sum(GameConstants.PIECE_VALUES[p] for p in captured_white)  # White captured = black's advantage
        advantage = white_value - black_value

        # Draw pieces above the board (with same margin as bottom)
        # pieces_above are captured white pieces (what black captured), so draw them as WHITE
        y_above = self.board_margin_y - piece_size - 10
        advantage_above = -advantage if not is_board_flipped else advantage  # Black's advantage
        self._draw_captured_pieces_row(screen, pieces_above, y_above, piece_size,
                                      chess.WHITE,  # Color of the captured pieces (white)
                                      advantage_above if advantage_above > 0 else 0)

        # Draw pieces below the board (below the file letters)
        # pieces_below are captured black pieces (what white captured), so draw them as BLACK
        # File letters are at: self.board_margin_y + self.board_size + 10
        # So captured pieces go below that with same spacing as top
        coord_text_height = self.font_small.get_height()
        y_below = self.board_margin_y + self.board_size + 10 + coord_text_height + 10
        advantage_below = advantage if not is_board_flipped else -advantage  # White's advantage
        self._draw_captured_pieces_row(screen, pieces_below, y_below, piece_size,
                                      chess.BLACK,  # Color of the captured pieces (black)
                                      advantage_below if advantage_below > 0 else 0)

    def _draw_captured_pieces_row(self, screen, piece_types: List[int], y: int, piece_size: int, color: bool, advantage: int = 0) -> None:
        """Draw a row of captured pieces with optional material advantage"""
        # Starting x position (left-aligned with board)
        x = self.board_margin_x

        # Draw each captured piece
        for piece_type in piece_types:
            # Create a piece key for the image lookup (format: "w1" for white pawn, "b5" for black queen)
            color_str = "w" if color == chess.WHITE else "b"
            piece_key = f"{color_str}{piece_type}"

            if piece_key in self.piece_images:
                # Scale the piece image to miniature size (pawns 30% smaller)
                original_image = self.piece_images[piece_key]
                if piece_type == chess.PAWN:
                    scaled_size = int(piece_size * 0.7)  # Pawns 30% smaller
                    scaled_image = pygame.transform.smoothscale(original_image, (scaled_size, scaled_size))
                    # Center pawn vertically
                    piece_y = y + (piece_size - scaled_size) // 2
                else:
                    scaled_image = pygame.transform.smoothscale(original_image, (piece_size, piece_size))
                    piece_y = y

                # Draw the piece
                screen.blit(scaled_image, (x, piece_y))

            x += piece_size + 5  # Space between pieces

        # Draw material advantage if positive
        if advantage > 0:
            advantage_text = f"+{advantage}"
            advantage_surface = self.font_small.render(advantage_text, True, Colors.RGB_BLACK)
            screen.blit(advantage_surface, (x + 5, y + (piece_size - advantage_surface.get_height()) // 2))

    def draw_dragged_piece(self, screen, piece, mouse_pos: Tuple[int, int], is_board_flipped: bool = False) -> None:
        """Draw a piece being dragged, snapped to center of square under mouse"""
        if piece:
            # Get the square under the mouse
            current_square = self.get_square_from_mouse(mouse_pos)

            if current_square:
                # Convert to board coordinates if needed
                if is_board_flipped:
                    board_square = (7 - current_square[0], 7 - current_square[1])
                else:
                    board_square = current_square

                # Get the display position of this square
                square_pos = self.get_square_display_position(board_square[0], board_square[1], is_board_flipped)
                if square_pos:
                    piece_x, piece_y = square_pos
                    # Draw the piece centered in the square
                    self.draw_piece(screen, piece, piece_x, piece_y, -1, -1)
            else:
                # If not over a square, draw at cursor position
                piece_x = mouse_pos[0] - self.square_size // 2
                piece_y = mouse_pos[1] - self.square_size // 2
                self.draw_piece(screen, piece, piece_x, piece_y, -1, -1)
    
    def draw_piece(self, screen, piece: chess.Piece, x: int, y: int, board_row: int = -1, board_col: int = -1) -> None:
        """Draw a piece at the specified screen coordinates"""
        # Check if this is the checkmated king and animation is active
        if (self.checkmate_animation_start_time is not None and
            self.checkmate_king_position is not None and
            piece.piece_type == chess.KING):
            # Check if this is the checkmated king's position
            if board_row != -1 and board_col != -1:
                king_coords = coords_from_square(self.checkmate_king_position)
                if (board_row, board_col) == king_coords:
                    import time
                    elapsed_time = time.time() - self.checkmate_animation_start_time
                    self.draw_rotating_king(screen, piece, x, y, elapsed_time)
                    return

        # Normal piece drawing
        color_str = "w" if piece.color == chess.WHITE else "b"
        key = f"{color_str}{piece.piece_type}"
        if key in self.piece_images:
            piece_surface = self.piece_images[key]
            # Center the piece in the square
            piece_x = x + (self.square_size - piece_surface.get_width()) // 2
            piece_y = y + (self.square_size - piece_surface.get_height()) // 2
            screen.blit(piece_surface, (piece_x, piece_y))
        else:
            # Fallback: draw piece as text
            piece_text = chess.piece_symbol(piece.piece_type).upper() if piece.color == chess.WHITE else chess.piece_symbol(piece.piece_type)
            text_surface = self.font_large.render(piece_text, True, self.RGB_BLACK)
            text_rect = text_surface.get_rect(center=(x + self.square_size//2, y + self.square_size//2))
            screen.blit(text_surface, text_rect)
    
    def draw_coordinates(self, screen, is_board_flipped: bool = False) -> None:
        """Draw board coordinates (a-h, 1-8)"""
        # Draw file letters (a-h)
        for col in range(8):
            letter = chr(ord('a') + (7 - col if is_board_flipped else col))
            x = self.board_margin_x + col * self.square_size + self.square_size // 2
            y = self.board_margin_y + self.board_size + 10
            
            text_surface = self.font_small.render(letter, True, self.RGB_BLACK)
            text_rect = text_surface.get_rect(center=(x, y))
            screen.blit(text_surface, text_rect)
        
        # Draw rank numbers (1-8)
        for row in range(8):
            number = str((row + 1) if is_board_flipped else (8 - row))
            x = self.board_margin_x - 20
            y = self.board_margin_y + row * self.square_size + self.square_size // 2
            
            text_surface = self.font_small.render(number, True, self.RGB_BLACK)
            text_rect = text_surface.get_rect(center=(x, y))
            screen.blit(text_surface, text_rect)

    def draw_activity_display(self, screen, board_state: BoardState, is_board_flipped: bool = False, force_recalculate: bool = False) -> None:
        """Draw activity scores underneath the board"""
        if force_recalculate or not self.activity_cache_valid:
            # Only recalculate when forced (preview) or cache invalid
            white_activity, black_activity = board_state.get_activity_scores()
            if not force_recalculate:
                # Update cache only if this is the main board state
                self.cached_activity_white = white_activity
                self.cached_activity_black = black_activity
                self.activity_cache_valid = True
        else:
            # Use cached values
            white_activity, black_activity = self.cached_activity_white, self.cached_activity_black

        # Determine player vs opponent based on board orientation
        if is_board_flipped:
            player_activity = black_activity
            opponent_activity = white_activity
        else:
            player_activity = white_activity
            opponent_activity = black_activity

        # Position below coordinates using dynamic spacing
        center_x = self.board_margin_x + self.board_size // 2
        font_height = self.font_medium.get_height()
        activity_y = self.board_margin_y + self.board_size + font_height + 10  # 10px gap below board

        # Create activity text: "Activity: XX YY"
        activity_text = f"Activity: {player_activity} {opponent_activity}"

        # Determine colors (bold black for winning score, medium grey for losing)
        if player_activity > opponent_activity:
            player_color = Colors.RGB_BLACK  # Bold black
            opponent_color = Colors.ANNOTATION_NEUTRAL  # Medium grey
        elif opponent_activity > player_activity:
            player_color = Colors.ANNOTATION_NEUTRAL  # Medium grey
            opponent_color = Colors.RGB_BLACK  # Bold black
        else:
            player_color = Colors.RGB_BLACK
            opponent_color = Colors.RGB_BLACK

        # Render text parts separately for color highlighting
        label_surface = self.font_medium.render("Activity: ", True, Colors.RGB_BLACK)
        # Use bold font for black (winning) scores, regular for grey (losing) scores
        player_font = self.font_medium_bold if player_color == Colors.RGB_BLACK else self.font_medium
        opponent_font = self.font_medium_bold if opponent_color == Colors.RGB_BLACK else self.font_medium
        player_surface = player_font.render(str(player_activity), True, player_color)
        space_surface = self.font_medium.render(" ", True, Colors.RGB_BLACK)
        opponent_surface = opponent_font.render(str(opponent_activity), True, opponent_color)

        # Calculate total width for centering
        total_width = (label_surface.get_width() + player_surface.get_width() +
                      space_surface.get_width() + opponent_surface.get_width())
        start_x = center_x - total_width // 2

        # Draw each part
        current_x = start_x
        screen.blit(label_surface, (current_x, activity_y))
        current_x += label_surface.get_width()
        screen.blit(player_surface, (current_x, activity_y))
        current_x += player_surface.get_width()
        screen.blit(space_surface, (current_x, activity_y))
        current_x += space_surface.get_width()
        screen.blit(opponent_surface, (current_x, activity_y))

    def draw_pawn_display(self, screen, board_state: BoardState, is_board_flipped: bool = False) -> None:
        """Draw pawn counts underneath the activity display in tabular format"""
        white_pawns, black_pawns = board_state.get_pawn_counts()

        # Determine player vs opponent based on board orientation
        if is_board_flipped:
            player_pawns = black_pawns
            opponent_pawns = white_pawns
        else:
            player_pawns = white_pawns
            opponent_pawns = black_pawns

        # Position below activity display using dynamic spacing
        center_x = self.board_margin_x + self.board_size // 2
        font_height = self.font_medium.get_height()
        line_spacing = font_height + 2  # Small gap between lines
        pawn_y = self.board_margin_y + self.board_size + font_height + 10 + line_spacing  # Below activity line

        # Create pawn text: "Pawns: XX YY"
        pawn_text = f"Pawns: {player_pawns} {opponent_pawns}"

        # Determine colors (bold black for more pawns, medium grey for fewer)
        if player_pawns > opponent_pawns:
            player_color = Colors.RGB_BLACK  # Bold black
            opponent_color = Colors.ANNOTATION_NEUTRAL  # Medium grey
        elif opponent_pawns > player_pawns:
            player_color = Colors.ANNOTATION_NEUTRAL  # Medium grey
            opponent_color = Colors.RGB_BLACK  # Bold black
        else:
            player_color = Colors.RGB_BLACK
            opponent_color = Colors.RGB_BLACK

        # Render text parts separately for color highlighting
        label_surface = self.font_medium.render("Pawns: ", True, Colors.RGB_BLACK)
        # Use bold font for black (winning) scores, regular for grey (losing) scores
        player_font = self.font_medium_bold if player_color == Colors.RGB_BLACK else self.font_medium
        opponent_font = self.font_medium_bold if opponent_color == Colors.RGB_BLACK else self.font_medium
        player_surface = player_font.render(str(player_pawns), True, player_color)
        space_surface = self.font_medium.render(" ", True, Colors.RGB_BLACK)
        opponent_surface = opponent_font.render(str(opponent_pawns), True, opponent_color)

        # Calculate total width for centering
        total_width = (label_surface.get_width() + player_surface.get_width() +
                      space_surface.get_width() + opponent_surface.get_width())
        start_x = center_x - total_width // 2

        # Draw each part
        current_x = start_x
        screen.blit(label_surface, (current_x, pawn_y))
        current_x += label_surface.get_width()
        screen.blit(player_surface, (current_x, pawn_y))
        current_x += player_surface.get_width()
        screen.blit(space_surface, (current_x, pawn_y))
        current_x += space_surface.get_width()
        screen.blit(opponent_surface, (current_x, pawn_y))

    def draw_pawn_statistics_display(self, screen, board_state: BoardState, is_board_flipped: bool = False) -> None:
        """Draw pawn statistics (backward, isolated, doubled) on separate lines underneath the pawn count display"""
        (white_stats, black_stats) = board_state.get_pawn_statistics()
        white_backward, white_isolated, white_doubled = white_stats
        black_backward, black_isolated, black_doubled = black_stats

        # Determine player vs opponent based on board orientation
        if is_board_flipped:
            player_stats = black_stats
            opponent_stats = white_stats
        else:
            player_stats = white_stats
            opponent_stats = black_stats

        player_backward, player_isolated, player_doubled = player_stats
        opponent_backward, opponent_isolated, opponent_doubled = opponent_stats

        # Get font height for dynamic spacing
        font_height = self.font_medium.get_height()
        line_spacing = font_height + 2  # Small gap between lines

        # Starting position below pawn count display
        center_x = self.board_margin_x + self.board_size // 2
        start_y = self.board_margin_y + self.board_size + font_height + 10 + (2 * line_spacing)  # Below pawns line

        # Statistics data with full names
        stats_data = [
            ("Backward", player_backward, opponent_backward),
            ("Isolated", player_isolated, opponent_isolated),
            ("Doubled", player_doubled, opponent_doubled)
        ]

        # Draw each statistic on its own line
        for i, (stat_name, player_count, opponent_count) in enumerate(stats_data):
            current_y = start_y + (i * line_spacing)

            # Since lower is better for all these statistics, determine colors
            if player_count < opponent_count:
                player_color = Colors.RGB_BLACK  # Bold black (better)
                opponent_color = Colors.ANNOTATION_NEUTRAL  # Medium grey (worse)
            elif opponent_count < player_count:
                player_color = Colors.ANNOTATION_NEUTRAL  # Medium grey (worse)
                opponent_color = Colors.RGB_BLACK  # Bold black (better)
            else:
                player_color = Colors.RGB_BLACK
                opponent_color = Colors.RGB_BLACK

            # Render text parts: "Hanging: X Y" format
            label_surface = self.font_medium.render(f"{stat_name}: ", True, Colors.RGB_BLACK)
            player_font = self.font_medium_bold if player_color == Colors.RGB_BLACK else self.font_medium
            opponent_font = self.font_medium_bold if opponent_color == Colors.RGB_BLACK else self.font_medium
            player_surface = player_font.render(str(player_count), True, player_color)
            space_surface = self.font_medium.render(" ", True, Colors.RGB_BLACK)
            opponent_surface = opponent_font.render(str(opponent_count), True, opponent_color)

            # Calculate total width for centering
            total_width = (label_surface.get_width() + player_surface.get_width() +
                          space_surface.get_width() + opponent_surface.get_width())
            start_x = center_x - total_width // 2

            # Draw each part
            current_x = start_x
            screen.blit(label_surface, (current_x, current_y))
            current_x += label_surface.get_width()
            screen.blit(player_surface, (current_x, current_y))
            current_x += player_surface.get_width()
            screen.blit(space_surface, (current_x, current_y))
            current_x += space_surface.get_width()
            screen.blit(opponent_surface, (current_x, current_y))

    def draw_text(self, screen, text: str, x: int, y: int, font: pygame.font.Font,
                  color: Tuple[int, int, int] = None) -> None:
        """Draw text at the specified position"""
        if color is None:
            color = self.RGB_BLACK
        
        text_surface = font.render(text, True, color)
        screen.blit(text_surface, (x, y))

    def draw_exchange_indicator(self, screen, x: int, y: int) -> None:
        """Draw a subtle indicator for squares with exchange potential"""
        # Small colored corner indicators to mark tactical squares
        corner_size = 12
        indicator_color = Colors.ANNOTATION_CAUTION  # Yellow for tactical awareness

        # Draw small triangle in the top-right corner
        triangle_points = [
            (x + self.square_size - corner_size, y),
            (x + self.square_size, y),
            (x + self.square_size, y + corner_size)
        ]
        pygame.draw.polygon(screen, indicator_color, triangle_points)

    def _create_hanging_glow_surface(self, size: int) -> pygame.Surface:
        """Create a cached solid color disk for hanging piece indicator"""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        radius = int(size * 0.4)  # 40% of square width

        # Draw solid red disk
        pygame.draw.circle(surface, Colors.ANNOTATION_WARNING, (center, center), radius)

        return surface

    def _create_attacked_glow_surface(self, size: int) -> pygame.Surface:
        """Create a cached solid color disk for attacked piece indicator"""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        radius = int(size * 0.4)  # 40% of square width

        # Draw solid yellow disk
        yellow = (255, 255, 0)
        pygame.draw.circle(surface, yellow, (center, center), radius)

        return surface

    def draw_hanging_indicator(self, screen, x: int, y: int) -> None:
        """Draw a red gradient glow behind hanging pieces (uses cached surface)"""
        # Create or reuse cached gradient surface
        if self.hanging_glow_surface is None or self.hanging_glow_size != self.square_size:
            self.hanging_glow_surface = self._create_hanging_glow_surface(self.square_size)
            self.hanging_glow_size = self.square_size

        # Blit the cached gradient
        screen.blit(self.hanging_glow_surface, (x, y))

    def draw_attacked_indicator(self, screen, x: int, y: int) -> None:
        """Draw a yellow gradient glow behind attacked pieces (uses cached surface)"""
        # Create or reuse cached gradient surface
        if self.attacked_glow_surface is None or self.attacked_glow_size != self.square_size:
            self.attacked_glow_surface = self._create_attacked_glow_surface(self.square_size)
            self.attacked_glow_size = self.square_size

        # Blit the cached gradient
        screen.blit(self.attacked_glow_surface, (x, y))

    def draw_pin_indicator(self, screen, x: int, y: int) -> None:
        """Draw a white circle with 'P' in the upper left corner of the square"""
        corner_size = int(self.square_size * 0.5)  # 50% of square size (doubled from 25%)

        # Circle position in upper left corner
        circle_center_x = x + corner_size // 2
        circle_center_y = y + corner_size // 2
        circle_radius = corner_size // 2

        # Draw white circle
        pygame.draw.circle(screen, (255, 255, 255), (circle_center_x, circle_center_y), circle_radius)

        # Draw black 'P' in the center
        font_size = int(circle_radius * 1.8)
        font = pygame.font.Font(None, font_size)
        text = font.render('P', True, (0, 0, 0))
        text_rect = text.get_rect(center=(circle_center_x, circle_center_y))
        screen.blit(text, text_rect)

    def draw_skewer_indicator(self, screen, x: int, y: int) -> None:
        """Draw a white circle with 'S' in the upper left corner of the square"""
        corner_size = int(self.square_size * 0.5)  # 50% of square size (doubled from 25%)

        # Circle position in upper left corner
        circle_center_x = x + corner_size // 2
        circle_center_y = y + corner_size // 2
        circle_radius = corner_size // 2

        # Draw white circle
        pygame.draw.circle(screen, (255, 255, 255), (circle_center_x, circle_center_y), circle_radius)

        # Draw black 'S' in the center
        font_size = int(circle_radius * 1.8)
        font = pygame.font.Font(None, font_size)
        text = font.render('S', True, (0, 0, 0))
        text_rect = text.get_rect(center=(circle_center_x, circle_center_y))
        screen.blit(text, text_rect)

    def draw_fork_arrow(self, screen, from_coords: Tuple[int, int], to_coords: Tuple[int, int], is_board_flipped: bool) -> None:
        """Draw an arrow from origin square to fork destination square"""
        # Get display positions for both squares
        from_pos = self.get_square_display_position(from_coords[0], from_coords[1], is_board_flipped)
        to_pos = self.get_square_display_position(to_coords[0], to_coords[1], is_board_flipped)

        if not from_pos or not to_pos:
            return

        # Calculate center points of each square
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        from_center = (from_x + self.square_size // 2, from_y + self.square_size // 2)
        to_center = (to_x + self.square_size // 2, to_y + self.square_size // 2)

        # Create a transparent surface for the arrow
        import math

        # Calculate bounding box for the arrow
        min_x = min(from_center[0], to_center[0]) - 50
        min_y = min(from_center[1], to_center[1]) - 50
        max_x = max(from_center[0], to_center[0]) + 50
        max_y = max(from_center[1], to_center[1]) + 50

        width = max_x - min_x
        height = max_y - min_y

        # Create transparent surface
        arrow_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Adjust coordinates relative to the surface
        from_relative = (from_center[0] - min_x, from_center[1] - min_y)
        to_relative = (to_center[0] - min_x, to_center[1] - min_y)

        # Semi-transparent gray color (R, G, B, Alpha)
        arrow_color = (128, 128, 128, 180)  # Gray with 70% opacity
        line_width = 12  # Doubled from 6

        # Draw arrowhead at destination
        arrow_length = 40  # Doubled from 20
        arrow_angle = 25  # degrees

        # Calculate angle of the line
        dx = to_relative[0] - from_relative[0]
        dy = to_relative[1] - from_relative[1]
        angle = math.atan2(dy, dx)

        # Calculate arrowhead points
        angle1 = angle + math.radians(180 - arrow_angle)
        angle2 = angle + math.radians(180 + arrow_angle)

        point1 = (
            to_relative[0] + arrow_length * math.cos(angle1),
            to_relative[1] + arrow_length * math.sin(angle1)
        )
        point2 = (
            to_relative[0] + arrow_length * math.cos(angle2),
            to_relative[1] + arrow_length * math.sin(angle2)
        )

        # Calculate the base of the triangle (midpoint between point1 and point2)
        # This is where the line shaft should terminate
        base_mid = (
            (point1[0] + point2[0]) / 2,
            (point1[1] + point2[1]) / 2
        )

        # Draw arrow line on transparent surface, stopping at triangle base
        pygame.draw.line(arrow_surface, arrow_color, from_relative, base_mid, line_width)

        # Draw filled triangle for arrowhead on transparent surface
        pygame.draw.polygon(arrow_surface, arrow_color, [to_relative, point1, point2])

        # Blit the transparent surface onto the screen
        screen.blit(arrow_surface, (min_x, min_y))

    def draw_gray_overlay(self, screen, x: int, y: int) -> None:
        """Draw a semi-transparent gray overlay to dim non-highlighted squares"""
        overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
        overlay.fill((128, 128, 128, 153))  # Gray with 60% opacity
        screen.blit(overlay, (x, y))

    def get_exchange_highlights(self, mouse_pos: Tuple[int, int], board_state, is_board_flipped: bool = False) -> List[Tuple[int, int]]:
        """
        Get list of piece positions to highlight based on mouse hover over tactical squares.
        Returns list of (row, col) positions that should be highlighted in blue.
        """
        # Check if mouse is over a tactically interesting square
        hovered_square = self.get_square_from_mouse(mouse_pos)
        if not hovered_square:
            return []

        # Convert display coordinates to board coordinates if flipped
        if is_board_flipped:
            board_square_coords = (7 - hovered_square[0], 7 - hovered_square[1])
        else:
            board_square_coords = hovered_square

        # Convert to chess.Square
        chess_square = square_from_coords(board_square_coords[0], board_square_coords[1])

        # Check if this square is tactically interesting
        interesting_squares = board_state.get_tactically_interesting_squares()
        if chess_square not in interesting_squares:
            return []

        # Get all attackers and defenders for this square
        attackers, defenders = board_state.get_all_attackers_and_defenders(chess_square)

        # Convert chess.Square back to (row, col) coordinates
        attacker_coords = [coords_from_square(sq) for sq in attackers]
        defender_coords = [coords_from_square(sq) for sq in defenders]

        # Include the hovered square itself (the attacked/defended piece)
        hovered_coords = coords_from_square(chess_square)

        # Return all positions that should be highlighted
        return attacker_coords + defender_coords + [hovered_coords]

    def get_square_display_position(self, row: int, col: int, is_board_flipped: bool = False) -> Optional[Tuple[int, int]]:
        """Get the display position (x, y) of a board square"""
        # Apply board flipping for display coordinates
        display_row = (7 - row) if is_board_flipped else row
        display_col = (7 - col) if is_board_flipped else col

        x = self.board_margin_x + display_col * self.square_size
        y = self.board_margin_y + display_row * self.square_size

        return (x, y)

    def get_square_from_mouse(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Convert mouse position to board square coordinates"""
        mouse_x, mouse_y = mouse_pos
        
        # Check if mouse is within board bounds
        if (self.board_margin_x <= mouse_x <= self.board_margin_x + self.board_size and
            self.board_margin_y <= mouse_y <= self.board_margin_y + self.board_size):
            
            col = (mouse_x - self.board_margin_x) // self.square_size
            row = (mouse_y - self.board_margin_y) // self.square_size
            
            if 0 <= row < 8 and 0 <= col < 8:
                return (row, col)
        
        return None
    
    def update_display(self, screen, board_state: BoardState, selected_square_coords: Optional[Tuple[int, int]] = None,
                      highlighted_moves: List[Tuple[int, int]] = None, is_board_flipped: bool = False,
                      preview_board_state: Optional[BoardState] = None, dragging_piece=None, drag_origin=None,
                      mouse_pos: Optional[Tuple[int, int]] = None, show_forks: bool = False) -> None:
        """Update the entire display"""
        # Check for checkmate and start animation if needed
        if board_state.is_in_checkmate and self.checkmate_animation_start_time is None:
            self.start_checkmate_animation(board_state)
        elif not board_state.is_in_checkmate and self.checkmate_animation_start_time is not None:
            # Reset animation state if we're no longer in checkmate (e.g., after undo)
            self.checkmate_animation_start_time = None
            self.checkmate_king_position = None

        # Clear screen
        screen.fill(self.RGB_WHITE)

        # Draw all components
        self.draw_board(screen, board_state, selected_square_coords, highlighted_moves, is_board_flipped, preview_board_state, dragging_piece, drag_origin, mouse_pos, show_forks)

        # Draw help panel with statistics (uses preview_board_state when dragging to legal square)
        stats_board_state = preview_board_state if preview_board_state else board_state
        self.draw_help_panel(screen, stats_board_state, is_board_flipped)

        # Draw stalemate overlay if needed
        if board_state.is_in_stalemate:
            self.draw_stalemate_overlay(screen)

        # Note: pygame.display.flip() is called in the main loop, not here

    def draw_stalemate_overlay(self, screen) -> None:
        """Draw a semi-transparent stalemate message overlay with rubber stamp effect"""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))  # Semi-transparent black
        screen.blit(overlay, (0, 0))

        # Calculate board width for text sizing
        board_width = self.square_size * 8

        # Create a large font to make text span the board width
        font_size = int(board_width * 0.2)  # 20% of board width for bigger text
        stamp_font = pygame.font.Font(None, font_size)

        # Draw stalemate message in bright red
        stalemate_text = "STALEMATE"
        text_surface = stamp_font.render(stalemate_text, True, Colors.STALEMATE_TEXT)

        # Scale text to exactly match board width
        text_width = text_surface.get_width()
        scale_factor = board_width / text_width
        new_width = int(text_width * scale_factor)
        new_height = int(text_surface.get_height() * scale_factor)
        text_surface = pygame.transform.smoothscale(text_surface, (new_width, new_height))

        # Rotate the text 30 degrees for rubber stamp effect
        rotated_surface = pygame.transform.rotate(text_surface, 30)

        # Create black outline for the rotated text
        outline_surface = stamp_font.render(stalemate_text, True, Colors.STALEMATE_OUTLINE)
        outline_surface = pygame.transform.smoothscale(outline_surface, (new_width, new_height))
        rotated_outline = pygame.transform.rotate(outline_surface, 30)

        # Center the rotated text on the board (not the whole window)
        board_center_x = self.board_margin_x + (self.square_size * 8) // 2
        board_center_y = self.board_margin_y + (self.square_size * 8) // 2

        rotated_rect = rotated_surface.get_rect(center=(board_center_x, board_center_y))
        outline_rect = rotated_outline.get_rect(center=(board_center_x, board_center_y))

        # Draw thick black outline for better visibility
        for dx in [-4, -3, -2, -1, 0, 1, 2, 3, 4]:
            for dy in [-4, -3, -2, -1, 0, 1, 2, 3, 4]:
                if dx != 0 or dy != 0:
                    screen.blit(rotated_outline, (outline_rect.x + dx, outline_rect.y + dy))

        # Draw main red text
        screen.blit(rotated_surface, rotated_rect)

    def draw_keyboard_shortcuts_panel(self, screen) -> None:
        """Draw a centered panel showing all keyboard shortcuts in cell/table format"""
        # Define shortcuts
        shortcuts = [
            ("F", "Flip board"),
            ("←", "Go backward one move"),
            ("→", "Go forward one move"),
            ("Ctrl ←", "Go to beginning"),
            ("Ctrl →", "Go to end"),
            ("Ctrl L", "Load PGN or FEN file"),
            ("Ctrl P", "Save as PGN"),
            ("Ctrl F", "Save as FEN"),
            ("/", "Show/hide this help"),
            ("Esc", "Exit game")
        ]

        # Panel dimensions - 80% of window height
        panel_height = int(self.window_height * 0.8)
        panel_width = int(self.window_width * 0.4)  # 40% of window width

        # Center the panel
        panel_x = (self.window_width - panel_width) // 2
        panel_y = (self.window_height - panel_height) // 2

        # Create semi-transparent background overlay
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Semi-transparent black
        screen.blit(overlay, (0, 0))

        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, Colors.HELP_PANEL_BACKGROUND, panel_rect)
        pygame.draw.rect(screen, Colors.RGB_BLACK, panel_rect, 3)

        # Title (using medium font instead of large)
        title_text = "Keyboard Shortcuts"
        title_surface = self.font_medium_bold.render(title_text, True, Colors.BLACK_TEXT)
        title_rect = title_surface.get_rect(center=(panel_x + panel_width // 2, panel_y + 30))
        screen.blit(title_surface, title_rect)

        # Calculate worst-case text width for centering
        max_key_width = 0
        max_desc_width = 0
        for key, description in shortcuts:
            key_surface = self.font_small_bold.render(key, True, Colors.RGB_BLACK)
            desc_surface = self.font_small.render(description, True, Colors.LABEL_TEXT_COLOR)
            max_key_width = max(max_key_width, key_surface.get_width())
            max_desc_width = max(max_desc_width, desc_surface.get_width())

        # Column widths based on content + padding
        key_col_width = max_key_width + 40  # Key column width with padding
        desc_col_width = max_desc_width + 20  # Description column width
        total_table_width = key_col_width + desc_col_width

        # Center the table horizontally in the panel
        table_x = panel_x + (panel_width - total_table_width) // 2

        # Calculate cell layout
        table_start_y = panel_y + 70  # Below title
        table_height = panel_height - 120  # Leave space for title and instruction
        row_height = table_height // len(shortcuts)

        # Draw shortcuts in cell format (no borders, just text positioning)
        current_y = table_start_y
        for key, description in shortcuts:
            # Key column (left-aligned within its column, bold)
            key_surface = self.font_small_bold.render(key, True, Colors.RGB_BLACK)
            key_x = table_x + 20  # 20px left padding
            key_y = current_y + (row_height - key_surface.get_height()) // 2
            screen.blit(key_surface, (key_x, key_y))

            # Description column (left-aligned within its column, regular)
            desc_surface = self.font_small.render(description, True, Colors.LABEL_TEXT_COLOR)
            desc_x = table_x + key_col_width + 20  # After key column + padding
            desc_y = current_y + (row_height - desc_surface.get_height()) // 2
            screen.blit(desc_surface, (desc_x, desc_y))

            current_y += row_height

        # Draw instructions at bottom
        instruction_text = "Press / again to close"
        instruction_surface = self.font_small.render(instruction_text, True, Colors.LABEL_TEXT_COLOR)
        instruction_rect = instruction_surface.get_rect(center=(panel_x + panel_width // 2, panel_y + panel_height - 30))
        screen.blit(instruction_surface, instruction_rect)

    def show_promotion_dialog(self, screen, color: bool) -> int:
        """Show promotion dialog and return selected piece type"""
        # Define promotion pieces (Queen, Rook, Bishop, Knight)
        promotion_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]

        # Dialog dimensions
        dialog_width = 400
        dialog_height = 150
        dialog_x = (self.window_width - dialog_width) // 2
        dialog_y = (self.window_height - dialog_height) // 2

        # Create semi-transparent overlay
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        screen.blit(overlay, (0, 0))

        # Draw dialog box
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(screen, self.RGB_WHITE, dialog_rect)
        pygame.draw.rect(screen, self.RGB_BLACK, dialog_rect, 3)

        # Draw title
        title_text = "Choose promotion piece:"
        title_surface = self.font_medium.render(title_text, True, self.RGB_BLACK)
        title_rect = title_surface.get_rect(center=(dialog_x + dialog_width//2, dialog_y + 30))
        screen.blit(title_surface, title_rect)

        # Draw piece options
        piece_size = 60
        piece_spacing = (dialog_width - 4 * piece_size) // 5
        piece_rects = []

        for i, piece_type in enumerate(promotion_pieces):
            piece_x = dialog_x + piece_spacing + i * (piece_size + piece_spacing)
            piece_y = dialog_y + 70
            piece_rect = pygame.Rect(piece_x, piece_y, piece_size, piece_size)
            piece_rects.append((piece_rect, piece_type))

            # Draw piece background
            pygame.draw.rect(screen, self.LIGHT_SQUARE, piece_rect)
            pygame.draw.rect(screen, self.RGB_BLACK, piece_rect, 2)

            # Draw piece image or text
            color_str = "w" if color == chess.WHITE else "b"
            key = f"{color_str}{piece_type}"
            if key in self.piece_images:
                # Scale the piece image to fit
                piece_surface = pygame.transform.smoothscale(self.piece_images[key], (piece_size - 10, piece_size - 10))
                piece_x_centered = piece_x + (piece_size - piece_surface.get_width()) // 2
                piece_y_centered = piece_y + (piece_size - piece_surface.get_height()) // 2
                screen.blit(piece_surface, (piece_x_centered, piece_y_centered))
            else:
                # Fallback to text
                piece_text = chess.piece_symbol(piece_type).upper() if color == chess.WHITE else chess.piece_symbol(piece_type)
                text_surface = self.font_large.render(piece_text, True, self.RGB_BLACK)
                text_rect = text_surface.get_rect(center=piece_rect.center)
                screen.blit(text_surface, text_rect)

        pygame.display.flip()

        # Wait for user selection
        while True:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    for piece_rect, piece_type in piece_rects:
                        if piece_rect.collidepoint(mouse_pos):
                            return piece_type
                elif event.type == pygame.KEYDOWN:
                    # Keyboard shortcuts
                    if event.key == pygame.K_q:
                        return chess.QUEEN
                    elif event.key == pygame.K_r:
                        return chess.ROOK
                    elif event.key == pygame.K_b:
                        return chess.BISHOP
                    elif event.key == pygame.K_n:
                        return chess.KNIGHT
                    elif event.key == pygame.K_ESCAPE:
                        return chess.QUEEN  # Default to queen

    def _load_settings(self) -> None:
        """Load checkbox states from settings file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)

                # Update help options with saved states
                for option in self.help_options:
                    key = option["key"]
                    if key in settings:
                        option["enabled"] = settings[key]
        except (json.JSONDecodeError, IOError):
            # If settings file is corrupted or unreadable, continue with defaults
            pass

    def _save_settings(self) -> None:
        """Save checkbox states to settings file"""
        try:
            settings = {}
            for option in self.help_options:
                settings[option["key"]] = option["enabled"]

            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except IOError:
            # If we can't save settings, continue silently (don't crash the game)
            pass

    def quit(self) -> None:
        """Clean up Pygame resources"""
        pygame.quit()

# Example usage
if __name__ == "__main__":
    from chess_board import BoardState
    
    # Initialize pygame and create screen
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption("Chess Game - Example")
    
    # Create display and board
    display = ChessDisplay(1000, 700)
    board = BoardState()
    
    # Simple display loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Update display
        display.update_display(screen, board)
        pygame.display.flip()
        clock.tick(60)
    
    display.quit()
