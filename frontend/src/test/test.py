import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.state_manager import GameStateManager

def test_game_flow():
    manager = GameStateManager()
    manager.initialize_game("PYTHON")
    
    # Test correct guess
    state = manager.process_guess("P")
    print(f"After guessing P: {state.display_word}")  # P _ _ _ _ _
    
    # Test incorrect guess
    state = manager.process_guess("X")
    print(f"Remaining attempts: {state.remaining_attempts}")  # 5
    
    # Test invalid guess
    state = manager.process_guess("3")
    print(f"Error message: {state.error_message}")  # Invalid guess
    
    # Test winning scenario
    # Guess remaining letters: Y, T, H, O, N (skip P)
    for letter in "YTHON":
        state = manager.process_guess(letter)
    
    print(f"Final display: {state.display_word}")  # P Y T H O N
    print(f"Final status: {state.game_status}")    # "won"

if __name__ == "__main__":
    test_game_flow()
