import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.app.state_manager import GameStateManager
from src.components.display import GameDisplay
from src.components.inputs import GameInputs
from src.config import config

def main(page: ft.Page):
    # Initialize core components
    state_manager = GameStateManager()
    state_manager.initialize_game()
    
    # Configure page
    page.title = "Multimodal Hangman"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.padding = 30

    # Create UI components
    display = GameDisplay()
    inputs = GameInputs(
        on_voice=lambda e: handle_guess("A"),  # Mock voice
        on_camera=lambda e: handle_guess("B")  # Mock camera
    )

    def handle_guess(letter: str):
        state = state_manager.process_guess(letter)
        display.update(state)
        page.update()

    def new_game(_):
        state_manager.initialize_game()
        display.update(state_manager._get_state())
        page.update()

    # Initial setup
    display.update(state_manager._get_state())

    # Assemble layout
    page.add(
        ft.Column([
            ft.Text("Hangman", style=config.TITLE_STYLE),
            ft.Divider(height=20),
            display,
            inputs,
            ft.ElevatedButton("New Game", on_click=new_game)
        ], spacing=25)
    )

ft.app(target=main)
