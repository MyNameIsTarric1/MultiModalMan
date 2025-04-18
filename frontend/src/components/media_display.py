import flet as ft
import os
import sys
import random
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

class VoiceAnimation(ft.Container):
    def __init__(self):
        super().__init__()
        self.height = 200
        self.width = None  # Remove fixed width to allow responsive sizing
        self.bgcolor = ft.colors.WHITE
        self.border = ft.border.all(2, config.COLOR_PALETTE["secondary"])
        self.border_radius = 10
        self.padding = 10
        self.recording = False
        self.animation_timer = None
        self.expand = True  # Make container expand to available space
        
        # Voice animation bars
        self.bars = []
        num_bars = 15
        for i in range(num_bars):
            self.bars.append(ft.Container(
                width=12,
                height=10,
                bgcolor=config.COLOR_PALETTE["primary"],
                border_radius=5,
                visible=False
            ))
        
        # Label
        self.label = ft.Text(
            "Voice Input Not Active",
            color=config.COLOR_PALETTE["secondary"],
            size=16,
            weight="bold"
        )
        
        # Layout
        self.content = ft.Column([
            self.label,
            ft.Container(height=10),
            ft.Row(
                self.bars,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.END,
                wrap=True  # Allow bars to wrap on smaller screens
            )
        ], alignment=ft.MainAxisAlignment.CENTER)
        
    def toggle_recording(self):
        self.recording = not self.recording
        
        if self.recording:
            self.label.value = "Recording Voice..."
            self.label.color = config.COLOR_PALETTE["error"]
            
            # Start animation
            self._start_animation()
        else:
            self.stop_recording()
            
    def stop_recording(self):
        self.recording = False
        self.label.value = "Voice Input Not Active"
        self.label.color = config.COLOR_PALETTE["secondary"]
        
        # Stop animation
        if self.animation_timer:
            self.animation_timer.cancel()
            self.animation_timer = None
            
        # Reset bars
        for bar in self.bars:
            bar.visible = False
            bar.height = 10
    
    def _start_animation(self):
        # Make bars visible
        for bar in self.bars:
            bar.visible = True
        
        # Animate bars with random heights
        def animate_bars():
            if not self.recording:
                return
                
            for bar in self.bars:
                bar.height = random.randint(10, 80)
                
            # Schedule next animation frame
            self.animation_timer = ft.app.get_running_app().page.after(100, animate_bars)
                
        animate_bars()


class CameraView(ft.Container):
    def __init__(self):
        super().__init__()
        self.height = 450 
        self.width = None  # Remove fixed width to allow responsive sizing
        self.bgcolor = ft.colors.BLACK
        self.border = ft.border.all(2, config.COLOR_PALETTE["secondary"])
        self.border_radius = 10
        self.padding = 10
        self.camera_active = False
        self.expand = True  # Make container expand to available space
        
        # Placeholder for camera image with responsive sizing
        self.camera_image = ft.Container(
            width=None,  # Remove fixed width
            height=200,
            bgcolor=ft.colors.BLACK,
            border_radius=5,
            alignment=ft.alignment.center,
            expand=True,  # Make it expand to fill parent
            content=ft.Icon(
                ft.icons.VIDEOCAM_OFF,
                size=50,
                color=ft.colors.WHITE
            )
        )
        
        # Label
        self.label = ft.Text(
            "Camera Not Active",
            color=config.COLOR_PALETTE["secondary"],
            size=16,
            weight="bold"
        )
        
        # Layout
        self.content = ft.Column([
            self.label,
            ft.Container(height=10),
            self.camera_image
        ], alignment=ft.MainAxisAlignment.CENTER)
        
    def toggle_camera(self):
        self.camera_active = not self.camera_active
        
        if self.camera_active:
            self.label.value = "Camera Active"
            self.label.color = config.COLOR_PALETTE["error"]
            self.camera_image.content = ft.Text(
                "CAMERA FEED",
                color=ft.colors.WHITE,
                size=24,
                weight="bold"
            )
            # In a real app, you would initialize the camera here
        else:
            self.stop_camera()
            
    def stop_camera(self):
        self.camera_active = False
        self.label.value = "Camera Not Active"
        self.label.color = config.COLOR_PALETTE["secondary"]
        self.camera_image.content = ft.Icon(
            ft.icons.VIDEOCAM_OFF,
            size=50,
            color=ft.colors.WHITE
        )
        # In a real app, you would release the camera here
