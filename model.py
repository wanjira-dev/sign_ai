
import cv2
import numpy as np
from tensorflow.keras.models import load_model

model = load_model('sign_model.h5')
labels = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def predict_sign(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (28, 28)).reshape(1, 28, 28, 1) / 255.0
    prediction = model.predict(img)
    return labels[np.argmax(prediction)]
