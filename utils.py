import sys
import os
import cv2
import numpy as np

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.framework.formats import landmark_pb2

import start


def list_camera_ports():
    """
    Test camera the ports and returns a tuple with the available ports and the ones that are working.

    can be used to find out what number to put in here
    |
    |
    v
    cv2.VideoCapture(0)
    """
    non_working_ports = []
    dev_port = 0
    working_ports = []
    available_ports = []
    while len(non_working_ports) < 6:  # if there are more than 5 non working ports stop the testing.
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            non_working_ports.append(dev_port)
            print("Port %s is not working." % dev_port)
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                print("[%s]\t Port is working and reads images (%s x %s)" % (dev_port, h, w))
                working_ports.append(dev_port)
                print("camera running at: ", camera.get(cv2.CAP_PROP_FPS))  # TODO: might break
            else:
                print("Port %s for camera ( %s x %s) is present but does not reads." % (dev_port, h, w))
                available_ports.append(dev_port)
        dev_port += 1
    return available_ports, working_ports, non_working_ports


BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
VisionRunningMode = mp.tasks.vision.RunningMode


class BlossomRobot:
    def __init__(self):
        self.options = None
        self.out_frame = np.array([])  # FIXME:

    def visualizer(self, result: GestureRecognizerResult, output_image: mp.Image):
        mp_hands = mp.solutions.hands
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles

        for hand_landmarks in result.hand_landmarks:
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            hand_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
            ])

            self.out_frame = output_image.numpy_view().copy()
            mp_drawing.draw_landmarks(self.out_frame,
                                      hand_landmarks_proto,
                                      mp_hands.HAND_CONNECTIONS,
                                      mp_drawing_styles.get_default_hand_landmarks_style(),
                                      mp_drawing_styles.get_default_hand_connections_style())

    def init_robot(self):
        try:
            start.imported_main(start.parse_args(sys.argv[1:]))
        except:
            print("robot probably not connected")
            exit(1)

    def init_model(self, path, callback_func):
        path = os.path.join(os.getcwd(), path)
        self.options = GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=path),
            running_mode=VisionRunningMode.LIVE_STREAM,
            result_callback=callback_func)

    def run_seq(self, seq):
        for bot in start.robots:
            if bot.seq_thread != None and bot.seq_thread.is_alive():
                continue
            print("playing:", seq)
            bot.play_recording(seq, idler=False)


model = BlossomRobot()


def init_model(path, run):
    """
    initializes the gesture recognizer model
    """

    def guard(result, output_image, timestamp_ms):
        if len(result.hand_world_landmarks) == 0:  # checks if gesture is detected
            return
        run(result, output_image, timestamp_ms)

    model.init_model(path, guard)


def init_robot():
    """
    initialized the blossom robot
    """
    model.init_robot()


def run_seq(seq):
    """
    runs the string seqence

    Args:
        seq: string for program sequence
    """
    model.run_seq(seq)


def visualizer(result: GestureRecognizerResult, output_image: mp.Image):
    """
    Draws the hand tracking landmarks on top of output_image

    Args:
        result: detected hand landmark object
        output_image: image from the camera
    """
    model.visualizer(result, output_image)

