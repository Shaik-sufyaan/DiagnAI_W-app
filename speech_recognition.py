import streamlit as st
import speech_recognition as sr
import wave
import pyaudio
import threading
import time
import os
import json
from datetime import datetime
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment


def check_microphone():
    """
    Check if a microphone is connected and accessible.
    Returns tuple of (boolean, string) indicating status and message.
    """
    try:
        p = pyaudio.PyAudio()
        input_devices = []

        # Check all audio devices
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info['name'])

        p.terminate()

        if input_devices:
            return True, f"Found {len(input_devices)} microphone(s): {', '.join(input_devices)}"
        else:
            return False, "No microphone detected. Please connect a microphone and try again."

    except Exception as e:
        return False, f"Error checking microphone: {str(e)}"


class AudioRecorder:
    def __init__(self):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.frames = []
        self.is_recording = False
        self.error = None

    def start_recording(self):
        """Start recording audio from the microphone."""
        self.frames = []
        self.is_recording = True
        threading.Thread(target=self._record_audio).start()
        return True

    def stop_recording(self):
        """Stop the audio recording."""
        self.is_recording = False

    def _record_audio(self):
        """Internal method to handle the recording process."""
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=self.FORMAT,
                            channels=self.CHANNELS,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK)

            while self.is_recording:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                self.frames.append(data)

            stream.stop_stream()
            stream.close()
            p.terminate()

            # Save the recording with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            self.save_audio(filename)
            st.session_state.audio_file = filename

        except Exception as e:
            self.error = str(e)
            self.is_recording = False

    def save_audio(self, filename):
        """Save the recorded audio to a WAV file."""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self.frames))
        except Exception as e:
            self.error = str(e)

import os
import wave
import json
from datetime import datetime
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import streamlit as st
from speech_recognition import AudioRecorder, check_microphone

# Update the model path to your specific location
MODEL_PATH = r"C:\Users\sufya\OneDrive\Desktop\streamlit\models\vosk-model-en-us-daanzu-20200905"


def convert_audio_to_text(audio_file_path, model_path=MODEL_PATH):
    """
    Convert an audio file to text using the Vosk speech recognition model.
    
    Args:
        audio_file_path (str): Path to the audio file.
        model_path (str): Path to the Vosk model directory.
        
    Returns:
        str: Transcribed text or None if transcription fails.
    """
    try:
        # Verify if the model path exists
        if not os.path.exists(model_path):
            raise ValueError(f"Model path '{model_path}' does not exist.")

        # Load the Vosk model
        model = Model(model_path)
        recognizer = KaldiRecognizer(model, 16000)

        # Convert audio to a compatible format using pydub (if necessary)
        audio = AudioSegment.from_file(audio_file_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export("temp_audio.wav", format="wav")

        # Read the processed WAV file
        with wave.open("temp_audio.wav", "rb") as wav_file:
            recognizer = KaldiRecognizer(model, wav_file.getframerate())
            recognizer.SetWords(True)
            transcribed_text = ""

            while True:
                data = wav_file.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    transcribed_text += result.get("text", "")

            # Get the final part of the recognition
            final_result = json.loads(recognizer.FinalResult())
            transcribed_text += final_result.get("text", "")

        return transcribed_text

    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def speech_to_text():
    st.title("Speech to Text Converter")

    mic_available, mic_message = check_microphone()
    if not mic_available:
        st.error(mic_message)
        st.stop()
    else:
        st.success(mic_message)

    # Initialize session state variables
    if 'audio_recorder' not in st.session_state:
        st.session_state.audio_recorder = AudioRecorder()
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    if 'transcribed_text' not in st.session_state:
        st.session_state.transcribed_text = ""

    with st.form("audio_form"):
        col1, col2 = st.columns(2)

        with col1:
            if not st.session_state.recording:
                if st.form_submit_button("🎤 Start Recording"):
                    if st.session_state.audio_recorder.start_recording():
                        st.session_state.recording = True
                    else:
                        st.error(f"Failed to start recording: {st.session_state.audio_recorder.error}")
            else:
                if st.form_submit_button("⏹️ Stop Recording"):
                    st.session_state.audio_recorder.stop_recording()
                    st.session_state.recording = False
                    # Save recording to a file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.session_state.audio_file = f"recording_{timestamp}.wav"

        with col2:
            if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
                if st.form_submit_button("📝 Transcribe Audio"):
                    with st.spinner("Transcribing..."):
                        transcribed_text = convert_audio_to_text(
                            st.session_state.audio_file, model_path=MODEL_PATH
                        )
                        if transcribed_text:
                            st.session_state.transcribed_text = transcribed_text
                            st.success("Transcription complete!")
                        else:
                            st.error("Transcription failed")

        if st.form_submit_button("🗑️ Clear"):
            st.session_state.transcribed_text = ""
            st.session_state.audio_file = None
            # Clean up audio files
            for file in os.listdir():
                if file.startswith("recording_") and file.endswith(".wav"):
                    try:
                        os.remove(file)
                    except Exception as e:
                        st.error(f"Error deleting file {file}: {e}")

    # Display the transcribed text in a text area
    st.text_area("Transcribed Text", st.session_state.transcribed_text, height=200, key="transcript_area")


    with st.expander("ℹ️ Instructions"):
        st.markdown("""
        1. Click the **Start Recording** button to begin recording audio.
        2. Speak clearly into your microphone.
        3. Click **Stop Recording** when you're finished.
        4. Click **Transcribe Audio** to convert your speech to text.
        5. The transcribed text will appear in the text area below.
        6. Use the **Clear** button to reset everything.
        """)


if __name__ == "__main__":
    speech_to_text()
