from deepface import DeepFace
import cv2
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
 

def main(): 
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
 
        # Analyze emotions
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
 
        # Print result
        dominant_emotion = result[0]["dominant_emotion"]
        print("Emotion:", dominant_emotion)
        confidence = result[0]["emotion"][dominant_emotion]
        print("Emotion confidences:", confidence/100)

        if dominant_emotion == "happy":
            mapped_emotion = "joy"
        elif dominant_emotion == "sad":
            mapped_emotion = "sadness"
        elif dominant_emotion == "angry":
            mapped_emotion = "anger"
        else:
            mapped_emotion = dominant_emotion

        movement_library = load_all_movements()

        movement = select_movement(mapped_emotion, confidence/100, movement_library)

        if movement:
            print(f"Selected: {movement['filename']} ({movement['emotion_strength']})")
            print(movement['animation'])
            run_seq(movement['animation'])
            time.sleep(5)
            run_seq('reset')
            time.sleep(5)
        # Send movement["frame_list"] to robot
        else:
            print("No suitable movement found.")
 
    # Display webcam feed
        cv2.imshow("Emotion Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    init_robot()
    while True:
        main()
