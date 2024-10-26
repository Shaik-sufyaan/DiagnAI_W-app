import streamlit as st
import speech_recognition as sr

def speech_to_text():
    """
    Captures audio from the microphone and converts it to text.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Speak now...")
        audio_data = r.record(source, duration=5)  # Adjust duration as needed
        try:
            text = r.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            st.write("Could not understand audio")
        except sr.RequestError as e:
            st.write(f"Could not request results from Google Speech Recognition service; {e}")
    return None

def main():
    st.title("Speech to Text")

    # Input box with a record button
    input_text = st.text_area("Input Text", "")
    record_button = st.button("Record")

    if record_button:
        # Start speech recognition
        recognized_text = speech_to_text()
        if recognized_text:
            input_text.text = recognized_text

# Run the app
if __name__ == "__main__":
    main()