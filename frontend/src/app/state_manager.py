from dataclasses import dataclass
from typing import Optional, List, Callable
from .game_logic import HangmanGame

@dataclass
class GameState:
    display_word: str
    guessed_letters: set
    remaining_attempts: int
    game_status: str  # "ongoing", "won", "lost", "revealed"
    error_message: Optional[str] = None
    secret_word: str = ""

class GameStateManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print("Creating new GameStateManager instance")
            cls._instance = super(GameStateManager, cls).__new__(cls)
            cls._instance._initialized = False
        else:
            print("Reusing existing GameStateManager instance")
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            print("Initializing GameStateManager for the first time")
            self.current_game: Optional[HangmanGame] = None
            self.word_bank = ["PYTHON", "HANGMAN", "DEVELOPER"]  # Temporary - replace with API later
            self._initialized = True
            # Add observers list for UI components
            self._observers: List[Callable[[GameState], None]] = []
        
    def add_observer(self, callback: Callable[[GameState], None]) -> None:
        """Add a callback function to be called when game state changes"""
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback: Callable[[GameState], None]) -> None:
        """Remove a callback function from the observers list"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, state: GameState) -> None:
        """Notify all observers of a state change"""
        for callback in self._observers:
            callback(state)
        
    def initialize_game(self, word: str = None):
        """Start a new game, optionally with specific word"""
        if not word:
            word = self._get_random_word()
            print(f"Initializing game with random word: {word}")
        else:
            print(f"Initializing game with provided word: {word}")
        self.current_game = HangmanGame(word)
        state = self._get_state()
        print(f"Notifying {len(self._observers)} observers of new game")
        self._notify_observers(state)
        return state

    def process_guess(self, letter: str) -> GameState:
        """Handle a guess attempt"""
        if not self.current_game or self.current_game.game_status != "ongoing":
            state = self._get_state(error="No active game")
            self._notify_observers(state)
            return state
            
        result = self.current_game.guess_letter(letter)
        
        if not result["valid"]:
            state = self._get_state(error=result["message"])
            self._notify_observers(state)
            return state
            
        state = self._get_state()
        self._notify_observers(state)
        return state

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
                error_message=error,
                secret_word=""
            )
            
        return GameState(
            display_word=self.current_game.display_word,
            guessed_letters=self.current_game.guessed_letters.copy(),
            remaining_attempts=self.current_game.remaining_attempts,
            game_status=self.current_game.game_status,
            error_message=error,
            secret_word=self.current_game.secret_word  # Add the secret word
        )
