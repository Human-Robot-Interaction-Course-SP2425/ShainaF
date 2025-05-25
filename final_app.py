import cv2 as cv
import csv
import copy
import time
import argparse
import itertools
from collections import Counter, deque
import numpy as np
import mediapipe as mp
import queue

from utils import CvFpsCalc
from model import KeyPointClassifier, PointHistoryClassifier
from utilities import init_robot, run_seq

import os
import time
import queue
import threading

# Speech side‐deps
import speech_recognition as sr
import pyttsx3
import openai
from transformers import pipeline
import random
import json
from openai import OpenAI
from dotenv import load_dotenv
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



hand_to_seq = {
    "Open": "reset",
    "Close": "sad_shrink",
    "OK": "happy_nodding",
    "Peace": "happy_head_bobbing",
    "Love": "happy_dance",
    "Loser": "anger",
    "Good": "happy_nodding",
    "Bad": "sad_down",
}


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--use_static_image_mode", action="store_true")
    parser.add_argument("--min_detection_confidence", type=float, default=0.7)
    parser.add_argument("--min_tracking_confidence", type=float, default=0.5)
    return parser.parse_args()


class HandGestureRecognizer:
    def __init__(
        self,
        event_queue: queue.Queue,
        device: int = 0,
        width: int = 960,
        height: int = 540,
        use_static_image_mode: bool = False,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
        history_length: int = 16,
    ):
        self.event_queue = event_queue
        # camera setup
        self.cap = cv.VideoCapture(device)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
        # MediaPipe hands
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=use_static_image_mode,
            max_num_hands=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        # classifiers
        self.keypoint_classifier = KeyPointClassifier()
        self.point_classifier = PointHistoryClassifier()
        # labels
        self.keypoint_labels = self._load_labels(
            'model/keypoint_classifier/keypoint_classifier_label.csv')
        self.point_labels = self._load_labels(
            'model/point_history_classifier/point_history_classifier_label.csv')
        # FPS
        self.cvFpsCalc = CvFpsCalc(buffer_len=10)
        # history buffers
        self.point_history = deque(maxlen=history_length)
        self.gesture_history = deque(maxlen=history_length)
        self.use_brect = True

    def _load_labels(self, path: str):
        with open(path, encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            return [row[0] for row in reader]

    def run(self):
        while True:
            fps = self.cvFpsCalc.get()
            key = cv.waitKey(10)
            if key == 27:  # ESC -> exit
                break
            number, mode = select_mode(key, 0)

            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv.flip(frame, 1)
            debug = copy.deepcopy(frame)

            # process
            rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = self.hands.process(rgb)
            rgb.flags.writeable = True

            debug = self._draw_and_detect(debug, results, mode, number, fps)
            cv.imshow('Hand Gesture Recognition', debug)

        self.cap.release()
        cv.destroyAllWindows()

    def _draw_and_detect(self, image, results, mode, number, fps):
        # update history
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks, results.multi_handedness
            ):
                brect = calc_bounding_rect(image, hand_landmarks)
                landmark_list = calc_landmark_list(image, hand_landmarks)

                pre_landmarks = pre_process_landmark(landmark_list)
                pre_history = pre_process_point_history(image, self.point_history)
                logging_csv(number, mode, pre_landmarks, pre_history)

                sign_id = self.keypoint_classifier(pre_landmarks)
                if sign_id == 2:
                    self.point_history.append(landmark_list[8])
                else:
                    self.point_history.append([0, 0])

                fg_id = 0
                if len(pre_history) == (len(self.point_history) * 2):
                    fg_id = self.point_classifier(pre_history)
                self.gesture_history.append(fg_id)

                # draw overlays
                image = draw_bounding_rect(self.use_brect, image, brect)
                image = draw_landmarks(image, landmark_list)
                common_fg = Counter(self.gesture_history).most_common(1)[0][0]
                image = draw_info_text(
                    image,
                    brect,
                    handedness,
                    self.keypoint_labels[sign_id],
                    self.point_labels[common_fg],
                )

                # emit event
                if sign_id != 2:
                    label = self.keypoint_labels[sign_id]
                    seq = hand_to_seq.get(label)
                    if seq:
                        self.event_queue.put(("gesture", seq))
                        run_seq(seq)
                        time.sleep(5)
        else:
            self.point_history.append([0, 0])

        image = draw_point_history(image, self.point_history)
        image = draw_info(image, fps, mode, number)
        return image

