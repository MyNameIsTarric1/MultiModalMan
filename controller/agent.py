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
def start_game(word_choice: str = "agente") -> str:
    """Starts a new hangman game
    
    Args:
        word_choice: Who chooses the word - 'agente' for agent, 'utente' for user
    """
    source = word_choice
    print(f"===AGENT DEBUG=== start_game called with source: {source}")
    if source == "agente":
        # Initialize game with a random word, which will trigger UI update via observer
        print("===AGENT DEBUG=== Starting game with random word")
        state["game_state"] = manager.initialize_game()
        print(f"===AGENT DEBUG=== Agent started game with word: {state['game_state'].secret_word}, game state observers: {len(manager._observers)}")
        return f"Ho scelto una parola di {len(state['game_state'].secret_word)} lettere. Inizia pure!"
    else:
        print("===AGENT DEBUG=== Asking user for word")
        return "Perfetto! Scrivi ora la parola che deve essere indovinata."

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
    return f"Parola impostata! È lunga {len(word)} lettere. Inizia pure."

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
        return f"Errore: {game_state.error_message}"

    state["game_state"] = game_state
    print(f"Agent guessed letter {letter} for word {game_state.secret_word}, current display: {game_state.display_word}")

    msg = f"Hai proposto la lettera '{letter}'. "
    msg += "✅ Corretta!" if letter in game_state.secret_word else "❌ Non è nella parola."
    msg += f" Parola attuale: {game_state.display_word} — Tentativi rimasti: {game_state.remaining_attempts}"

    if game_state.game_status == "won":
        return msg + " 🎉 Hai indovinato la parola! Vuoi iniziare una nuova partita?"
    elif game_state.game_status == "lost":
        return msg + f" 💀 Hai perso. La parola era '{game_state.secret_word}'. Vuoi riprovare?"
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
    return "Nuova partita! Vuoi che scelga io la parola o vuoi inserirla tu?"

#  WELCOME AGENT
welcome_agent = Agent(
    name="welcome_agent",
    instructions="Accogli l'utente e spiega le regole del gioco dell'impiccato.",
    tools=[start_game],
)

# WORDSETTER AGENT
wordsetter_agent = Agent(
    name="wordsetter_agent",
    instructions="Scegli una parola da indovinare o chiedi all'utente di inserirne una.",
    tools=[set_user_word],
)

# LETTER GUESSER AGENT
letter_guesser_agent = Agent(
    name="letter_guesser_agent",
    instructions="Proponi una lettera da indovinare.",
    tools=[guess_letter],
)

# GAME RESTARTER AGENT
game_restarter_agent = Agent(
    name="game_restarter_agent",
    instructions="Riavvia una nuova partita.",
    tools=[restart],
)

agent = Agent(
    name="impiccato_game_agent",
    instructions=
    """
		Sei il gestore del gioco dell'impiccato. Accogli l'utente con un messaggio di benvenuto e spiega brevemente le regole:
			- L'utente può indovinare lettere una alla volta.
			- La parola può essere scelta da te o inserita dal gioco in modo randomico.
			- Le lettere possono essere inserite scrivendole, dicendole a voce o disegnandole.

		Dopo ogni lettera:
			- Dai conferma all’utente di cosa ha proposto.
			- Aggiorna lo stato del gioco.
			- Dì se ha vinto o perso.

		Se la parola è completata o si perdono tutti i tentativi, chiedi se vuole iniziare una nuova partita.
	""",
    tools=[
        welcome_agent.as_tool(
            tool_name = "welcome_agent",
            tool_description = "Accoglie l'utente e spiega le regole del gioco.",
        ),
        wordsetter_agent.as_tool(
            tool_name = "wordsetter_agent",
            tool_description = "L'utente o l'agente sceglie una parola da indovinare.",
        ),
        letter_guesser_agent.as_tool(
            tool_name = "letter_guesser_agent",
            tool_description = "L'utente propone una lettera da indovinare.",
        ),
        game_restarter_agent.as_tool(
            tool_name = "game_restarter_agent",
            tool_description = "Riavvia una nuova partita.",
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

