import streamlit as st
import cv2
import numpy as np
import uuid
import time
import os
from collections import deque

# Realtime video streaming
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode

# Project modules
import tidb as db
from model import load_sign_model, preprocess_image
from utils import speak_text, listen_voice

# Page configuration and Initialization
st.set_page_config(layout="wide", page_title="AI Sign Language Interpreter", page_icon="🧏‍♂️")
st.title("🧏‍♂️ AI Sign Language Interpreter")

# Load model and connect to Database
@st.cache_resource

def initialize_system():
    """Load model and connect to DB. Caching prevents re-loading on every rerun."""
    model = load_sign_model('sign_model.h5')
    connection = db.get_db_connection()
    if connection:
        db.setup_database(connection)
    return model, connection

model, db_connection = initialize_system()
label_mapping = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

if not db_connection:
    st.error("Could not connect to TiDB.")
    st.stop()
    
# Session State Management
# For user authentication
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
    
# For the interpreter
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'translated_sentence' not in st.session_state:
    st.session_state.translated_sentence = ""
if 'last_log_id' not in st.session_state:
    st.session_state.last_log_id = None
if 'prediction_buffer' not in st.session_state:
    st.session_state.prediction_buffer = deque(maxlen=5) # To stabilize predictions
    
# User authentication and navigation
menu = ["Sign In", "Sign Up"] if not st.session_state.user_info else ["Interpreter", "Sign Out"]
choice = st.sidebar.selectbox("Menu", menu)

st.sidebar.title("User Account")

# Sign Up Page
if choice == "Sign Up":
    st.subheader("Create New Account")
    with st.form("signup_form"):
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type='password')
        gender = st.selectbox("Gender (for avatar)", ["female", "male"])
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            if db.register_user(db_connection, new_user, new_pass, gender):
                st.success("Account created successfully! Please Sign In.")
            else:
                st.error("Username already exists.")
                
# Sign In page
elif choice == "Sign In":
    st.subheader("Welcome Back!")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        submitted = st.form_submit_button("Login")
        if submitted:
            user_data = db.login_user(db_connection, username, password)
            if user_data:
                st.session_state.user_info = user_data
                st.rerun()
            else:
                st.error("Invalid username or password")
                
# Sign Out logic
elif choice == "Sign Out":
    st.session_state.user_info = None
    st.success("You have been signed out.")
    time.sleep(1)
    st.rerun()
    
# Main Interpreter Application
elif choice == "Interpreter" and st.session_state.user_info:
    st.success(f"Logged in as ** {st.session_state.user_info['username']}**")
    action = st.radio("Select Mode", ["Sign to Voice", "Voice to Sign"], horizontal=True)
    
    # SIGN TO VOICE (Realtime)
    if action == "Sign to Voice":
        # Real-time video processing class
        class SignVideoTransformer(VideoTransformerBase):
            def recv(self, frame):
                img = frame.to_ndarray(format="bgr24")
                
                # Preprocessing frame for the model
                processed_img, display_img = preprocess_image(img, target_size=(64, 64))
                
                # Perform inference
                prediction = model.predict(processed_img)
                predicted_index = np.argmax(prediction)
                predicted_sign = label_mapping[predicted_index]
                confidence = float(np.max(prediction))
                
                # Stores prediction in session state and pass data to the main thread
                st.session_state.current_prediction_data = {
                    "sign": predicted_sign,
                    "confidence": confidence
                }
                st.session_state.prediction_buffer.append(predicted_sign)
                
                # Draw prediction on the frame for visual feedback
                cv2.putText(display_img, f"{predicted_sign} ({confidence:.2f})", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                return display_img
            
        # UI Layout
        col_video, col_text = st.columns([2, 1])
            
        with col_video:
            st.header("Live Feed")
            webrtc_streamer(
                key="sign-interpreter-stream",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=SignVideoTransformer,
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True,
            )
        with col_text:
            st.header("Translated Sentence")
            sentence_placeholder = st.empty()
            sentence_placeholder.markdown(f"## `{st.session_state.translated_sentence}`")
            st.header("Prediction Details")
            details_placeholder = st.empty()
                
        # Add a feedback mechanism
        st.sidebar.header("Correction")
        correct_sign_input = st.sidebar.text_input("If the last letter was wrong correct it here:", max_chars=1).upper()
        if st.sidebar.button("Submit Correction"):
            if st.session_state.last_log_id and correct_sign_input:
                db.log_feedback(db.connection, st.session_state.last_log_id, correct_sign_input)
                st.sidebar.success(f"Feedback submitted.")
            else:
                st.sidebar.warning("A prediction must be logged first")
                    
    elif action == "Voice to Sign":
        st.header("Speak a word or sentence")
        if st.button("Start Listening", type="primary"):
            with st.pinner("Listening...0"):
                sentence = listen_voice()
                
            if sentence:
                st.success(f"You said: \"{sentence}\"")
                st.info("Displaying sign language avatar...")
                
                user_gender = st.session_state.user_info.get('gender', 'female')
                
                for char in sentence.upper():
                    if char.isalpha():
                        gif_path = f"avatars/{user_gender}/{char.lower()}.gif"
                        if os.path.exists(gif_path):
                            st.image(gif_path, caption=f"Sign for '{char}'", width=250)
                            time.sleep(1) # Pause between signs
                            
                        else:
                            st.warning(f"No avatar found for '{char}'")
                    elif char.isspace():
                        time.sleep(1) # Pause for spaces
            else:
                st.error("Could not understand the audio. Please try again")
                
# Main application loop (for updating UI from session state)
if st.session_state.user_info and choice == "Interpreter" and action == "Sign to Voice":
    confidence_threshold = 0.90 # Only accept high-confidence predictions
    details_placeholder = st.empty()
    sentence_placeholder = st.empty()
    while True:
        if "current_prediction_data" in st.session_state:
            data = st.session_state.current_prediction_data
            
            # Update the details placeholder
            details_placeholder.info(f"**Current Sign:**{data['sign']}\n\n" f"**Confidence:**{data['confidence']:.2f}")
            
            # Checks for a stable prediction for the buffer
            if len(st.session_state.prediction_buffer) == st.session_state.prediction_buffer.maxlen:
                stable_sign = max(set(st.session_state.prediction_buffer), key=st.session_state.prediction_buffer.count)
                
                # Checks if this stable sign is new and confident
                if stable_sign != st.session_state.get('last_spoken_sign') and data['confidence'] > confidence_threshold:
                    # Update the sentence and UI
                    st.session_state.translated_sentence += stable_sign
                    sentence_placeholder.markdown(f"## `st.session_state.translated_sentence`")
                    
                    # Speak the new letter
                    speak_text(stable_sign)
                    st.session_state.last_spoken_sign = stable_sign # To prevent re-speaking
                    
                    # Log to TiDB
                    current_user_id = st.session_state.user_info['user_id']
                    log_id = db.log_prediction(
                        connection=db_connection,
                        session_id=st.session_state.session_id,
                        prediction=stable_sign,
                        confidence=data['confidence'],
                        user_id=current_user_id
                    )
                    st.session_state.last_log_id = log_id
                    
                    # Clears buffer after successful action
                    st.session_state.prediction_buffer.clear()
                    
        time.sleep(0.1)