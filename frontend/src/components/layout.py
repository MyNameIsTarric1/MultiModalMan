import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

class AppLayout:
    def __init__(self, page: ft.Page):
        self.page = page
        
        # Set responsive page properties
        self.page.title = "Multimodal Hangman"
        self.page.vertical_alignment = "start"  # Changed to start for better mobile layout
        self.page.horizontal_alignment = "center"
        self.page.bgcolor = config.COLOR_PALETTE["background"]
        self.page.scroll = "auto"  # Enable scrolling if content overflows
        
        # Notification banner
        self.notification = ft.Banner(
            bgcolor=config.COLOR_PALETTE["primary"],
            leading=ft.Icon(ft.Icons.INFO_OUTLINED, color=ft.Colors.WHITE, size=40),
            content=ft.Text(
                "Notification message here",
                color=ft.Colors.WHITE,
            ),
            actions=[
                ft.TextButton("OK", on_click=lambda e: setattr(self.notification, 'open', False)),
            ],
            open=False,  # Initially closed
        )
        self.page.overlay.append(self.notification)
        
    def show_notification(self, message):
        """Show a notification banner with the given message"""
        self.notification.content.value = message
        self.notification.open = True
        self.page.update()
        
    def create_layout(self, left_panel, right_panel):
        """Create the main layout with game panel and controls"""
        # Vertical divider
        divider = ft.VerticalDivider(
            width=2, 
            color=config.COLOR_PALETTE["secondary"],
            visible=True
        )
        
        # Main row with fixed two-column layout
        main_row = ft.Row(
            [
                left_panel,  # Media controls on the left
                divider,
                right_panel,  # Game panel always on the right
            ],
            spacing=0,
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        
        # Define responsive behavior
        def page_resize(e):
            # Adjust layout based on window width
            if self.page.width < 800:  # For smaller screens
                # Keep panels side by side but adjust their relative sizes
                left_panel.expand = 1
                right_panel.expand = 1
                divider.visible = False
            else:  # For larger screens
                # Left panel takes up less space than the game panel
                left_panel.expand = 2  # 2 parts
                right_panel.expand = 3  # 3 parts
                divider.visible = True
            self.page.update()
            
        self.page.on_resize = page_resize
        self.page.add(main_row)
        
        # Trigger initial layout
        page_resize(None)
