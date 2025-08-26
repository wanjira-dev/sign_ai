import pyttsx3
import speech_recognition as sr
import streamlit as st
import threading

# Text to speech functions
@st.cache_resource
def init_tts_engine():
    """
    Initializes the pyttsx3 engine and caches it using Streamlit
    This ensures the engine is created only once, improving performance
    """
    print("Initializing TTS engine...")
    engine = pyttsx3.init()
    return engine

def _speak_thread(text, engine):
    """
    Internal function to run the blocking TTS call in a seperate thread
    """
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in TTS thread: {e}")

def speak_text(text, engine):
    """
    Speaks the given text in non-blocking way by using a separate thread.
    The main Streamlit app will remain responsive while the text is being spoken.

    Args:
        text (str): The text to be spoken.
        engine: The cached pyttsx3 engine instance.
    """
    # To prevent issues with the engine being used by multiple threads at once
    engine.stop()

    # Create and start a new thread for the speech synthesis
    thread = threading.Thread(target=_speak_thread, args=(text, engine))
    thread.start()

# Speech to text function
def listen_voice():
    """
    Listens for voice input from the microphone and returns the recognized text.
    Handles common recognition errors gracefully.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        # Adjust for ambient noise once to improve accuracy
        r.adjust_for_ambient_noise(source, duration=0.5)
        st.info("Listening... please speak clearly")
        try:
            # The timeout and phrase_time_limit help prevent it from listening forever
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            st.warning("No speech detected. Listening timed out.")
            return None

    try:
        st.info("Recognizing...")
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.warning("Sorry, Google Speech Recognition could not understand the audio.")
        return None
    except sr.RequestError as e:
        st.error(f"Could not request results from Google service; {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occured during speech recognition: {e}")
        return None
