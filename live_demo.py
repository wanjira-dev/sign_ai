import cv2
import sys
import os
import threading
import numpy as np
from gtts import gTTS
import tensorflow as tf

# Disable TensorFlow 2.x warnings and enable v1 compatibility
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.compat.v1.disable_eager_execution()

# Language in which you want to convert
language = 'en'

# Get a live stream from the webcam
live_stream = cv2.VideoCapture(0)

# Word for which letters are currently being signed
current_word = ""

# Load training labels file
label_lines = [line.rstrip() for line in tf.io.gfile.GFile("training_set_labels.txt")]

# Load trained model's graph
with tf.io.gfile.GFile("trained_model_graph.pb", 'rb') as f:
    graph_def = tf.compat.v1.GraphDef()
    graph_def.ParseFromString(f.read())
    _ = tf.import_graph_def(graph_def, name='')


def predict(image_data):
    # Focus on Region of Interest
    resized_image = image_data[70:350, 70:350]

    # Resize to 200 x 200
    resized_image = cv2.resize(resized_image, (200, 200))

    # Encode image to JPEG and get byte string
    image_data = cv2.imencode('.jpg', resized_image)[1].tobytes()

    # Run prediction
    predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})

    # Sort to show top predictions
    top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]

    max_score = 0.0
    res = ''
    for node_id in top_k:
        label = label_lines[node_id + 1] if label_lines[node_id].upper() == 'Z' else label_lines[node_id]
        score = predictions[0][node_id]
        if score > max_score:
            max_score = score
            res = label

    return res, max_score


def speak_letter(letter):
    prediction_text = letter
    speech_object = gTTS(text=prediction_text, lang=language, slow=False)
    speech_object.save("prediction.mp3")

    # Try to play on macOS, fallback to Linux/Windows
    if os.system("afplay prediction.mp3") != 0:
        os.system("start prediction.mp3" if os.name == "nt" else "mpg321 prediction.mp3")


with tf.compat.v1.Session() as sess:
    softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')

    time_counter = 0
    captureFlag = False
    realTime = True
    spell_check = False  # If you re-enable spell checking, import the module at the top

    while True:
        keypress = cv2.waitKey(1)
        ret, img = live_stream.read()
        if not ret:
            print("❌ Failed to capture video.")
            break

        # Draw region of interest
        cv2.rectangle(img, (70, 70), (350, 350), (0, 255, 0), 2)
        cv2.imshow("Live Stream", img)

        # Real-time prediction every ~45 frames
        if time_counter % 45 == 0 and realTime:
            letter, score = predict(img)
            print("Letter: ", letter.upper(), " Score: ", score)
            print("Current word: ", current_word)

            if letter.upper() not in ['NOTHING', 'SPACE', 'DEL']:
                current_word += letter.upper()
                speak_letter(letter)
            elif letter.upper() == 'SPACE':
                if current_word:
                    speak_letter(current_word)
                current_word = ""
            elif letter.upper() == 'DEL':
                current_word = current_word[:-1] if current_word else current_word

        # 'C' to capture one frame
        if keypress == ord('c'):
            captureFlag = True
            realTime = False

        # 'R' to resume real-time
        if keypress == ord('r'):
            realTime = True

        if captureFlag:
            captureFlag = False
            letter, score = predict(img)
            print("Letter: ", letter.upper(), " Score: ", score)
            print("Current word: ", current_word)

            if letter.upper() not in ['NOTHING', 'SPACE', 'DEL']:
                current_word += letter.upper()
                speak_letter(letter)
            elif letter.upper() == 'SPACE':
                if current_word:
                    speak_letter(current_word)
                current_word = ""
            elif letter.upper() == 'DEL':
                current_word = current_word[:-1] if current_word else current_word

        # ESC key to exit
        if keypress == 27:
            break

        time_counter += 1

# Clean up
live_stream.release()
cv2.destroyAllWindows()
