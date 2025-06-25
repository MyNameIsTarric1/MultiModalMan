from agents import ItemHelpers, MessageOutputItem, Runner, trace, function_tool, Agent
import sys
import os
import inspect
import asyncio
import uuid
from dotenv import load_dotenv
from typing import TypedDict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frontend.src.app.state_manager import GameStateManager

load_dotenv()

# Define TResponseInputItem type for type hints
class TResponseInputItem(TypedDict):
    content: str
    role: str

# Using the singleton pattern for GameStateManager
# Print debug info about the import
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
def sync_with_game() -> str:
    """Checks if there's an active game and syncs the agent with it"""
    current_state = get_current_state()
    print("===AGENT DEBUG=== Checking for active game")
    
    if not current_state or not manager.current_game:
        print("===AGENT DEBUG=== No active game found during sync")
        return "There's no active game at the moment. Would you like to start a new one?"
    
    # Store the game state
    state["game_state"] = current_state
    
    # Get game details for a useful response
    secret_word = current_state.secret_word
    display_word = current_state.display_word
    remaining_attempts = current_state.remaining_attempts
    guessed_letters = ", ".join(sorted(current_state.guessed_letters)) if current_state.guessed_letters else "none"
    game_status = current_state.game_status
    
    print(f"===AGENT DEBUG=== Successfully synced with active game, word: {secret_word}, display: {display_word}, status: {game_status}")
    
    # Provide different responses based on game status
    if game_status == "won":
        return f"I've synced with your active game! The game has already been won! The word was '{secret_word}'. Would you like to start a new game?"
    elif game_status == "lost":
        return f"I've synced with your active game! The game has already been lost. The word was '{secret_word}'. Would you like to start a new game?"
    else:
        # Game is still ongoing
        return f"I've synced with your active game! You have {remaining_attempts} attempts remaining. Letters guessed so far: {guessed_letters}. What letter would you like to guess next?"

@function_tool
def start_game(word_choice: str = "agent") -> str:
    """Starts a new hangman game
    
    Args:
        word_choice: Who chooses the word - 'agent' for agent, 'user' for user
    """
    # Check if there's already an active game
    current_state = get_current_state()
    if current_state and manager.current_game:
        # If there's an active game, sync with it first
        state["game_state"] = current_state
        print(f"===AGENT DEBUG=== Found active game with word: {state['game_state'].secret_word}")
        
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
    
    # Check if there's already an active game
    current_state = get_current_state()
    if current_state and manager.current_game:
        # If there's an active game, sync with it first
        state["game_state"] = current_state
        print(f"===AGENT DEBUG=== Found active game with word: {state['game_state'].secret_word}, syncing first")
        
        # Initialize game with user's word, which will trigger UI update via observer
        state["game_state"] = manager.initialize_game(word)
        print(f"===AGENT DEBUG=== User set word: {word}, game state observers: {len(manager._observers)}")
        return f"Word set! It's {len(word)} letters long. You can start now!"
    else:
        # Initialize game with user's word, which will trigger UI update via observer
        state["game_state"] = manager.initialize_game(word)
        print(f"===AGENT DEBUG=== User set word: {word}, game state observers: {len(manager._observers)}")
        return f"Word set! It's {len(word)} letters long. You can start now!"

@function_tool
def guess_letter(letter: str) -> str:
    """Guesses a letter in the hangman game
    
    Args:
        letter: The letter to guess
    """
    letter = letter.upper()
    print(f"===AGENT DEBUG=== guess_letter called with letter: {letter}")
    
    # Make sure we have the latest game state
    current_state = get_current_state()
    
    # If no active game, try to sync first and then clearly indicate we need to start a game
    if not current_state or not manager.current_game:
        print("===AGENT DEBUG=== No active game found when trying to guess letter")
        return "I need to check if there's an active game first. It seems there's no active game yet. Would you like to start a new game?"
    
    # We have an active game, so sync with it
    if current_state:
        print(f"===AGENT DEBUG=== Found active game with word: {manager.current_game.secret_word}, syncing state")
        state["game_state"] = current_state
        
        # Check if the game is already over
        if current_state.game_status == "won":
            return f"This game has already been won! The word was '{current_state.secret_word}'. Would you like to start a new game?"
        elif current_state.game_status == "lost":
            return f"This game has already been lost. The word was '{current_state.secret_word}'. Would you like to start a new game?"
    
    try:
        # Process the guess and get updated state
        print(f"===AGENT DEBUG=== Processing guess for letter: {letter} in word: {manager.current_game.secret_word}")
        game_state = manager.process_guess(letter)
        
        if game_state.error_message:
            print(f"===AGENT DEBUG=== Error processing guess: {game_state.error_message}")
            return f"Error: {game_state.error_message}"

        # Update the state dictionary
        state["game_state"] = game_state
        
        # Build the response
        print(f"===AGENT DEBUG=== Guess processed successfully, word: {game_state.secret_word}, display: {game_state.display_word}")
        
        # Format the response
        msg = f"You suggested the letter '{letter}'. "
        msg += "✅ Correct!" if letter in game_state.secret_word else "❌ Not in the word."
        msg += f" Attempts remaining: {game_state.remaining_attempts}"

        if game_state.game_status == "won":
            return msg + " 🎉 You guessed the word! Want to start a new game?"
        elif game_state.game_status == "lost":
            return msg + f" 💀 You lost. The word was '{game_state.secret_word}'. Would you like to try again?"
        return msg
        
    except Exception as e:
        print(f"===AGENT DEBUG=== Exception in guess_letter: {str(e)}")
        return f"I encountered an error processing your guess: {str(e)}. Let's try syncing with the game first."

