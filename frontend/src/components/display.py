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
        self.word.value = state.display_word
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
        else:
            self.status.value = state.error_message or ""
