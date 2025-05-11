import flet as ft
import sys
import os
import threading
import time
import cv2
import numpy as np
from PIL import Image
import io
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.src.tracker import HandTracker
from backend.src.hand_model import HandModel
from config import config

class HandDrawingRecognition(ft.Container):
    def __init__(self, on_prediction_callback=None):
        super().__init__()
        self.height = 620  # Further increased for better visibility
        self.width = None
        self.bgcolor = ft.Colors.WHITE
        self.border = ft.border.all(2, config.COLOR_PALETTE["secondary"])
        self.border_radius = 10
        self.padding = 10
        self.expand = True
        
        # Initialize hand tracker and model
        self.tracker = HandTracker(max_hands=1, min_detection_confidence=0.7)
        self.model = HandModel()
        
        # Video capture
        self.video_capture = None
        self.camera_thread = None
        self.stop_thread = False
        self.is_active = False
        
        # Canvas for drawing
        self.drawing_canvas = np.zeros((400, 400, 3), dtype=np.uint8)
        
        # Prediction data
        self.last_prediction = None
        self.prediction_confidence = 0.0
        self.on_prediction_callback = on_prediction_callback
        
        # Camera feed container
        self.camera_container = ft.Container(
            width=420,
            height=240,  # Camera height increased for better visibility
            border_radius=5,
            padding=0,
            margin=0,
            alignment=ft.alignment.center,
            expand=False
        )
        
        # Camera image
        self.camera_image = ft.Image(
            fit=ft.ImageFit.COVER,
            width=420,
            height=240,  # Camera height increased for better visibility
            src_base64="",
            expand=False
        )
        
        # Canvas container
        self.canvas_container = ft.Container(
            width=420,
            height=240,  # Canvas height increased for better visibility
            border_radius=5,
            padding=0,
            margin=0,
            alignment=ft.alignment.center,
            expand=False
        )
        
        # Canvas image
        self.canvas_image = ft.Image(
            fit=ft.ImageFit.COVER,
            width=420,
            height=240,  # Canvas height increased for better visibility
            src_base64="",
            expand=False
        )
        
        # Placeholder for camera
        self.camera_placeholder = ft.Container(
            width=420,
            height=240,  # Increased height for better visibility
            bgcolor=ft.Colors.BLACK,
            border_radius=5,
            alignment=ft.alignment.center,
            expand=False,
            content=ft.Icon(
                ft.Icons.VIDEOCAM_OFF,
                size=48,
                color=ft.Colors.WHITE
            )
        )
        
        # Placeholder for canvas
        self.canvas_placeholder = ft.Container(
            width=420,
            height=240,  # Increased height for better visibility
            bgcolor=ft.Colors.BLACK,
            border_radius=5,
            alignment=ft.alignment.center,
            expand=False,
            content=ft.Icon(
                ft.Icons.DRAW,
                size=48,
                color=ft.Colors.WHITE
            )
        )
        
        # Label
        self.status_label = ft.Text(
            "Hand Drawing Not Active",
            color=config.COLOR_PALETTE["secondary"],
            size=16,
            weight="bold"
        )
        
        # Prediction Text
        self.prediction_text = ft.Text(
            color=config.COLOR_PALETTE["primary"],
            size=18,
            weight="bold"
        )
        
        # Layout
        self.content = ft.Column([
            self.status_label,
            ft.Container(height=10),
            # Camera section
            ft.Container(height=5),
            self.camera_placeholder,
            
            ft.Container(height=15),  # Spacer between camera and canvas
            
            # Canvas section
            ft.Container(height=5),
            self.canvas_placeholder,
            
            ft.Container(height=10),  # Spacer before prediction display
            
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
    def start_camera(self):
        """Start camera and hand tracking"""
        try:
            # Initialize video capture
            self.video_capture = cv2.VideoCapture(0)
            
            if not self.video_capture.isOpened():
                raise Exception("Could not open video device")
            
            # Set active flag
            self.is_active = True
            self.status_label.value = "Hand Drawing Active"
            self.status_label.color = config.COLOR_PALETTE["error"]
            
            # Add images to containers
            self.camera_container.content = self.camera_image
            self.canvas_container.content = self.canvas_image
            
            # Update layout
            new_content = ft.Column([
                self.status_label,
                ft.Container(height=10),
                
                # Camera section
                ft.Container(height=5),
                self.camera_container,
                
                ft.Container(height=15),  # Spacer between camera and canvas
                
                # Canvas section
                ft.Container(height=5),
                self.canvas_container,
                
                ft.Container(height=10),  # Spacer before prediction display
                
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            self.content = new_content
            
            # Start camera thread
            self.stop_thread = False
            self.camera_thread = threading.Thread(target=self._camera_loop)
            self.camera_thread.daemon = True
            self.camera_thread.start()
            
        except Exception as e:
            print(f"Error starting camera: {e}")
            self.status_label.value = f"Camera Error: {str(e)}"
            self.status_label.color = config.COLOR_PALETTE["error"]
            self.is_active = False
    
    def stop_camera(self):
        """Stop camera and hand tracking"""
        if not self.is_active:
            return
        
        self.is_active = False
        self.stop_thread = True
        self.status_label.value = "Hand Drawing Not Active"
        self.status_label.color = config.COLOR_PALETTE["secondary"]
        
        # If camera thread is running, wait for it to terminate
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1.0)
        
        # Release the camera
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        
        # Update layout to show placeholders
        new_content = ft.Column([
            self.status_label,
            ft.Container(height=10),
            
            # Camera section
            ft.Container(height=5),
            self.camera_placeholder,
            
            ft.Container(height=15),  # Spacer between camera and canvas
            
            # Canvas section
            ft.Container(height=5),
            self.canvas_placeholder,
            
            ft.Container(height=10),  # Spacer before prediction display
            
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.content = new_content
    
    def clear_canvas(self):
        """Clear the drawing canvas"""
        if self.tracker:
            self.tracker.clear_drawing()
            self.drawing_canvas = np.zeros((400, 400, 3), dtype=np.uint8)
            # Update the canvas image
            self._update_canvas_image()
            # Reset prediction
            self.prediction_text.value = "Draw a letter and click 'Recognize'"
            self.prediction_text.color = config.COLOR_PALETTE["primary"]
            self.last_prediction = None
            self.prediction_confidence = 0.0
    
    def recognize_letter(self):
        """Recognize the drawn letter"""
        if not self.is_active or self.tracker is None:
            return
        
        canvas = self.tracker.canvas
        if canvas is None or np.sum(canvas) == 0:
            self.prediction_text.value = "No drawing detected"
            self.prediction_text.color = config.COLOR_PALETTE["error"]
            return
        
        try:
            # Convert the canvas to grayscale for prediction
            gray_canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
            
            # EMNIST images have black letter on white background, but our canvas has white on black
            gray_canvas = cv2.bitwise_not(gray_canvas)
            
            # Use a less aggressive threshold to preserve more detail
            _, binary = cv2.threshold(gray_canvas, 100, 255, cv2.THRESH_BINARY)
            
            # Find non-zero pixels for ROI detection
            y_indices, x_indices = np.where(binary < 255)
            
            if len(y_indices) > 0 and len(x_indices) > 0:
                # Find the bounds with all non-zero pixels
                x_min, x_max = np.min(x_indices), np.max(x_indices)
                y_min, y_max = np.min(y_indices), np.max(y_indices)
                
                # Add padding around the letter
                padding = 30
                x_min = max(0, x_min - padding)
                y_min = max(0, y_min - padding)
                x_max = min(binary.shape[1], x_max + padding)
                y_max = min(binary.shape[0], y_max + padding)
                
                # Extract the ROI containing the letter
                if x_max > x_min and y_max > y_min:
                    letter_roi = binary[y_min:y_max, x_min:x_max]
                    
                    # Create a square image with the letter centered
                    max_dim = max(letter_roi.shape[0], letter_roi.shape[1])
                    square_img = np.ones((max_dim, max_dim), dtype=np.uint8) * 255
                    
                    # Calculate offsets to center the letter
                    offset_x = (max_dim - letter_roi.shape[1]) // 2
                    offset_y = (max_dim - letter_roi.shape[0]) // 2
                    
                    # Place the letter in the center of the square
                    square_img[offset_y:offset_y+letter_roi.shape[0], 
                              offset_x:offset_x+letter_roi.shape[1]] = letter_roi
                    
                    # Try different preprocessing variations
                    processed_versions = []
                    
                    # Original version
                    processed_img = cv2.resize(square_img, (28, 28))
                    processed_versions.append(("Original", processed_img))
                    
                    # Rotated version
                    rotated_img = cv2.rotate(square_img, cv2.ROTATE_90_CLOCKWISE)
                    processed_rotated = cv2.resize(rotated_img, (28, 28))
                    processed_versions.append(("Rotated 90°", processed_rotated))
                    
                    # Dilated version
                    kernel = np.ones((3, 3), np.uint8)
                    dilated_img = cv2.dilate(square_img, kernel, iterations=1)
                    processed_dilated = cv2.resize(dilated_img, (28, 28))
                    processed_versions.append(("Dilated", processed_dilated))
                    
                    # Eroded version
                    eroded_img = cv2.erode(square_img, kernel, iterations=1)
                    processed_eroded = cv2.resize(eroded_img, (28, 28))
                    processed_versions.append(("Eroded", processed_eroded))
                    
                    # Try different preprocessing approaches
                    best_confidence = 0
                    best_prediction = None
                    
                    for version_name, img in processed_versions:
                        # Basic thresholding
                        _, img = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY)
                        
                        # Ensure white background with black letter
                        if np.sum(img == 0) < np.sum(img == 255):
                            pass  # Already white background
                        else:
                            img = cv2.bitwise_not(img)
                        
                        # Make prediction
                        prediction, confidence = self.model.predict_from_memory(img)
                        print(f"{version_name}: {prediction}, Conf: {confidence:.4f}")
                        
                        # Keep the best result
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_prediction = prediction
                    
                    # Update prediction display
                    self.last_prediction = best_prediction
                    self.prediction_confidence = best_confidence
                    
                    confidence_color = config.COLOR_PALETTE["primary"] if best_confidence > 0.7 else config.COLOR_PALETTE["error"]
                    
                    self.prediction_text.value = f"Prediction: {best_prediction} (Confidence: {best_confidence:.2f})"
                    self.prediction_text.color = confidence_color
                    
                    # Call the callback function with the prediction
                    if self.on_prediction_callback:
                        self.on_prediction_callback(best_prediction, best_confidence)
        
        except Exception as e:
            print(f"Error recognizing letter: {e}")
            self.prediction_text.value = f"Error: {str(e)}"
            self.prediction_text.color = config.COLOR_PALETTE["error"]
    
    def _camera_loop(self):
        """Camera capture loop running in a separate thread"""
        # Helper function to update UI
        def update_ui():
            try:
                # Capture the page reference once
                page_ref = getattr(ft, 'page', None)
                if page_ref is not None:
                    # Use a single update to refresh the entire component
                    # This is safer than updating individual containers
                    page_ref.update(self)
            except AssertionError:
                # Silently ignore assertion errors which are common during initialization
                pass
            except Exception as e:
                # Log other errors without causing a broken pipe
                print(f"Camera update error: {str(e)[:100]}")
        
        # Loop while active
        while not self.stop_thread and self.video_capture and self.video_capture.isOpened():
            try:
                # Read a frame from the camera
                ret, frame = self.video_capture.read()
                if not ret:
                    print("Failed to capture frame")
                    break
                
                # Flip the frame horizontally for a more intuitive experience
                frame = cv2.flip(frame, 1)
                
                # Process the frame with the hand tracker
                annotated_frame, result = self.tracker.process_frame(frame)
                
                # Update the drawing canvas
                self.drawing_canvas = result.canvas.copy()
                
                # Convert the frame to format usable by Flet
                img_camera = Image.fromarray(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
                
                # Resize to fill container using new height for vertical layout
                img_camera = img_camera.resize((370, 200))
                
                # Convert to base64
                buffer_camera = io.BytesIO()
                img_camera.save(buffer_camera, format='JPEG', quality=90)
                img_camera_base64 = base64.b64encode(buffer_camera.getvalue()).decode('utf-8')
                
                # Update the camera image
                self.camera_image.src_base64 = img_camera_base64
                
                # Update the canvas image
                self._update_canvas_image()
                
                # Request UI update
                update_ui()
                
                # Control frame rate
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                print(f"Error in camera loop: {e}")
                time.sleep(0.1)
        
        # Clean up
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
            print("Camera released")
    
    def _update_canvas_image(self):
        """Update the canvas image from the drawing canvas"""
        try:
            # Create a copy of the canvas with cursor visualization
            canvas_with_cursor = self.drawing_canvas.copy()
            
            # Convert the canvas to format usable by Flet
            img_canvas = Image.fromarray(cv2.cvtColor(canvas_with_cursor, cv2.COLOR_BGR2RGB))
            
            # Resize to fill container - use new height for vertical layout
            img_canvas = img_canvas.resize((370, 200))
            
            # Convert to base64
            buffer_canvas = io.BytesIO()
            img_canvas.save(buffer_canvas, format='JPEG', quality=90)
            img_canvas_base64 = base64.b64encode(buffer_canvas.getvalue()).decode('utf-8')
            
            # Update the canvas image
            self.canvas_image.src_base64 = img_canvas_base64
        except Exception as e:
            # Catch any errors that might occur during image processing
            print(f"Error updating canvas image: {str(e)[:100]}")
