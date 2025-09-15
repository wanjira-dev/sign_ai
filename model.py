import cv2
import streamlit as st
import numpy as np

import mediapipe as mp
import tensorflow as tf

from mediapipe.python.solutions import hands as mp_hands
from mediapipe.python.solutions import drawing_utils as mp_drawing

# Initializing hand solution
hands_solution = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.5    
)


# Model loading
@st.cache_resource # Using streamlit caching for efficiency
def load_landmark_model(model_path='landmark_model.h5'):
    """Loads the trained Keras Embedding model"""
    try:
        model = tf.keras.models.load_model(model_path)
        print(f"Embedding model loaded successfully from {model_path}")
        return model
    except Exception as e:
        print(f"Error loading embedding models: {e}")
        return None
    
# Landmark extraction
def extract_hand_landmarks(frame):
    """
    Uses MediaPipe to detect hand landmarks from a single frame.
    
    Args:
        frame (numpy.ndarray): The raw BGR frame from OpenCV
        
    Returns:
        tuple: A tuple containing:
            - landmarks (list | None): A flattened list of 63 coordinates (21 * 3) or None if no hand is detected.
            - display_img (numpy.ndarray): The original frame with landmarks drawn on it for visual feedback.
    """
    display_img = frame.copy()
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_rgb.flags.writeable = False
    results = hands_solution.process(image_rgb)
    image_rgb.flags.writeable = True
    landmarks_list = None
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(display_img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        wrist_coords = hand_landmarks.landmark[0]
        landmarks_list = []
        for landmark in hand_landmarks.landmark:
            landmarks_list.extend([
                landmark.x - wrist_coords.x,
                landmark.y - wrist_coords.y,
                landmark.z - wrist_coords.z
            ])
    return landmarks_list, display_img

# Pipeline function
def get_embedding_from_frame(frame, model):
    """
    Organises the full pipeline: Frame -> Landmarks -> Embedding
    
    Args:
        frame (numpy.ndarray): The raw BGR frame from OpenCV.
        model: The loaded Keras embedding model
        
    Returns:
        tuple: A tuple containing:
            - embedding (list | None): The 128-dim embedding vector or None.
            - display img (numpy.ndarray): The frame with landmarks drawn
    """
    # Get the landmarks using Pipeline
    landmarks, display_img = extract_hand_landmarks(frame)
    
    if landmarks:
        # Convert to numpy and reshape for the model
        landmarks_np = np.array(landmarks).reshape(1, 63, 1)
        
        # Use the model to predict the embedding
        embedding = model.predict(landmarks_np)[0]
        return embedding.tolist(), display_img
    
    return None, display_img