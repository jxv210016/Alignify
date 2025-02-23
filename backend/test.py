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
from concurrent.futures import ThreadPoolExecutor
import threading

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QProgressBar, QSizePolicy, QFrame, QScrollArea
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QFont

# -------------------------------
# Load Environment Variables
# -------------------------------
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_f2ab8eeecc9d8654b047f708c2d0d0c3045636f119dd60e5")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "IKne3meq5aSn9XLyUdCD")

# -------------------------------
# TTS Manager for Non-blocking Speech
# -------------------------------
class TTSManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.current_task = None
    
    def speak(self, text):
        """Non-blocking TTS function that runs in a separate thread."""
        def tts_task():
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
        
        # Cancel any existing TTS task
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
        
        # Start new TTS task
        self.current_task = self.executor.submit(tts_task)

# -------------------------------
# MediaPipe Setup
# -------------------------------
mp_pose = mp.solutions.pose
pose_detector = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Drawing specifications
landmark_drawing_spec = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=4, circle_radius=6)
connection_drawing_spec = mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=4, circle_radius=2)

# Feedback thresholds
x_threshold = 0.1
y_threshold = 0.1

body_parts = {
    'ARM': {
        'RIGHT': ['LEFT_WRIST', 'LEFT_ELBOW', 'LEFT_SHOULDER'],
        'LEFT': ['RIGHT_WRIST', 'RIGHT_ELBOW', 'RIGHT_SHOULDER']
    },
    'LEG': {
        'RIGHT': ['LEFT_ANKLE', 'LEFT_KNEE', 'LEFT_HIP'],
        'LEFT': ['RIGHT_ANKLE', 'RIGHT_KNEE', 'RIGHT_HIP']
    }
}
# -------------------------------
# Custom Frontend Widgets
# -------------------------------
class ModernButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Arial", 14))
        self.setMinimumHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2D3142;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #404659;
            }
            QPushButton:pressed {
                background-color: #1F2232;
            }
            QPushButton:disabled {
                background-color: #E5E5E5;
                color: #9E9E9E;
            }
        """)

class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(8)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #F5F5F5;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2D3142;
                border-radius: 4px;
            }
        """)
        self.setTextVisible(False)

class InfoPanel(QFrame):
    """Modern info panel for displaying text, instructions, images, and the Begin button."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
                border: 1px solid #E5E5E5;
            }
            QLabel {
                color: #2D3142;
                padding: 8px;
            }
        """)
        self.setFixedWidth(400)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)
        
        # Title
        self.title = QLabel("Welcome")
        self.title.setFont(QFont("Arial", 18, QFont.Bold))
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignLeft)
        
        # Timer display
        self.timer = QLabel("Timer or Countdowns here")
        self.timer.setFont(QFont("Arial", 24, QFont.Bold))
        self.timer.setAlignment(Qt.AlignCenter)
        self.timer.setStyleSheet("""
            color: #2D3142;
            background-color: #F8F9FA;
            border-radius: 8px;
            padding: 12px;
        """)
        
        # Instructions
        self.instruction = QLabel("Instructions for user")
        self.instruction.setFont(QFont("Arial", 14))
        self.instruction.setWordWrap(True)
        
        # Reference Image
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # BEGIN button
        self.begin_button = ModernButton("Begin")
        self.begin_button.setFixedSize(180, 50)
        self.begin_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 25px;
                padding: 12px 24px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        # Add widgets to layout
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.timer)
        self.layout.addWidget(self.instruction)
        self.layout.addWidget(self.image_label)
        
        # Center the button horizontally
        button_container = QWidget()
        bc_layout = QHBoxLayout()
        bc_layout.addStretch()
        bc_layout.addWidget(self.begin_button)
        bc_layout.addStretch()
        button_container.setLayout(bc_layout)
        
        self.layout.addWidget(button_container)
        self.layout.addStretch()
        
        self.setLayout(self.layout)
    
    def update_info(self, title="", timer="", instruction="", image_path=None):
        """Update panel text and image."""
        self.title.setText(title)
        self.timer.setText(timer)
        self.instruction.setText(instruction)
        
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.clear()


class PoseFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 4px solid black;  /* Adds a 4px black border all around */
                border-radius: 16px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        # Left side: Video container
        video_container = QFrame()
        video_container.setStyleSheet("background-color: transparent; border: none;")
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(1000, 750)
        self.video_label.setStyleSheet("border: none;")
        
        video_layout.addWidget(self.video_label)
        video_container.setLayout(video_layout)
        
        # Right side: Info panel
        self.info_panel = InfoPanel()
        
        layout.addWidget(video_container, 3)  # Expand more
        layout.addWidget(self.info_panel, 1)  # Narrower panel
        self.setLayout(layout)


        # -------------------------------
# Helper Functions
# -------------------------------
def convert_frame_to_qpixmap(frame):
    """Convert an OpenCV BGR frame to QPixmap."""
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = frame_rgb.shape
    bytes_per_line = ch * w
    qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
    return QPixmap.fromImage(qt_image)

def get_direction_feedback(user_landmarks, ref_landmarks):
    """Compare user's pose with reference pose and return feedback."""
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

# -------------------------------
# Main Application Class
# -------------------------------
class YogaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initBackend()
    
    def initUI(self):
        self.showFullScreen()
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QScrollArea {
                border: none;
                background-color: #FFFFFF;
            }
            QWidget {
                background-color: #FFFFFF;
            }
        """)

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # Optional Top Header
        header_label = QLabel("ALIGNIFY")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setFont(QFont("Arial", 48, QFont.Bold))
        header_label.setStyleSheet("color: #2D3142;")
        main_layout.addWidget(header_label)

        # PoseFrame (with video on left, info panel on right)
        self.live_feed = PoseFrame()
        self.live_feed.info_panel.begin_button.clicked.connect(self.start_workout)
        main_layout.addWidget(self.live_feed, stretch=1)


        # Bottom panel for status, progress, and control buttons
        bottom_panel = QFrame()
        bottom_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 12px;
            }
        """)
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(24, 24, 24, 24)
        bottom_layout.setSpacing(24)

        # Left side: status + progress
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(12)

        self.status_label = QLabel("Status: Ready to begin")
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setStyleSheet("color: #2D3142;")

        self.progress_bar = ModernProgressBar()
        self.progress_bar.setMaximum(4)

        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        bottom_layout.addLayout(progress_layout, 2)

        # Right side: Start, Recalibrate, Exit
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(16)

        self.start_button = ModernButton("Start Session")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.on_start_button)

        self.recalibrate_button = ModernButton("Recalibrate")
        self.recalibrate_button.setEnabled(False)
        self.recalibrate_button.clicked.connect(self.on_recalibrate_button)
        self.recalibrate_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #E5E5E5;
                color: #9E9E9E;
            }
        """)

        self.exit_button = ModernButton("Exit")
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
            QPushButton:pressed {
                background-color: #D32F2F;
            }
        """)
        self.exit_button.clicked.connect(self.close)

        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.recalibrate_button)
        buttons_layout.addWidget(self.exit_button)
        bottom_layout.addLayout(buttons_layout, 1)

        bottom_panel.setLayout(bottom_layout)
        main_layout.addWidget(bottom_panel)

        main_widget.setLayout(main_layout)

        # Wrap everything in a scroll area (optional if you need scrolling)
        scroll = QScrollArea()
        scroll.setWidget(main_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        self.setCentralWidget(scroll)

    def initBackend(self):
    # Initialize camera
        self.cap = cv2.VideoCapture(0)
    
    # Initialize TTS manager
        self.tts_manager = TTSManager()
        
        # Start in initial phase instead of warmup
        self.phase = "initial"
        self.phase_start_time = time.time()
        self.warmup_duration = 5
        
        # Calibration settings with correct file paths
        self.calibration_poses = [
            {"name": "Warrior 1", "file": "calibration/Cal_WarriorI.png"},
            {"name": "Warrior 2", "file": "calibration/Cal_WarriorII.png"},
            {"name": "Star", "file": "calibration/Cal_Star.png"},
            {"name": "Goddess", "file": "calibration/Cal_Goddess.png"}
        ]
        self.calibration_initial_delay = 5
        self.baseline_capture_delay = 5
        self.calibration_post_delay = 5
        self.current_calibration_index = 0
        self.baseline_landmarks = {}
        self.baseline_images = {}
        
        # Session settings
        self.session_countdown_duration = 10
        self.session_hold_duration = 5
        self.session_post_delay = 2
        self.current_pose_index = 0
        self.latest_pose_time = None
        self.prev_feedback_time = 0
        self.feedback_interval = 2
        
        # Initial reference image
        self.current_ref_image = None
        
        # Start frame updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def start_workout(self):
        """Start the workout when welcome button is clicked"""
        self.phase = "warmup"
        self.phase_start_time = time.time()
        self.live_feed.info_panel.begin_button.setVisible(False)
        self.tts_manager.speak("Welcome to Alineify. Get ready for your warm-up.")

    def create_welcome_overlay(self, overlay):
        """Create a professional welcome screen overlay with centered text and button"""
        h, w = overlay.shape[:2]
        
        # Create dark overlay with higher opacity
        overlay_layer = overlay.copy()
        overlay_dark = np.zeros((h, w, 3), dtype=np.uint8)
        overlay_dark.fill(0)  # Black background
        alpha = 0.80  # 80% opacity for darker, more professional look
        cv2.addWeighted(overlay_dark, alpha, overlay_layer, 1 - alpha, 0, overlay_layer)
        
        # Add main title "ALIGNIFY"
        font = cv2.FONT_HERSHEY_SIMPLEX
        title = "ALIGNIFY"
        font_scale = 5.0  # Larger text
        thickness = 5
        
        # Get size of the text
        (text_width, text_height), baseline = cv2.getTextSize(
            title, font, font_scale, thickness)
        
        # Calculate center position
        text_x = (w - text_width) // 2
        text_y = (h - text_height) // 2 - 50  # Move text up to make room for button
        
        # Draw title with shadow effect
        cv2.putText(overlay_layer, title, (text_x+3, text_y+3), font, font_scale,
                    (50, 50, 50), thickness)  # Shadow
        cv2.putText(overlay_layer, title, (text_x, text_y), font, font_scale,
                    (255, 255, 255), thickness)  # Main text
        
        return overlay_layer

    def create_countdown_overlay(self, overlay, countdown_number):
        """Create a semi-transparent overlay with large countdown numbers in a modern font"""
        h, w = overlay.shape[:2]
        
        # Create semi-transparent dark overlay
        overlay_layer = overlay.copy()
        overlay_dark = np.zeros((h, w, 3), dtype=np.uint8)
        overlay_dark.fill(32)  # Very dark gray
        alpha = 0.6  # Slightly more transparent
        cv2.addWeighted(overlay_dark, alpha, overlay_layer, 1 - alpha, 0, overlay_layer)
        
        # Add large countdown number
        font = cv2.FONT_HERSHEY_SIMPLEX  # Cleaner font
        font_scale = 12.0  # Slightly smaller for better proportions
        thickness = 20  # Thicker for better visibility
        text_str = str(countdown_number)
        
        # Get size of the text
        (text_width, text_height), baseline = cv2.getTextSize(
            text_str, font, font_scale, thickness)
        
        # Calculate center position
        text_x = (w - text_width) // 2
        text_y = (h + text_height) // 2
        
        # Draw white text with black outline
        # Bigger outline for better visibility
        cv2.putText(overlay_layer, text_str, (text_x, text_y), font, font_scale,
                    (0, 0, 0), thickness + 12)  # Thicker black outline
        cv2.putText(overlay_layer, text_str, (text_x, text_y), font, font_scale,
                    (255, 255, 255), thickness)  # White text
        
        return overlay_layer

    def update_frame(self):
        try:
            ret, frame = self.cap.read()
            if not ret:
                return
                
            frame = cv2.flip(frame, 1)
            overlay = frame.copy()
            current_time = time.time()
            results = None
            
            # Phase handling
            # At the start of your phase handling in update_frame
            # At the start of your phase handling in update_frame
            if self.phase == "initial":
            # Show the welcome overlay
                overlay = self.create_welcome_overlay(overlay)
            
            # Still update the info panel but keep layout consistent
                self.live_feed.info_panel.update_info(
                title="Welcome to Alignify",
                timer="",
                instruction="Get ready for your guided yoga session",
                image_path=None
            )
            
            # Keep the Begin button visible and other buttons hidden
            # self.welcome_button.setVisible(True)
                self.start_button.setVisible(False)
                self.recalibrate_button.setVisible(False)
            else:
            # Hide welcome button in all other phases
                self.live_feed.info_panel.begin_button.setVisible(False)
                
                # Info panel
            self.live_feed.info_panel.update_info(
                    title="Welcome",
                    timer="",
                    instruction="Get ready for your guided yoga session"
                )
            self.status_label.setText("Status: Ready to begin")

            if self.phase == "warmup":
                remaining = int(self.warmup_duration - (current_time - self.phase_start_time))
                self.live_feed.info_panel.update_info(
                    title="Warm-up Phase",
                    timer="",
                    instruction="Get ready to begin your yoga session"
                )
                overlay = self.create_countdown_overlay(overlay, remaining)
                self.status_label.setText("Status: Warm-up")
                if remaining <= 0:
                    self.phase = "calibration"
                    self.phase_start_time = current_time
                    self.tts_manager.speak("Warm-up complete. Let's begin calibration.")
            
            elif self.phase == "calibration":
                if self.current_calibration_index < len(self.calibration_poses):
                    current_calib = self.calibration_poses[self.current_calibration_index]
                    pose_name = current_calib["name"]
                    image_path = current_calib["file"]
                    
                    if self.current_calibration_index == 0 and (current_time - self.phase_start_time) < self.calibration_initial_delay:
                        remaining = int(self.calibration_initial_delay - (current_time - self.phase_start_time))
                        self.live_feed.info_panel.update_info(
                            title=f"Preparing for {pose_name}",
                            timer="",
                            instruction="Get into position and follow the reference pose",
                            image_path=image_path
                        )
                        overlay = self.create_countdown_overlay(overlay, remaining)
                        self.status_label.setText(f"Status: Prepare for {pose_name}")
                    else:
                        if self.current_calibration_index == 0:
                            capture_start = self.phase_start_time + self.calibration_initial_delay
                            remaining = int(self.baseline_capture_delay - (current_time - capture_start))
                        else:
                            remaining = int(self.baseline_capture_delay - (current_time - self.phase_start_time))
                        
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = pose_detector.process(frame_rgb)
                        
                        if results and results.pose_landmarks:
                            mp_drawing.draw_landmarks(
                                overlay,
                                results.pose_landmarks,
                                mp_pose.POSE_CONNECTIONS,
                                landmark_drawing_spec,
                                connection_drawing_spec
                            )
                            overlay = self.create_countdown_overlay(overlay, remaining)
                            
                            if remaining <= 0:
                                landmarks = {mp_pose.PoseLandmark(i).name: (lm.x, lm.y, lm.z)
                                          for i, lm in enumerate(results.pose_landmarks.landmark)}
                                self.baseline_landmarks[pose_name] = landmarks
                                self.baseline_images[pose_name] = frame.copy()
                                self.current_ref_image = frame.copy()
                                self.tts_manager.speak(f"{pose_name} calibrated.")
                                self.progress_bar.setValue(self.current_calibration_index + 1)
                                self.phase = "calibration_delay"
                                self.phase_start_time = current_time
                        
                        self.live_feed.info_panel.update_info(
                            title=f"Calibrating {pose_name}",
                            timer="",
                            instruction="Hold the pose while we calibrate",
                            image_path=image_path
                        )
                        self.status_label.setText(f"Status: Calibrating {pose_name}")
            
            elif self.phase == "calibration_delay":
                remaining = int(self.calibration_post_delay - (current_time - self.phase_start_time))
                current_pose = self.calibration_poses[self.current_calibration_index]
                self.live_feed.info_panel.update_info(
                    title=f"{current_pose['name']} Calibrated",
                    timer="",
                    instruction="Preparing for next pose...",
                    image_path=current_pose["file"]
                )
                overlay = self.create_countdown_overlay(overlay, remaining)
                self.status_label.setText("Status: Preparing next calibration pose")
                if remaining <= 0:
                    self.current_calibration_index += 1
                    if self.current_calibration_index < len(self.calibration_poses):
                        next_pose = self.calibration_poses[self.current_calibration_index]["name"]
                        self.tts_manager.speak(f"Get ready for {next_pose}.")
                        self.phase = "calibration"
                        self.phase_start_time = current_time
                    else:
                        with open('landmarks.json', 'w') as f:
                            json.dump(self.baseline_landmarks, f)
                        self.status_label.setText("Status: Calibration complete")
                        self.start_button.setEnabled(True)
                        self.recalibrate_button.setEnabled(True)
                        self.tts_manager.speak("Calibration complete. Press Start Session when you're ready.")
                        self.phase = "calibration_complete"
            
            elif self.phase == "calibration_complete":
                # Just show the final calibration image without countdown
                if self.current_ref_image is not None:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = pose_detector.process(frame_rgb)
                    if results and results.pose_landmarks:
                        mp_drawing.draw_landmarks(
                            overlay,
                            results.pose_landmarks,
                            mp_pose.POSE_CONNECTIONS,
                            landmark_drawing_spec,
                            connection_drawing_spec
                        )
            
            elif self.phase == "session_countdown":
                remaining = int(self.session_countdown_duration - (current_time - self.phase_start_time))
                self.live_feed.info_panel.update_info(
                    title="Session Starting Soon",
                    timer="",
                    instruction="Get ready for your guided session"
                )
                overlay = self.create_countdown_overlay(overlay, remaining)
                self.status_label.setText("Status: Get ready for your session")
                if remaining <= 0:
                    self.phase = "session"
                    self.phase_start_time = current_time
                    self.current_pose_index = 0
                    self.latest_pose_time = None
                    self.tts_manager.speak("Let's begin your yoga session!")
                    first_pose = self.calibration_poses[self.current_pose_index]["name"]
                    self.current_ref_image = self.baseline_images.get(first_pose, self.current_ref_image)
            
            elif self.phase == "session":
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose_detector.process(frame_rgb)
                if results and results.pose_landmarks:
                    mp_drawing.draw_landmarks(
                        overlay,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec,
                        connection_drawing_spec
                    )
                    current_pose = self.calibration_poses[self.current_pose_index]
                    user_landmarks = {mp_pose.PoseLandmark(i).name: (lm.x, lm.y, lm.z)
                                   for i, lm in enumerate(results.pose_landmarks.landmark)}
                    ref_landmarks = self.baseline_landmarks.get(current_pose["name"])
                    feedback = None
                    if ref_landmarks:
                        feedback = get_direction_feedback(user_landmarks, ref_landmarks)
                    if feedback:
                        if current_time - self.prev_feedback_time > self.feedback_interval:
                            self.tts_manager.speak(feedback)
                            self.prev_feedback_time = current_time
                            self.live_feed.info_panel.update_info(
                                title=current_pose["name"],
                                timer="",
                                instruction=feedback,
                                image_path=current_pose["file"]
                            )
                        self.latest_pose_time = None
                    else:
                        if self.latest_pose_time is None:
                            self.latest_pose_time = current_time
                            self.tts_manager.speak("Perfect! Hold this pose.")
                        hold_time = int(current_time - self.latest_pose_time)
                        remaining = self.session_hold_duration - hold_time
                        overlay = self.create_countdown_overlay(overlay, remaining)
                        self.live_feed.info_panel.update_info(
                            title=current_pose["name"],
                            timer="",
                            instruction="Hold this pose",
                            image_path=current_pose["file"]
                        )
                        if hold_time >= self.session_hold_duration:
                            self.phase = "session_delay"
                            self.phase_start_time = current_time
                            self.tts_manager.speak(f"Good job on {current_pose['name']}.")
                    self.status_label.setText(f"Status: Session - {current_pose['name']}")
            
            elif self.phase == "session_delay":
                remaining = int(self.session_post_delay - (current_time - self.phase_start_time))
                current_pose = self.calibration_poses[self.current_pose_index]
                self.live_feed.info_panel.update_info(
                    title="Transitioning",
                    timer="",
                    instruction="Get ready for the next pose",
                    image_path=current_pose["file"]
                )
                overlay = self.create_countdown_overlay(overlay, remaining)
                if remaining <= 0:
                    self.current_pose_index += 1
                    if self.current_pose_index >= len(self.calibration_poses):
                        self.phase = "completed"
                        self.tts_manager.speak("Congratulations! You've completed the Alineify Yoga routine!")
                    else:
                        next_pose = self.calibration_poses[self.current_pose_index]["name"]
                        self.tts_manager.speak(f"Next pose: {next_pose}")
                        self.latest_pose_time = None
                        self.phase = "session"
                        self.phase_start_time = current_time
                        self.current_ref_image = self.baseline_images.get(next_pose, self.current_ref_image)
            
            elif self.phase == "completed":
                self.live_feed.info_panel.update_info(
                    title="Session Complete!",
                    timer="",
                    instruction="Great job! You've completed your yoga session."
                )
                self.status_label.setText("Status: Routine Completed")
            
            # Add reference pose overlay if we have valid calibration data
            if self.current_ref_image is not None and self.baseline_landmarks:
                ref_h, ref_w = self.current_ref_image.shape[:2]
                scale_factor = 0.25
                new_w = int(ref_w * scale_factor)
                new_h = int(ref_h * scale_factor)
                
                ref_small = cv2.resize(self.current_ref_image, (new_w, new_h))
                
                # Position in bottom-right corner of video area
                margin = 20
                y_offset = overlay.shape[0] - new_h - margin
                x_offset = overlay.shape[1] - new_w - margin
                
                # Add semi-transparent background
                bg = np.zeros((new_h, new_w, 3), dtype=np.uint8)
                bg.fill(255)
                alpha = 0.8
                ref_small = cv2.addWeighted(ref_small, alpha, bg, 1-alpha, 0)
                
                overlay[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = ref_small
            
            # Update video feed
            live_pix = convert_frame_to_qpixmap(overlay)
            self.live_feed.video_label.setPixmap(live_pix.scaled(
                self.live_feed.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        
        except Exception as e:
            print(f"Error in update_frame: {e}")

    def on_start_button(self):
        """Handle start button click."""
        self.phase = "session_countdown"
        self.phase_start_time = time.time()
        self.status_label.setText("Status: Session starting soon...")
        self.start_button.setEnabled(False)
        self.tts_manager.speak("Get ready for your guided yoga session!")

    def on_recalibrate_button(self):
            """Handle recalibrate button click."""
            self.phase = "calibration"
            self.phase_start_time = time.time()
            self.current_calibration_index = 0
            self.baseline_landmarks = {}
            self.baseline_images = {}
            self.current_ref_image = None  # Clear the reference image
            self.progress_bar.setValue(0)
            self.start_button.setEnabled(False)
            self.recalibrate_button.setEnabled(False)  # Disable until calibration is complete
            self.tts_manager.speak("Let's recalibrate your poses.")

    
    def closeEvent(self, event):
        """Clean up resources when closing the application."""
        self.cap.release()
        event.accept()

# -------------------------------
# Main Execution
# -------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application-wide stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #FFFFFF;
        }
        QScrollArea {
            border: none;
            background-color: #FFFFFF;
        }
        QWidget {
            background-color: #FFFFFF;
        }
        QLabel {
            color: #2D3142;
        }
    """)
    
    window = YogaApp()
    window.show()
    sys.exit(app.exec_())