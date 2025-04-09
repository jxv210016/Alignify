# Alignify - Running Instructions

## What We've Built

We've transformed the Alignify application to use real-time MediaPipe pose detection from the backend, while keeping the frontend webcam feed. This gives us the best of both worlds:

1. Efficient pose detection using MediaPipe in Python
2. Direct webcam display in the browser for minimal latency
3. Real-time landmark overlay from actual pose detection (not mock data)

## Running the Application

### Step 1: Install Dependencies

First, install all required dependencies:

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies (in a new terminal)
cd frontend
npm install
```

### Step 2: Test MediaPipe

Make sure MediaPipe is working correctly on your system:

```bash
cd backend
python test_mediapipe.py
```

This should open a window showing your webcam feed with pose detection. Press 'q' to exit the test.

### Step 3: Start the Backend Server

Start the WebSocket server with real-time pose detection:

```bash
cd backend
python app.py
```

You should see: "WebSocket server started at ws://127.0.0.1:5000"

### Step 4: Start the Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

### Step 5: Open the Application

Open your browser and navigate to http://localhost:3000

## Using the Application

1. Go to the Workouts page
2. Allow camera access if prompted
3. You should see your webcam feed with pose landmarks overlaid
4. Calibrate a pose by standing in the pose and clicking "Calibrate Pose"
5. Start a session by clicking "Start Session"
6. You'll receive real-time feedback based on your alignment compared to the calibrated pose

## What to Expect

- The MediaPipe pose detection happens on the backend
- The landmarks are sent via WebSocket to the frontend
- Your webcam feed is displayed directly in the browser
- The landmarks are overlaid on your webcam feed in real-time
- During a session, your current pose is compared to the calibrated reference pose
- Feedback is provided based on the comparison

## Troubleshooting

If you encounter issues:

1. Check browser console for frontend errors
2. Check terminal for backend errors
3. Ensure webcam permissions are granted
4. Verify MediaPipe is working with the test script
5. Try reconnecting by refreshing the page 