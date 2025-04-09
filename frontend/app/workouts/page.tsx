'use client'

import React, { useEffect, useRef, useState } from 'react'
import { useWebSocket, PoseData } from '@/hooks/useWebSocket'

// Define the available poses
const POSES = ['Warrior I', 'Warrior II', 'Tree Pose']

// Define the landmark position interface
interface LandmarkPosition {
  x: number
  y: number
  z: number
}

export default function WorkoutsPage() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isWebcamActive, setIsWebcamActive] = useState(false)
  const [currentPose, setCurrentPose] = useState(POSES[0])
  const [isCalibrating, setIsCalibrating] = useState(false)
  const [isInSession, setIsInSession] = useState(false)
  const [countdown, setCountdown] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [calibrationStatus, setCalibrationStatus] = useState<Record<string, boolean>>({})
  const [poseProgress, setPoseProgress] = useState<number>(0)
  
  // Use our WebSocket hook with all the functions
  const { 
    isConnected, 
    poseData, 
    lastMessage,
    lastEvent,
    feedback: wsFeedback,
    startCalibration: wsStartCalibration,
    startSession: wsStartSession,
    endSession: wsEndSession,
    changePose: wsChangePose
  } = useWebSocket()

  // Process pose data and feedback from WebSocket
  useEffect(() => {
    // Use feedback from the WebSocket hook if available
    if (wsFeedback) {
      setFeedback(wsFeedback);
    }
    
    // Process data from the websocket
    if (poseData) {
      // Use actual accuracy data from backend
      if (isInSession && 'accuracy' in lastEvent) {
        setPoseProgress(lastEvent.accuracy || 0);
      }
    }
    
    // Process calibration success messages from backend
    if (lastEvent?.calibration_success) {
      setCalibrationStatus(prev => ({
        ...prev,
        [currentPose]: true
      }));
    }
  }, [poseData, lastEvent, wsFeedback, currentPose, isInSession]);

  // Setup webcam - COMPLETE REWRITE for reliable webcam display
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const setupWebcam = async () => {
        try {
          // Clear the state first to ensure we handle new setup cleanly
          setIsWebcamActive(false);
          
          console.log("Attempting to access webcam...");
          
          // Try to get user media with more options for compatibility
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { 
              facingMode: 'user',
              width: { ideal: 1280 },
              height: { ideal: 720 }
            },
            audio: false
          });
          
          // Safely store the video element reference
          const videoElement = videoRef.current;
          if (!videoElement) {
            console.error("Video element not found");
            return;
          }
          
          // Stop any existing streams
          if (videoElement.srcObject) {
            (videoElement.srcObject as MediaStream).getTracks().forEach(track => track.stop());
          }
          
          // Set the new stream
          videoElement.srcObject = stream;
          
          // Create a promise to wait for the video to be ready
          const playPromise = videoElement.play();
          
          if (playPromise !== undefined) {
            playPromise
              .then(() => {
                console.log("Video playing successfully");
                setIsWebcamActive(true);
                
                // Log video dimensions for debugging
                console.log(`Video dimensions: ${videoElement.videoWidth}x${videoElement.videoHeight}`);
                
                // Ensure canvas is properly sized once video is playing
                if (canvasRef.current) {
                  canvasRef.current.width = videoElement.videoWidth || canvasRef.current.clientWidth;
                  canvasRef.current.height = videoElement.videoHeight || canvasRef.current.clientHeight;
                }
              })
              .catch(err => {
                console.error("Error playing video:", err);
                setFeedback("Error playing video. Please ensure webcam permissions are granted.");
              });
          }
        } catch (err) {
          console.error("Error accessing webcam:", err);
          setFeedback("Could not access webcam. Please check your camera and permissions.");
        }
      };
      
      // Call setup function
      setupWebcam();
      
      // Clean up properly
      return () => {
        const videoElement = videoRef.current;
        if (videoElement && videoElement.srcObject) {
          const stream = videoElement.srcObject as MediaStream;
          stream.getTracks().forEach(track => {
            track.stop();
          });
          videoElement.srcObject = null;
          setIsWebcamActive(false);
        }
      };
    }
  }, []); // Keep empty dependency array to run once on mount

  // Update the pose overlay drawing function to handle real landmarks
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) {
      console.log("Canvas or video ref not available");
      return;
    }
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const video = videoRef.current;
    
    if (!ctx) {
      console.error("Could not get canvas context");
      return;
    }
    
    // Function to ensure canvas matches video size
    const resizeCanvas = () => {
      // Check if the video metadata is loaded
      if (video.videoWidth && video.videoHeight) {
        // Always set canvas to the exact size of its container for proper scaling
        const displayWidth = video.clientWidth;
        const displayHeight = video.clientHeight;
        
        // Set canvas dimensions to match the display area
        if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
          canvas.width = displayWidth;
          canvas.height = displayHeight;
          console.log(`Canvas resized to ${displayWidth}x${displayHeight}`);
        }
      } else {
        // If video dimensions aren't available yet, try again later
        setTimeout(resizeCanvas, 100);
      }
    };
    
    // Listen for video element changes
    video.addEventListener('loadedmetadata', resizeCanvas);
    video.addEventListener('play', resizeCanvas);
    video.addEventListener('resize', resizeCanvas);
    window.addEventListener('resize', resizeCanvas);
    
    // Initial resize
    resizeCanvas();
    
    let animationId: number;
    
    // We'll draw the landmarks in a render loop for smoother updates
    const renderFrame = () => {
      if (!videoRef.current || !canvasRef.current) return; // Early exit if refs not ready
      
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      
      if (!ctx) return; // Early exit if context not available
      
      // Ensure canvas dimensions match video display dimensions
      // This should be handled by resizeCanvas, but double-check here
      if (canvas.width !== video.clientWidth || canvas.height !== video.clientHeight) {
        canvas.width = video.clientWidth;
        canvas.height = video.clientHeight;
        if (canvas.width === 0 || canvas.height === 0) {
          // If dimensions are zero, wait for next frame
          requestAnimationFrame(renderFrame);
          return;
        }
      }
      
      // Clear previous drawing
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Get intrinsic video dimensions
      const videoIntrinsicWidth = video.videoWidth;
      const videoIntrinsicHeight = video.videoHeight;
      
      if (!videoIntrinsicWidth || !videoIntrinsicHeight) {
        requestAnimationFrame(renderFrame); // Try again next frame if video dimensions not ready
        return;
      }
      
      const canvasWidth = canvas.width;
      const canvasHeight = canvas.height;
      
      // Calculate the scale factors and offsets needed to map the video onto the canvas with object-cover
      const videoAspectRatio = videoIntrinsicWidth / videoIntrinsicHeight;
      const canvasAspectRatio = canvasWidth / canvasHeight;
      
      let drawWidth = canvasWidth;
      let drawHeight = canvasHeight;
      let offsetX = 0;
      let offsetY = 0;
      let scale = 1;
      
      if (canvasAspectRatio > videoAspectRatio) {
        // Canvas is wider than video; video is pillarboxed if object-contain, but cropped vertically if object-cover
        // For object-cover, scale based on width
        scale = canvasWidth / videoIntrinsicWidth;
        drawHeight = videoIntrinsicHeight * scale;
        offsetY = (canvasHeight - drawHeight) / 2; // Center vertically
      } else {
        // Canvas is taller than video; video is letterboxed if object-contain, but cropped horizontally if object-cover
        // For object-cover, scale based on height
        scale = canvasHeight / videoIntrinsicHeight;
        drawWidth = videoIntrinsicWidth * scale;
        offsetX = (canvasWidth - drawWidth) / 2; // Center horizontally
      }
      
      // Format the landmark data to ensure keys are numbers
      const formattedLandmarks: Record<number, LandmarkPosition> = {};
      
      if (poseData?.landmarks) {
        Object.entries(poseData.landmarks).forEach(([key, value]) => {
          const index = parseInt(key);
          if (!isNaN(index) && value && typeof value.x === 'number' && typeof value.y === 'number' && typeof value.z === 'number') {
            formattedLandmarks[index] = {
              x: value.x,
              y: value.y,
              z: value.z
            };
          }
        });
        
        // Only draw if we have landmarks
        if (Object.keys(formattedLandmarks).length > 0) {
          // Pass the calculated draw area dimensions and offsets to the drawing functions
          drawConnections(
            ctx, 
            formattedLandmarks, 
            drawWidth, 
            drawHeight,
            offsetX,
            offsetY
          );
          
          // Draw joints relative to the actual video render area
          drawJoints(
            ctx, 
            formattedLandmarks, 
            drawWidth, 
            drawHeight,
            offsetX,
            offsetY
          );
        }
      }
      
      // Request next frame
      animationId = requestAnimationFrame(renderFrame);
    };
    
    // Start render loop
    animationId = requestAnimationFrame(renderFrame);
    
    // Clean up on unmount
    return () => {
      cancelAnimationFrame(animationId);
      video.removeEventListener('loadedmetadata', resizeCanvas);
      video.removeEventListener('play', resizeCanvas);
      video.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('resize', resizeCanvas);
    };
  }, [poseData]);

  // Enhanced draw connections function with better visualization
  const drawConnections = (
    ctx: CanvasRenderingContext2D, 
    landmarks: Record<number, LandmarkPosition>, 
    width: number, 
    height: number,
    offsetX: number = 0,
    offsetY: number = 0
  ) => {
    // Define connections between landmarks with meaningful labels
    const connections = [
      // Torso
      { from: 11, to: 12, color: '#4CAF50', width: 3, label: 'shoulders' },
      { from: 12, to: 24, color: '#4CAF50', width: 3, label: 'right torso' },
      { from: 24, to: 23, color: '#4CAF50', width: 3, label: 'hips' },
      { from: 23, to: 11, color: '#4CAF50', width: 3, label: 'left torso' },
      
      // Right arm
      { from: 12, to: 14, color: '#2196F3', width: 3, label: 'right upper arm' },
      { from: 14, to: 16, color: '#2196F3', width: 3, label: 'right lower arm' },
      
      // Left arm
      { from: 11, to: 13, color: '#2196F3', width: 3, label: 'left upper arm' },
      { from: 13, to: 15, color: '#2196F3', width: 3, label: 'left lower arm' },
      
      // Right leg
      { from: 24, to: 26, color: '#FF9800', width: 3, label: 'right thigh' },
      { from: 26, to: 28, color: '#FF9800', width: 3, label: 'right calf' },
      
      // Left leg
      { from: 23, to: 25, color: '#FF9800', width: 3, label: 'left thigh' },
      { from: 25, to: 27, color: '#FF9800', width: 3, label: 'left calf' }
    ];
    
    // Draw connections with glow effect for better visibility
    connections.forEach(connection => {
      const { from, to, color, width: lineWidth } = connection;
      const startPoint = landmarks[from];
      const endPoint = landmarks[to];
      
      if (startPoint && endPoint) {
        // Scale coordinates to fit container size
        const startX = offsetX + startPoint.x * width;
        const startY = offsetY + startPoint.y * height;
        const endX = offsetX + endPoint.x * width;
        const endY = offsetY + endPoint.y * height;
        
        // Draw glow effect
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.lineWidth = lineWidth + 2;
        ctx.stroke();
        
        // Draw main line
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.stroke();
      }
    });
  };

  // Function to draw joints with labels
  const drawJoints = (
    ctx: CanvasRenderingContext2D, 
    landmarks: Record<number, LandmarkPosition>, 
    width: number, 
    height: number,
    offsetX: number = 0,
    offsetY: number = 0
  ) => {
    // Define joint names for key points
    const jointNames: Record<number, string> = {
      0: 'nose',
      11: 'left shoulder',
      12: 'right shoulder',
      13: 'left elbow',
      14: 'right elbow',
      15: 'left wrist',
      16: 'right wrist',
      23: 'left hip',
      24: 'right hip',
      25: 'left knee',
      26: 'right knee',
      27: 'left ankle',
      28: 'right ankle'
    };
    
    // Draw joints
    Object.entries(landmarks).forEach(([indexStr, landmark]) => {
      const index = parseInt(indexStr);
      const x = offsetX + landmark.x * width;
      const y = offsetY + landmark.y * height;
      const isKeyJoint = jointNames[index] !== undefined;
      
      // Draw circle with glow effect for better visibility
      if (isKeyJoint) {
        // Outer glow
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(255, 87, 34, 0.3)';
        ctx.fill();
      }
      
      // Draw main circle
      ctx.beginPath();
      ctx.arc(x, y, isKeyJoint ? 4 : 2, 0, 2 * Math.PI);
      ctx.fillStyle = isKeyJoint ? '#FF5722' : '#FFC107';
      ctx.fill();
      
      // Add stroke for better visibility
      ctx.strokeStyle = 'white';
      ctx.lineWidth = 1;
      ctx.stroke();
      
      // Optional: Add labels for key joints to help with debugging
      if (isKeyJoint && index % 10 === 0) { // Show even fewer labels to avoid clutter
        ctx.fillStyle = 'white';
        ctx.font = '10px Arial';
        ctx.fillText(jointNames[index], x + 6, y);
      }
    });
  };

  // Handle pose selection
  const handlePoseChange = (pose: string) => {
    setCurrentPose(pose)
    if (isInSession) {
      wsChangePose(pose)
      setFeedback(`Switching to ${pose} pose. Adjust your position to match.`)
    }
  }

  // Start calibration with countdown
  const handleCalibrate = () => {
    setIsCalibrating(true)
    setCountdown(3)
    setFeedback(`Get ready to calibrate ${currentPose} pose. Stand in position.`)
    
    // Countdown timer
    const timer = setInterval(() => {
      setCountdown((prev: number | null) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer)
          // Start calibration when countdown reaches 0
          wsStartCalibration(currentPose)
          setTimeout(() => {
            setIsCalibrating(false)
            setCountdown(null)
          }, 2000) // Give some time for calibration to complete
          return null
        }
        return prev - 1
      })
    }, 1000)
  }

  // Start or end yoga session
  const toggleSession = () => {
    if (isInSession) {
      wsEndSession()
      setIsInSession(false)
      setFeedback('Session ended. Great job!')
      setPoseProgress(0)
    } else {
      wsStartSession(currentPose)
      setIsInSession(true)
      setFeedback(`Starting session with ${currentPose}. Adjust your position to match the reference.`)
    }
  }

  // Get the calibration status for UI display
  const getPoseCalibrationStatus = (pose: string) => {
    return calibrationStatus[pose] ? 'Calibrated' : 'Not calibrated'
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Yoga Workouts</h1>
      
      {/* Feedback panel - Always visible */}
      {feedback && (
        <div className={`p-4 mb-4 rounded-lg ${
          isCalibrating ? 'bg-blue-100 text-blue-800 border border-blue-300' :
          isInSession ? 'bg-green-100 text-green-800 border border-green-300' :
          'bg-gray-100 text-gray-800 border border-gray-300'
        }`}>
          <div className="flex items-center">
            {isCalibrating && (
              <svg className="w-6 h-6 mr-2 text-blue-600 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
            {isInSession && (
              <svg className="w-6 h-6 mr-2 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            )}
            <span className="font-medium text-lg">{feedback}</span>
          </div>
          
          {/* Progress indicator for active sessions */}
          {isInSession && (
            <div className="mt-2">
              <div className="flex justify-between text-sm mb-1">
                <span>Pose Accuracy</span>
                <span>{poseProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-green-600 h-2.5 rounded-full" 
                  style={{ width: `${poseProgress}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      )}
      
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left panel: Video and controls */}
        <div className="lg:w-2/3 relative">
          {/* Webcam and overlay - Using object-cover to fill the container */}
          <div className="relative bg-black rounded-lg overflow-hidden w-full" style={{ height: "calc(100vh - 300px)", minHeight: "500px", maxHeight: "800px" }}>
            <video 
              ref={videoRef} 
              autoPlay 
              playsInline
              muted
              className="absolute top-0 left-0 w-full h-full object-cover" // Change back to object-cover
            />
            <canvas 
              ref={canvasRef} 
              className="absolute top-0 left-0 w-full h-full pointer-events-none" 
            />
            
            {/* Calibration countdown - keep this as it's functional */}
            {countdown !== null && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="bg-black bg-opacity-70 text-white text-6xl font-bold rounded-full w-32 h-32 flex items-center justify-center">
                  {countdown}
                </div>
              </div>
            )}
            
            {/* Reference pose - simplified */}
            <div className="absolute bottom-4 right-4 w-32 h-32 bg-black bg-opacity-50 rounded-lg overflow-hidden">
              <img 
                src={`/poses/${currentPose.replace(/\s+/g, '_')}.jpg`} 
                alt={`${currentPose} reference`}
                className="w-full h-full object-cover"
              />
            </div>
          </div>
          
          {/* Controls */}
          <div className="mt-4 flex flex-wrap gap-3">
            <button 
              onClick={toggleSession}
              disabled={!isConnected}
              className={`px-4 py-2 rounded-md font-medium ${
                !isConnected ? 'bg-gray-300 text-gray-500 cursor-not-allowed' :
                isInSession 
                  ? 'bg-red-500 hover:bg-red-600 text-white' 
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              }`}
            >
              {isInSession ? 'End Session' : 'Start Session'}
            </button>
            
            <button 
              onClick={handleCalibrate}
              disabled={isCalibrating || isInSession || !isConnected}
              className={`px-4 py-2 rounded-md font-medium ${
                isCalibrating || isInSession || !isConnected
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-green-500 hover:bg-green-600 text-white'
              }`}
            >
              Calibrate Pose
            </button>
          </div>
        </div>
        
        {/* Right panel: Pose selection and stats */}
        <div className="lg:w-1/3 bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold mb-4">Select Pose</h2>
          
          <div className="grid grid-cols-1 gap-3 mb-6">
            {POSES.map(pose => (
              <button
                key={pose}
                onClick={() => handlePoseChange(pose)}
                disabled={isCalibrating && !isInSession}
                className={`p-4 rounded-lg border-2 flex items-center ${
                  isCalibrating && !isInSession ? 'opacity-50 cursor-not-allowed ' : ''
                } ${
                  currentPose === pose 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-blue-300'
                }`}
              >
                <div className="w-16 h-16 bg-gray-100 rounded-lg mr-4 flex-shrink-0 overflow-hidden">
                  <img 
                    src={`/poses/${pose.replace(/\s+/g, '_')}.jpg`} 
                    alt={pose}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="flex-1">
                  <div className="flex justify-between">
                    <h3 className="font-medium">{pose}</h3>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      calibrationStatus[pose] ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {getPoseCalibrationStatus(pose)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    {currentPose === pose ? 'Currently selected' : 'Click to select'}
                  </p>
                </div>
              </button>
            ))}
          </div>
          
          <h2 className="text-xl font-bold mb-4">Session Stats</h2>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex justify-between mb-2">
              <span className="text-gray-500">Status:</span>
              <span className={isInSession ? 'text-green-600 font-medium' : 'text-gray-600'}>
                {isInSession ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-500">Current Pose:</span>
              <span className="font-medium">{currentPose}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-500">Connection:</span>
              <span className={isConnected ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {isInSession && (
              <div className="flex justify-between">
                <span className="text-gray-500">Accuracy:</span>
                <span className="font-medium">{poseProgress}%</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 