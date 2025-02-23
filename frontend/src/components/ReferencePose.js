// src/components/ReferencePose.js
import React from 'react';

function ReferencePose({ pose }) {
  return (
    <div className="reference-section">
      <div className="ref-container">
        <img src={pose.image} alt={pose.name} className="ref-image" />
        <div className="pose-name">{pose.name}</div>
      </div>
    </div>
  );
}

export default ReferencePose;
