import cv2
import numpy as np
from tensorflow.keras.models import load_model

# Load trained CNN model
model = load_model('sign_model.tflite')

#Labels for prediction
labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def predict_sign(image):
    # Convert to RGB 
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Resize to match model input
    img = cv2.resize(img, (64, 64))

    # Normalize and add batch dimension
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=0)

    #Predict
    prediction = model.predict(img)
    predicted_index = np.argmax(prediction)
    confidence = prediction[0][predicted_index]

    return labels[predicted_index], confidence
