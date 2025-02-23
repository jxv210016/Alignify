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
ELEVENLABS_VOICE_ID = "fCgaP7ly9dCduQaZ4pck"  # Replace with your chosen voice ID

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

# -------------------------------
# Initialize MediaPipe Pose
# -------------------------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Set custom drawing specifications (unused in API mode)
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

# -------------------------------
# API Endpoint to Process a Single Frame
# -------------------------------
@app.route('/process_frame', methods=['POST'])
def process_frame_endpoint():
    """
    Expects a JSON payload with key "image" containing a base64‑encoded image.
    Returns a JSON response with feedback text.
    """
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400

    image_data = data['image']
    # Remove header (if present) from base64 string.
    if ',' in image_data:
        _, encoded = image_data.split(',', 1)
    else:
        encoded = image_data

    try:
        image_bytes = base64.b64decode(encoded)
    except Exception:
        return jsonify({'error': 'Invalid image encoding'}), 400

    try:
        image = Image.open(io.BytesIO(image_bytes))
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    except Exception:
        return jsonify({'error': 'Failed to process image'}), 500

    # Process the frame with MediaPipe.
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frame_rgb)
    response = {}
    if results.pose_landmarks:
        user_landmarks = {
            mp_pose.PoseLandmark(i).name: (lm.x, lm.y, lm.z)
            for i, lm in enumerate(results.pose_landmarks.landmark)
        }
        current_pose = pose_sequence[current_pose_index]
        ref_landmarks = ref_data[current_pose]
        feedback_messages = get_direction_feedback(user_landmarks, ref_landmarks)
        if feedback_messages:
            response['display'] = feedback_messages[0]
        else:
            response['display'] = "Perfect! Hold this pose."
    else:
        response['display'] = "No pose detected"
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
