import streamlit as st
import sqlite3
from datetime import datetime
from speech_recognition import AudioRecorder, convert_audio_to_text, check_microphone
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

# User dashboard with speech-to-text functionality
def user_dashboard():
    st.title("User Dashboard")

    if 'user_id' in st.session_state:
        st.write(f"Welcome, User ID: {st.session_state['user_id']}")

        # Initialize session state variables if they don't exist
        if 'audio_recorder' not in st.session_state:
            st.session_state.audio_recorder = AudioRecorder()
        if 'recording' not in st.session_state:
            st.session_state.recording = False
        if 'audio_file' not in st.session_state:
            st.session_state.audio_file = None
        if 'transcribed_text' not in st.session_state:
            st.session_state.transcribed_text = ""

        # Check if a microphone is available
        mic_available, mic_message = check_microphone()
        if not mic_available:
            st.error(mic_message)
        else:
            st.success(mic_message)

        # Manual text input area
        input_text = st.text_area("Manual Input Text", "", height=100)
        if st.button("Save Input Text"):
            if input_text.strip():
                st.session_state.transcribed_text = input_text.strip()
                st.success("Input text saved!")

        # File uploader for audio files
        uploaded_audio_file = st.file_uploader("Upload an Audio File", type=["wav", "mp3"])
        if uploaded_audio_file is not None:
            # Save the uploaded file for processing
            try:
                file_path = f"uploaded_{uploaded_audio_file.name}"
                with open(file_path, "wb") as f:
                    f.write(uploaded_audio_file.getbuffer())
                st.session_state.audio_file = file_path
                st.success("Audio file uploaded successfully.")
            except Exception as e:
                st.error(f"Failed to save the audio file: {e}")

        # Form for user actions: recording, stopping, and transcribing
        with st.form("audio_form"):
            col1, col2 = st.columns(2)

            # Recording button
            with col1:
                if not st.session_state.recording:
                    if st.form_submit_button("🎤 Start Recording"):
                        if st.session_state.audio_recorder.start_recording():
                            st.session_state.recording = True
                        else:
                            st.error(f"Failed to start recording: {st.session_state.audio_recorder.error}")
                else:
                    if st.form_submit_button("⏹️ Stop Recording"):
                        st.session_state.recording = False
                        st.session_state.audio_recorder.stop_recording()
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.session_state.audio_file = f"recording_{timestamp}.wav"

            # Transcribe button for uploaded or recorded audio
            with col2:
                if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
                    if st.form_submit_button("📝 Transcribe Audio"):
                        with st.spinner("Transcribing..."):
                            transcribed_text = convert_audio_to_text(
                                st.session_state.audio_file
                            )
                            if transcribed_text:
                                st.session_state.transcribed_text = transcribed_text
                                st.success("Transcription complete!")
                            else:
                                st.error("Transcription failed")

            # Clear button
            if st.form_submit_button("🗑️ Clear"):
                st.session_state.transcribed_text = ""
                st.session_state.audio_file = None
                # Clean up audio files
                for file in os.listdir():
                    if file.startswith("recording_") or file.startswith("uploaded_"):
                        try:
                            os.remove(file)
                        except Exception as e:
                            st.error(f"Error deleting file {file}: {e}")

        # Display the transcribed text in a text area
        st.text_area("Transcribed Text",
                     st.session_state.transcribed_text,
                     height=200,
                     key="transcript_area")

        # Add some usage instructions
        with st.expander("ℹ️ Instructions"):
            st.markdown("""
            1. Type text directly into the **Manual Input Text** area and save it.
            2. Alternatively, **upload an audio file** or **record audio** using the buttons.
            3. Click **Transcribe Audio** to convert uploaded or recorded audio to text.
            4. The transcribed or manually entered text will appear in the **Transcribed Text** area below.
            5. Use the **Clear** button to reset everything.
            """)

# Main app logic
if 'user_id' not in st.session_state:
    option = st.sidebar.selectbox("Login/Signup", ["Login", "Signup"])
    if option == "Signup":
        signup()
    else:
        login()
else:
    user_dashboard()

# Close the database connection when done
conn.close()
