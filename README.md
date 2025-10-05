
# Capablanca - Think about Positional Strategy like Capablanca

Capablanca went undefeated for 8 years straight, a feat that is unmatched today.

He was a strong positional player - his thought was to always play the "next best move",
unlike grandmasters today who calculate deeply for tactical advantage.  


## Here's a breakdown of his key positional principles:
### Maximize Piece Activity:
Develop all your pieces to active squares where they control many squares and support each other. 
### Protect Your Position:
Keep your pieces and pawns connected and mutually supportive, avoiding isolated or unsupported units. 
### Neutralize Enemy Pieces:
Drive back or neutralize your opponent's active pieces on your side of the board. 
### Practice Prophylaxis:
Anticipate and prevent your opponent's plans and threats, even when you have your own active ideas. 
### Build Strong Pawn Structures:
Create and maintain a solid pawn structure, especially by forming passed pawns in the endgame. 
### Simplify When Necessary:
Don't be afraid to trade off pieces or pawns when it clarifies the position, improves your structure, or maintains a tangible advantage. 
### Follow a Clear Plan:
Have a definite, clear, and logical plan, and carry it out with precision rather than resorting to overly complicated tactics. 
### Value King Activity:
In the endgame, the king becomes a powerful piece and should be used actively to support your pawns and attack the opponent's. 
### Development Prioritization:
Prioritize piece development in the opening and early middlegame to complete the activation of your army. 

## What Capablanca the program Does:
Capablanca the program is not a chess engine that recommends moves.  Rather, it lets you see your current position so that you can play positionally like Capablanca the person.  It can help identify how well you're doing with you position.  It can help you see where potential blunders are, which is the number one reason chess games are lost.  It will tell you and your opponents pawn structure, piece development and piece activity, potential forks, and other valuable stuff.

## What not to do with Capablanca:
Dont use Capablanca to play with opponents in real time.  That is forbidden in online play.  But what you should do is save your real chess games in PGN format, and then load them into Capablanca.  Then you can play through your game and see if you had the wrong priorities, why you made blunders, or you miscounted an exchange.

Let me know if your have questions or ideas.  Or fork this repo and improve it on your own.

Enjoy!
rick.franklin@gmail.com


## Running Capablanca

```bash
pip install -r requirements.txt
python main.py
```

**Controls:**
- **Mouse** - Drag and drop pieces with square snapping, hover over pieces for tactical analysis
- **F** - Flip board perspective
- **Left Arrow** - Go backward one move (undo)
- **Right Arrow** - Go forward one move (redo)
- **Ctrl+Left Arrow** - Rewind to start
- **Ctrl+Right Arrow** - Fast forward to end
- **VCR Buttons** - Navigate through game history (rewind, back, forward, fast-forward)
- **Ctrl+L** - Load position from PGN file
- **Ctrl+P** - Save game to PGN file
- **Ctrl+F** - Save position to FEN file
- **/** - Show/hide keyboard shortcuts help panel
- **ESC** - Quit


## Technical Requirements

- **Python 3.x** with Pygame for graphics

For technical architecture and development details, see [CLAUDE.md](CLAUDE.md).
