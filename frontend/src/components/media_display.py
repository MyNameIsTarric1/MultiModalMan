import flet as ft
import os
import sys
import random
import time
import threading
import cv2
from PIL import Image
import io
import base64
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

class VoiceAnimation(ft.Container):
    def __init__(self):
        super().__init__()
        self.height = 450  # Standardized height
        self.width = None  # Remove fixed width to allow responsive sizing
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.border.all(2, config.COLOR_PALETTE["secondary"])
        self.border_radius = 10
        self.padding = 10
        self.recording = False
        self.animation_timer = None
        self.animation_thread = None
        self.stop_thread = False
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

        # Display for the recognized letter/text - made more prominent
        self.letter_display = ft.Text(
            value="",  # initially empty
            size=32,  # Larger text size
            weight="bold",
            color=config.COLOR_PALETTE["primary"],
            text_align=ft.TextAlign.CENTER,
            selectable=False
        )

        
        
        # Layout
        self.content = ft.Column([
            # Center the animation bars with a container to ensure vertical centering
            ft.Container(
                content=ft.Column([
                    # Display voice recognition output in the center of the box
                    self.letter_display,
                    ft.Container(height=20),  # Spacing between text and animation
                    ft.Row(
                        self.bars,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        wrap=True  # Allow bars to wrap on smaller screens
                    )
                ], 
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True  # Make it take available space for vertical centering
            )
        ], alignment=ft.MainAxisAlignment.CENTER, expand=True)
        
    def toggle_recording(self):
        self.recording = not self.recording
        
        if self.recording:
            # Show "Listening..." in the letter display instead of using label
            self.letter_display.value = "Listening..."
            self.letter_display.color = config.COLOR_PALETTE["error"]
            self.letter_display.size = 28
            
            # Start animation
            self._start_animation()
        else:
            self.stop_recording()
            
    def stop_recording(self):
        self.recording = False
        
        # Stop animation thread
        self.stop_thread = True
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
            
        # Reset bars and completely hide them
        for bar in self.bars:
            bar.visible = False
            bar.height = 10
            
        # Clear letter display
        self.letter_display.value = ""
        
        # Force UI update to clear the animation
        try:
            if hasattr(ft, 'page') and ft.page is not None:
                ft.page.update(self)
        except Exception as e:
            print(f"Error updating UI after stopping recording: {e}")
    
    def _start_animation(self):
        # Make bars visible
        for bar in self.bars:
            bar.visible = True
        
        # Start animation in a thread
        self.stop_thread = False
        self.animation_thread = threading.Thread(target=self._animate_bars)
        self.animation_thread.daemon = True
        self.animation_thread.start()
    
    def _animate_bars(self):
        """Animation loop for voice bars"""
        page_ref = None
        try:
            # Try to capture page reference at the start of the thread
            # This is safer than accessing ft.page in a thread
            page_ref = ft.page
        except Exception as e:
            print(f"Could not get page reference: {e}")
            pass
            
        while self.recording and not self.stop_thread:
            try:
                # Update bar heights
                for bar in self.bars:
                    bar.height = random.randint(10, 80)
                
                # Schedule UI update if we have page reference
                if page_ref:
                    page_ref.update()
                
                # Control animation speed
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in animation loop: {e}")
                break


class CameraView(ft.Container):
    def __init__(self):
        super().__init__()
        self.height = 320  # Standardized height
        self.width = None
        self.bgcolor = ft.Colors.BLACK
        self.border = ft.border.all(2, config.COLOR_PALETTE["secondary"])
        self.border_radius = 10
        self.padding = 8  # Reduced padding
        self.camera_active = False
        self.expand = True
        self.video_capture = None
        self.camera_thread = None
        self.stop_thread = False
        
        # Container to hold the camera image (this provides better control)
        self.image_container = ft.Container(
            width=350,              # Standardized width
            height=280,             # Standardized height
            border_radius=5,
            padding=0,
            margin=0,
            alignment=ft.alignment.center,
            expand=True             # Fill available space
        )
        
        # Placeholder for camera image with better sizing
        self.camera_image = ft.Image(
            fit=ft.ImageFit.COVER,  
            width=370,              # Slightly larger to ensure full coverage
            height=320,             # Slightly larger to ensure full coverage
            src_base64="",
            expand=True             # Fill available space
        )
        
        # Initial placeholder content
        self.placeholder = ft.Container(
            width=350,              
            height=280,             
            bgcolor=ft.Colors.BLACK,
            border_radius=5,
            alignment=ft.alignment.center,
            expand=True,            
            content=ft.Icon(
                ft.Icons.VIDEOCAM_OFF,
                size=50,
                color=ft.Colors.WHITE
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
            self.placeholder  # Start with placeholder
        ], alignment=ft.MainAxisAlignment.CENTER, expand=True)
        
    def start_camera(self):
        """Start camera capture"""
        try:
            # Initialize video capture (0 is usually the default webcam)
            self.video_capture = cv2.VideoCapture(0)
            
            if not self.video_capture.isOpened():
                raise Exception("Could not open video device")
                
            # Set camera active
            self.camera_active = True
            self.label.value = "Camera Active"
            self.label.color = config.COLOR_PALETTE["error"]
            
            # Add the image to the container
            self.image_container.content = self.camera_image
            
            # Update layout to show camera feed
            new_content = ft.Column([
                self.label,
                ft.Container(height=4),  # Reduced spacing
                self.image_container  # Use container instead of direct image
            ], alignment=ft.MainAxisAlignment.CENTER, expand=True)
            
            self.content = new_content
            
            # Start camera thread
            self.stop_thread = False
            self.camera_thread = threading.Thread(target=self._camera_loop)
            self.camera_thread.daemon = True
            self.camera_thread.start()
            
        except Exception as e:
            print(f"Error starting camera: {e}")
            self.label.value = f"Camera Error: {str(e)}"
            self.label.color = config.COLOR_PALETTE["error"]
            self.camera_active = False
            
    def stop_camera(self):
        """Stop camera capture"""
        if not self.camera_active:
            return
            
        self.camera_active = False
        self.stop_thread = True
        self.label.value = "Camera Not Active"
        self.label.color = config.COLOR_PALETTE["secondary"]
        
        # If camera thread is running, wait for it to terminate
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1.0)
            
        # Release the camera
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
            
        # Update layout to show placeholder
        new_content = ft.Column([
            self.label,
            ft.Container(height=10),
            self.placeholder  # Switch back to placeholder
        ], alignment=ft.MainAxisAlignment.CENTER, expand=True)
        
        self.content = new_content
            
    def _camera_loop(self):
        """Camera capture loop running in a separate thread"""
        # Create a simpler update function that directly updates the image
        def update_image():
            try:
                if hasattr(ft, 'page') and ft.page is not None:
                    # Update the entire container instead of just the image
                    ft.page.update(self.image_container)
            except Exception as e:
                print(f"Error updating camera image: {e}")
        
        # Get device aspect ratio
        if self.video_capture:
            frame_width = self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            frame_height = self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            aspect_ratio = frame_width / frame_height if frame_height > 0 else 4/3
            print(f"Camera aspect ratio: {aspect_ratio}")
        
        # Process frames while active
        while not self.stop_thread and self.video_capture and self.video_capture.isOpened():
            try:
                # Read a frame from the camera
                ret, frame = self.video_capture.read()
                if not ret:
                    print("Failed to capture frame")
                    break
                
                # Convert frame to format usable by Flet
                frame = cv2.flip(frame, 1)  # Mirror effect
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)
                
                # Resize to fill container completely
                # Using a slightly larger size to ensure no gaps
                img = img.resize((370, 320))
                
                # Convert to base64 with higher quality
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=90)  # Increased quality further
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Update the image source
                self.camera_image.src_base64 = img_base64
                
                # Request UI update
                update_image()
                
                # Control frame rate
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                print(f"Error in camera loop: {e}")
                time.sleep(0.1)
                
        # Make sure to release the camera when the loop exits
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
            print("Camera released")
