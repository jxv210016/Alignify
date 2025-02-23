import cv2
import mediapipe as mp
import json
import numpy as np
import pyttsx3
import time

# -------------------------------
# Load reference pose landmarks
# -------------------------------
with open('landmarks.json', 'r') as f:
    ref_data = json.load(f)

# Define the sequence of poses
pose_sequence = ['warrior.jpg', 'warrrior_II_left.jpg', 'warrrior_II_right.jpg', 'tree.jpg', 'downward_dog.jpg']
current_pose_index = 0
hold_duration = 5  # seconds to hold each pose
pose_transition_delay = 5  # seconds between poses

# -------------------------------
# Initialize Text-to-Speech Engine
# -------------------------------
engine = pyttsx3.init()

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
# Set up OpenCV Windows
# -------------------------------
cv2.namedWindow("Reference Pose", cv2.WINDOW_NORMAL)
cv2.namedWindow("YN Yoga - Live", cv2.WINDOW_NORMAL)
cv2.moveWindow("Reference Pose", 0, 0)
cv2.moveWindow("YN Yoga - Live", 600, 0)

# -------------------------------
# Thresholds for movement
# -------------------------------
x_threshold = .1
y_threshold = .1

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
            # Calculate average position for the limb
            user_x = np.mean([user_landmarks[lm][0] for lm in landmarks if lm in user_landmarks])
            user_y = np.mean([user_landmarks[lm][1] for lm in landmarks if lm in user_landmarks])
            ref_x = np.mean([ref_landmarks[lm][0] for lm in landmarks if lm in ref_landmarks])
            ref_y = np.mean([ref_landmarks[lm][1] for lm in landmarks if lm in ref_landmarks])
            
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
    
    # Return the most significant correction needed
    if all_feedback:
        all_feedback.sort(key=lambda x: x['diff'], reverse=True)
        return [all_feedback[0]['message']]
    return []

# -------------------------------
# Main Program Loop
# -------------------------------
cap = cv2.VideoCapture(0)
prev_feedback_time = 0
feedback_interval = 2  # Reduced interval for more responsive feedback
processing_interval = 0.5
last_processed_time = 0

# State variables
pose_start_time = time.time()
transition_start_time = time.time()
pose_achieved_time = None
in_transition = True
routine_complete = False

while cap.isOpened() and not routine_complete:
    ret, frame = cap.read()
    if not ret:
        break
    
    current_time = time.time()
    
    # Load current reference pose
    current_pose = pose_sequence[current_pose_index]
    ref_landmarks = ref_data[current_pose]
    ref_img = cv2.imread(current_pose)
    
    # Handle pose transitions
    if in_transition:
        remaining = int(transition_start_time + pose_transition_delay - current_time)
        if remaining > 0:
            cv2.rectangle(frame, (20, 20), (500, 100), (0, 0, 0), -1)
            countdown_text = f"Get ready for {current_pose.split('.')[0]}... {remaining}"
            cv2.putText(frame, countdown_text, (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3, cv2.LINE_AA)
            
            if remaining == pose_transition_delay - 1:
                pose_name = current_pose.split('.')[0]
                engine.say(f"Next pose: {pose_name}")
                engine.runAndWait()
        else:
            in_transition = False
            pose_start_time = current_time
    else:
        if current_time - last_processed_time >= processing_interval:
            last_processed_time = current_time
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)
            
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec,
                    connection_drawing_spec
                )
                
                user_landmarks = {
                    mp_pose.PoseLandmark(i).name: (lm.x, lm.y, lm.z)
                    for i, lm in enumerate(results.pose_landmarks.landmark)
                }
                
                feedback_messages = get_direction_feedback(user_landmarks, ref_landmarks)
                
                if not feedback_messages:
                    if pose_achieved_time is None:
                        pose_achieved_time = current_time
                        engine.say("Perfect! Hold this pose.")
                        engine.runAndWait()
                    
                    hold_time = int(current_time - pose_achieved_time)
                    remaining_hold = hold_duration - hold_time
                    if remaining_hold >= 0:
                        cv2.rectangle(frame, (20, 20), (500, 100), (0, 0, 0), -1)
                        cv2.putText(frame, f"Hold for: {remaining_hold}", (30, 80),
                                  cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3, cv2.LINE_AA)
                    
                    if hold_time >= hold_duration:
                        current_pose_index += 1
                        if current_pose_index >= len(pose_sequence):
                            routine_complete = True
                            engine.say("Congratulations! You've completed the YN Yoga routine!")
                            engine.runAndWait()
                            break
                        
                        pose_achieved_time = None
                        in_transition = True
                        transition_start_time = current_time
                        
                elif current_time - prev_feedback_time > feedback_interval:
                    feedback_text = feedback_messages[0]  # Only speak the most important correction
                    engine.say(feedback_text)
                    engine.runAndWait()
                    prev_feedback_time = current_time
    
    # Display frames
    cv2.imshow("YN Yoga - Live", frame)
    if ref_img is not None:
        ref_img_resized = cv2.resize(ref_img, (frame.shape[1] // 2, frame.shape[0]))
        cv2.imshow("Reference Pose", ref_img_resized)
    
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()