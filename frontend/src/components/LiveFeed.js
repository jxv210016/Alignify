// src/components/LiveFeed.js
import React, { useRef, useEffect } from 'react';

function LiveFeed({ setFeedback, overlayText }) {
  const videoRef = useRef(null);

  // Start the webcam feed when the component mounts.
  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        })
        .catch(err => console.error("Webcam error:", err));
    }
  }, []);

  // Capture frames periodically and send them to Flask.
  useEffect(() => {
    const interval = setInterval(() => {
      if (videoRef.current && videoRef.current.videoWidth && videoRef.current.videoHeight) {
        // Create a canvas element to capture the current video frame.
        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg');

        // Send the captured frame to the Flask backend.
        fetch('http://127.0.0.1:5000/process_frame', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ image: dataUrl })
        })
          .then(response => response.json())
          .then(data => {
            // Update the feedback state from the response.
            if (data.display) {
              setFeedback(data.display);
            }
          })
          .catch(err => console.error('Error processing frame:', err));
      }
    }, 1000); // Adjust the interval (milliseconds) as needed.

    return () => clearInterval(interval);
  }, [setFeedback]);

  return (
    <div className="live-section">
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="video"
      />
      {overlayText && <div className="overlay">{overlayText}</div>}
    </div>
  );
}

export default LiveFeed;
