// src/components/CompletionScreen.js
import React from 'react';

function CompletionScreen({ onRestart }) {
  return (
    <div className="complete-screen">
      <div>Congratulations! You've completed the YN Yoga routine!</div>
      <button onClick={onRestart} className="restart-button">
        Restart
      </button>
    </div>
  );
}

export default CompletionScreen;
