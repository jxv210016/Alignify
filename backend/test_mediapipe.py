import cv2
import mediapipe as mp
import time

print("Testing MediaPipe installation...")

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    static_image_mode=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

print("MediaPipe Pose initialized")

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam")
    exit()

print("Webcam opened successfully")
print("Press 'q' to exit test")

# Test for a few frames
start_time = time.time()
frame_count = 0
landmarks_count = 0

try:
    while time.time() - start_time < 10:  # Run for 10 seconds
        success, image = cap.read()
        if not success:
            print("Error: Could not read frame")
            continue
        
        # Flip the image horizontally for a selfie-view display
        image = cv2.flip(image, 1)
        
        # Convert the image from BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process the image with MediaPipe Pose
        results = pose.process(image_rgb)
        
        # Draw the pose landmarks on the image
        if results.pose_landmarks:
            landmarks_count += 1
            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=1)
            )
        
        # Display the image with landmarks
        cv2.imshow('MediaPipe Pose Test', image)
        
        # Exit if 'q' is pressed
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break
        
        frame_count += 1
except Exception as e:
    print(f"Error during processing: {e}")
finally:
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    pose.close()

    print(f"Test completed")
    print(f"Processed {frame_count} frames")
    print(f"Detected landmarks in {landmarks_count} frames")
    print(f"Landmarks detection rate: {landmarks_count/frame_count*100:.2f}%")
    
    if landmarks_count > 0:
        print("RESULT: MediaPipe is working correctly!")
    else:
        print("RESULT: No landmarks detected. Please check your webcam and lighting.") 