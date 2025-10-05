import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import warnings
warnings.filterwarnings('ignore', message='.*pkg_resources is deprecated.*')

import pygame
import sys
import chess
from chess_board import BoardState, square_from_coords, coords_from_square
from display import ChessDisplay
from config import GameConfig, Colors

# Try to import file dialog functionality
try:
    import tkinter as tk
    from tkinter import filedialog
    DIALOG_AVAILABLE = True
except ImportError:
    DIALOG_AVAILABLE = False
    # File dialog not available - PGN files will use default names

# Set window behavior before pygame init (removed problematic positioning)

# Initialize Pygame
pygame.init()

# Get screen dimensions and calculate window size
screen_info = pygame.display.Info()
SCREEN_WIDTH = screen_info.current_w
SCREEN_HEIGHT = screen_info.current_h

# Calculate window size using config values (restored to normal size)
WINDOW_HEIGHT = int(min(SCREEN_WIDTH * GameConfig.SCREEN_SIZE_PERCENTAGE,
                       SCREEN_HEIGHT * GameConfig.SCREEN_SIZE_PERCENTAGE))
WINDOW_WIDTH = int(WINDOW_HEIGHT * GameConfig.WINDOW_ASPECT_RATIO)

# Create display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Capablanca")

# Display splash screen
def show_splash_screen():
    """Display the Capablanca splash screen"""
    try:
        from display import get_resource_path
        splash_image = pygame.image.load(get_resource_path("images/capa.png"))

        # Center the image
        image_rect = splash_image.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

        # Fill screen and draw splash
        screen.fill((255, 255, 255))  # White background
        screen.blit(splash_image, image_rect)
        pygame.display.flip()

        return True
    except Exception as e:
        print(f"Could not load splash screen: {e}")
        return False

# Show splash screen
show_splash_screen()

# Keep splash screen visible for 1 second
pygame.time.delay(1000)

# Simple error beep function
def play_error_beep():
    """Play a simple error beep sound"""
    try:
        import winsound
        winsound.Beep(800, 200)  # 800Hz for 200ms
    except (ImportError, RuntimeError):
        # winsound not available (non-Windows) or failed - fail silently
        pass

# Create global board state in starting position
game = BoardState()

# Create display object
display = ChessDisplay(WINDOW_WIDTH, WINDOW_HEIGHT)

# Font setup using config values - modern system font (for any UI text if needed)
font_size = int(WINDOW_WIDTH * GameConfig.FONT_BUTTON_PERCENTAGE)
try:
    font = pygame.font.SysFont('segoeui,arial,helvetica,sans-serif', font_size, bold=False)
except:
    font = pygame.font.Font(None, font_size)

# Helper functions for file operations
def get_load_position_filename():
    """Get filename for loading position (PGN or FEN)"""
    if DIALOG_AVAILABLE:
        # Hide main window temporarily
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.askopenfilename(
            title="Load Position (PGN or FEN)",
            filetypes=[("Position files", "*.pgn;*.fen"), ("PGN files", "*.pgn"), ("FEN files", "*.fen"), ("All files", "*.*")],
            defaultextension=".pgn"
        )
        root.destroy()
        return filename if filename else None
    else:
        # Fallback to default filename
        return "game.pgn" if os.path.exists("game.pgn") else None

def get_save_pgn_filename():
    """Get filename for saving PGN file"""
    if DIALOG_AVAILABLE:
        # Hide main window temporarily
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.asksaveasfilename(
            title="Save Game to PGN",
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
            defaultextension=".pgn"
        )
        root.destroy()
        return filename if filename else None
    else:
        # Fallback to default filename
        return "game.pgn"

def get_save_fen_filename():
    """Get filename for saving FEN file"""
    if DIALOG_AVAILABLE:
        # Hide main window temporarily
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.asksaveasfilename(
            title="Save Position to FEN",
            filetypes=[("FEN files", "*.fen"), ("All files", "*.*")],
            defaultextension=".fen"
        )
        root.destroy()
        return filename if filename else None
    else:
        # Fallback to default filename
        return "position.fen"

# Game state
selected_square_coords = None
highlighted_moves = []


# Drag state
dragging_piece = None  # The piece being dragged
drag_origin = None     # Original square coordinates

# Rendering optimization
needs_redraw = True  # Initially need to draw
last_hovered_square = None  # Track which board square mouse is over
last_hover_was_legal = False  # Was the last hovered square a legal move?

# Help panel state
show_help_panel = False


