import cv2
import mediapipe as mp
import json
import numpy as np
import requests
import tempfile
import os
from playsound import playsound
import time
import threading
import queue
from dotenv import load_dotenv
import pyttsx3
import base64
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)
@app.route('/')
def index():
    return "Flask server is running!"


# -------------------------------
# ElevenLabs API configuration
# -------------------------------
load_dotenv()
ELEVENLABS_API_KEY = os.environ.get("ELEVEN_LABS_KEY")
ELEVENLABS_VOICE_ID = "fCgaP7ly9dCduQaZ4pck"    # Replace with your chosen voice ID

def speak(text):
    """
    Uses ElevenLabs TTS to speak out the provided text.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(response.content)
            tmp_filename = tmp_file.name
        playsound(tmp_filename)
        os.remove(tmp_filename)
    else:
        print("Error with ElevenLabs TTS:", response.text)

# -------------------------------
# Load reference pose landmarks
# -------------------------------
with open('landmarks.json', 'r') as f:
    ref_data = json.load(f)

# Define the sequence of poses
pose_sequence = ['warrior.jpg', 'warrrior_II_left.jpg', 'warrrior_II_right.jpg', 'tree.jpg']

# Global state variables
current_pose_index = 0
hold_duration = 5           # seconds to hold each pose
pose_transition_delay = 5   # seconds between poses
in_transition = True
routine_complete = False
latest_pose_achieved_time = None
prev_feedback_time = 0
transition_start_time = time.time()
latest_pose_landmarks = None

# -------------------------------
# Initialize MediaPipe Pose
# -------------------------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Set custom drawing specifications
landmark_drawing_spec = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=4, circle_radius=6)
connection_drawing_spec = mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=4, circle_radius=2)

# -------------------------------
# Thresholds for movement
# -------------------------------
x_threshold = 0.12
y_threshold = 0.12

# Simplified body parts mapping
body_parts = {
    'ARM': {
        'LEFT': ['LEFT_WRIST', 'LEFT_ELBOW', 'LEFT_SHOULDER'],
        'RIGHT': ['RIGHT_WRIST', 'RIGHT_ELBOW', 'RIGHT_SHOULDER']
    },
    'LEG': {
        'LEFT': ['LEFT_ANKLE', 'LEFT_KNEE', 'LEFT_HIP'],
        'RIGHT': ['RIGHT_ANKLE', 'RIGHT_KNEE', 'RIGHT_HIP']
    }
}

def get_direction_feedback(user_landmarks, ref_landmarks):
    """
    Compare arms and legs positions between user's pose and reference.
    Returns the most important feedback message.
    """
    all_feedback = []
    
    # Check each limb (arms and legs)
    for limb_type, sides in body_parts.items():
        for side, landmarks in sides.items():
            # Ensure all required landmarks exist before computing averages
            if all(lm in user_landmarks for lm in landmarks) and all(lm in ref_landmarks for lm in landmarks):
                user_x = np.mean([user_landmarks[lm][0] for lm in landmarks])
                user_y = np.mean([user_landmarks[lm][1] for lm in landmarks])
                ref_x = np.mean([ref_landmarks[lm][0] for lm in landmarks])
                ref_y = np.mean([ref_landmarks[lm][1] for lm in landmarks])
                
                diff_x = user_x - ref_x
                diff_y = user_y - ref_y
                
                description = f"{side.lower()} {limb_type.lower()}"
                
                if abs(diff_x) > x_threshold:
                    direction = "left" if diff_x > 0 else "right"
                    all_feedback.append({
                        'part': description,
                        'message': f"Move your {description} {direction}",
                        'diff': abs(diff_x)
                    })
                
                if abs(diff_y) > y_threshold:
                    direction = "up" if diff_y > 0 else "down"
                    all_feedback.append({
                        'part': description,
                        'message': f"Move your {description} {direction}",
                        'diff': abs(diff_y)
                    })
    
    if all_feedback:
        all_feedback.sort(key=lambda x: x['diff'], reverse=True)
        return [all_feedback[0]['message']]
    return []

# Thread-safe queue to pass frames to the background processor
frame_queue = queue.Queue(maxsize=1)
global_lock = threading.Lock()

feedback_interval = 2  # seconds between spoken feedback

def background_processing():
    global latest_pose_landmarks, latest_pose_achieved_time, current_pose_index
    global in_transition, transition_start_time, routine_complete, prev_feedback_time
    while not routine_complete:
        try:
            # Get the most recent frame (non-blocking wait)
            frame = frame_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        # Skip processing while in transition (between poses)
        if in_transition:
            frame_queue.task_done()
            continue
        
        # Run pose detection on the frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        
        if results.pose_landmarks:
            user_landmarks = {
                mp_pose.PoseLandmark(i).name: (lm.x, lm.y, lm.z)
                for i, lm in enumerate(results.pose_landmarks.landmark)
            }
            current_pose = pose_sequence[current_pose_index]
            ref_landmarks = ref_data[current_pose]
            feedback_messages = get_direction_feedback(user_landmarks, ref_landmarks)
            current_time = time.time()
            
            if not feedback_messages:
                if latest_pose_achieved_time is None:
                    latest_pose_achieved_time = current_time
                    speak("Perfect! Hold this pose.")
                hold_time = int(current_time - latest_pose_achieved_time)
                if hold_time >= hold_duration:
                    current_pose_index += 1
                    if current_pose_index >= len(pose_sequence):
                        routine_complete = True
                        speak("Congratulations! You've completed the YN Yoga routine!")
                    else:
                        latest_pose_achieved_time = None
                        in_transition = True
                        transition_start_time = current_time
            else:
                if current_time - prev_feedback_time > feedback_interval:
                    speak(feedback_messages[0])
                    prev_feedback_time = current_time
            
            with global_lock:
                latest_pose_landmarks = results.pose_landmarks
        
        frame_queue.task_done()

# Start the background processing thread (daemon thread ends when main thread exits)
processing_thread = threading.Thread(target=background_processing, daemon=True)
processing_thread.start()

# -------------------------------
# Set up OpenCV Windows
# -------------------------------
cv2.namedWindow("Reference Pose", cv2.WINDOW_NORMAL)
cv2.namedWindow("YN Yoga - Live", cv2.WINDOW_NORMAL)
cv2.moveWindow("Reference Pose", 0, 0)
cv2.moveWindow("YN Yoga - Live", 600, 0)

cap = cv2.VideoCapture(0)

while cap.isOpened() and not routine_complete:
    ret, frame = cap.read()
    if not ret:
        break
    
    current_time = time.time()
    current_pose = pose_sequence[current_pose_index]
    ref_img = cv2.imread(current_pose)
    
    # If in transition, overlay a countdown; else, send a frame for processing
    if in_transition:
        remaining = int(transition_start_time + pose_transition_delay - current_time)
        if remaining > 0:
            cv2.rectangle(frame, (20, 20), (500, 100), (0, 0, 0), -1)
            countdown_text = f"Get ready for {current_pose.split('.')[0]}... {remaining}"
            cv2.putText(frame, countdown_text, (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3, cv2.LINE_AA)
            if remaining == pose_transition_delay - 1:
                speak("Alright Next pose: " + current_pose.split('.')[0])
        else:
            in_transition = False
            latest_pose_achieved_time = None
    else:
        # Offer the latest frame for processing if the queue is empty
        if frame_queue.empty():
            frame_queue.put(frame.copy())
        
        # Overlay the pose landmarks computed by the background thread
        with global_lock:
            if latest_pose_landmarks is not None:
                mp_drawing.draw_landmarks(
                    frame,
                    latest_pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec,
                    connection_drawing_spec
                )
        # If a pose has been achieved, show the hold time countdown
        if latest_pose_achieved_time is not None:
            hold_time = int(current_time - latest_pose_achieved_time)
            remaining_hold = hold_duration - hold_time
            if remaining_hold >= 0:
                cv2.rectangle(frame, (20, 20), (500, 100), (0, 0, 0), -1)
                cv2.putText(frame, f"Hold for: {remaining_hold}", (30, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3, cv2.LINE_AA)
    
    # Display the live feed and reference pose
    cv2.imshow("YN Yoga - Live", frame)
    if ref_img is not None:
        ref_img_resized = cv2.resize(ref_img, (frame.shape[1] // 2, frame.shape[0]))
        cv2.imshow("Reference Pose", ref_img_resized)
    
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()