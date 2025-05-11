from agents import ItemHelpers, MessageOutputItem, Runner, trace,TResponseInputItem, function_tool, Agent
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frontend.src.app.state_manager import GameStateManager
import asyncio
import uuid
from dotenv import load_dotenv

load_dotenv()

# Using the singleton pattern for GameStateManager
# Print debug info about the import
import inspect
print(f"Agent using GameStateManager from: {inspect.getmodule(GameStateManager).__file__}")

manager = GameStateManager()
print(f"Agent's GameStateManager instance: {id(manager)}")
state = {"initialized": False}

# Helper function to get current game state
def get_current_state():
    """Get the current game state from the singleton manager"""
    if manager.current_game:
        return manager._get_state()
    return None

@function_tool
def start_game(word_choice: str = "agent") -> str:
    """Starts a new hangman game
    
    Args:
        word_choice: Who chooses the word - 'agent' for agent, 'user' for user
    """
    source = word_choice
    print(f"===AGENT DEBUG=== start_game called with source: {source}")
    if source == "agent":
        # Initialize game with a random word, which will trigger UI update via observer
        print("===AGENT DEBUG=== Starting game with random word")
        state["game_state"] = manager.initialize_game()
        print(f"===AGENT DEBUG=== Agent started game with word: {state['game_state'].secret_word}, game state observers: {len(manager._observers)}")
        return f"I've chosen a word with {len(state['game_state'].secret_word)} letters. You can start now!"
    else:
        print("===AGENT DEBUG=== Asking user for word")
        return "Perfect! Now type the word that needs to be guessed."

@function_tool
def set_user_word(word: str) -> str:
    """Sets a user-provided word for the hangman game
    
    Args:
        word: The word to use in the game
    """
    print(f"===AGENT DEBUG=== set_user_word called with word: {word}")
    # Initialize game with user's word, which will trigger UI update via observer
    state["game_state"] = manager.initialize_game(word)
    print(f"===AGENT DEBUG=== User set word: {word}, game state observers: {len(manager._observers)}")
    return f"Word set! It's {len(word)} letters long. You can start now."

@function_tool
def guess_letter(letter: str) -> str:
    """Guesses a letter in the hangman game
    
    Args:
        letter: The letter to guess
    """
    letter = letter.upper()
    
    # Make sure we have the latest game state
    current_state = get_current_state()
    if current_state:
        state["game_state"] = current_state
    
    # Process the guess and get updated state
    game_state = manager.process_guess(letter)

    if game_state.error_message:
        return f"Error: {game_state.error_message}"

    state["game_state"] = game_state
    print(f"Agent guessed letter {letter} for word {game_state.secret_word}, current display: {game_state.display_word}")

    msg = f"You suggested the letter '{letter}'. "
    msg += "✅ Correct!" if letter in game_state.secret_word else "❌ Not in the word."
    msg += f" Current word: {game_state.display_word} — Attempts remaining: {game_state.remaining_attempts}"

    if game_state.game_status == "won":
        return msg + " 🎉 You guessed the word! Want to start a new game?"
    elif game_state.game_status == "lost":
        return msg + f" 💀 You lost. The word was '{game_state.secret_word}'. Would you like to try again?"
    return msg

@function_tool
def restart() -> str:
    """Restarts the hangman game with a new random word
    """
    # Instead of just setting state to None, properly initialize a new game
    # This will trigger the observer notifications
    print(f"===AGENT DEBUG=== restart called, observers before restart: {len(manager._observers)}")
    state["game_state"] = manager.initialize_game()
    print(f"===AGENT DEBUG=== Agent restarted game with new word: {state['game_state'].secret_word}")
    return "New game! Do you want me to choose the word or do you want to enter it yourself?"

#  WELCOME AGENT
welcome_agent = Agent(
    name="welcome_agent",
    instructions="Welcome the user and explain the rules of the hangman game.",
    tools=[start_game],
)

# WORDSETTER AGENT
wordsetter_agent = Agent(
    name="wordsetter_agent",
    instructions="Choose a word to guess or ask the user to enter one.",
    tools=[set_user_word],
)

# LETTER GUESSER AGENT
letter_guesser_agent = Agent(
    name="letter_guesser_agent",
    instructions="Suggest a letter to guess.",
    tools=[guess_letter],
)

# GAME RESTARTER AGENT
game_restarter_agent = Agent(
    name="game_restarter_agent",
    instructions="Restart a new game.",
    tools=[restart],
)

agent = Agent(
    name="hangman_game_agent",
    instructions=
    """
        You are the manager of the hangman game. Welcome the user with a welcome message and briefly explain the rules:
            - The user can guess letters one at a time.
            - The word can be chosen by you or inserted by the game randomly.
            - Letters can be entered by typing, speaking, or drawing.

        Always mention input options to the user:
            - If they want to draw a letter, tell them to say "I want to draw a letter"
            - If they want to say a letter, tell them to say "I want to use voice input"
            - To return to chat mode, they can say "I want to use chat" or "back to chat"
            - They can always type letters in the chat

        After each letter:
            - Confirm to the user what they proposed.
            - Update the game state.
            - Tell them if they won or lost.

        If the word is completed or all attempts are lost, ask if they want to start a new game.
        Remind users they can switch input methods at any time.
    """,
    tools=[
        welcome_agent.as_tool(
            tool_name = "welcome_agent",
            tool_description = "Welcomes the user and explains the rules of the game.",
        ),
        wordsetter_agent.as_tool(
            tool_name = "wordsetter_agent",
            tool_description = "The user or agent chooses a word to guess.",
        ),
        letter_guesser_agent.as_tool(
            tool_name = "letter_guesser_agent",
            tool_description = "The user suggests a letter to guess.",
        ),
        game_restarter_agent.as_tool(
            tool_name = "game_restarter_agent",
            tool_description = "Restarts a new game.",
        ),
    ]
)

async def main():
    inputs: list[TResponseInputItem] = []
    conversation_id = str(uuid.uuid4().hex[:16])

    while True:
        user_input = input("User: ")
        inputs.append({"content": user_input, "role": "user"})

        with trace("Game Agent", group_id=conversation_id):
            result = await Runner.run(agent, input=inputs)

            for item in result.new_items:
                if isinstance(item, MessageOutputItem):
                    text = ItemHelpers.text_message_output(item)
                    if text:
                        print(f"Bot: {text}")
        inputs = result.to_input_list()
            

if __name__ == "__main__":
    asyncio.run(main())
