import requests
import pygame
import os
import speech_recognition as sr
from pydub import AudioSegment
import langchain_implementation

# Set your OpenAI API key
api_key = <your-key>

def stt(file):
    # Define the API endpoint
    url = "https://api.openai.com/v1/audio/transcriptions"

    # Set the request headers
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    # Set the request body
    files = {'file': (f'{file}.mp3', open(f'/{file}.mp3', 'rb'))}
    data = {
        "model": "whisper-1",  # Currently only whisper-1 is available
        "language": "en",  # ISO-639-1 language code (optional)
        "prompt": "Optional prompt text to guide the model's style",  # Optional prompt
        "response_format": "json",  # Choose the format of the transcript output
        "temperature": 0.5,  # Choose the sampling temperature (optional)
    }

    # Make the POST request
    response = requests.post(url, headers=headers, files=files, data=data)

    # Print the response
    print(response.status_code)
    print(response.json())

def tts(file,txt):
    # Define the API endpoint
    url = "https://api.openai.com/v1/audio/speech"

    # Set the request headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # Define the request body
    data = {
        "model": "tts-1",  # Choose the TTS model
        "input": txt,  # Input text to generate audio for
        "voice": "alloy",  # Choose the voice
        "response_format": "mp3",  # Choose the audio format
        "speed": 1.0,  # Choose the speed of the generated audio
    }

    # Make the POST request
    response = requests.post(url, headers=headers, json=data)

    # Print the response
    print(response.status_code)
    print(response.headers['Content-Type'])

    # Save the audio file
    with open(f'{file}.mp3', 'wb') as audio_file:
        audio_file.write(response.content)


## SAVING SPEECH AS AN AUDIO FILE:
def listen(trigger_word, output_file_path,timeout=5):
    # Initialize the speech recognition recognizer and microphone
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    # Adjust the ambient noise level (you may need to calibrate this)
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)

    print(f"Listening for trigger word: '{trigger_word}'")

    while True:
        with microphone as source:
            try:
                audio_data = recognizer.listen(source)
                spoken_text = recognizer.recognize_google(audio_data)
                print(f"Recognized: {spoken_text}")

                if trigger_word.lower() in spoken_text.lower():
                    print("Trigger word detected! Recording audio...")

                    # Continue recording until no speech is detected for 5 seconds
                    audio_data = recognizer.listen(source, timeout)

                    # Convert the audio data to an AudioSegment
                    audio_segment = AudioSegment(
                        audio_data.frame_data,
                        sample_width=audio_data.sample_width,
                        channels=audio_data.channel_count,
                        frame_rate=audio_data.sample_rate
                    )

                    # Export the audio segment to a WAV file
                    audio_segment.export(output_file_path, format="wav")

                    print(f"Audio saved to: {output_file_path}")
                    return output_file_path

            except sr.UnknownValueError:
                # No speech detected
                pass
            except sr.RequestError as e:
                print(f"Speech recognition request failed: {e}")

def play_audio(file_path):
    ## PLAYING AN AUDIO FILE:
    pygame.init()
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        # Add a delay to ensure the audio plays before the program exits
        pygame.time.wait(int(pygame.mixer.music.get_length() * 1000))
    except pygame.error as e:
        print(f"Error playing audio: {e}")

    pygame.mixer.quit()
    pygame.quit()