import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class HandTrackingResult:
    """Store hand tracking results"""
    index_finger_tip: Tuple[float, float]  # x, y coordinates
    drawing_path: List[Tuple[float, float]]  # List of points in the path
    is_drawing: bool
    canvas: Optional[np.ndarray] = None  # Drawing canvas

class HandTracker:
    def __init__(self, max_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7):
        """Initialize the hand tracker with MediaPipe"""
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize MediaPipe Hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # Drawing parameters
        self.drawing_path = []
        self.is_drawing = False
        self.draw_cooldown = 0
        self.canvas = None
        self.canvas_size = (400, 400)  # Size of the drawing canvas
        
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, HandTrackingResult]:
        """Process a single frame and track hands"""
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        
        # Initialize or reset canvas if needed - BLACK background
        if self.canvas is None:
            self.canvas = np.zeros((self.canvas_size[1], self.canvas_size[0], 3), dtype=np.uint8)
        
        # Process the frame with MediaPipe
        results = self.hands.process(rgb_frame)
        
        # Create a copy of the frame to draw on
        annotated_frame = frame.copy()
        
        # Initialize default results
        index_finger_tip = (0, 0)
        
        # Check if hands are detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks on the frame
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # Get index finger tip coordinates
                index_finger = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                index_finger_tip = (int(index_finger.x * w), int(index_finger.y * h))
                
                # Get thumb tip coordinates to detect drawing gesture
                thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                thumb_tip_coords = (int(thumb_tip.x * w), int(thumb_tip.y * h))
                
                # Calculate distance between thumb and index finger
                distance = np.sqrt((index_finger_tip[0] - thumb_tip_coords[0])**2 + 
                                  (index_finger_tip[1] - thumb_tip_coords[1])**2)
                
                # If the thumb and index finger are close, we're drawing
                drawing_threshold = 50  # Adjust based on your needs
                
                # Add cooldown to prevent jitter
                if self.draw_cooldown > 0:
                    self.draw_cooldown -= 1
                
                # Toggle drawing state if gesture changes and cooldown is zero
                if distance < drawing_threshold and not self.is_drawing and self.draw_cooldown == 0:
                    self.is_drawing = True
                    self.draw_cooldown = 5  # Set cooldown frames
                elif distance >= drawing_threshold and self.is_drawing and self.draw_cooldown == 0:
                    self.is_drawing = False
                    self.draw_cooldown = 5  # Set cooldown frames
                
                # If drawing, add the point to the path
                if self.is_drawing:
                    # Scale coordinates to canvas size
                    canvas_x = int((index_finger.x * w) * (self.canvas_size[0] / w))
                    canvas_y = int((index_finger.y * h) * (self.canvas_size[1] / h))
                    self.drawing_path.append((canvas_x, canvas_y))
        
        # Draw the path on the canvas in WHITE
        if len(self.drawing_path) > 1:
            for i in range(1, len(self.drawing_path)):
                cv2.line(
                    self.canvas, 
                    self.drawing_path[i-1], 
                    self.drawing_path[i], 
                    (255, 255, 255),  # WHITE color 
                    thickness=5
                )
        
        # Draw a dot at the index finger position
        cv2.circle(annotated_frame, index_finger_tip, 10, (0, 255, 0), -1)
        
        # Draw drawing status on the frame
        status_text = "Drawing" if self.is_drawing else "Not Drawing"
        cv2.putText(
            annotated_frame, 
            status_text, 
            (20, 50), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 255, 0) if self.is_drawing else (0, 0, 255), 
            2
        )
        
        # Create the result object
        result = HandTrackingResult(
            index_finger_tip=index_finger_tip,
            drawing_path=self.drawing_path.copy(),
            is_drawing=self.is_drawing,
            canvas=self.canvas.copy()
        )
        
        return annotated_frame, result
    
    def clear_drawing(self):
        """Clear the current drawing"""
        self.drawing_path = []
        self.canvas = np.zeros((self.canvas_size[1], self.canvas_size[0], 3), dtype=np.uint8)
    
    def release(self):
        """Release resources"""
        self.hands.close()
