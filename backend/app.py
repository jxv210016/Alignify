import asyncio
import websockets
import json
import logging
import random
import time
import cv2
import mediapipe as mp
import numpy as np
import threading
from collections import deque
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MediaPipe pose setup
mp_pose = mp.solutions.pose
pose_detector = mp_pose.Pose(
    static_image_mode=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Store client connections
clients = set()

# Calibration data storage - this will store calibration state for each pose
calibration_data = {}

# Session state for clients
client_sessions = {}

# Global variables for video processing
frame_buffer = deque(maxlen=5)  # Store recent frames
current_landmarks = {}  # Store current landmarks
processing_active = True
video_capture = None

# Feedback thresholds
x_threshold = 0.1
y_threshold = 0.1

# Body parts mapping for feedback
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

# Initialize video capture in a background thread
def initialize_video_capture():
    global video_capture
    try:
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            logger.error("Error: Could not open video capture device")
            return False
        return True
    except Exception as e:
        logger.error(f"Error initializing video capture: {str(e)}")
        return False

# Process video frames in a background thread
def process_video_frames():
    global current_landmarks, processing_active, video_capture
    
    logger.info("Starting video processing thread")
    
    while processing_active:
        if video_capture is None or not video_capture.isOpened():
            logger.warning("Video capture not available, attempting to initialize...")
            if not initialize_video_capture():
                logger.error("Failed to initialize video capture, retrying in 3 seconds...")
                time.sleep(3)
                continue
        
        try:
            # Read a frame from the camera
            success, frame = video_capture.read()
            if not success:
                logger.warning("Failed to read frame, retrying...")
                time.sleep(0.1)
                continue
            
            # No longer flipping the frame - displaying the raw camera output
            # frame = cv2.flip(frame, 1)
            
            # Add the frame to our buffer
            frame_buffer.append(frame)
            
            # Convert the frame to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame with MediaPipe Pose
            results = pose_detector.process(frame_rgb)
            
            # Extract landmarks if detected
            if results.pose_landmarks:
                # Convert landmarks to dictionary format for WebSocket transmission
                landmarks_dict = {}
                for i, landmark in enumerate(results.pose_landmarks.landmark):
                    landmarks_dict[i] = {
                        "x": landmark.x,
                        "y": landmark.y,
                        "z": landmark.z
                    }
                
                # Update the global landmarks
                current_landmarks = landmarks_dict
            else:
                # If no landmarks detected, keep the last detected landmarks for a smoother experience
                pass
                
            # Add short delay to prevent CPU overuse
            time.sleep(0.03)  # ~30 fps
            
        except Exception as e:
            logger.error(f"Error in video processing: {str(e)}")
            time.sleep(0.1)
    
    # Clean up resources when stopping
    if video_capture is not None:
        video_capture.release()
    logger.info("Video processing thread stopped")

# Compare user landmarks with reference pose and generate feedback
def get_direction_feedback(user_landmarks, ref_landmarks):
    """Compare user's pose with reference pose and return feedback."""
    all_feedback = []
    
    # Convert numeric indices to MediaPipe pose landmark names
    named_user_landmarks = {}
    named_ref_landmarks = {}
    
    for index, values in user_landmarks.items():
        if hasattr(mp_pose.PoseLandmark, str(index)):
            name = mp_pose.PoseLandmark(int(index)).name
            named_user_landmarks[name] = (values["x"], values["y"], values["z"])
    
    for index, values in ref_landmarks.items():
        if hasattr(mp_pose.PoseLandmark, str(index)):
            name = mp_pose.PoseLandmark(int(index)).name
            named_ref_landmarks[name] = (values["x"], values["y"], values["z"])
    
    # Compare body parts
    for limb_type, sides in body_parts.items():
        for side, landmarks in sides.items():
            if all(lm in named_user_landmarks for lm in landmarks) and all(lm in named_ref_landmarks for lm in landmarks):
                user_x = np.mean([named_user_landmarks[lm][0] for lm in landmarks])
                user_y = np.mean([named_user_landmarks[lm][1] for lm in landmarks])
                ref_x = np.mean([named_ref_landmarks[lm][0] for lm in landmarks])
                ref_y = np.mean([named_ref_landmarks[lm][1] for lm in landmarks])
                
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
    return "Good alignment! Hold the pose"

# WebSocket handler
async def ws_handler(websocket, path):
    # Add the client to our set and create session state
    client_id = id(websocket)
    clients.add(websocket)
    client_sessions[client_id] = {
        "active_pose": None,
        "calibrated_poses": set(),
        "session_active": False,
        "last_feedback_time": time.time()
    }
    
    logger.info(f"New client connected. ID: {client_id}. Total clients: {len(clients)}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get('action')
                
                logger.info(f"Received action: {action} from client {client_id}")
                
                if action == 'calibrate':
                    # Store calibration data for a pose
                    pose_name = data.get('pose')
                    logger.info(f"Calibrating pose: {pose_name} for client {client_id}")
                    
                    # Use current landmarks for calibration
                    if current_landmarks:
                        calibration_data[pose_name] = current_landmarks
                        
                        # Mark this pose as calibrated for this client
                        client_sessions[client_id]["calibrated_poses"].add(pose_name)
                        
                        # Send confirmation with current landmarks
                        await asyncio.sleep(0.5)  # Add artificial delay to make it feel like processing
                        
                        await websocket.send(json.dumps({
                            "message": f"Calibrated pose: {pose_name}",
                            "landmarks": current_landmarks,
                            "calibration_success": True
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "message": f"Failed to calibrate {pose_name}. No landmarks detected.",
                            "landmarks": {},
                            "calibration_success": False,
                            "feedback": "Please ensure you are visible in the camera"
                        }))
                
                elif action == 'startSession':
                    # Start a pose session
                    pose_name = data.get('pose')
                    logger.info(f"Starting session for pose: {pose_name} for client {client_id}")
                    
                    # Update client session state
                    client_sessions[client_id]["session_active"] = True
                    client_sessions[client_id]["active_pose"] = pose_name
                    
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "message": f"Session started for pose: {pose_name}",
                        "landmarks": current_landmarks,
                        "feedback": f"Begin {pose_name}. Adjust your position to match the reference."
                    }))
                
                elif action == 'endSession':
                    # End the current session
                    logger.info(f"Session ended for client {client_id}")
                    
                    # Update client session state
                    client_sessions[client_id]["session_active"] = False
                    client_sessions[client_id]["active_pose"] = None
                    
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "message": "Session ended",
                        "landmarks": current_landmarks,
                        "feedback": "Session complete. Great work!"
                    }))
                
                elif action == 'changePose':
                    # Change the current pose
                    pose_name = data.get('pose')
                    logger.info(f"Changed pose to: {pose_name} for client {client_id}")
                    
                    # Update client session state
                    client_sessions[client_id]["active_pose"] = pose_name
                    
                    # Send confirmation
                    await websocket.send(json.dumps({
                        "message": f"Changed to pose: {pose_name}",
                        "landmarks": current_landmarks,
                        "feedback": f"Transitioning to {pose_name}. Find your balance and alignment."
                    }))
                
            except json.JSONDecodeError:
                logger.error(f"Received invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {str(e)}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    finally:
        if websocket in clients:
            clients.remove(websocket)
        if client_id in client_sessions:
            del client_sessions[client_id]
        logger.info(f"Client {client_id} removed. Total clients: {len(clients)}")

# Function to send periodic updates to all clients
async def send_updates():
    while True:
        if clients:
            for client in list(clients):
                try:
                    client_id = id(client)
                    session_state = client_sessions.get(client_id, {})
                    
                    # Create response with current landmarks
                    response = {"landmarks": current_landmarks}
                    
                    # Add feedback if in active session
                    if session_state.get("session_active", False):
                        pose_name = session_state.get("active_pose")
                        
                        # Generate feedback by comparing current pose with calibrated pose
                        if pose_name in calibration_data and current_landmarks:
                            # Only send feedback occasionally to avoid spam
                            current_time = time.time()
                            if current_time - session_state.get("last_feedback_time", 0) > 2.0:  # Every 2 seconds
                                ref_landmarks = calibration_data.get(pose_name)
                                if ref_landmarks:
                                    feedback = get_direction_feedback(current_landmarks, ref_landmarks)
                                    response["feedback"] = feedback
                                    client_sessions[client_id]["last_feedback_time"] = current_time
                                    
                                    # Calculate a simple accuracy percentage
                                    if len(current_landmarks) > 0 and len(ref_landmarks) > 0:
                                        # Simple calculation based on key points
                                        key_points = [11, 12, 13, 14, 23, 24, 25, 26, 27, 28]  # Shoulders, elbows, hips, knees, ankles
                                        errors = []
                                        
                                        for point in key_points:
                                            if str(point) in current_landmarks and str(point) in ref_landmarks:
                                                curr = current_landmarks[str(point)]
                                                ref = ref_landmarks[str(point)]
                                                
                                                # Calculate distance between current and reference
                                                dx = curr["x"] - ref["x"]
                                                dy = curr["y"] - ref["y"]
                                                distance = (dx**2 + dy**2)**0.5
                                                errors.append(distance)
                                                
                                        if errors:
                                            avg_error = sum(errors) / len(errors)
                                            # Convert to accuracy (0-100%)
                                            accuracy = max(0, min(100, 100 * (1 - avg_error / 0.2)))  # Normalize error
                                            response["accuracy"] = int(accuracy)
                    
                    await client.send(json.dumps(response))
                        
                except websockets.exceptions.ConnectionClosed:
                    if client in clients:
                        clients.remove(client)
                    client_id = id(client)
                    if client_id in client_sessions:
                        del client_sessions[client_id]
                    logger.info(f"Client removed during update. Total clients: {len(clients)}")
                except Exception as e:
                    logger.error(f"Error sending update: {str(e)}")
        
        await asyncio.sleep(0.1)  # Send updates 10 times per second

# Check if calibration directory exists and load reference poses
def load_reference_images():
    if os.path.exists('calibration'):
        logger.info("Found calibration directory, checking for reference poses")
        for filename in os.listdir('calibration'):
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                logger.info(f"Found reference image: {filename}")

# Start WebSocket server
async def main():
    global processing_active
    
    # Initialize video capture
    if not initialize_video_capture():
        logger.error("Failed to initialize video capture, exiting")
        return
    
    # Check for reference images
    load_reference_images()
    
    # Start video processing thread
    video_thread = threading.Thread(target=process_video_frames)
    video_thread.daemon = True
    video_thread.start()
    
    try:
        server = await websockets.serve(ws_handler, "127.0.0.1", 5000)
        logger.info("WebSocket server started at ws://127.0.0.1:5000")
        
        # Create task for sending updates
        update_task = asyncio.create_task(send_updates())
        
        # Keep the server running
        await asyncio.Future()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        # Clean up resources
        processing_active = False
        if video_capture is not None:
            video_capture.release()
        logger.info("Resources cleaned up")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down WebSocket server")
        # Ensure video processing is stopped
        processing_active = False
        if video_capture is not None:
            video_capture.release()
