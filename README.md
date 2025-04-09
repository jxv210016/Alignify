# Alignify - Real-time Yoga Pose Detection

A web application for real-time yoga pose detection and feedback using MediaPipe and WebSocket communication.

### Features

- Python backend with MediaPipe pose detection
- Real-time pose landmark detection and visualization
- Pose comparison and alignment feedback
- Calibration and session management
- Modern Next.js frontend with real-time feedback

### Setup Instructions

#### Backend Setup

1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Test MediaPipe installation:
   ```bash
   python test_mediapipe.py
   ```
   This will open your webcam and verify MediaPipe is working correctly.

3. Start the WebSocket server:
   ```bash
   python app.py
   ```
   This will start the server at `ws://127.0.0.1:5000`.

#### Frontend Setup

1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```
   This will start the frontend at `http://localhost:3000`.

### Using the Application

1. Open `http://localhost:3000` in your browser
2. Navigate to the Workouts page
3. Allow webcam access when prompted
4. Calibrate each pose by clicking "Calibrate Pose"
5. Start a session by clicking "Start Session"
6. Follow the alignment feedback to improve your pose

### Troubleshooting

- If the webcam doesn't appear, check browser permissions
- If landmarks aren't detected, ensure you're visible in the camera frame
- For backend issues, check the terminal for error messages
- For MediaPipe installation issues, run `python test_mediapipe.py`

### Project Structure

- `/backend` - Python backend with MediaPipe and WebSocket server
  - `app.py` - Main WebSocket server with pose detection
  - `test_mediapipe.py` - Test script for MediaPipe functionality
  - `calibration/` - Reference pose images
  
- `/frontend` - Next.js frontend application
  - `app/workouts/page.tsx` - Main page for yoga pose detection
  - `src/hooks/useWebSocket.ts` - WebSocket connection handling
  - `public/poses/` - Reference pose images

### How It Works

1. The backend captures video from your webcam and processes it with MediaPipe
2. Real-time pose landmarks are extracted and sent via WebSocket
3. The frontend displays your webcam feed and overlays the landmarks
4. During calibration, your pose is saved as a reference
5. During a session, your current pose is compared to the calibrated references
6. Real-time feedback helps you adjust your alignment

### Development

For more detail on the workings of the application, check out these key files:
- `backend/app.py` - Main server implementation with MediaPipe integration
- `frontend/app/workouts/page.tsx` - Main frontend interface for pose detection
- `frontend/src/hooks/useWebSocket.ts` - WebSocket communication 