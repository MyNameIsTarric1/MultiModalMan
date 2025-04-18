import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from src.components.display import GameDisplay
from src.app.state_manager import GameStateManager

class GamePanel:
    def __init__(self, on_reset_callback=None, page=None):
        self.state_manager = GameStateManager()
        self.state_manager.initialize_game()
        self.on_reset = on_reset_callback
        self.page = page  # Store page reference
        
        # Game display components
        self.display = GameDisplay()
        self.display.update(self.state_manager._get_state())
        
        # Game control buttons
        self.start_btn = ft.ElevatedButton(
            "Start New Game", 
            icon=ft.Icons.PLAY_ARROW,
            on_click=self.start_game,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600,
                padding=15
            )
        )
        
        self.stop_btn = ft.ElevatedButton(
            "Reset Game", 
            icon=ft.Icons.STOP,
            on_click=self.new_game,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_600,
                padding=15
            )
        )
        
        self.finish_btn = ft.ElevatedButton(
            "Reveal Word", 
            icon=ft.Icons.VISIBILITY,
            on_click=self.reveal_word,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.ORANGE_600,
                padding=15
            )
        )
        
    def handle_guess(self, letter: str):
        """Process a letter guess"""
        state = self.state_manager.process_guess(letter)
        self.display.update(state)
        return state
    
    def start_game(self, e=None):
        """Start a new game with custom word"""
        # Use page from instance or global fallback
        page_ref = self.page or ft.page
        
        def close_dialog(e):
            word_input_dialog.open = False
            page_ref.update()
            
            # Check if a word was entered
            if word_input.value:
                word = word_input.value.strip().upper()  # Convert to uppercase
                if word.isalpha():
                    # Show confirmation notification
                    if hasattr(page_ref, 'show_snack_bar'):
                        page_ref.show_snack_bar(
                            ft.SnackBar(
                                content=ft.Text(f"New game started with a {len(word)} letter word!"),
                                action="OK"
                            )
                        )
                    
                    self.state_manager.initialize_game(word)
                    self.display.update(self.state_manager._get_state())
                    
                    # Call reset callback if provided
                    if self.on_reset:
                        self.on_reset()
                else:
                    # Show error if word contains non-alphabetic characters
                    if hasattr(page_ref, 'show_snack_bar'):
                        page_ref.show_snack_bar(
                            ft.SnackBar(
                                content=ft.Text("Please enter only letters"),
                                action="OK"
                            )
                        )
        
        # Create word input dialog
        word_input = ft.TextField(
            label="Enter a word for the game",
            password=True,  # Hide the word being typed
            autofocus=True,
            on_submit=close_dialog  # Allow Enter key to submit
        )
        
        word_input_dialog = ft.AlertDialog(
            title=ft.Text("Start New Game"),
            content=ft.Column([
                ft.Text("Enter a word for the opponent to guess:"),
                word_input,
                ft.Text("The word will be hidden as you type.", 
                       size=12, 
                       italic=True, 
                       color=ft.Colors.GREY_600)
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Start", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        # Show the dialog
        if page_ref:
            page_ref.dialog = word_input_dialog
            word_input_dialog.open = True
            page_ref.update()
        
    def new_game(self, e=None):
        """Reset the current game"""
        self.state_manager.initialize_game()
        self.display.update(self.state_manager._get_state())
        
        # Show notification using page reference
        if self.page:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Game reset with a new random word!"),
                    action="OK"
                )
            )
        
        # Call reset callback if provided
        if self.on_reset:
            self.on_reset()
            
    def reveal_word(self, e=None):
        """Reveal the hidden word"""
        if not self.state_manager.current_game:
            return
            
        # Get the current state
        state = self.state_manager._get_state()
        
        # Only reveal if the game is still ongoing or already revealed
        if state.game_status == "ongoing" or state.game_status == "revealed":
            # Toggle between revealed and hidden
            if state.game_status == "revealed":
                # Switch back to normal display
                state.game_status = "ongoing"
                state.error_message = "Word hidden again"
                # The normal display will be shown
            else:
                # Show the actual word instead of underscores
                state.game_status = "revealed"
                # We don't change error_message here as we'll display the word differently
                
            # Update display with current state
            self.display.update(state)
            # Force page update
            if self.page:
                self.page.update()
        
    def create_panel(self):
        """Create the left panel with game display"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Hangman", style=config.TITLE_STYLE),
                ft.Divider(height=10),
                
                # Game control buttons in a row
                ft.Row([
                    self.start_btn,
                    self.stop_btn,
                    self.finish_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Divider(height=20),
                
                # Game display
                self.display
            ], spacing=15),
            expand=True,
            padding=20
        )
