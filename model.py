import cv2
import numpy as np
import tensorflow as tf

def load_sign_model(model_path='sign_model.h5'):
    """
    Loads the trained Keras model from the specified H5 file.
    Args:
        model_path (str): The path to the .h5 model file.
    Returns:
        A loaded Keras model object
    """
    try:
        model = tf.keras.models.load_model(model_path)
        print(f"Model loaded successfully from {model_path}")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Please ensure 'sign_model.h5' is in the correct directory and is a valid Keras model.")
        return None

def preprocess_image(frame, target_size=(64, 64)):
    """
    Preprocesses a single frame from the webcam for model prediction.
    This function implements a Region of Interest (ROI) to isolate the hand.

    Args:
        frame (numpy.ndarray): The raw BGR frame from OpenCV.
        target_size (tuple): The target image size (width, height) for the model.

    Returns:
        tuple: A tuple containing:
            - preprocessed_img (numpy.ndarray): The final image ready for model input.
            - display_img (numpy.ndarray): The original frame with ROI box drawn on it.
    """

    # 1. Define and draw the Region of Interest (ROI)
    h, w, _ = frame.shape

    # Define a square ROI in the center of the frame
    # This guides the user to place their hand in predictable location.
    roi_size = 300
    x1 = int((w - roi_size) / 2)
    y1 = int((h - roi_size) / 2)
    x2 = x1 + roi_size
    y2 = y1 + roi_size

    # Create a copy of the frame to draw on for display
    display_img = frame.copy()
    cv2.rectangle(display_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # 2. Extract and process the ROI
    # Crop the frame to the defined ROI
    roi = frame[y1:y2, x1:x2]

    # Convert the ROI to grayscale, as color is often not critical for sign shape
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Apply a Gaussian Blur to reduce noise and improve model generalization
    blurred_roi = cv2.GaussianBlur(gray_roi, (5, 5), 0)

    # Resize the processed ROI to the size your model expects
    resized_img = cv2.resize(blurred_roi, target_size)

    # 3. Normalize and Reshape for model input
    # Normalize pixel values to be between 0 and 1
    normalized_img = resized_img / 255.0

    # Reshape the image to match the model's expected input shape:
    # (1, height, width, 1) -> (batch_size, height, width, channels)
    preprocessed_img = np.expand_dims(np.expand_dims(normalized_img, axis=-1), axis=0)

    return preprocessed_img, display_img