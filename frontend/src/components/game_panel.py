import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from src.components.display import GameDisplay
from src.app.state_manager import GameStateManager

class GamePanel:
    def __init__(self, on_reset_callback=None):
        self.state_manager = GameStateManager()
        self.state_manager.initialize_game()
        self.on_reset = on_reset_callback
        
        # Game display components
        self.display = GameDisplay()
        self.display.update(self.state_manager._get_state())
        
    def handle_guess(self, letter: str):
        """Process a letter guess"""
        state = self.state_manager.process_guess(letter)
        self.display.update(state)
        return state
        
    def new_game(self, e=None):
        """Start a new game"""
        self.state_manager.initialize_game()
        self.display.update(self.state_manager._get_state())
        
        # Call reset callback if provided
        if self.on_reset:
            self.on_reset()
            
    def create_panel(self):
        """Create the left panel with game display"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Hangman", style=config.TITLE_STYLE),
                ft.Divider(height=20),
                self.display,
                ft.ElevatedButton("New Game", on_click=self.new_game)
            ], spacing=25),
            expand=True,
            padding=20
        )
