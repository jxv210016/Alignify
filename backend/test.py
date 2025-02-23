import sys
import cv2
import mediapipe as mp
import numpy as np
import json
import requests
import tempfile
import os
import time
from playsound import playsound
from dotenv import load_dotenv

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QProgressBar, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QFont

# -------------------------------
# ElevenLabs TTS configuration
# -------------------------------
load_dotenv()
ELEVENLABS_API_KEY = "sk_d99fbd27f466d8e06fe48c2fc497442b60d9cf5c048d52af"
ELEVENLABS_VOICE_ID = "IKne3meq5aSn9XLyUdCD"  # Replace with your chosen voice ID

def speak(text):
    """Uses ElevenLabs TTS to speak the provided text."""
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
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(response.content)
                tmp_filename = tmp_file.name
            playsound(tmp_filename)
            os.remove(tmp_filename)
        else:
            print("Error with ElevenLabs TTS:", response.text)
    except Exception as e:
        print("TTS Exception:", e)

# -------------------------------
# MediaPipe Pose initialization
# -------------------------------
mp_pose = mp.solutions.pose
pose_detector = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# -------------------------------
# Drawing specifications for landmarks
# -------------------------------
landmark_drawing_spec = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=4, circle_radius=6)
connection_drawing_spec = mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=4, circle_radius=2)

