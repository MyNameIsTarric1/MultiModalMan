import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from src.components.display import GameDisplay
from src.app.state_manager import GameStateManager
from src.components.hangman_visual import HangmanVisual
from src.components.manual_input import ManualInput

class GamePanel:
    def __init__(self, on_reset_callback=None, page=None, state_manager=None):
        # Use provided state_manager or create a new one if not provided
        self.state_manager = state_manager if state_manager else GameStateManager()
        print(f"GamePanel initialized with state_manager: {id(self.state_manager)}")
        self.on_reset = on_reset_callback
        self.page = page  # Store page reference
        
        # Create a snackbar
        self.snackbar = ft.SnackBar(
            content=ft.Text(""),
            action="OK"
        )
        
        if self.page:
            self.page.overlay.append(self.snackbar)
        
        # Game display components
        self.display = GameDisplay()
        
        # Add hangman visual component
        self.hangman_visual = HangmanVisual()
        
        # Add manual input component
        self.manual_input = ManualInput(on_guess_callback=self.handle_guess)
        
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
        
        # Store current state but don't update visuals yet
        # We'll update them after the controls are added to the page
        self._initial_state = self.state_manager._get_state()
        
        # Check if a game is already running, otherwise initialize a new one
        # but don't update the UI immediately
        if not self.state_manager.current_game:
            self._initial_state = self.state_manager.initialize_game()
        
        # Register as an observer to the state manager AFTER getting initial state
        # to avoid early updates
        self.state_manager.add_observer(self.on_state_changed)
        
        # Flag to indicate if controls have been properly added to the page
        self._controls_added = False
    
    def on_state_changed(self, state):
        """Called when the game state changes"""
        try:
            print(f"GamePanel received state change notification, word: {state.secret_word if hasattr(state, 'secret_word') else 'unknown'}")
            print(f"Current display: {state.display_word}")
            
            # Only update UI components if they've been added to the page
            if not hasattr(self, '_controls_added') or not self._controls_added:
                print("Controls not yet added to page, skipping visual update")
                # Store the state for later update
                self._initial_state = state
                return
            
            # Update the display
            self.display.update(state)
            
            # Update the hangman visual
            if self.state_manager.current_game:
                wrong_guesses = self.state_manager.current_game.max_attempts - state.remaining_attempts
                try:
                    self.hangman_visual.update_state(wrong_guesses)
                    print(f"Updated hangman visual to {wrong_guesses} wrong guesses")
                except AssertionError as e:
                    print(f"Couldn't update hangman visual yet: {e}")
            
            # Update the page to reflect changes
            if self.page:
                self.page.update()
                print("Updated page with new game state")
                
            # Show error messages if any
            if state.error_message:
                self.show_message(state.error_message)
        except Exception as e:
            print(f"Error updating UI: {e}")
    
    # Helper method to show snackbar messages
    def show_message(self, message):
        """Show a message in the snackbar"""
        if not self.page:
            return
            
        self.snackbar.content.value = message
        self.snackbar.open = True
        self.page.update()
    
    def handle_guess(self, letter: str):
        """Process a letter guess"""
        print(f"GamePanel handling guess for letter: {letter}")
        
        # Print debug info about current game state before processing guess
        if self.state_manager.current_game:
            print(f"Current game word before guess: {self.state_manager.current_game.secret_word}")
            
        state = self.state_manager.process_guess(letter)
        print(f"Guess processed, result: {state.display_word}, remaining attempts: {state.remaining_attempts}")
        
        # Skip UI updates if controls haven't been added yet
        if not hasattr(self, '_controls_added') or not self._controls_added:
            print("Controls not yet added - skipping visual updates for this guess")
            return state
            
        self.display.update(state)
        
        # Update the hangman visual based on wrong guesses
        # We can calculate wrong guesses from max attempts and remaining attempts
        wrong_guesses = self.state_manager.current_game.max_attempts - state.remaining_attempts
        try:
            self.hangman_visual.update_state(wrong_guesses)
            print(f"Updated hangman visual after guess: wrong guesses = {wrong_guesses}")
        except Exception as e:
            print(f"Error updating hangman visual: {e}")
        
        # Update the page to reflect changes
        if self.page:
            self.page.update()
            print("Updated page after guess")
            
        return state
    
    def start_game(self, e=None):
        """Start a new game with either random or custom word"""
        print("Start game button clicked")
        
        # Make sure we have a page reference
        if not self.page:
            print("No page reference found!")
            return
            
        print(f"Page reference found: {self.page}")
        
        # Create a modal overlay container
        modal_overlay = ft.Container(
            width=self.page.width,
            height=self.page.height,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            alignment=ft.alignment.center,
            expand=True
        )
        
        # Create a Container to act as our custom dialog
        dialog_container = ft.Container(
            width=400,
            height=450,  # Increased height to accommodate new elements
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=20,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLACK54,
                offset=ft.Offset(0, 0),
            ),
        )
        
        # Create word input field with password visibility toggle
        word_input = ft.TextField(
            label="Enter a word for the game",
            password=True,  # Start with hidden text
            autofocus=True,
            width=300
        )
        
        # Create custom word button (initially disabled)
        custom_word_button = ft.ElevatedButton(
            "Start with Custom Word",
            icon=ft.Icons.CREATE,
            on_click=None,  # Will be set later
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_600  # Start with red color
            ),
            width=200,  # Reduced width to fit better
            disabled=True  # Initially disabled
        )
        
        # Visibility toggle for password field
        show_password = False
        
        def toggle_password_visibility(e):
            nonlocal show_password
            show_password = not show_password
            word_input.password = not show_password
            password_toggle.icon = ft.Icons.VISIBILITY if show_password else ft.Icons.VISIBILITY_OFF
            dialog_container.update()
        
        password_toggle = ft.IconButton(
            icon=ft.Icons.VISIBILITY_OFF,
            tooltip="Show/Hide Word",
            on_click=toggle_password_visibility
        )
        
        # Function to validate input and enable/disable button
        def validate_input(e):
            if word_input.value and word_input.value.strip():
                custom_word_button.disabled = False
                # Change to green when text is entered
                custom_word_button.style.bgcolor = ft.Colors.GREEN_600
            else:
                custom_word_button.disabled = True
                # Change back to red when empty
                custom_word_button.style.bgcolor = ft.Colors.RED_600
            dialog_container.update()
        
        # Add on_change handler to the input field
        word_input.on_change = validate_input
        
        # Define button callbacks
        def start_with_random_word(e):
            print("Random word button clicked")
            # Remove dialog
            self.page.overlay.remove(modal_overlay)
            self.page.update()
            
            # Initialize with random word
            self.state_manager.initialize_game()
            self.display.update(self.state_manager._get_state())
            
            # Reset hangman visual
            self.hangman_visual.update_state(0)
            
            # Show confirmation message
            self.show_message("New game started with a random word!")
            
            # Call reset callback if provided
            if self.on_reset:
                self.on_reset()
        
        def start_with_custom_word(e):
            print("Start with custom word button clicked")
            # Only process if a valid word was entered
            if word_input.value:
                word = word_input.value.strip().upper()  # Convert to uppercase
                if word.isalpha():
                    # Remove dialog
                    self.page.overlay.remove(modal_overlay)
                    self.page.update()
                    
                    # Initialize with custom word
                    self.state_manager.initialize_game(word)
                    self.display.update(self.state_manager._get_state())
                    
                    # Reset hangman visual
                    self.hangman_visual.update_state(0)
                    
                    # Show confirmation message
                    self.show_message(f"New game started with a {len(word)} letter word!")
                    
                    # Call reset callback if provided
                    if self.on_reset:
                        self.on_reset()
                else:
                    # Show error if word contains non-alphabetic characters
                    self.show_message("Please enter only letters")
        
        # Set the click handler
        custom_word_button.on_click = start_with_custom_word
                
        def close_dialog(e):
            print("Dialog close button clicked")
            self.page.overlay.remove(modal_overlay)
            self.page.update()
        
        # Create dialog content
        dialog_content = ft.Column([
            ft.Row([
                ft.Text("Start New Game", size=22, weight="bold"),
                ft.IconButton(icon=ft.Icons.CLOSE, on_click=close_dialog)
            ], alignment="spaceBetween"),
            ft.Divider(),
            ft.Text("Choose how to start a new game:"),
            ft.Container(height=10),
            ft.ElevatedButton(
                "Use Random Word",
                icon=ft.Icons.CASINO,
                on_click=start_with_random_word,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.GREEN_600
                ),
                width=300
            ),
            ft.Text("— OR —", 
                   size=14,
                   color=ft.Colors.GREY_600,
                   text_align=ft.TextAlign.CENTER),
            ft.Text("Enter your own word:", size=14),
            ft.Row([
                word_input,
                password_toggle
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text("The word will be hidden as you type.", 
                   size=12, 
                   italic=True, 
                   color=ft.Colors.GREY_600),
            ft.Container(height=10),
            # Final buttons row
            ft.Row([
                ft.OutlinedButton(
                    "Cancel", 
                    on_click=close_dialog,
                    width=120  # Set specific width
                ),
                custom_word_button  # Use our new styled button
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND),  # Change to SPACE_AROUND for better distribution
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10)
        
        # Set dialog content
        dialog_container.content = dialog_content
        
        # Add dialog to modal overlay
        modal_overlay.content = dialog_container
        
        # Add modal to page overlay
        try:
            # Add to overlay
            self.page.overlay.append(modal_overlay)
            print("Dialog added to overlay")
            self.page.update()
            print("Page updated after adding dialog")
        except Exception as e:
            print(f"Error showing dialog: {e}")
            self.show_message(f"Error starting game: {str(e)}")
        
    def new_game(self, e=None):
        """Reset the current game"""
        self.state_manager.initialize_game()
        state = self.state_manager._get_state()
        self.display.update(state)
        
        # Reset hangman visual
        self.hangman_visual.update_state(0)
        
        # Show notification using our helper method
        self.show_message("Game reset with a new random word!")
        
        # Call reset callback if provided
        if self.on_reset:
            self.on_reset()
            
    def reveal_word(self, e=None):
        """Reveal the hidden word"""
        if not self.state_manager.current_game:
            # Check if no game is active
            self.show_message("No active game to reveal word")
            return
            
        # Get the current state - make sure we're getting the freshest state
        # This ensures we'll get the word that was set by the agent if it was used
        state = self.state_manager._get_state()
        
        # Debug print to check what word we're revealing
        print(f"Attempting to reveal word: {self.state_manager.current_game.secret_word}")
        
        # Only reveal if the game is still ongoing or already revealed
        if state.game_status == "ongoing" or state.game_status == "revealed":
            # Toggle between revealed and hidden
            if state.game_status == "revealed":
                # Switch back to normal display
                state.game_status = "ongoing"
                state.error_message = "Word hidden again"
                # Show notification
                self.show_message("Word hidden again")
            else:
                # Show the actual word instead of underscores
                state.game_status = "revealed"
                # Show notification
                self.show_message(f"Word revealed: {self.state_manager.current_game.secret_word}")
                
            # Update display with current state
            self.display.update(state)
            # Force page update
            if self.page:
                self.page.update()
        
    def create_panel(self):
        """Create the left panel with game display"""
        panel = ft.Container(
            content=ft.Column([
                ft.Text("Hangman", style=config.TITLE_STYLE),
                # Game control buttons in a row
                ft.Row([
                    self.start_btn,
                    self.stop_btn,
                    self.finish_btn
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                
                
                # Game display (updated word)
                self.display,
                
                # Add hangman visual in a row with centered alignment
                ft.Row([
                    self.hangman_visual
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Divider(height=20),
                
                # Add manual input at the bottom
                self.manual_input
                
            ], spacing=15),
            expand=True,
            padding=20
        )
        
        # Use a one-time callback to update UI components when they've been added to the page
        def init_ui_components(e):
            try:
                print("Initializing UI components now that they're added to the page")
                # Mark controls as added
                self._controls_added = True
                
                # Now update the display with our stored state
                if self._initial_state:
                    self.display.update(self._initial_state)
                    
                # Now update the hangman visual if we have a game
                if self.state_manager.current_game:
                    wrong_guesses = self.state_manager.current_game.max_attempts - self._initial_state.remaining_attempts
                    self.hangman_visual.update_state(wrong_guesses)
                    print(f"Updated hangman visual to {wrong_guesses} wrong guesses")
                    
                # Force page update
                if self.page:
                    self.page.update()
            except Exception as e:
                print(f"Error in init_ui_components: {e}")
        
        # Schedule the initialization for after controls are added to the page
        if self.page:
            self.page.on_load = init_ui_components
            
        return panel
