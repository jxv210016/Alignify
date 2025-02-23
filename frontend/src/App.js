// src/App.js
import React from 'react';
import LivePoseFeed from './components/LivePoseFeed';
import ReferencePose from './components/ReferencePose';

function App() {
  // Example reference image in public/assets
  const referencePoseImage = '/assets/warrior.jpg';
  const referencePoseName = 'Warrior Pose';

  return (
    <div className="app-container">
      <h1>YN Yoga Pose Analysis</h1>
      <div className="windows-container">
        {/* Left window: live feed with pose detection */}
        <div className="window live-window">
          <h2>Live Analysis</h2>
          <LivePoseFeed />
        </div>

        {/* Right window: reference pose image */}
        <div className="window reference-window">
          <h2>Reference Pose</h2>
          <ReferencePose imageSrc={referencePoseImage} poseName={referencePoseName} />
        </div>
      </div>
    </div>
  );
}

export default App;