def select_mode(key, mode):
    number = -1
    if 48 <= key <= 57:  # 0 ~ 9
        number = key - 48
    if key == 110:  # n
        mode = 0
    if key == 107:  # k
        mode = 1
    if key == 104:  # h
        mode = 2
    return number, mode

def calc_bounding_rect(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_array = np.empty((0, 2), int)

    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)

        landmark_point = [np.array((landmark_x, landmark_y))]

        landmark_array = np.append(landmark_array, landmark_point, axis=0)

    x, y, w, h = cv.boundingRect(landmark_array)

    return [x, y, x + w, y + h]

def calc_landmark_list(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_point = []

    # Keypoint
    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        # landmark_z = landmark.z

        landmark_point.append([landmark_x, landmark_y])

    return landmark_point

def pre_process_landmark(landmark_list):
    temp_landmark_list = copy.deepcopy(landmark_list)

    # Convert to relative coordinates
    base_x, base_y = 0, 0
    for index, landmark_point in enumerate(temp_landmark_list):
        if index == 0:
            base_x, base_y = landmark_point[0], landmark_point[1]

        temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
        temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y

    # Convert to a one-dimensional list
    temp_landmark_list = list(
        itertools.chain.from_iterable(temp_landmark_list))

    # Normalization
    max_value = max(list(map(abs, temp_landmark_list)))

    def normalize_(n):
        return n / max_value

    temp_landmark_list = list(map(normalize_, temp_landmark_list))

    return temp_landmark_list


def pre_process_point_history(image, point_history):
    image_width, image_height = image.shape[1], image.shape[0]

    temp_point_history = copy.deepcopy(point_history)

    # Convert to relative coordinates
    base_x, base_y = 0, 0
    for index, point in enumerate(temp_point_history):
        if index == 0:
            base_x, base_y = point[0], point[1]

        temp_point_history[index][0] = (temp_point_history[index][0] -
                                        base_x) / image_width
        temp_point_history[index][1] = (temp_point_history[index][1] -
                                        base_y) / image_height

    # Convert to a one-dimensional list
    temp_point_history = list(
        itertools.chain.from_iterable(temp_point_history))

    return temp_point_history


def logging_csv(number, mode, landmark_list, point_history_list):
    if mode == 0:
        pass
    if mode == 1 and (0 <= number <= 9):
        csv_path = 'model/keypoint_classifier/keypoint.csv'
        with open(csv_path, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([number, *landmark_list])
    if mode == 2 and (0 <= number <= 9):
        csv_path = 'model/point_history_classifier/point_history.csv'
        with open(csv_path, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([number, *point_history_list])
    return


def draw_landmarks(image, landmark_point):
    if len(landmark_point) > 0:
        # Thumb
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[3]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[3]), tuple(landmark_point[4]),
                (255, 255, 255), 2)

        # Index finger
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[6]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[6]), tuple(landmark_point[7]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[7]), tuple(landmark_point[8]),
                (255, 255, 255), 2)

        # Middle finger
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[10]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[10]), tuple(landmark_point[11]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[11]), tuple(landmark_point[12]),
                (255, 255, 255), 2)

        # Ring finger
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[14]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[14]), tuple(landmark_point[15]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[15]), tuple(landmark_point[16]),
                (255, 255, 255), 2)

        # Little finger
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[18]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[18]), tuple(landmark_point[19]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[19]), tuple(landmark_point[20]),
                (255, 255, 255), 2)

        # Palm
        cv.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[0]), tuple(landmark_point[1]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[1]), tuple(landmark_point[2]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[2]), tuple(landmark_point[5]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[5]), tuple(landmark_point[9]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[9]), tuple(landmark_point[13]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[13]), tuple(landmark_point[17]),
                (255, 255, 255), 2)
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
                (0, 0, 0), 6)
        cv.line(image, tuple(landmark_point[17]), tuple(landmark_point[0]),
                (255, 255, 255), 2)

    # Key Points
    for index, landmark in enumerate(landmark_point):
        if index == 0:  # 手首1
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 1:  # 手首2
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 2:  # 親指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 3:  # 親指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 4:  # 親指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 5:  # 人差指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 6:  # 人差指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 7:  # 人差指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 8:  # 人差指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 9:  # 中指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 10:  # 中指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 11:  # 中指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 12:  # 中指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 13:  # 薬指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 14:  # 薬指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 15:  # 薬指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 16:  # 薬指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)
        if index == 17:  # 小指：付け根
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 18:  # 小指：第2関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 19:  # 小指：第1関節
            cv.circle(image, (landmark[0], landmark[1]), 5, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 5, (0, 0, 0), 1)
        if index == 20:  # 小指：指先
            cv.circle(image, (landmark[0], landmark[1]), 8, (255, 255, 255),
                      -1)
            cv.circle(image, (landmark[0], landmark[1]), 8, (0, 0, 0), 1)

    return image


