import cv2
import mediapipe as mp
import json

# Initialize MediaPipe Pose in static image mode.
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)

def extract_landmarks(image_path):
    """
    Extracts pose landmarks from a given image file.
    
    Args:
        image_path (str): Path to the image file.
        
    Returns:
        dict: A dictionary with landmark names as keys and their (x, y, z) coordinates as values.
              Returns None if no landmarks are detected.
    """
    # Load the image using OpenCV.
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image '{image_path}'")
        return None
    
    # Convert the image from BGR to RGB as MediaPipe expects RGB images.
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Process the image with MediaPipe Pose.
    results = pose.process(image_rgb)
    
    if results.pose_landmarks:
        # Create a dictionary mapping landmark names to their normalized coordinates.
        landmarks = {
            mp_pose.PoseLandmark(i).name: (lm.x, lm.y, lm.z)
            for i, lm in enumerate(results.pose_landmarks.landmark)
        }
        return landmarks
    else:
        print(f"No landmarks detected in '{image_path}'.")
        return None

def main():
    # List of your image files.
    image_files = [
            "warrior.jpg",
    "warrrior_II_left.jpg",
    "warrrior_II_right.jpg",
    "tree.jpg",
    "downward_dog.jpg"
    ]
    
    # Dictionary to store landmark data for each image.
    landmarks_data = {}
    
    # Process each image and store its landmarks.
    for file in image_files:
        print(f"\nProcessing '{file}'...")
        landmarks = extract_landmarks(file)
        if landmarks:
            landmarks_data[file] = landmarks
            for name, coords in landmarks.items():
                print(f"{name}: {coords}")
        else:
            print(f"Landmark extraction failed for '{file}'.")
    
    # Save the landmark data to a JSON file.
    with open("landmarks.json", "w") as f:
        json.dump(landmarks_data, f, indent=4)
    
    print("\nLandmark extraction complete. Data saved to 'landmarks.json'.")

if __name__ == "__main__":
    main()
