import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class HangmanVisual(ft.Container):
    def __init__(self):
        super().__init__()
        self.width = 320  # Increased from 200
        self.height = 400  # Increased from 250
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.border.all(2, ft.Colors.GREY_400)  # Slightly thicker border
        self.border_radius = ft.border_radius.all(8)  # Slightly larger border radius
        self.padding = 15  # Slightly more padding
        
        # States of hangman (0-6)
        self.states = [
            self._create_state0(),
            self._create_state1(),
            self._create_state2(),
            self._create_state3(),
            self._create_state4(),
            self._create_state5(),
            self._create_state6()
        ]
        
        # Initial empty state
        self.current_state = 0
        self.content = self.states[0]
        
    def update_state(self, wrong_guesses):
        """Update the hangman visual based on number of wrong guesses"""
        # Ensure wrong_guesses is within valid range
        wrong_guesses = max(0, min(wrong_guesses, 6))
        self.current_state = wrong_guesses
        self.content = self.states[wrong_guesses]
        
        # Only call update if this control has been added to the page
        # This prevents the "Control must be added to the page first" error
        try:
            self.update()
        except AssertionError as e:
            if "must be added to the page first" in str(e):
                print("Hangman visual not yet added to page, state will be visible when added")
            else:
                raise
        
    def _create_state0(self):
        # Base only
        return ft.Stack([
            # Base horizontal line
            ft.Container(
                width=160,  # Increased from 100
                height=6,   # Increased from 4
                bgcolor=ft.Colors.BLUE,
                left=64,    # Increased from 40
                top=320     # Increased from 200
            )
        ])
        
    def _create_state1(self):
        # Base + vertical pole
        return ft.Stack([
            # Base horizontal line
            ft.Container(
                width=160,  # Increased from 100
                height=6,   # Increased from 4
                bgcolor=ft.Colors.BLUE,
                left=64,    # Increased from 40
                top=320     # Increased from 200
            ),
            # Vertical pole
            ft.Container(
                width=6,    # Increased from 4
                height=240,  # Increased from 150
                bgcolor=ft.Colors.BLUE,
                left=96,    # Increased from 60
                top=80      # Increased from 50
            )
        ])
        
    def _create_state2(self):
        # Base + vertical pole + horizontal beam
        return ft.Stack([
            # Base horizontal line
            ft.Container(
                width=160,  # Increased from 100
                height=6,   # Increased from 4
                bgcolor=ft.Colors.BLUE,
                left=64,    # Increased from 40
                top=320     # Increased from 200
            ),
            # Vertical pole
            ft.Container(
                width=6,    # Increased from 4
                height=240,  # Increased from 150
                bgcolor=ft.Colors.BLUE,
                left=96,    # Increased from 60
                top=80      # Increased from 50
            ),
            # Horizontal beam
            ft.Container(
                width=96,    # Increased from 60
                height=6,    # Increased from 4
                bgcolor=ft.Colors.BLUE,
                left=96,     # Increased from 60
                top=80       # Increased from 50
            )
        ])
        
    def _create_state3(self):
        # Base + vertical pole + horizontal beam + rope
        return ft.Stack([
            # Base horizontal line
            ft.Container(
                width=160,
                height=6,
                bgcolor=ft.Colors.BLUE,
                left=64,
                top=320
            ),
            # Vertical pole
            ft.Container(
                width=6,
                height=240,
                bgcolor=ft.Colors.BLUE,
                left=96,
                top=80
            ),
            # Horizontal beam
            ft.Container(
                width=96,
                height=6,
                bgcolor=ft.Colors.BLUE,
                left=96,
                top=80
            ),
            # Rope
            ft.Container(
                width=3,
                height=32,
                bgcolor=ft.Colors.GREY_700,
                left=189,
                top=80
            )
        ])
        
    def _create_state4(self):
        # Base + vertical pole + horizontal beam + rope + head
        return ft.Stack([
            # Base horizontal line
            ft.Container(
                width=160,
                height=6,
                bgcolor=ft.Colors.BLUE,
                left=64,
                top=320
            ),
            # Vertical pole
            ft.Container(
                width=6,
                height=240,
                bgcolor=ft.Colors.BLUE,
                left=96,
                top=80
            ),
            # Horizontal beam
            ft.Container(
                width=96,
                height=6,
                bgcolor=ft.Colors.BLUE,
                left=96,
                top=80
            ),
            # Rope
            ft.Container(
                width=3,
                height=32,
                bgcolor=ft.Colors.GREY_700,
                left=189,
                top=80
            ),
            # Head (circle)
            ft.Container(
                width=48,
                height=48,
                border=ft.border.all(3, ft.Colors.BLACK),
                border_radius=24,
                left=165,
                top=112
            )
        ])
        
    def _create_state5(self):
        # Base + vertical pole + horizontal beam + rope + head + body + arms
        return ft.Stack([
            # Base horizontal line
            ft.Container(
                width=160,
                height=6,
                bgcolor=ft.Colors.BLUE,
                left=64,
                top=320
            ),
            # Vertical pole
            ft.Container(
                width=6,
                height=240,
                bgcolor=ft.Colors.BLUE,
                left=96,
                top=80
            ),
            # Horizontal beam
            ft.Container(
                width=96,
                height=6,
                bgcolor=ft.Colors.BLUE,
                left=96,
                top=80
            ),
            # Rope
            ft.Container(
                width=3,
                height=32,
                bgcolor=ft.Colors.GREY_700,
                left=189,
                top=80
            ),
            # Head (circle)
            ft.Container(
                width=48,
                height=48,
                border=ft.border.all(3, ft.Colors.BLACK),
                border_radius=24,
                left=165,
                top=112
            ),
            # Body
            ft.Container(
                width=3,
                height=80,
                bgcolor=ft.Colors.BLACK,
                left=189,
                top=160
            ),
            # Left arm
            ft.Container(
                width=48,
                height=3,
                bgcolor=ft.Colors.BLACK,
                rotate=0.4,
                left=144,
                top=176
            ),
            # Right arm
            ft.Container(
                width=48,
                height=3,
                bgcolor=ft.Colors.BLACK,
                rotate=-0.4,
                left=189,
                top=176
            )
        ])
        
    def _create_state6(self):
        # Base + vertical pole + horizontal beam + rope + head + body + arms + legs
        return ft.Stack([
            # Base horizontal line
            ft.Container(
                width=160,
                height=6,
                bgcolor=ft.Colors.BLUE,
                left=64,
                top=320
            ),
            # Vertical pole
            ft.Container(
                width=6,
                height=240,
                bgcolor=ft.Colors.BLUE,
                left=96,
                top=80
            ),
            # Horizontal beam
            ft.Container(
                width=96,
                height=6,
                bgcolor=ft.Colors.BLUE,
                left=96,
                top=80
            ),
            # Rope
            ft.Container(
                width=3,
                height=32,
                bgcolor=ft.Colors.GREY_700,
                left=189,
                top=80
            ),
            # Head (circle)
            ft.Container(
                width=48,
                height=48,
                border=ft.border.all(3, ft.Colors.BLACK),
                border_radius=24,
                left=165,
                top=112
            ),
            # Body
            ft.Container(
                width=3,
                height=80,
                bgcolor=ft.Colors.BLACK,
                left=189,
                top=160
            ),
            # Left arm
            ft.Container(
                width=48,
                height=3,
                bgcolor=ft.Colors.BLACK,
                rotate=0.4,
                left=144,
                top=176
            ),
            # Right arm
            ft.Container(
                width=48,
                height=3,
                bgcolor=ft.Colors.BLACK,
                rotate=-0.4,
                left=189,
                top=176
            ),
            # Left leg
            ft.Container(
                width=3,
                height=64,
                bgcolor=ft.Colors.BLACK,
                left=189,
                top=240,
                rotate=ft.transform.Rotate(
                    angle=0.5,
                    alignment=ft.alignment.top_center
                ),
            ),
            # Right leg
            ft.Container(
                width=3,
                height=64,
                bgcolor=ft.Colors.BLACK,
                left=189,
                top=240,
                rotate=ft.transform.Rotate(
                    angle=-0.5,
                    alignment=ft.alignment.top_center
                ),
            ),

        ])