@function_tool
def restart() -> str:
    """Restarts the hangman game with a new random word
    """
    # Print debug info about current state
    if manager.current_game:
        print(f"===AGENT DEBUG=== restart called, current word before restart: {manager.current_game.secret_word}")
    else:
        print("===AGENT DEBUG=== restart called but no active game found")
        
    print(f"===AGENT DEBUG=== restart called, observers before restart: {len(manager._observers)}")
    
    # Initialize a new game, which will trigger the observer notifications
    state["game_state"] = manager.initialize_game()
    print(f"===AGENT DEBUG=== Agent restarted game with new word: {state['game_state'].secret_word}")
    
    return "New game! Do you want me to choose the word or do you want to enter it yourself?"

# Create a sync agent
sync_agent = Agent(
    name="sync_agent",
    instructions="Sync with an active game if one exists.",
    tools=[sync_with_game],
    model="gpt-4o"  # Set the model here
)

#  WELCOME AGENT
welcome_agent = Agent(
    name="welcome_agent",
    instructions="Welcome the user and explain the rules of the hangman game.",
    tools=[start_game],
    model="gpt-4o"  # Set the model here
)

# WORDSETTER AGENT
wordsetter_agent = Agent(
    name="wordsetter_agent",
    instructions="Choose a word to guess or ask the user to enter one.",
    tools=[set_user_word],
    model="gpt-4o"  # Set the model here
)

# LETTER GUESSER AGENT
letter_guesser_agent = Agent(
    name="letter_guesser_agent",
    instructions="Suggest a letter to guess.",
    tools=[guess_letter],
    model="gpt-4o"  # Set the model here
)

# GAME RESTARTER AGENT
game_restarter_agent = Agent(
    name="game_restarter_agent",
    instructions="Restart a new game.",
    tools=[restart],
    model="gpt-4o"  # Set the model here
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

        IMPORTANT WORKFLOW FOR GUESSING LETTERS:
            - ALWAYS call the sync_agent tool first before processing any letter guesses
            - This ensures you connect to any active game that might have been started manually
            - Only after confirming an active game exists, use the letter_guesser_agent to process the guess
            - If sync_agent indicates no active game, offer to start a new game

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
        sync_agent.as_tool(
            tool_name = "sync_agent",
            tool_description = "Syncs with an active game if one exists.",
        ),
    ],
    model="gpt-4o"  # Set the model here
)

async def main():
    inputs: List[TResponseInputItem] = []
    conversation_id = str(uuid.uuid4().hex[:16])

    while True:
        try:
            user_input = input("User: ")
            inputs.append({"content": user_input, "role": "user"})

            print(f"===AGENT RUNNER=== Running agent with inputs, conversation ID: {conversation_id}")
            
            with trace("Game Agent", group_id=conversation_id):
                result = await Runner.run(
                    agent, 
                    input=inputs,
                )

                for item in result.new_items:
                    if isinstance(item, MessageOutputItem):
                        text = ItemHelpers.text_message_output(item)
                        if text:
                            print(f"Bot: {text}")
                            
                            # After each agent response, check game state
                            current_state = get_current_state()
                            if current_state and manager.current_game:
                                print(f"===AGENT RUNNER=== Current game state: word={manager.current_game.secret_word}, display={current_state.display_word}")
            
            # Update inputs for the next conversation turn
            inputs = result.to_input_list()
        except Exception as e:
            print(f"===AGENT RUNNER=== Error in main loop: {str(e)}")
            # Continue the conversation even after an error
            if not inputs:
                inputs = [{"content": "Hello", "role": "user"}]
            

if __name__ == "__main__":
    asyncio.run(main())