def draw_bounding_rect(use_brect, image, brect):
    if use_brect:
        # Outer rectangle
        cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[3]),
                     (0, 0, 0), 1)

    return image


def draw_info_text(image, brect, handedness, hand_sign_text,
                   finger_gesture_text):
    cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22),
                 (0, 0, 0), -1)

    info_text = handedness.classification[0].label[0:]
    if hand_sign_text != "":
        info_text = info_text + ':' + hand_sign_text
    cv.putText(image, info_text, (brect[0] + 5, brect[1] - 4),
               cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)

    if finger_gesture_text != "":
        cv.putText(image, "Finger Gesture:" + finger_gesture_text, (10, 60),
                   cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv.LINE_AA)
        cv.putText(image, "Finger Gesture:" + finger_gesture_text, (10, 60),
                   cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2,
                   cv.LINE_AA)

    return image

def draw_point_history(image, point_history):
    for index, point in enumerate(point_history):
        if point[0] != 0 and point[1] != 0:
            cv.circle(image, (point[0], point[1]), 1 + int(index / 2),
                      (152, 251, 152), 2)

    return image


def draw_info(image, fps, mode, number):
    cv.putText(image, "FPS:" + str(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX,
               1.0, (0, 0, 0), 4, cv.LINE_AA)
    cv.putText(image, "FPS:" + str(fps), (10, 30), cv.FONT_HERSHEY_SIMPLEX,
               1.0, (255, 255, 255), 2, cv.LINE_AA)

    mode_string = ['Logging Key Point', 'Logging Point History']
    if 1 <= mode <= 2:
        cv.putText(image, "MODE:" + mode_string[mode - 1], (10, 90),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                   cv.LINE_AA)
        if 0 <= number <= 9:
            cv.putText(image, "NUM:" + str(number), (10, 110),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                       cv.LINE_AA)
    return image

#—————————————————————————————————————————————
# ChatBot
#—————————————————————————————————————————————
openai.api_key = os.getenv("OPENAI_API_KEY")

class ChatBot:
    def __init__(self, event_queue: queue.Queue, mic_index=0,
                 system_prompt=None):
        self.emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None
        )
        self.preprompt = """
        Keep this response as a short and concise message as if you
        were talking to someone one to one.
        The following text has been taking in from an audio transcription
        so also watch out for weird spellings:
        """
        load_dotenv(override=True)
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.pipeline_queue = queue.Queue()
        self.event_queue = event_queue
        self.recognizer = sr.Recognizer()
        self.mic        = sr.Microphone(device_index=mic_index)
        self.system_prompt = system_prompt or (
            "You are a friendly assistant that responds concisely to user speech "
            "and adapts responses to human gestures."
        )
        self.listening = True
        self.listen_thread = threading.Thread(
            target=self._background_listen, daemon=True
        )
        self.listen_thread.start()
    
    def run_pipeline_loop(self):
        while True:
            text = self.pipeline_queue.get()
            print(f"[pipeline thread] Received input: {text}")
            try:
                response = self.run_pipline(text)
                self.speak(response)  # this goes to TTS queue (which is non-blocking)
            except Exception as e:
                print(f"[pipeline thread] Error: {e}")


    def run_loop(self):
        """ Handle incoming gesture events """
        while True:
            event_type, payload = self.event_queue.get()
            if event_type == "gesture":
                resp = self.on_gesture(payload)
                
    
    def load_all_movements(self, directory=".\src\sequences\woody"):
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

    def select_movement(self, emotion: str, confidence: float, movement_library: list):
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
    
    def run_pipline(self, text, chat_model="gpt-4o-mini", text2speech_model="tts-1",
                    text2speech_voice="alloy"):
        print("---")
        # print(f"output file: {res}")
       

        
        print(f"[transcribed text]: {text}")

        text_response = self.prompt_gpt(text, self.preprompt, chat_model)
        print(f"[{chat_model} response]: {text_response}")
        

        top_result = self.emotion_classifier(text_response)[0]
        top_emotion_data = sorted(top_result, key=lambda x: x['score'], reverse=True)[0]
        top_emotion = top_emotion_data['label']
        confidence_score = top_emotion_data['score']

        print(f"Top emotion: {top_emotion} ({confidence_score:.2f})")

        movement_library = self.load_all_movements()

        movement = self.select_movement(top_emotion, confidence_score, movement_library)
        filename = self.text2speech(text_response, text2speech_model, text2speech_voice)

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

        #filename = self.text2speech(text_response, text2speech_model, text2speech_voice)
        # print(f"output file {filename}")
        

        self.preprompt += f"""
        past input:
            {text}
        past response:
            {text_response}\n
        """

        
    
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
    
    

    def _background_listen(self):
        with self.mic as src:
            self.recognizer.adjust_for_ambient_noise(src)
        while self.listening:
            with self.mic as src:
                print("[Listening for speech...]")
                try:
                    audio = self.recognizer.listen(src, timeout=5)
                except sr.WaitTimeoutError:
                    print("[Timeout — no speech detected]")
                    continue
            try:
                text = self.recognizer.recognize_google(audio)
                print("[Recognized]:", text)
            except sr.UnknownValueError:
                print("[Could not understand audio]")
                continue
            except sr.RequestError as e:
                print(f"[Recognition error: {e}]")
                continue

            response = self.on_speech(text)


    def on_gesture(self, gesture_name):
        msgs = [
            {"role":"system","content":self.system_prompt},
            {"role":"user","content":f"User made gesture: {gesture_name}"}
        ]
        try:
            c = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=msgs,
                max_tokens=100, temperature=0.7
            )
            return c.choices[0].message.content.strip()
        except Exception as e:
            return f"[Gesture error: {e}]"

    def on_speech(self, text):
        print(f"[on_speech] Received: {text}")
        self.pipeline_queue.put(text)


    def stop(self):
        self.listening = False
        self.listen_thread.join()


#—————————————————————————————————————————————
# Integration Manager & Entry Point
#—————————————————————————————————————————————
class InteractionManager:
    def __init__(self, mic_index=0, cam_index=0):
        self.event_queue = queue.Queue()
        self.gesture = HandGestureRecognizer(self.event_queue,
                                             device=cam_index)
        self.chatbot = ChatBot(self.event_queue,
                               mic_index=mic_index)

    def start(self):
        threads = [
            threading.Thread(target=self.gesture.run,   name="GestureThread"),
            threading.Thread(target=self.chatbot.run_loop, name="ChatbotThread"),
            threading.Thread(target=self.chatbot.run_pipeline_loop, name="PipelineThread", daemon=True),
        ]
        for t in threads:
            t.daemon = True
            t.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
            self.chatbot.stop()

if __name__ == "__main__":
    # parse any CLI args here if you like (e.g. argparse for mic/cam indices)
    init_robot()
    mgr = InteractionManager(mic_index=0, cam_index=0)
    mgr.start()