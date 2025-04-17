
class HangmanGame:
    def __init__(self, secret_word: str, max_attempts: int = 6):
        self.secret_word = secret_word.upper()
        self.guessed_letters = set()
        self.max_attempts = max_attempts
        self.remaining_attempts = max_attempts
        self.game_status = "ongoing"  # Possible: "ongoing", "won", "lost"

    def guess_letter(self, letter: str) -> dict:
        """Process a letter guess and return game state update."""
        letter = letter.upper().strip()
        
        if len(letter) != 1 or not letter.isalpha():
            return {"valid": False, "message": "Invalid guess - must be a single letter"}
            
        if letter in self.guessed_letters:
            return {"valid": False, "message": "Letter already guessed"}
            
        self.guessed_letters.add(letter)
        
        if letter not in self.secret_word:
            self.remaining_attempts -= 1
            
        self._update_game_status()
        
        return {
            "valid": True,
            "is_correct": letter in self.secret_word,
            "remaining_attempts": self.remaining_attempts,
            "game_status": self.game_status
        }

    def _update_game_status(self):
        """Check win/lose conditions"""
        if self.remaining_attempts <= 0:
            self.game_status = "lost"
        elif all(c in self.guessed_letters for c in self.secret_word):
            self.game_status = "won"
        else:
            self.game_status = "ongoing"

    @property
    def display_word(self) -> str:
        """Get the word with underscores for unguessed letters"""
        return " ".join(
            c if c in self.guessed_letters else "_"
            for c in self.secret_word
        )

    def reset(self, new_word: str = None):
        """Reset game with optional new word"""
        if new_word:
            self.secret_word = new_word.upper()
        self.guessed_letters = set()
        self.remaining_attempts = self.max_attempts
        self.game_status = "ongoing"
