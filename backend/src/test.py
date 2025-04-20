import cv2
import numpy as np
from tracker import HandTracker
from hand_model import HandModel
import time

def main():
    # Initialize the hand tracker
    tracker = HandTracker(max_hands=1, min_detection_confidence=0.7)
    
    # Initialize the hand model for letter recognition
    model = HandModel()
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    # Set display window properties
    cv2.namedWindow('Hand Tracking', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Hand Tracking', 800, 600)
    
    # Create a window for the canvas
    cv2.namedWindow('Drawing Canvas', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Drawing Canvas', 400, 400)
    
    # Create a window for processed image
    cv2.namedWindow('Processed Image', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Processed Image', 280, 280)
    
    # Variables for prediction
    last_prediction = None
    last_prediction_time = 0
    prediction_cooldown = 2  # Seconds between predictions
    prediction_confidence = 0.0
    
    while cap.isOpened():
        # Read frame from webcam
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
            
        # Flip the frame horizontally for a more intuitive experience
        frame = cv2.flip(frame, 1)
        
        # Process the frame with the hand tracker
        annotated_frame, result = tracker.process_frame(frame)
        
        # Get the canvas from the result
        canvas = result.canvas
        
        # Display the drawing canvas
        cv2.imshow('Drawing Canvas', canvas)
        
        # Display prediction text on the annotated frame
        if last_prediction:
            prediction_text = f"Prediction: {last_prediction} ({prediction_confidence:.2f})"
            cv2.putText(
                annotated_frame,
                prediction_text,
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 0, 255),
                2
            )
        
        # Display instructions
        cv2.putText(
            annotated_frame,
            "Press 'c' to clear, 'p' to predict, 'q' to quit",
            (20, annotated_frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )
        
        # Show the frame
        cv2.imshow('Hand Tracking', annotated_frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            # Quit
            break
        elif key == ord('c'):
            # Clear the drawing
            tracker.clear_drawing()
            last_prediction = None
        elif key == ord('p'):
            # Make a prediction if there's something drawn
            current_time = time.time()
            if canvas is not None and np.sum(canvas) > 0 and (current_time - last_prediction_time) > prediction_cooldown:
                # Convert the canvas to grayscale for prediction
                gray_canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
                
                # IMPORTANT: Save the original grayscale before any processing
                original_copy = gray_canvas.copy()
                
                # Display the raw grayscale image for comparison
                raw_display = cv2.resize(original_copy, (280, 280))
                cv2.imshow('Raw Canvas', raw_display)
                
                # EMNIST images have black letter on white background, but our canvas has white on black
                # Invert the image to match EMNIST format
                gray_canvas = cv2.bitwise_not(gray_canvas)
                
                # Use a less aggressive threshold to preserve more detail
                # Lower threshold value keeps more of the drawing visible
                _, binary = cv2.threshold(gray_canvas, 100, 255, cv2.THRESH_BINARY)
                
                # Display the binary image after thresholding
                binary_display = cv2.resize(binary, (280, 280))
                cv2.imshow('Binary Image', binary_display)
                
                # Use a different approach for finding the region of interest
                # Instead of contours, find non-zero pixels directly
                y_indices, x_indices = np.where(binary < 255)
                
                if len(y_indices) > 0 and len(x_indices) > 0:
                    # Find the bounds with all non-zero pixels
                    x_min, x_max = np.min(x_indices), np.max(x_indices)
                    y_min, y_max = np.min(y_indices), np.max(y_indices)
                    
                    # Add padding around the letter
                    padding = 30  # Increased padding
                    x_min = max(0, x_min - padding)
                    y_min = max(0, y_min - padding)
                    x_max = min(binary.shape[1], x_max + padding)
                    y_max = min(binary.shape[0], y_max + padding)
                    
                    # Extract the ROI containing the letter
                    if x_max > x_min and y_max > y_min:
                        letter_roi = binary[y_min:y_max, x_min:x_max]
                        
                        # Display the ROI before further processing
                        roi_display = cv2.resize(letter_roi, (280, 280))
                        cv2.imshow('ROI', roi_display)
                        
                        # Create a square image with the letter centered
                        max_dim = max(letter_roi.shape[0], letter_roi.shape[1])
                        square_img = np.ones((max_dim, max_dim), dtype=np.uint8) * 255  # White background
                        
                        # Calculate offsets to center the letter
                        offset_x = (max_dim - letter_roi.shape[1]) // 2
                        offset_y = (max_dim - letter_roi.shape[0]) // 2
                        
                        # Place the letter in the center of the square
                        square_img[offset_y:offset_y+letter_roi.shape[0], 
                                  offset_x:offset_x+letter_roi.shape[1]] = letter_roi
                        
                        # Try more preprocessing variations for EMNIST compatibility
                        processed_versions = []
                        
                        # Original version
                        processed_img = cv2.resize(square_img, (28, 28))
                        processed_versions.append(("Original", processed_img))
                        
                        # Rotated version - EMNIST often requires rotation
                        rotated_img = cv2.rotate(square_img, cv2.ROTATE_90_CLOCKWISE)
                        processed_rotated = cv2.resize(rotated_img, (28, 28))
                        processed_versions.append(("Rotated 90°", processed_rotated))
                        
                        # Dilated version to make the letter thicker
                        kernel = np.ones((3, 3), np.uint8)
                        dilated_img = cv2.dilate(square_img, kernel, iterations=1)
                        processed_dilated = cv2.resize(dilated_img, (28, 28))
                        processed_versions.append(("Dilated", processed_dilated))
                        
                        # Eroded version to make the letter thinner
                        eroded_img = cv2.erode(square_img, kernel, iterations=1)
                        processed_eroded = cv2.resize(eroded_img, (28, 28))
                        processed_versions.append(("Eroded", processed_eroded))
                        
                        # Try different preprocessing approaches
                        best_confidence = 0
                        best_prediction = None
                        best_version = None
                        
                        for version_name, img in processed_versions:
                            # Basic thresholding to clean up noise but preserve more information
                            _, img = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY)
                            
                            # Ensure white background with black letter
                            if np.sum(img == 0) < np.sum(img == 255):  # More white than black
                                pass  # Already white background
                            else:
                                img = cv2.bitwise_not(img)
                            
                            # Debug info
                            print(f"--- {version_name} ---")
                            print(f"Shape: {img.shape}, Black pixels: {np.sum(img == 0)}")
                            
                            # Save a zoomed version for display
                            display_img = cv2.resize(img, (280, 280))
                            
                            # Make prediction
                            prediction, confidence = model.predict_from_memory(img)
                            print(f"Prediction: {prediction}, Confidence: {confidence:.4f}")
                            
                            # Keep the best result
                            if confidence > best_confidence:
                                best_confidence = confidence
                                best_prediction = prediction
                                best_version = display_img
                        
                        # Show the best version
                        cv2.imshow('Processed Image', best_version)
                        
                        # Update the prediction
                        last_prediction = best_prediction
                        prediction_confidence = best_confidence
                        last_prediction_time = current_time
                        
                        print(f"Final prediction: {last_prediction} with confidence {prediction_confidence:.4f}")
                    else:
                        print("Invalid ROI dimensions")
                else:
                    print("No drawing detected")
    
    # Clean up
    cap.release()
    tracker.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
