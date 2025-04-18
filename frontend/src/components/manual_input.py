import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

class ManualInput(ft.Container):
    def __init__(self, on_guess_callback=None):
        super().__init__()
        self.padding = 10
        self.bgcolor = ft.Colors.BLUE_50
        self.border_radius = ft.border_radius.all(5)
        self.on_guess = on_guess_callback
        
        # Input field
        self.input_field = ft.TextField(
            label="Enter a letter",
            hint_text="Type a letter to guess",
            width=100,
            max_length=1,
            autofocus=False,
            on_submit=self._handle_input
        )
        
        # Submit button
        self.submit_button = ft.ElevatedButton(
            "Guess",
            icon=ft.icons.CHECK,
            on_click=self._handle_input,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=config.COLOR_PALETTE["primary"]
            )
        )
        
        # Status message
        self.status_message = ft.Text(
            "",
            color=config.COLOR_PALETTE["secondary"],
            size=14,
            italic=True
        )
        
        # Layout
        self.content = ft.Column([
            ft.Text("Manual Letter Input", weight="bold"),
            ft.Row([
                self.input_field,
                self.submit_button
            ], alignment=ft.MainAxisAlignment.CENTER),
            self.status_message
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
    def _handle_input(self, e):
        """Process the input when the user submits a guess"""
        letter = self.input_field.value.strip().upper()
        
        if not letter:
            self.status_message.value = "Please enter a letter"
            self.status_message.color = config.COLOR_PALETTE["error"]
        elif not letter.isalpha():
            self.status_message.value = "Only letters are allowed"
            self.status_message.color = config.COLOR_PALETTE["error"]
        else:
            # Clear the input field
            self.input_field.value = ""
            
            # Call the callback function if provided
            if self.on_guess:
                result = self.on_guess(letter)
                
                # Update the status message based on the result
                if result.error_message:
                    self.status_message.value = result.error_message
                    self.status_message.color = config.COLOR_PALETTE["error"]
                elif letter in result.secret_word:
                    self.status_message.value = f"Good guess! '{letter}' is in the word"
                    self.status_message.color = config.COLOR_PALETTE["success"]
                else:
                    self.status_message.value = f"Sorry, '{letter}' is not in the word"
                    self.status_message.color = config.COLOR_PALETTE["error"]
        
        # Update the UI
        self.update()
        
        # Set focus back to the input field
        self.input_field.focus()
