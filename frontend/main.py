import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.components.layout import AppLayout
from src.components.media_controls import MediaControls
from src.components.game_panel import GamePanel

def main(page: ft.Page):
    # Debug print to confirm main is being called
    print("Main function called")
    
    # Store page in a global variable for thread access
    ft.page = page
    print(f"Global page reference set: {page}")
    
    # Import the agent's GameStateManager to ensure we're using the same instance
    from controller.agent import manager as agent_game_manager
    import inspect
    print(f"Main using agent's GameStateManager from: {inspect.getmodule(agent_game_manager).__file__}")
    print(f"Agent's GameStateManager instance in main: {id(agent_game_manager)}")
    
    # Set up page properties
    page.title = "Hangman Game"
    page.on_disconnect = lambda _: print("Page disconnected")
    
    # Initialize the app layout
    app_layout = AppLayout(page)
    
    # Initialize game panel with the agent's GameStateManager
    game_panel = GamePanel(page=page, state_manager=agent_game_manager)
    print(f"Game panel initialized with page: {page} and agent's GameStateManager")
    
    # Initialize media controls with a reference to the agent's GameStateManager
    media_controls = MediaControls(
        show_notification_callback=app_layout.show_notification,
        on_guess_callback=game_panel.handle_guess
    )
    
    # Set up the reset callback
    game_panel.on_reset = media_controls.reset
    
    # Create the layout with both panels
    app_layout.create_layout(
        left_panel=game_panel.create_panel(),
        right_panel=media_controls.create_panel()
    )
    
    # Update page once all components are initialized
    page.update()
    print("Initial page update called")

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER)
