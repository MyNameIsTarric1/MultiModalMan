import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from flet import Column, Text

class GameDisplay(Column):
    def __init__(self):
        super().__init__()
        self.word = Text(style=config.TITLE_STYLE)
        self.guessed = Text(style=config.STATUS_STYLE)
        self.attempts = Text(style=config.STATUS_STYLE)
        self.status = Text(style=config.STATUS_STYLE)
        
        self.controls = [
            self.word,
            self.guessed,
            self.attempts,
            self.status
        ]
        self.spacing = 15

    def update(self, state):
        # Debug print
        print(f"GameDisplay updating with state: game_status={state.game_status}, word={state.secret_word if state.secret_word else 'No word'}")
        
        # If in revealed mode, show the actual word instead of display_word
        if state.game_status == "revealed" and state.secret_word:
            # Display the actual word with spaces between letters
            self.word.value = " ".join(state.secret_word)
            print(f"Revealed word in display: {state.secret_word}")
            # Change style to indicate it's revealed
            self.word.color = config.COLOR_PALETTE["error"]
        else:
            # Normal display with underscores
            self.word.value = state.display_word
            print(f"Showing masked word: {state.display_word}")
            # Reset color
            self.word.color = None  # Use default color
            
        self.guessed.value = f"Guessed: {', '.join(sorted(state.guessed_letters))}"
        self.attempts.value = f"Attempts left: {state.remaining_attempts}"
        self._update_status(state)

    def _update_status(self, state):
        if state.game_status == "won":
            self.status.value = "🎉 You won!"
            self.status.color = config.COLOR_PALETTE["success"]
        elif state.game_status == "lost":
            self.status.value = f"Game Over! Word: {state.secret_word}"
            self.status.color = config.COLOR_PALETTE["error"]
        elif state.game_status == "revealed":
            # Show a message that the word is revealed
            self.status.value = "Word is revealed! Continue playing or reset."
            self.status.color = config.COLOR_PALETTE["secondary"]
        else:
            self.status.value = state.error_message or ""
