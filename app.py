
import os

import cv2
import streamlit as st
from db import init_db, login_user, register_user
from model import predict_sign
from utils import listen_voice, speak_text

# Initialize DB
init_db()
st.title("🧏‍♂️ AI Sign Language Interpreter")

# Session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "gender" not in st.session_state:
    st.session_state.gender = None

# Navigation
menu = ["Sign In", "Sign Up"] if not st.session_state.logged_in else ["Interpreter", "Sign Out"]
choice = st.sidebar.selectbox("Menu", menu)

# Sign up
if choice == "Sign Up":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type='password')
    gender = st.selectbox("Gender", ["female", "male"])
    if st.button("Sign Up"):
        if register_user(new_user, new_pass, gender):
            st.success("Account created. You can now log in.")
        else:
            st.error("Username already exists.")

# Sign in
elif choice == "Sign In" and not st.session_state.logged_in:
    st.subheader("Welcome Back")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        gender = login_user(username, password)
        if gender:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.gender = gender
            st.rerun()
        else:
            st.error("Invalid username or password.")

# Sign out
elif choice == "Sign Out":
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.gender = None
    st.success("Signed out successfully.")
    st.experimental_rerun()

# Main Interpreter
elif choice == "Interpreter" and st.session_state.logged_in:
    st.success(f"Logged in as {st.session_state.username} ({st.session_state.gender})")
    action = st.selectbox("Select Mode", ["Select", "Sign to Voice", "Voice to Sign"])

    # SIGN TO VOICE
    if action == "Sign to Voice":
        st.subheader("Use Webcam to Show Sign Language Letter")
        start = st.button("Start Webcam")

        if start:
            stframe = st.empty()
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                st.error("Could not access webcam.")
            else:
                st.info("Webcam started. Show a sign...")

                while True:
                    ret, frame = camera.read()
                    if not ret:
                        st.error("Failed to capture frame.")
                        break

                    # Resize and predict
                    prediction = predict_sign(frame)

                    # Show camera frame
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    stframe.image(frame, caption=f"Predicted: {prediction}", use_column_width=True)

                    # Speak prediction
                    speak_text(prediction)
                    break  # Remove this break if you want to keep looping

                camera.release()

    # VOICE TO SIGN
    elif action == "Voice to Sign":
        st.subheader("Speak and See Animated Interpreter")
        if st.button("Start Speaking"):
            st.write("Listening ...")
            text = listen_voice()  # ✅ use listen_voice() from utils.py

            if text and "Sorry" not in text:  # check valid recognition
                # Show full sentence
                st.subheader("You said:")
                st.write(text)

                # Define simple mapping of words → sign symbols (fallback if no avatar)
                sign_dict = {
                    "hi": "👋",
                    "hello": "🙌",
                    "my": "🤟",
                    "name": "📛",
                    "is": "➡️",
                    "al": "🧑‍🦱"
                }

                # Build emoji sign sentence
                words = text.split()
                sign_output = [sign_dict.get(word.lower(), "❓") for word in words]

                st.subheader("Avatar Signing")
                st.write(" ".join(sign_output))  # show emoji-based sentence

                # Try to show avatars (GIFs) if available
                for word in words:
                    gif_path = f"avatars/{st.session_state.gender}/{word.lower()}.gif"
                    if os.path.exists(gif_path):
                        st.image(gif_path, caption=word, use_container_width=True)
                    else:
                        st.info(f"({word}) → {sign_dict.get(word.lower(), '❓')}")
            else:
                st.error("Sorry, I could not recognize what you said.")

    
   # elif action == "Voice to Sign":
   #     st.subheader("Speak and See Animated Interpreter")
   #     if st.button("Start Speaking"):
   #         st.write("Listening ...")
   #         text = recognize_speech()

   #         if text:
   #             st.subheader("You said:")
   #             st.write(text)

    #            st.subheader("Avatar Signing")
    #            words = text.split()

    #            for word in words:
    #                sign = get_sign_for_word(word.lowe())
    #                if sign:
    #                    st.image(sign, caption=word, use_container_width=True)
    #                else:
    #                    st.error("sorry i could not recognize what you said")
  



        