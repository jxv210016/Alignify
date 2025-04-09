import React, { useState, useEffect, useRef, useMemo } from 'react';
import useWebSocket from '../hooks/useWebSocket';

function Workouts() {
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const [currentPose, setCurrentPose] = useState('Warrior I');
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [calibrationStep, setCalibrationStep] = useState(0);
  const [calibrationCountdown, setCalibrationCountdown] = useState(5);
  const [sessionCountdown, setSessionCountdown] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [countdownActive, setCountdownActive] = useState(false);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const timerRef = useRef(null);
  
  // Get the correct WebSocket URL based on the current window location
  const wsUrl = (() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use localhost and port 5000 for the backend WebSocket
    return `${protocol}//127.0.0.1:5000/ws`;
  })();
  
  // Using our custom WebSocket hook with the dynamically determined URL
  const { isConnected, lastMessage, sendMessage } = useWebSocket(wsUrl);
  
  // Use useMemo to prevent recreation of poses array on each render
  const poses = useMemo(() => [
    { id: 1, name: 'Warrior I', image: '/poses/warrior1.png' },
    { id: 2, name: 'Warrior II', image: '/poses/warrior2.png' },
    { id: 3, name: 'Tree Pose', image: '/poses/tree.png' },
    { id: 4, name: 'Downward Dog', image: '/poses/downward_dog.png' }
  ], []);
  
  // Start webcam
  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            setIsWebcamActive(true);
          }
        })
        .catch(err => {
          console.error("Error accessing webcam:", err);
        });
      
      // Clean up function to stop the webcam when component unmounts
      return () => {
        const video = videoRef.current;
        if (video && video.srcObject) {
          const tracks = video.srcObject.getTracks();
          tracks.forEach(track => track.stop());
        }
      };
    }
  }, []);
  
  // Process WebSocket messages to update UI
  useEffect(() => {
    if (lastMessage && lastMessage.landmarks) {
      drawPoseOverlay(lastMessage.landmarks);
      
      // If session is active and we received feedback, update the UI
      if (isSessionActive && lastMessage.feedback) {
        setFeedback(lastMessage.feedback);
      }
    }
  }, [lastMessage, isSessionActive]);
  
  // Calibration countdown timer (fixed)
  useEffect(() => {
    if (isCalibrating && countdownActive) {
      if (calibrationCountdown > 0) {
        timerRef.current = setTimeout(() => {
          setCalibrationCountdown(prev => prev - 1);
        }, 1000);
      } else {
        // Countdown finished, send calibration data to server
        sendMessage({
          action: 'calibrate',
          pose: poses[calibrationStep].name
        });
        
        // Reset countdown for next pose or finish calibration
        if (calibrationStep < poses.length - 1) {
          // Move to next pose
          setCalibrationStep(prev => prev + 1);
          setCalibrationCountdown(5);
          setFeedback(`Get ready to calibrate "${poses[calibrationStep + 1].name}" pose in 5 seconds`);
        } else {
          // Calibration completed
          setIsCalibrating(false);
          setCalibrationStep(0);
          setCountdownActive(false);
          setFeedback('Calibration completed! You can now start a session.');
        }
      }
    }
    
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [isCalibrating, calibrationCountdown, calibrationStep, poses, sendMessage, countdownActive]);
  
  // Session countdown timer
  useEffect(() => {
    if (isSessionActive && sessionCountdown > 0) {
      timerRef.current = setTimeout(() => {
        setSessionCountdown(prev => prev - 1);
      }, 1000);
    } else if (isSessionActive && sessionCountdown === 0) {
      // Send session start command to server
      sendMessage({
        action: 'startSession',
        pose: currentPose
      });
      setFeedback('Session started! Follow the reference pose.');
    }
    
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [isSessionActive, sessionCountdown, currentPose, sendMessage]);
  
  // Draw pose overlay on canvas
  const drawPoseOverlay = (landmarks) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    
    if (!canvas || !video || !video.videoWidth) return;
    
    const ctx = canvas.getContext('2d');
    const videoWidth = video.videoWidth;
    const videoHeight = video.videoHeight;
    
    canvas.width = videoWidth;
    canvas.height = videoHeight;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw connecting lines
    const connections = [
      // Torso
      [11, 12], [12, 24], [24, 23], [23, 11],
      // Right arm
      [12, 14], [14, 16],
      // Left arm
      [11, 13], [13, 15],
      // Right leg
      [24, 26], [26, 28],
      // Left leg
      [23, 25], [25, 27]
    ];
    
    ctx.strokeStyle = '#4CAF50';
    ctx.lineWidth = 4;
    
    connections.forEach(([startIdx, endIdx]) => {
      if (landmarks[startIdx] && landmarks[endIdx]) {
        ctx.beginPath();
        ctx.moveTo(landmarks[startIdx].x * videoWidth, landmarks[startIdx].y * videoHeight);
        ctx.lineTo(landmarks[endIdx].x * videoWidth, landmarks[endIdx].y * videoHeight);
        ctx.stroke();
      }
    });
    
    // Draw landmarks
    ctx.fillStyle = '#FF5722';
    
    Object.values(landmarks).forEach(point => {
      ctx.beginPath();
      ctx.arc(point.x * videoWidth, point.y * videoHeight, 8, 0, 2 * Math.PI);
      ctx.fill();
    });
  };
  
  // Handler for calibrate button
  const handleCalibrate = () => {
    if (!isCalibrating && !isSessionActive) {
      setIsCalibrating(true);
      setCalibrationCountdown(5);
      setCalibrationStep(0);
      setCountdownActive(true);
      setFeedback(`Get ready to calibrate "${poses[0].name}" pose in 5 seconds`);
    }
  };
  
  // Handler for start session button
  const handleStartSession = () => {
    if (!isSessionActive && !isCalibrating) {
      setIsSessionActive(true);
      setSessionCountdown(3);
      setFeedback(`Session starting in 3 seconds. Prepare for "${currentPose}" pose.`);
    } else if (isSessionActive) {
      setIsSessionActive(false);
      setFeedback('Session ended.');
      
      // Send session end command to server
      sendMessage({
        action: 'endSession'
      });
    }
  };
  
  // Change the current pose
  const handleChangePose = (poseName) => {
    setCurrentPose(poseName);
    setFeedback(`Pose changed to "${poseName}"`);
    
    // Send pose change command to server
    if (isSessionActive) {
      sendMessage({
        action: 'changePose',
        pose: poseName
      });
    }
  };
  
  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Workouts</h1>
      
      <div className="flex justify-between mb-4">
        <div>
          <button 
            className={`px-4 py-2 rounded mr-2 ${isSessionActive ? 'bg-red-600 text-white' : 'bg-purple-600 text-white'}`}
            onClick={handleStartSession}
            disabled={!isConnected}
          >
            {isSessionActive ? 'End Session' : 'Start Session'}
          </button>
          <button 
            className="bg-gray-200 px-4 py-2 rounded"
            onClick={handleCalibrate}
            disabled={isCalibrating || isSessionActive || !isConnected}
          >
            Calibrate
          </button>
        </div>
        <div className={`px-4 py-2 rounded ${isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>
      
      {/* Connection Status Information */}
      {!isConnected && (
        <div className="p-4 mb-4 rounded bg-yellow-100 text-yellow-800">
          <p className="font-bold">Connection Status:</p>
          <p>Unable to connect to the backend server. Please ensure:</p>
          <ol className="list-decimal ml-6 mt-2">
            <li>The backend server is running at 127.0.0.1:5000</li>
            <li>There are no firewall or network restrictions blocking WebSocket connections</li>
            <li>You can try refreshing the page to reconnect</li>
          </ol>
        </div>
      )}
      
      {/* Feedback and Status */}
      {(feedback || isCalibrating || isSessionActive) && (
        <div className={`p-4 mb-4 rounded ${isCalibrating ? 'bg-blue-100 text-blue-800' : isSessionActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
          {isCalibrating && (
            <div className="font-bold mb-2">
              Calibrating: {poses[calibrationStep].name} {calibrationCountdown > 0 && `(${calibrationCountdown}s)`}
            </div>
          )}
          {isSessionActive && sessionCountdown > 0 && (
            <div className="font-bold mb-2">
              Session starting in {sessionCountdown}s
            </div>
          )}
          <div>{feedback}</div>
        </div>
      )}
      
      {/* Video container */}
      <div className="relative">
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline 
          className="w-full h-auto rounded shadow-md"
          style={{ maxHeight: '70vh' }}
        />
        
        <canvas 
          ref={canvasRef} 
          className="absolute top-0 left-0 w-full h-full"
        />
        
        {/* Loading overlay during calibration or countdown */}
        {((isCalibrating && countdownActive) || (isSessionActive && sessionCountdown > 0)) && (
          <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
            <div className="text-white text-6xl font-bold">
              {isCalibrating ? calibrationCountdown : sessionCountdown}
            </div>
          </div>
        )}
        
        {/* Current pose reference */}
        <div className="absolute bottom-4 right-4 p-2 bg-white rounded shadow-md">
          <p className="text-sm font-bold mb-1">Current Pose:</p>
          <div className="flex items-center">
            <img 
              src={poses.find(p => p.name === currentPose)?.image || '/poses/warrior1.png'} 
              alt={currentPose} 
              className="w-24 h-24 object-cover rounded mr-2"
            />
            <span className="font-bold">{currentPose}</span>
          </div>
        </div>
      </div>
      
      {/* Pose selection */}
      <div className="mt-4 flex flex-wrap gap-4">
        {poses.map(pose => (
          <button
            key={pose.id}
            className={`px-4 py-2 rounded border ${currentPose === pose.name ? 'border-purple-600 bg-purple-100' : 'border-gray-300'}`}
            onClick={() => handleChangePose(pose.name)}
            disabled={isCalibrating}
          >
            {pose.name}
          </button>
        ))}
      </div>
    </div>
  );
}

export default Workouts; 