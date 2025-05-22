from pynput.keyboard import Listener, Key
from pynput import keyboard
from pvrecorder import PvRecorder
import struct
import wave
from openai import OpenAI
from pathlib import Path
import time
from pygame import mixer
import os
from dotenv import load_dotenv
from transformers import pipeline
import json
import random
from utilities import *
import time


def list_audio_devices():
    """
    list which mic index are available

    can be used to find out what number to put in the mic_index
    |
    |
    v
    ChatBot(mic_index=5)
    """
    for index, device in enumerate(PvRecorder.get_available_devices()):
        print(f"[{index}] {device}")
    print("")

    return len(PvRecorder.get_available_devices())


class ChatBot:
    def __init__(self, mic_index):
        self.preprompt = """
        Keep this response as a short and concise message as if you
        were talking to someone one to one.
        The following text has been taking in from an audio transcription
        so also watch out for weird spellings:
        """
        load_dotenv(override=True)
        print(os.environ.get("OPENAI_API_KEY"))
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.mic_index = mic_index

    def record_audio(self) -> str:
        """
        Returns:
            file name saved to
        """
        recorder = PvRecorder(device_index=self.mic_index, frame_length=512)

        # Flag to control recording state
        is_recording = False
        audio = []

        # Define callback functions for key press and release
        def on_press(key):
            nonlocal is_recording, audio
            if key == keyboard.Key.space and not is_recording:
                print("Recording...")
                recorder.start()
                is_recording = True
                audio = []

        def on_release(key):
            nonlocal is_recording
            if key == keyboard.Key.space and is_recording:
                print("Finished recording.")
                recorder.stop()
                is_recording = False

                print("saving to test.wav")
                with wave.open("./test.wav", 'w') as f:
                    f.setparams((1, 2, 16000, 512, "NONE", "NONE"))
                    f.writeframes(struct.pack("h" * len(audio), *audio))

        # Collect events until released
        def record_audio():
            nonlocal is_recording, audio
            temp = False
            while True:
                if is_recording:
                    frame = recorder.read()
                    audio.extend(frame)
                    temp = True
                if temp and not is_recording:
                    break

        # Start listening to keyboard events
        listener = Listener(
            on_press=on_press,
            on_release=on_release
        )
        listener.start()
        try:
            print("Press and hold the space bar to record.")
            record_audio()
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            listener.stop()
            recorder.delete()

        return "./test.wav"

    def speach2text(self, filename, model="whisper-1") -> str:
        """
        Returns:
            transcribed text
        """

        audio_file = open(filename, "rb")
        transcription = self.client.audio.transcriptions.create(
            model=model,
            file=audio_file
        )
        #print(transcription.text)
        return transcription.text

    def prompt_gpt(self, text, input_prompt, model="gpt-4o-mini") -> str:
        """
        Return:
            chatgpt string response
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                # {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": input_prompt + text
                 }
            ]
        )
        return response.choices[0].message.content

    def text2speech(self, prompt_output, model="tts-1", voice="alloy") -> str:
        """
        Return:
            speech output filename
        """
        speech_file_path = Path(__file__).parent / "speech.mp3"
        with self.client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=prompt_output
        ) as response:
            response.stream_to_file(speech_file_path)
 
        mixer.init()
        mixer.music.load("speech.mp3")
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(1)
        mixer.music.stop()
        mixer.quit()
 
        os.remove("speech.mp3")
 
 
        return "speech.mp3"

    def run_pipline(self, speech2text_model="whisper-1", chat_model="gpt-4o-mini", text2speech_model="tts-1",
                    text2speech_voice="alloy"):
        res = self.record_audio()
        print("---")
        # print(f"output file: {res}")
        classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)

        transcribed_text = self.speach2text(res, speech2text_model)
        print(f"[transcribed text]: {transcribed_text}")

        text_response = self.prompt_gpt(transcribed_text, self.preprompt, chat_model)
        print(f"[{chat_model} response]: {text_response}")

        top_result = classifier(text_response)[0]
        top_emotion_data = sorted(top_result, key=lambda x: x['score'], reverse=True)[0]
        top_emotion = top_emotion_data['label']
        confidence_score = top_emotion_data['score']

        print(f"Top emotion: {top_emotion} ({confidence_score:.2f})")

        movement_library = load_all_movements()

        movement = select_movement(top_emotion, confidence_score, movement_library)

        if movement:
            print(f"Selected: {movement['filename']} ({movement['emotion_strength']})")
            print(movement['animation'])
            run_seq(movement['animation'])
            time.sleep(10)
            run_seq('reset')
            time.sleep(5)
        # Send movement["frame_list"] to robot
        else:
            print("No suitable movement found.")

        filename = self.text2speech(text_response, text2speech_model, text2speech_voice)
        # print(f"output file {filename}")

        self.preprompt += f"""
        past input:
            {transcribed_text}
        past response:
            {text_response}\n
        """
        return transcribed_text, text_response, self.preprompt
    

def load_all_movements(directory="src\sequences\woody"):
    movements = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                try:
                    data = json.load(f)
                    if "emotion" in data and "emotion_strength" in data:
                        data["filename"] = filename  
                        movements.append(data)
                except json.JSONDecodeError:
                    print(f"Skipping {filename}: not valid JSON")
    return movements

def select_movement(emotion: str, confidence: float, movement_library: list):
    # Filter movements that match the emotion
    candidates = [m for m in movement_library if m.get("emotion") == emotion]

    # Keep only those with emotion_strength ≤ confidence
    eligible = [m for m in candidates if m.get("emotion_strength", 0) <= confidence]

    if not eligible:
        print(f"No matching movement for emotion '{emotion}' with confidence {confidence}.")
        # fallback to the closest match
        if candidates:
            closest = min(candidates, key=lambda m: abs(m["emotion_strength"] - confidence))
            return closest
        return None

    return random.choice(eligible)


if __name__ == '__main__':
    # example usage

    # list all audio devices
    print("== pick you audio device ==\n")
    num_dev = list_audio_devices()
    while True:
        num = input(f"choose from 0-{num_dev-1}: ")
        if num.isnumeric() and int(num) in range(0, num_dev):
            break
        print("not a valid input :\ \n")

    MIC_INDEX = int(num) # run list_audio_devices() to choose which mic to use

    # input selected audio device index
    cb = ChatBot(mic_index=MIC_INDEX)
    init_robot()

    # run the chatbot
    # num = 0
    # while num:
    #     cb.run_pipline()
    #     num = input("Run again? 1: yes, 0: no")

    #classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)
    

    # run the chat bot again
    #transcribed_text, response, old_convo = cb.run_pipline()

    try:
        while True:
            cb.run_pipline()
            print("Ready for the next input. Press SPACE to talk...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Shutting down gracefully...")

    #result = classifier(response)
    #print(result)
    # print result
    # print("\n---convo log:---")
    # print(transcribed_text, response, old_convo)

