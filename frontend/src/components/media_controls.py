import flet as ft
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from src.components.media_display import VoiceAnimation
from src.components.hand_drawing_recognition import HandDrawingRecognition

class MediaControls:
    def __init__(self, show_notification_callback, on_guess_callback):
        self.show_notification = show_notification_callback
        self.on_guess = on_guess_callback
        
        # Media display components
        self.voice_animation = VoiceAnimation()
        self.hand_drawing = HandDrawingRecognition(on_prediction_callback=self._handle_drawing_prediction)
        
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
            visible=True
        )
        
        # Hand drawing control buttons
        self.drawing_start_btn = ft.ElevatedButton(
            "Start Hand Drawing",
            icon=ft.Icons.DRAW,
            on_click=self._start_hand_drawing,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        self.drawing_stop_btn = ft.ElevatedButton(
            "Stop Hand Drawing",
            icon=ft.Icons.CANCEL,
            on_click=self._stop_hand_drawing,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        self.drawing_clear_btn = ft.ElevatedButton(
            "Clear Canvas",
            icon=ft.Icons.CLEAR,
            on_click=self._clear_drawing_canvas,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        self.drawing_recognize_btn = ft.ElevatedButton(
            "Recognize Letter",
            icon=ft.Icons.SEARCH,
            on_click=self._recognize_drawn_letter,
            style=config.BUTTON_STYLE,
            visible=True
        )
        
        # Currently active view (to track which one is open)
        self.active_view = None
        
    def _start_voice_recording(self, e):
        self._reset_all_views()
        self.active_view = "voice"
        self.voice_animation.toggle_recording()
        self.show_notification("Voice recording started")
        self.on_guess("A")  # Mock voice input
    
    def _stop_voice_recording(self, e):
        if self.active_view == "voice":
            self.voice_animation.stop_recording()
            self.active_view = None
            self.show_notification("Voice recording stopped")
    
    def _start_hand_drawing(self, e):
        self._reset_all_views()
        self.active_view = "drawing"
        self.hand_drawing.start_camera()
        self.show_notification("Hand drawing activated")
    
    def _stop_hand_drawing(self, e):
        if self.active_view == "drawing":
            self.hand_drawing.stop_camera()
            self.active_view = None
            self.show_notification("Hand drawing deactivated")
    
    def _clear_drawing_canvas(self, e):
        if self.active_view == "drawing":
            self.hand_drawing.clear_canvas()
            self.show_notification("Drawing canvas cleared")
    
    def _recognize_drawn_letter(self, e):
        if self.active_view == "drawing":
            self.show_notification("Analyzing drawn letter...")
            
            # Recognize the letter
            prediction, confidence = self.hand_drawing.recognize_letter()
            
            # If the recognition returned a valid prediction directly
            if prediction and confidence > 0.5:
                self.on_guess(prediction)
                self.show_notification(f"Recognized letter: {prediction} (Confidence: {confidence:.2f})")
            else:
                self.show_notification("Could not recognize letter with sufficient confidence")
    
    def _handle_drawing_prediction(self, prediction, confidence):
        """Handle prediction result from hand drawing recognition"""
        if confidence > 0.5:  # Only use prediction if confidence is reasonable
            self.on_guess(prediction)
            self.show_notification(f"Recognized letter: {prediction} (Confidence: {confidence:.2f})")
    
    def _reset_all_views(self):
        """Reset all views before activating a new one"""
        self.voice_animation.stop_recording()
        self.hand_drawing.stop_camera()
        self.active_view = None
        
    def reset(self):
        """Reset all media controls"""
        self._reset_all_views()
        
    def create_panel(self):
        """Create the right panel with media controls"""
        return ft.Container(
            content=ft.Column([
                # Voice section
                ft.Text("Voice Input", style=config.SUBTITLE_STYLE),
                self.voice_animation,
                ft.Row([self.voice_start_btn, self.voice_stop_btn], 
                       alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Divider(height=10),
                
                # Hand Drawing section
                ft.Text("Hand Drawing Recognition", style=config.SUBTITLE_STYLE),
                self.hand_drawing,
                ft.Row([self.drawing_start_btn, self.drawing_stop_btn], 
                       alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([self.drawing_clear_btn, self.drawing_recognize_btn], 
                       alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            expand=True,
            padding=20
        )
