import speech_recognition as sr
import pyttsx3
import queue

class ChatBot:
    def __init__(self, event_queue: queue.Queue, mic_index: int = 0):
        self.event_queue = event_queue
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone(device_index=mic_index)
        self.tts = pyttsx3.init()

    def run_loop(self):
        """
        Main loop for chatbot. Listens for two types of events:
        - 'gesture' from the recognizer
        - direct speech from the microphone
        When an event arrives, processes accordingly.
        """
        while True:
            try:
                event_type, payload = self.event_queue.get(timeout=1)
            except queue.Empty:
                # No gesture event: you can optionally trigger listening
                self.listen_and_respond()
                continue

            if event_type == "gesture":
                # handle gesture
                response = self.on_gesture(payload)
                self.speak(response)

    def listen_and_respond(self):
        """
        Block on microphone input, transcribe, get response, and speak.
        """
        with self.mic as source:
            audio = self.recognizer.listen(source, timeout=5)
        try:
            text = self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return
        response = self.on_speech(text)
        self.speak(response)

    def on_gesture(self, gesture_name: str) -> str:
        # TODO: map gestures to responses
        return f"I saw you make the {gesture_name} gesture."

    def on_speech(self, text: str) -> str:
        # TODO: integrate with your chatbot pipeline
        return f"You said: {text}"

    def speak(self, text: str):
        self.tts.say(text)
        self.tts.runAndWait()