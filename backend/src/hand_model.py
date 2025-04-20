import cv2
import numpy as np
from tensorflow.keras.models import load_model

class HandModel:
    def __init__(self, model_path="/Users/lucian/University/L-impiccato2.0/backend/models/letter_recognition.h5"):
        """Initialize the model with the given model path"""
        self.model = load_model(model_path)
        self.mapping = ['0', '1','2','3','4','5','6','7','8','9',
                        'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
                        'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    
    def predict_from_memory(self, image):
        """Process and predict from an in-memory image (numpy array)"""
        # EMNIST format preparation:
        # - Ensure black letter on white background
        # - Normalize to 0-1 range
        
        # Add stronger thresholding to ensure clean black/white
        _, binary = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)
        
        # Print unique values to debug
        unique_values = np.unique(binary)
        print(f"Unique values in image: {unique_values}")
        
        # Normalize to 0-1 range (invert so black is 1 and white is 0)
        # This is often how EMNIST is processed
        pred_img = 1.0 - (binary / 255.0)
        
        # EMNIST expects a specific shape
        pred_img = pred_img.reshape(1, 28, 28, 1)  # Add batch and channel dimensions
        
        # Make prediction
        predictions = self.model.predict(pred_img)
        
        # Debugging: print top 3 predictions
        top_3_indices = np.argsort(predictions[0])[-3:][::-1]
        print("Top 3 predictions:")
        for idx in top_3_indices:
            print(f"  {self.mapping[idx]}: {predictions[0][idx]:.4f}")
        
        predicted_class = np.argmax(predictions, axis=1)[0]
        prediction = self.mapping[predicted_class]
        confidence = float(predictions[0][predicted_class])
        
        return prediction, confidence
    
    def predict_from_file(self, img_path):
        """Original method to predict from image file"""
        if img_path is None:
            return None, 0.0
            
        img = cv2.imread(img_path, 0)  # Read as grayscale
        return self.predict_from_memory(img)
