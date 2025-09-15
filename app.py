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
from model import load_landmark_model, get_embedding_from_frame
from utils import speak_text, init_tts_engine, listen_voice

# Page configuration and Initialization
st.set_page_config(layout="wide", page_title="AI Sign Language Interpreter", page_icon="🧏‍♂️")
st.title("🧏‍♂️ AI Sign Language Interpreter")
st.markdown("An Advanced interpreter using MediaPipe, learned embeddings, and TiDB vector database.")

# Load model and connect to Database
@st.cache_resource
def initialize_system():
    """Loads DB Connection, embedding and TTS Engine"""
    connection = db.get_db_connection()
    if connection:
        db.setup_database(connection)
    
    embedding_model = load_landmark_model('landmark_model.h5')
    tts_engine = None
    
    return connection, embedding_model, tts_engine

# Load all core components
db_connection, model, tts_engine = initialize_system()

if not all([db_connection, model, tts_engine]):
    st.error("Could not initialize system components. Check terminal for logs")
    st.stop()

# Session State Management
# For user authentication
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
    
# For the interpreter
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'last_match' not in st.session_state:
    st.session_state.last_match = None
if 'last_spoken_label' not in st.session_state:
    st.session_state.last_spoken_label = ""

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
    
    # App moe selection in the sidebar
    app_mode = st.sidebar.radio(
        "Select Mode",
        ["Interpreter (Sign to Voice)", "Voice to Sign (Avatars)", "Admin: Teach AI New Signs"]
    )
    
    # 1st Mode: Interpreter
    if app_mode == "Interpreter (Sign to Voice)":
        st.header("Real time Sign Interpreter")
        st.info("Place your hand in the camera view. The system will find the closest matching sign")
        
        class SignVideoTransformer(VideoTransformerBase):
            def recv(self, frame):
                img = frame.to_ndarray(format="bgr24")
                query_embedding, display_img = get_embedding_from_frame(img, model)
                if query_embedding:
                    results = db.find_similar_signs(db_connection, query_embedding, top_k=1)
                    if results:
                        st.session_state.last_match = results[0]
                return display_img
            
        col_video, col_result = st.columns([2, 1])
        with col_video:
           webrtc_streamer(key="interpreter-stream", video_processor_factory=SignVideoTransformer, async_processing=True)
        with col_result:
            st.subheader("Interpretation Result")
            result_placeholder = st.empty()
            while True:
                if st.session_state.last_match:
                    match = st.session_state.last_match
                    label, similarity = match['label'], match['similarity']
                    if similarity > 0.85:
                        result_placeholder.success(f"##{label}\n(Similarity: {similarity:.2f})")
                        if label != st.session_state.last_spoken_label:
                            speak_text(label, tts_engine)
                            st.session_state.last_spoken_label = label
                            
                    else:
                        result_placeholder.warning("Match not found")
                        st.session_state.last_spoken_label = ""
                        
                else:
                    result_placeholder.info("Show a sign to the camera...")
                time.sleep(0.1)
                
    # 2nd Mode: Voice to Sign
    elif app_mode == "Voice to Sign (Avatars)":
        st.header("Speak a word or sentence")
        if st.button("Start listening", type="summary"):
            with st.spinner("Listening..."):
                sentence = listen_voice()
                
            if sentence:
                st.success(f"You said: \"{sentence}\"")
                st.info("Displaing sign language avatar...")
                user_gender = st.session_state.user_info.get('gender', 'female')
                for char in sentence.upper():
                    if char.isalpha():
                        gif_path = f"avatars/{user_gender}/{char.lower()}.gif"
                        if os.path.exists(gif_path):
                            st.image(gif_path, caption=f"Sign for '{char}'", width=250)
                            time.sleep(1)
                        else:
                            st.warning(f"No avatar found for '{char}'")
                    elif char.isspace():
                        time.sleep()
            else:
                st.error("Could not understand the audio. Please try again")
                
    # 3rd Mode: Admin (for populating the vector DB)
    elif app_mode == "Admin: Teach AI New Signs":
        st.header("Add New Signs to the Knowledge Base")
        st.info("Teach AI by showing it a sign and giving it a label. This will create and store a high-quality embedding in the TiDB vector database.")
        
        sign_label = st.text_input("Enter the word or letter for this sign:", placeholder="e.g., A, Hello").strip()
        webrtc_ctx = webrtc_streamer(key="ingest-stream", async_processing=True)
        
        if st.button("Generate and Save Embedding", type="primary"):
            if webrtc_ctx.video_receiver and sign_label:
                frame = webrtc_ctx.video_receiver.get_latest_frame()
                img = frame.to_ndarray(format="bgr24")
                embedding, display_img = get_embedding_from_frame(img, model)
                
                if embedding:
                    st.image(display_img, channels="BGR", caption="Captured Hand for Embedding")
                    user_id = st.session_state.user_info['user_id']
                    success = db.add_sign_vector(db_connection, sign_label, embedding, user_id)
                    if success:
                        st.success(f"Successfully saved embedding for '{sign_label}'!")
                        st.balloons()
                    else:
                        st.error("Fialed to save embedding. Check terminal logs.")
                
                else:
                    st.warning("No hand detected, Please position the hand clearly.")
                    
            else:
                st.warning("Please start webcam and enter label.")