# Main game loop
is_running = True
clock = pygame.time.Clock()

while is_running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if show_help_panel:
                    show_help_panel = False
                    needs_redraw = True
                else:
                    is_running = False
            elif event.key == pygame.K_f:  # F key to toggle flip board (or Ctrl+F to save FEN)
                ctrl_pressed = pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]
                if ctrl_pressed:
                    # Ctrl+F: save FEN
                    filename = get_save_fen_filename()
                    if filename:
                        success = game.save_fen_file(filename)
                        if success:
                            print(f"Saved position to FEN: {filename}")
                        else:
                            play_error_beep()
                            print(f"Failed to save FEN: {filename}")
                    else:
                        play_error_beep()
                else:
                    # Plain F: flip board
                    display.toggle_help_option("flip_board")
                    needs_redraw = True
            elif event.key == pygame.K_LEFT:  # Left arrow to go backward
                ctrl_pressed = pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]
                if ctrl_pressed:
                    # Ctrl+Left: rewind to start (no animation for bulk operations)
                    success = game.rewind_to_start()
                else:
                    # Left: go back one move
                    if game.can_undo() and game.last_move:
                        move_to_animate = game.last_move
                        from_square = move_to_animate.from_square
                        to_square = move_to_animate.to_square
                        # Get piece at TO square (before undo)
                        piece = game.board.piece_at(to_square)
                        success = game.undo_move()
                        if success and piece:
                            # Animate reverse (from to -> from)
                            display.start_move_animation(to_square, from_square, piece)
                    else:
                        success = game.undo_move()

                if success:
                    # Clear any current selection
                    selected_square_coords = None
                    highlighted_moves = []
                    display.invalidate_activity_cache()
                    needs_redraw = True
                else:
                    play_error_beep()
            elif event.key == pygame.K_RIGHT:  # Right arrow to go forward
                ctrl_pressed = pygame.key.get_pressed()[pygame.K_LCTRL] or pygame.key.get_pressed()[pygame.K_RCTRL]
                if ctrl_pressed:
                    # Ctrl+Right: fast forward to end (no animation for bulk operations)
                    success = game.fast_forward_to_end()
                else:
                    # Right: go forward one move
                    if game.can_redo() and len(game.redo_stack) > 0:
                        # Peek at the next move in redo stack
                        next_board, next_history, next_last_move = game.redo_stack[-1]
                        if next_last_move:
                            from_square = next_last_move.from_square
                            to_square = next_last_move.to_square
                            # Get piece at FROM square (current board)
                            piece = game.board.piece_at(from_square)
                            success = game.redo_move()
                            if success and piece:
                                display.start_move_animation(from_square, to_square, piece)
                        else:
                            success = game.redo_move()
                    else:
                        success = game.redo_move()

                if success:
                    # Clear any current selection
                    selected_square_coords = None
                    highlighted_moves = []
                    display.invalidate_activity_cache()
                    needs_redraw = True
                else:
                    play_error_beep()
            elif event.key == pygame.K_SLASH:  # Slash (/) key to show help
                show_help_panel = not show_help_panel
                needs_redraw = True
            elif event.key == pygame.K_l and pygame.key.get_pressed()[pygame.K_LCTRL]:  # Ctrl+L to load position
                filename = get_load_position_filename()
                if filename:
                    success = game.load_position_file(filename)
                    if success:
                        # Clear any current selection and highlights
                        selected_square_coords = None
                        highlighted_moves = []
                        dragging_piece = None
                        drag_origin = None
                        last_hovered_square = None
                        last_hover_was_legal = False
                        display.invalidate_activity_cache()
                        needs_redraw = True
                        print(f"Loaded position from: {filename}")
                    else:
                        play_error_beep()
                        print(f"Failed to load position from: {filename}")
                else:
                    play_error_beep()
            elif event.key == pygame.K_p and pygame.key.get_pressed()[pygame.K_LCTRL]:  # Ctrl+P to save PGN
                filename = get_save_pgn_filename()
                if filename:
                    success = game.save_pgn_file(filename)
                    if success:
                        print(f"Saved game to PGN: {filename}")
                    else:
                        play_error_beep()
                        print(f"Failed to save PGN: {filename}")
                else:
                    play_error_beep()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # Check if a VCR button was clicked
            vcr_button = display.get_vcr_button_at_pos(mouse_pos)
            if vcr_button:
                success = False
                if vcr_button == "rewind":
                    # Rewind to start (no animation for bulk operations)
                    success = game.rewind_to_start()
                elif vcr_button == "back":
                    # Animate undo
                    if game.can_undo() and game.last_move:
                        move_to_animate = game.last_move
                        from_square = move_to_animate.from_square
                        to_square = move_to_animate.to_square
                        piece = game.board.piece_at(to_square)
                        success = game.undo_move()
                        if success and piece:
                            display.start_move_animation(to_square, from_square, piece)
                    else:
                        success = game.undo_move()
                elif vcr_button == "forward":
                    # Animate redo
                    if game.can_redo() and len(game.redo_stack) > 0:
                        next_board, next_history, next_last_move = game.redo_stack[-1]
                        if next_last_move:
                            from_square = next_last_move.from_square
                            to_square = next_last_move.to_square
                            piece = game.board.piece_at(from_square)
                            success = game.redo_move()
                            if success and piece:
                                display.start_move_animation(from_square, to_square, piece)
                        else:
                            success = game.redo_move()
                    else:
                        success = game.redo_move()
                elif vcr_button == "fast_forward":
                    # Fast forward to end (no animation for bulk operations)
                    success = game.fast_forward_to_end()

                if success:
                    # Clear any current selection
                    selected_square_coords = None
                    highlighted_moves = []
                    display.invalidate_activity_cache()
                    needs_redraw = True
                else:
                    play_error_beep()
            # Check if a help checkbox was clicked
            elif display.get_checkbox_at_pos(mouse_pos):
                checkbox_key = display.get_checkbox_at_pos(mouse_pos)
                display.toggle_help_option(checkbox_key)
                needs_redraw = True
            else:
                # Handle board clicks for piece selection/movement
                square = display.get_square_from_mouse(mouse_pos)
                if square:
                    # Convert square coordinates if board is flipped
                    if display.is_help_option_enabled("flip_board"):
                        square = (7 - square[0], 7 - square[1])

                    # Convert display coordinates to chess square
                    chess_square = square_from_coords(square[0], square[1])

                    if selected_square_coords is None:
                        # Start dragging a piece
                        piece = game.board.piece_at(chess_square)
                        if piece and piece.color == game.board.turn:
                            # Set up drag state
                            dragging_piece = piece
                            drag_origin = square
                            selected_square_coords = square

                            # Calculate possible moves for the selected piece
                            possible_squares = game.get_possible_moves(chess_square)
                            highlighted_moves = [coords_from_square(sq) for sq in possible_squares]
                            # Reset hover state since highlighted_moves changed
                            last_hovered_square = None
                            last_hover_was_legal = False
                            needs_redraw = True
                    else:
                            # Try to move the piece
                            if square in highlighted_moves:
                                # Convert coordinates to chess squares
                                from_square = square_from_coords(selected_square_coords[0], selected_square_coords[1])
                                to_square = square_from_coords(square[0], square[1])

                                # Check if this is a pawn promotion
                                if game.is_pawn_promotion(from_square, to_square):
                                    # Show promotion dialog
                                    current_piece = game.board.piece_at(from_square)
                                    promotion_piece = display.show_promotion_dialog(screen, current_piece.color)

                                    # Execute the move with promotion
                                    move_successful = game.make_move_with_promotion(
                                        from_square, to_square, promotion_piece
                                    )
                                    if not move_successful:
                                        play_error_beep()
                                else:
                                    # Execute regular move
                                    move_successful = game.make_move(from_square, to_square)
                                    if not move_successful:
                                        play_error_beep()

                                # Clear selection regardless
                                selected_square_coords = None
                                highlighted_moves = []
                                display.invalidate_activity_cache()  # Invalidate cache when move is made
                                # Reset hover state since highlighted_moves changed
                                last_hovered_square = None
                                last_hover_was_legal = False
                                needs_redraw = True
                            elif square == selected_square_coords:
                                # Deselect
                                selected_square_coords = None
                                highlighted_moves = []
                                # Reset hover state since highlighted_moves changed
                                last_hovered_square = None
                                last_hover_was_legal = False
                                needs_redraw = True
                            else:
                                # Select different piece
                                piece = game.board.piece_at(chess_square)
                                if piece and piece.color == game.board.turn:
                                    selected_square_coords = square
                                    possible_squares = game.get_possible_moves(chess_square)
                                    highlighted_moves = [coords_from_square(sq) for sq in possible_squares]
                                    # Reset hover state since highlighted_moves changed
                                    last_hovered_square = None
                                    last_hover_was_legal = False
                                    needs_redraw = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if dragging_piece and drag_origin:
                # Complete the drag operation
                mouse_pos = pygame.mouse.get_pos()
                target_square = display.get_square_from_mouse(mouse_pos)

                if target_square:
                    # Convert square coordinates if board is flipped
                    if display.is_help_option_enabled("flip_board"):
                        target_square = (7 - target_square[0], 7 - target_square[1])

                    # Try to complete the move
                    if target_square in highlighted_moves:
                        # Convert coordinates to chess squares
                        from_square = square_from_coords(drag_origin[0], drag_origin[1])
                        to_square = square_from_coords(target_square[0], target_square[1])

                        # Check if this is a pawn promotion
                        if game.is_pawn_promotion(from_square, to_square):
                            # Show promotion dialog
                            promotion_piece = display.show_promotion_dialog(screen, dragging_piece.color)
                            # Execute the move with promotion
                            move_successful = game.make_move_with_promotion(
                                from_square, to_square, promotion_piece
                            )
                        else:
                            # Execute regular move
                            move_successful = game.make_move(from_square, to_square)

                # Reset drag state regardless of whether move was successful
                dragging_piece = None
                drag_origin = None
                selected_square_coords = None
                highlighted_moves = []
                display.invalidate_activity_cache()  # Invalidate cache when move is made
                last_hovered_square = None
                last_hover_was_legal = False
                needs_redraw = True

    # Check for smart hover detection (only redraw when entering/leaving legal move squares)
    current_mouse_pos = pygame.mouse.get_pos()

    # Get current square under mouse
    current_hovered_square = display.get_square_from_mouse(current_mouse_pos)
    if current_hovered_square and display.is_help_option_enabled("flip_board"):
        current_hovered_square = (7 - current_hovered_square[0], 7 - current_hovered_square[1])

    # Check if current hover is over a legal move square
    current_hover_is_legal = (current_hovered_square in highlighted_moves) if current_hovered_square else False

    # Create preview board state if hovering over a legal move
    preview_game = None
    if current_hover_is_legal and selected_square_coords:
        # Create a copy of the board state for preview
        preview_game = game.copy()

        # Execute the candidate move on the preview board
        from_row, from_col = selected_square_coords
        to_row, to_col = current_hovered_square
        from_square = square_from_coords(from_row, from_col)
        to_square = square_from_coords(to_row, to_col)
        preview_game.make_move(from_square, to_square)

    # Update statistics hover detection
    previous_hovered_statistic = display.hovered_statistic
    display.update_statistics_hover(current_mouse_pos)
    statistics_hover_changed = (display.hovered_statistic != previous_hovered_statistic)

    # Only redraw if hover state changed in a meaningful way
    hover_state_changed = (
        current_hovered_square != last_hovered_square or  # Different square
        current_hover_is_legal != last_hover_was_legal or # Legal status changed
        statistics_hover_changed                          # Statistics hover changed
    )

    if hover_state_changed:
        last_hovered_square = current_hovered_square
        last_hover_was_legal = current_hover_is_legal
        needs_redraw = True


    # Force redraws during animations (temporarily return to continuous rendering)
    was_animating = display.is_animation_active()
    if was_animating:
        needs_redraw = True

    # Only redraw if something changed
    if needs_redraw:
        # Draw the chess board (with flip consideration)
        current_mouse_pos = pygame.mouse.get_pos()
        display.update_display(screen, game, selected_square_coords, highlighted_moves, display.is_help_option_enabled("flip_board"), preview_game, dragging_piece, drag_origin, current_mouse_pos, show_forks=True)

        # Draw dragged piece snapped to square center
        if dragging_piece:
            display.draw_dragged_piece(screen, dragging_piece, current_mouse_pos, display.is_help_option_enabled("flip_board"))


        # Draw help panel if requested
        if show_help_panel:
            display.draw_keyboard_shortcuts_panel(screen)

        # Update the display
        pygame.display.flip()
        needs_redraw = False

    # Check if animation just stopped - force one more redraw to show final state
    is_animating_now = display.is_animation_active()
    if was_animating and not is_animating_now:
        needs_redraw = True

    # Use higher frame rate during animations for smoother motion
    if is_animating_now:
        clock.tick(60)  # 60 FPS during animations
    else:
        clock.tick(30)  # 30 FPS normally for lower CPU usage

# Quit Pygame
pygame.quit()
sys.exit()
