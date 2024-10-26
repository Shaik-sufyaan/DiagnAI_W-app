import streamlit as st
import sqlite3
from datetime import datetime
from speech_recognition import speech_to_text

import streamlit as st
from speech_recognition import AudioRecorder, convert_audio_to_text, check_microphone
from datetime import datetime
import os


# Database setup
conn = sqlite3.connect('user_data.db', check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS user_main (
    id INTEGER PRIMARY KEY,
    username TEXT,
    email TEXT,
    password TEXT,
    dob TEXT,
    sex TEXT,
    height REAL,
    weight REAL,
    nationality TEXT
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    input_text TEXT,
    retrieved_data TEXT,
    FOREIGN KEY (user_id) REFERENCES user_main (id)
)''')

# Signup function
def signup():
    st.title("Sign Up")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    dob = st.date_input("Date of Birth")
    sex = st.selectbox("Sex", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)")
    weight = st.number_input("Weight (kg)")
    nationality = st.text_input("Nationality")

    if st.button("Sign Up"):
        if password == confirm_password:
            c.execute("INSERT INTO user_main (username, email, password, dob, sex, height, weight, nationality) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (username, email, password, dob, sex, height, weight, nationality))
            conn.commit()
            st.success("Account created successfully! Please log in.")
        else:
            st.error("Passwords do not match")

# Login function
def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = c.execute("SELECT * FROM user_main WHERE email = ? AND password = ?", (email, password)).fetchone()
        if user:
            st.success("Logged in successfully")
            st.session_state['user_id'] = user[0]  # Store user ID in session state
        else:
            st.error("Invalid credentials")

# User dashboard
def user_dashboard():
    st.title("User Dashboard")

    if 'user_id' in st.session_state:
        st.write(f"Welcome, User ID: {st.session_state['user_id']}")

        # Display the input text area with existing input text
        input_text = st.session_state.get('input_text', '')
        st.text_area("Input Text", input_text, height=200, key='input_text_area')

        # Button to start recording
        if st.button("Record"):
            recognized_text = speech_to_text()
            if recognized_text:
                st.session_state['input_text'] = recognized_text
                st.success("Audio recorded and converted to text")
                st.experimental_rerun()

        # Button to save the session data
        if st.button("Save Session"):
            input_text = st.session_state.get('input_text', '')
            if input_text:
                c.execute("INSERT INTO user_sessions (user_id, input_text, retrieved_data) VALUES (?, ?, ?)",
                          (st.session_state['user_id'], input_text, ""))
                conn.commit()
                st.success("Session data saved!")

# Main app logic
if 'user_id' not in st.session_state:
    option = st.sidebar.selectbox("Login/Signup", ["Login", "Signup"])
    if option == "Signup":
        signup()
    else:
        login()
else:
    user_dashboard()

conn.close()
