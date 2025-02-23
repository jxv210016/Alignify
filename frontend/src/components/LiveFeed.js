// src/components/LiveFeed.js
import React, { useRef, useEffect } from 'react';

function LiveFeed({ overlayText }) {
  const videoRef = useRef(null);

  useEffect(() => {
    // Start webcam feed
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        })
        .catch(err => {
          console.error("Error accessing webcam: ", err);
        });
    }
  }, []);

  return (
    <div className="live-section">
      <video ref={videoRef} autoPlay muted playsInline className="video" />
      {overlayText && <div className="overlay">{overlayText}</div>}
    </div>
  );
}

export default LiveFeed;
