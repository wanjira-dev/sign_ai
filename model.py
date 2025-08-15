import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Load trained CNN model
model = load_model('sign_model.h5')

#Labels for prediction
labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def predict_sign(image):
    # Convert to RGB 
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Resize to match model input
    img = cv2.resize(img, (28, 28)).reshape(1, 28, 28, 1) / 255.0

    #Predict
    prediction = model.predict(img)

    return labels[np.argmax(prediction)]
