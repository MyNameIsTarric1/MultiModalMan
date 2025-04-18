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
        self.page.vertical_alignment = "center"
        self.page.horizontal_alignment = "center"
        self.page.padding = 30
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
        """Create the main layout with left and right panels"""
        # Vertical divider
        divider = ft.VerticalDivider(
            width=2, 
            color=config.COLOR_PALETTE["secondary"],
            visible=True
        )
        
        # Main row with responsive properties
        main_row = ft.Row(
            [left_panel, divider, right_panel],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        
        # Define responsive behavior
        def page_resize(e):
            # Adjust layout based on window width
            if self.page.width < 800:  # For smaller screens
                main_row.horizontal_alignment = "center"
                main_row.wrap = True  # Allow wrapping of columns
                left_panel.expand = True
                right_panel.expand = True
                divider.visible = False
            else:  # For larger screens
                main_row.horizontal_alignment = "center"
                main_row.wrap = False
                left_panel.expand = True
                right_panel.expand = True
                divider.visible = True
            self.page.update()
            
        self.page.on_resize = page_resize
        self.page.add(main_row)
        
        # Trigger initial layout
        page_resize(None)
