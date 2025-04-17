from dataclasses import dataclass
from typing import Optional
from .game_logic import HangmanGame

@dataclass
class GameState:
    display_word: str
    guessed_letters: set
    remaining_attempts: int
    game_status: str  # "ongoing", "won", "lost"
    error_message: Optional[str] = None

class GameStateManager:
    def __init__(self):
        self.current_game: Optional[HangmanGame] = None
        self.word_bank = ["PYTHON", "HANGMAN", "DEVELOPER"]  # Temporary - replace with API later
        
    def initialize_game(self, word: str = None):
        """Start a new game, optionally with specific word"""
        if not word:
            word = self._get_random_word()
        self.current_game = HangmanGame(word)
        return self._get_state()

    def process_guess(self, letter: str) -> GameState:
        """Handle a guess attempt"""
        if not self.current_game or self.current_game.game_status != "ongoing":
            return self._get_state(error="No active game")
            
        result = self.current_game.guess_letter(letter)
        
        if not result["valid"]:
            return self._get_state(error=result["message"])
            
        return self._get_state()

    def _get_random_word(self) -> str:
        """Temporary - replace with API call later"""
        import random
        return random.choice(self.word_bank)

    def _get_state(self, error: str = None) -> GameState:
        """Convert current game state to GameState dataclass"""
        if not self.current_game:
            return GameState(
                display_word="",
                guessed_letters=set(),
                remaining_attempts=0,
                game_status="lost",
                error_message=error
            )
            
        return GameState(
            display_word=self.current_game.display_word,
            guessed_letters=self.current_game.guessed_letters.copy(),
            remaining_attempts=self.current_game.remaining_attempts,
            game_status=self.current_game.game_status,
            error_message=error
        )
