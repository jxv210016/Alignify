// src/components/LivePoseFeed.js
import React, { useRef, useEffect } from 'react';
import { Pose, POSE_CONNECTIONS } from '@mediapipe/pose';
import { Camera } from '@mediapipe/camera_utils';
import { drawConnectors, drawLandmarks } from '@mediapipe/drawing_utils';

function LivePoseFeed() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    // 1. Create a Pose instance for local landmark detection.
    const pose = new Pose({
      locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
      }
    });
    pose.setOptions({
      modelComplexity: 1,
      smoothLandmarks: true,
      enableSegmentation: false,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });

    // 2. onResults callback: Draw the pose landmarks on the canvas.
    pose.onResults((results) => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas) return;

      const canvasCtx = canvas.getContext('2d');

      // Match canvas size to video.
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Clear the canvas for the new frame.
      canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw the video feed first.
      canvasCtx.drawImage(results.image, 0, 0, canvas.width, canvas.height);

      // Draw pose landmarks over the video.
      if (results.poseLandmarks) {
        drawConnectors(
          canvasCtx,
          results.poseLandmarks,
          POSE_CONNECTIONS,
          { color: '#00FF00', lineWidth: 4 }
        );
        drawLandmarks(
          canvasCtx,
          results.poseLandmarks,
          { color: '#FF0000', lineWidth: 2 }
        );
      }
    });

    // 3. Set up the MediaPipe Camera to stream video and send frames to Pose.
    let camera = null;
    if (videoRef.current) {
      camera = new Camera(videoRef.current, {
        onFrame: async () => {
          await pose.send({ image: videoRef.current });
        },
        width: 640,
        height: 480
      });
      camera.start();
    }

    // Cleanup when unmounting.
    return () => {
      if (camera) {
        camera.stop();
      }
      pose.close();
    };
  }, []);

  // 4. Periodically capture the canvas as a base64 image and send it to Flask.
  useEffect(() => {
    const interval = setInterval(() => {
      // If the canvas is rendering, capture it as a JPEG data URL.
      if (canvasRef.current) {
        const dataUrl = canvasRef.current.toDataURL('image/jpeg');

        fetch('http://127.0.0.1:5000/process_frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: dataUrl })
        })
          .then(res => res.json())
          .then(data => {
            // 'data' might contain text feedback from your backend.
            console.log('Backend response:', data);
          })
          .catch(err => console.error('Error sending frame:', err));
      }
    }, 2000); // every 2 seconds; adjust as needed

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ position: 'relative' }}>
      {/* Hidden video element used by the Camera utility */}
      <video ref={videoRef} style={{ display: 'none' }} />
      {/* Canvas displays the local pose detection overlays */}
      <canvas ref={canvasRef} style={{ width: '100%' }} />
    </div>
  );
}

export default LivePoseFeed;
