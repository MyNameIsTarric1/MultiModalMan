import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.components.layout import AppLayout
from src.components.media_controls import MediaControls
from src.components.game_panel import GamePanel

def main(page: ft.Page):
    # Initialize the app layout
    app_layout = AppLayout(page)
    
    # Initialize game panel
    game_panel = GamePanel()
    
    # Initialize media controls
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

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER)
