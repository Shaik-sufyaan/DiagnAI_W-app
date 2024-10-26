''' import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime
import speech_recognition as sr
from audio_processing import process_audio_threaded

from pydub import AudioSegment
import os
from audio_recorder_streamlit import audio_recorder
import tempfile

# Set page config
st.set_page_config(
    page_title="Speech to Text App",
    page_icon="🎤",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3rem;
        background-color: #ff4b4b;
        color: white;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .success-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        color: #155724;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        color: #721c24;
        margin: 1rem 0;
    }
    .speech-result {
        padding: 1rem;
        border-radius: 5px;
        background-color: #e9ecef;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Database functions
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Speech to text data table
    c.execute('''CREATE TABLE IF NOT EXISTS speech_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  speech_text TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def get_user_id(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def save_speech_data(user_id, speech_text):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO speech_data (user_id, speech_text) VALUES (?, ?)',
              (user_id, speech_text))
    conn.commit()
    conn.close()

def get_user_speech_data(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT speech_text, created_at 
                 FROM speech_data 
                 WHERE user_id = ? 
                 ORDER BY created_at DESC''', (user_id,))
    result = c.fetchall()
    conn.close()
    return result

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?',
              (username, hash_password(password)))
    result = c.fetchone()
    conn.close()
    return bool(result)

# Speech recognition function
def process_audio(audio_bytes):
    recognizer = sr.Recognizer()
    
    # Save audio bytes to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name
    
    try:
        with sr.AudioFile(temp_audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except Exception as e:
        return f"Error processing audio: {str(e)}"
    finally:
        os.unlink(temp_audio_path)

# Initialize session state
if 'username' not in st.session_state:
    st.session_state.username = None

# Initialize database
init_db()

# Sidebar navigation
def sidebar():
    with st.sidebar:
        st.title("Navigation")
        if st.session_state.username:
            st.write(f"Welcome, {st.session_state.username}!")
            if st.button("Logout"):
                st.session_state.username = None
                st.experimental_rerun()
        else:
            menu = ["Login", "Sign Up"]
            choice = st.radio("Choose an option", menu)
            return choice

# Login page
def login_page():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if verify_user(username, password):
                st.session_state.username = username
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

# Sign up page
def signup_page():
    st.title("Sign Up")
    with st.form("signup_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Sign Up")
        
        if submit:
            if not username or not email or not password:
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif not is_valid_email(email):
                st.error("Invalid email address")
            else:
                try:
                    conn = sqlite3.connect('users.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                             (username, hash_password(password), email))
                    conn.commit()
                    conn.close()
                    st.success("Account created successfully! Please login.")
                except sqlite3.IntegrityError:
                    st.error("Username or email already exists")

# Dashboard page
def dashboard():
    st.title("Speech to Text Dashboard")
    
    # Speech recording section
    st.subheader("Record Speech")
    audio_bytes = audio_recorder()
    
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        text = process_audio(audio_bytes)
        
        if text:
            st.markdown(f'<div class="speech-result">Transcription: {text}</div>',
                       unsafe_allow_html=True)
            
            user_id = get_user_id(st.session_state.username)
            save_speech_data(user_id, text)
    
    # Display history
    st.subheader("Your Speech History")
    user_id = get_user_id(st.session_state.username)
    speech_data = get_user_speech_data(user_id)
    
    if speech_data:
        for text, timestamp in speech_data:
            with st.expander(f"Recording from {timestamp}"):
                st.write(text)
    else:
        st.info("No recordings yet")

# Main app
def main():
    if st.session_state.username:
        dashboard()
    else:
        choice = sidebar()
        if choice == "Login":
            login_page()
        else:
            signup_page()

if __name__ == "__main__":
    main() 
    '''