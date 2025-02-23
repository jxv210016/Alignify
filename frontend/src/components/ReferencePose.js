// src/components/ReferencePose.js
import React from 'react';

function ReferencePose({ imageSrc, poseName }) {
  return (
    <div className="reference-pose" style={{ textAlign: 'center' }}>
      <img
        src={imageSrc}
        alt={poseName}
        style={{ maxWidth: '100%', borderRadius: '8px' }}
      />
      <h3>{poseName}</h3>
    </div>
  );
}

export default ReferencePose;