# -------------------------------
# Feedback thresholds and body parts mapping
# -------------------------------
x_threshold = 0.1
y_threshold = 0.1

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
    Note: The horizontal feedback is inverted to account for the mirrored display.
    """
    all_feedback = []
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
                # Invert horizontal direction because the image is mirrored.
                if abs(diff_x) > x_threshold:
                    direction = "left" if diff_x < 0 else "right"
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
        return all_feedback[0]['message']
    return None

def convert_frame_to_qpixmap(frame):
    """Convert an OpenCV BGR frame to QPixmap."""
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = frame_rgb.shape
    bytes_per_line = ch * w
    qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
    return QPixmap.fromImage(qt_image)

# -------------------------------
# Main Application Class
# -------------------------------
class YogaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YN Yoga - Guided Session")
        self.showFullScreen()  # Full-screen mode
        
        # Set global font to Arial
        global_font = QFont("Arial", 12)
        
        # Header label
        self.header_label = QLabel("YN Yoga Guided Session")
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.header_label.setStyleSheet("background-color: #005F99; color: white; padding: 10px;")
        
        # Create UI elements
        self.live_feed_label = QLabel()
        self.live_feed_label.setAlignment(Qt.AlignCenter)
        self.live_feed_label.setStyleSheet("background-color: #000;")
        self.live_feed_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.live_feed_label.setFont(global_font)
        
        self.ref_pose_label = QLabel()
        self.ref_pose_label.setAlignment(Qt.AlignCenter)
        self.ref_pose_label.setStyleSheet("background-color: #222; color: #fff;")
        self.ref_pose_label.setFixedWidth(300)  # Fixed panel on right
        self.ref_pose_label.setFont(global_font)
        
        self.status_label = QLabel("Status: Starting up...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setStyleSheet("color: #007ACC; padding: 5px;")
        
        self.start_button = QPushButton("Start Session")
        self.start_button.setFont(global_font)
        self.start_button.setStyleSheet("padding: 10px; background-color: #28A745; color: white;")
        self.start_button.clicked.connect(self.on_start_button)
        self.start_button.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(4)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Calibration: %v / %m")
        self.progress_bar.setFont(global_font)
        self.progress_bar.setStyleSheet("padding: 5px;")
        
        # Layout for main video and reference panel
        video_layout = QHBoxLayout()
        video_layout.addWidget(self.live_feed_label, 1)
        video_layout.addWidget(self.ref_pose_label)
        
        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.header_label)
        main_layout.addLayout(video_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.start_button)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # Camera capture
        self.cap = cv2.VideoCapture(0)
        
        # Timer for updating UI (approx. 30 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        
        # Phases:
        # 'warmup', 'calibration', 'calibration_delay', 'calibration_complete',
        # 'session_countdown', 'session', 'session_delay', 'completed'
        self.phase = "warmup"
        self.phase_start_time = time.time()
        self.warmup_duration = 5
        
        speak("Welcome to YN Yoga. Get ready for a warm-up.")
        
        # Calibration settings with overlay images
        self.calibration_poses = [
            {"name": "Warrior 1", "file": "calibration/Cal_WarriorI.png"},
            {"name": "Warrior 2", "file": "calibration/Cal_WarriorII.png"},
            {"name": "Star", "file": "calibration/Cal_Star.png"},
            {"name": "Goddess", "file": "calibration/Cal_Goddess.png"}
        ]
        self.baseline_capture_delay = 5
        self.current_calibration_index = 0
        self.baseline_landmarks = {}
        self.baseline_images = {}
        
        # Delay after capture before next calibration pose: 5 seconds
        self.calibration_post_delay = 5
        # Initial delay for first calibration pose: 5 seconds
        self.calibration_initial_delay = 5
        
        self.session_countdown_duration = 10
        
        # Guided session settings
        self.session_hold_duration = 5
        self.pose_transition_delay = 5
        self.session_post_delay = 2
        self.current_pose_index = 0
        self.latest_pose_time = None
        self.prev_feedback_time = 0
        self.feedback_interval = 2
        
        self.current_ref_image = np.zeros((480, 320, 3), dtype=np.uint8)
        cv2.putText(self.current_ref_image, "Reference", (10, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
    
    def on_start_button(self):
        self.phase = "session_countdown"
        self.phase_start_time = time.time()
        self.status_label.setText("Status: Session starting soon...")
        self.start_button.setEnabled(False)
        speak("Calibration complete. Get ready for your guided yoga session!")
    
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        overlay = frame.copy()
        current_time = time.time()
        
        # --- Phase: Warmup ---
        if self.phase == "warmup":
            remaining = int(self.warmup_duration - (current_time - self.phase_start_time))
            cv2.putText(overlay, f"Warm-up: Starting in {remaining}", (30, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,0), 3, cv2.LINE_AA)
            self.status_label.setText("Status: Warm-up")
            if remaining <= 0:
                self.phase = "calibration"
                self.phase_start_time = current_time
                speak("Warm-up complete. Let's begin calibration. Please mimic the pose shown on the screen.")
        
        # --- Phase: Calibration ---
        elif self.phase == "calibration":
            if self.current_calibration_index < len(self.calibration_poses):
                current_calib = self.calibration_poses[self.current_calibration_index]
                pose_name = current_calib["name"]
                if self.current_calibration_index == 0 and (current_time - self.phase_start_time) < self.calibration_initial_delay:
                    remaining = int(self.calibration_initial_delay - (current_time - self.phase_start_time))
                    cv2.putText(overlay, f"Get ready for {pose_name} in {remaining}", (30, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,255), 3, cv2.LINE_AA)
                    self.status_label.setText(f"Status: Prepare for {pose_name}")
                else:
                    if self.current_calibration_index == 0:
                        capture_start = self.phase_start_time + self.calibration_initial_delay
                        remaining = int(self.baseline_capture_delay - (current_time - capture_start))
                    else:
                        remaining = int(self.baseline_capture_delay - (current_time - self.phase_start_time))
                    cv2.putText(overlay, f"Calibrate: {pose_name}", (30, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,255), 3, cv2.LINE_AA)
                    cv2.putText(overlay, f"Capturing in: {remaining}", (30, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3, cv2.LINE_AA)
                    self.status_label.setText(f"Status: Calibrating {pose_name}")
                
                calib_path = current_calib["file"]
                calib_overlay = cv2.imread(calib_path, cv2.IMREAD_UNCHANGED)
                if calib_overlay is None:
                    print(f"Warning: Calibration image not found at {calib_path}")
                else:
                    desired_width = overlay.shape[1] // 3
                    scale = desired_width / calib_overlay.shape[1]
                    new_height = int(calib_overlay.shape[0] * scale)
                    calib_overlay = cv2.resize(calib_overlay, (desired_width, new_height))
                    x_offset = overlay.shape[1] - calib_overlay.shape[1] - 20
                    y_offset = 20
                    if calib_overlay.shape[2] == 4:
                        alpha_s = calib_overlay[:, :, 3] / 255.0
                        alpha_l = 1.0 - alpha_s
                        for c in range(0, 3):
                            overlay[y_offset:y_offset+calib_overlay.shape[0],
                                    x_offset:x_offset+calib_overlay.shape[1], c] = (
                                alpha_s * calib_overlay[:, :, c] +
                                alpha_l * overlay[y_offset:y_offset+calib_overlay.shape[0],
                                                  x_offset:x_offset+calib_overlay.shape[1], c]
                            )
                    else:
                        overlay[y_offset:y_offset+calib_overlay.shape[0],
                                x_offset:x_offset+calib_overlay.shape[1]] = calib_overlay
                
                if self.current_calibration_index == 0 and (current_time - self.phase_start_time) < (self.calibration_initial_delay + self.baseline_capture_delay):
                    pass
                elif remaining <= 0:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = pose_detector.process(frame_rgb)
                    if results.pose_landmarks:
                        landmarks = { mp_pose.PoseLandmark(i).name: (lm.x, lm.y, lm.z)
                                      for i, lm in enumerate(results.pose_landmarks.landmark) }
                        self.baseline_landmarks[pose_name] = landmarks
                        self.baseline_images[pose_name] = frame.copy()
                        self.current_ref_image = frame.copy()
                        speak(f"{pose_name} calibrated.")
                        self.progress_bar.setValue(self.current_calibration_index + 1)
                        self.phase = "calibration_delay"
                        self.phase_start_time = current_time
                    else:
                        speak(f"Pose not detected for {pose_name}. Please try again.")
                        return
            
            # --- Phase: Calibration Delay ---
        elif self.phase == "calibration_delay":
            remaining = int(self.calibration_post_delay - (current_time - self.phase_start_time))
            cv2.putText(overlay, f"Next pose in {remaining}", (30, 180),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 3, cv2.LINE_AA)
            self.status_label.setText("Status: Preparing next calibration pose")
            if remaining <= 0:
                self.current_calibration_index += 1
                if self.current_calibration_index < len(self.calibration_poses):
                    speak(f"Get ready for {self.calibration_poses[self.current_calibration_index]['name']}.")
                    self.phase = "calibration"
                    self.phase_start_time = current_time
                else:
                    with open('landmarks.json', 'w') as f:
                        json.dump(self.baseline_landmarks, f)
                    self.status_label.setText("Status: Calibration complete.")
                    self.start_button.setEnabled(True)
                    speak("Calibration complete. Press Start Session when you're ready.")
                    self.phase = "calibration_complete"
        
        # --- Phase: Session Countdown ---
        elif self.phase == "session_countdown":
            remaining = int(self.session_countdown_duration - (current_time - self.phase_start_time))
            cv2.putText(overlay, f"Session starts in: {remaining}", (30, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,0), 3, cv2.LINE_AA)
            self.status_label.setText("Status: Get ready for your session")
            if remaining <= 0:
                self.phase = "session"
                self.phase_start_time = current_time
                self.current_pose_index = 0
                self.latest_pose_time = None
                speak("Let's begin your yoga session!")
                first_pose = self.calibration_poses[self.current_pose_index]["name"]
                self.current_ref_image = self.baseline_images.get(first_pose, self.current_ref_image)
        
        # --- Phase: Session (Guided) ---
        elif self.phase == "session":
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose_detector.process(frame_rgb)
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    overlay,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec,
                    connection_drawing_spec
                )
                user_landmarks = { mp_pose.PoseLandmark(i).name: (lm.x, lm.y, lm.z)
                                   for i, lm in enumerate(results.pose_landmarks.landmark) }
                current_pose = self.calibration_poses[self.current_pose_index]["name"]
                ref_landmarks = self.baseline_landmarks.get(current_pose)
                feedback = None
                if ref_landmarks:
                    feedback = get_direction_feedback(user_landmarks, ref_landmarks)
                if feedback:
                    if current_time - self.prev_feedback_time > self.feedback_interval:
                        speak(feedback)
                        self.prev_feedback_time = current_time
                    self.latest_pose_time = None  # reset hold timer if feedback is issued
                else:
                    if self.latest_pose_time is None:
                        self.latest_pose_time = current_time
                        speak("Perfect! Hold this pose.")
                    hold_time = int(current_time - self.latest_pose_time)
                    cv2.putText(overlay, f"Hold for: {self.session_hold_duration - hold_time}", (30, 180),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 3, cv2.LINE_AA)
                    if hold_time >= self.session_hold_duration:
                        self.phase = "session_delay"
                        self.phase_start_time = current_time
                        speak(f"Good job on {current_pose}.")
            self.status_label.setText(f"Status: Session - {self.calibration_poses[self.current_pose_index]['name']}")
        
        # --- Phase: Session Delay ---
        elif self.phase == "session_delay":
            remaining = int(self.session_post_delay - (current_time - self.phase_start_time))
            cv2.putText(overlay, f"Next pose in: {remaining}", (30, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,0,255), 3, cv2.LINE_AA)
            self.status_label.setText("Status: Preparing next pose")
            if remaining <= 0:
                self.current_pose_index += 1
                if self.current_pose_index >= len(self.calibration_poses):
                    self.phase = "completed"
                    speak("Congratulations! You've completed the YN Yoga routine!")
                else:
                    next_pose = self.calibration_poses[self.current_pose_index]["name"]
                    speak(f"Next pose: {next_pose}")
                    self.latest_pose_time = None
                    self.phase = "session"
                    self.phase_start_time = current_time
                    self.current_ref_image = self.baseline_images.get(next_pose, self.current_ref_image)
        
        # --- Phase: Completed ---
        elif self.phase == "completed":
            cv2.putText(overlay, "Routine Completed!", (30, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 4, cv2.LINE_AA)
            self.status_label.setText("Status: Routine Completed")
        
        live_pix = convert_frame_to_qpixmap(overlay)
        self.live_feed_label.setPixmap(live_pix.scaled(
            self.live_feed_label.width(), self.live_feed_label.height(), Qt.KeepAspectRatio))
        ref_pix = convert_frame_to_qpixmap(self.current_ref_image)
        self.ref_pose_label.setPixmap(ref_pix.scaled(
            self.ref_pose_label.width(), self.ref_pose_label.height(), Qt.KeepAspectRatio))
    
    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YogaApp()
    window.show()
    sys.exit(app.exec_())
