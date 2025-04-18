import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from src.components.media_display import VoiceAnimation, CameraView

class MediaControls:
    def __init__(self, show_notification_callback, on_guess_callback):
        self.show_notification = show_notification_callback
        self.on_guess = on_guess_callback
        
        # Media display components
        self.voice_animation = VoiceAnimation()
        self.camera_view = CameraView()
        
        # Voice control buttons
        self.voice_start_btn = ft.ElevatedButton(
            "Start Voice Input",
            icon=ft.Icons.MIC,
            on_click=self._start_voice_recording,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        self.voice_stop_btn = ft.ElevatedButton(
            "Stop Voice Input",
            icon=ft.Icons.MIC_OFF,
            on_click=self._stop_voice_recording,
            style=config.BUTTON_STYLE,
            visible=False
        )
        
        # Camera control buttons
        self.camera_start_btn = ft.ElevatedButton(
            "Start Camera",
            icon=ft.Icons.CAMERA_ALT,
            on_click=self._start_camera_view,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        self.camera_stop_btn = ft.ElevatedButton(
            "Stop Camera",
            icon=ft.Icons.VIDEOCAM_OFF,
            on_click=self._stop_camera_view,
            style=config.BUTTON_STYLE,
            visible=False
        )
        
    def _start_voice_recording(self, e):
        self.voice_animation.toggle_recording()
        self.camera_view.stop_camera()  # Stop camera when voice starts
        self.show_notification("Voice recording started")
        self.voice_start_btn.visible = False
        self.voice_stop_btn.visible = True
        self.on_guess("A")  # Mock voice input
    
    def _stop_voice_recording(self, e):
        self.voice_animation.stop_recording()
        self.show_notification("Voice recording stopped")
        self.voice_start_btn.visible = True
        self.voice_stop_btn.visible = False
    
    def _start_camera_view(self, e):
        self.camera_view.toggle_camera()
        self.voice_animation.stop_recording()  # Stop voice when camera starts
        self.show_notification("Camera activated")
        self.camera_start_btn.visible = False
        self.camera_stop_btn.visible = True
        self.on_guess("B")  # Mock camera input
    
    def _stop_camera_view(self, e):
        self.camera_view.stop_camera()
        self.show_notification("Camera deactivated")
        self.camera_start_btn.visible = True
        self.camera_stop_btn.visible = False
        
    def reset(self):
        """Reset all media controls"""
        self.voice_animation.stop_recording()
        self.camera_view.stop_camera()
        self.voice_start_btn.visible = True
        self.voice_stop_btn.visible = False
        self.camera_start_btn.visible = True
        self.camera_stop_btn.visible = False
        
    def create_panel(self):
        """Create the right panel with media controls"""
        return ft.Container(
            content=ft.Column([
                # Voice section
                ft.Text("Voice Input", style=config.SUBTITLE_STYLE),
                self.voice_animation,
                ft.Row([self.voice_start_btn, self.voice_stop_btn], 
                       alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Divider(height=20),
                
                # Camera section
                ft.Text("Camera Input", style=config.SUBTITLE_STYLE),
                self.camera_view,
                ft.Row([self.camera_start_btn, self.camera_stop_btn], 
                       alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=15),
            expand=True,
            padding=20
        )
