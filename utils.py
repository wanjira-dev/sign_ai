
import pyttsx3
import speech_recognition as sr
import streamlit as st


def listen_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except:
        return "Sorry, couldn't understand."

def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
