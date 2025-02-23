// src/App.js
import React, { useEffect, useState, useRef } from 'react';
import './App.css';
import Header from './components/Header';
import LiveFeed from './components/LiveFeed';
import ReferencePose from './components/ReferencePose';
import CompletionScreen from './components/CompletionScreen';

// Define your pose sequence (adjust asset paths as needed)
const poseSequence = [
  { image: '/assets/warrior.jpg', name: 'Warrior', holdDuration: 5 },
  { image: '/assets/warrior_II_left.jpg', name: 'Warrior II (Left)', holdDuration: 5 },
  { image: '/assets/warrior_II_right.jpg', name: 'Warrior II (Right)', holdDuration: 5 },
  { image: '/assets/tree.jpg', name: 'Tree', holdDuration: 5 },
  { image: '/assets/downward_dog.jpg', name: 'Downward Dog', holdDuration: 5 },
];

function App() {
  const [currentPoseIndex, setCurrentPoseIndex] = useState(0);
  const [sessionState, setSessionState] = useState('transition'); // 'transition', 'active', 'complete'
  const [countdown, setCountdown] = useState(5);
  const [overlayText, setOverlayText] = useState('');
  
  // Start transition countdown for the current pose
  useEffect(() => {
    if (sessionState === 'transition') {
      setCountdown(5);
      setOverlayText(`Get ready for ${poseSequence[currentPoseIndex].name}... 5`);
      const intervalId = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(intervalId);
            setSessionState('active');
            return 0;
          } else {
            setOverlayText(`Get ready for ${poseSequence[currentPoseIndex].name}... ${prev - 1}`);
            return prev - 1;
          }
        });
      }, 1000);
      return () => clearInterval(intervalId);
    }
  }, [sessionState, currentPoseIndex]);

  // Active pose state: simulate hold duration
  useEffect(() => {
    if (sessionState === 'active') {
      setOverlayText('Hold the pose!');
      const holdTime = poseSequence[currentPoseIndex].holdDuration * 1000;
      const timeoutId = setTimeout(() => {
        if (currentPoseIndex + 1 < poseSequence.length) {
          setCurrentPoseIndex(currentPoseIndex + 1);
          setSessionState('transition');
        } else {
          setSessionState('complete');
          setOverlayText('');
        }
      }, holdTime);
      return () => clearTimeout(timeoutId);
    }
  }, [sessionState, currentPoseIndex]);

  const handleQuit = () => {
    // For now, simply reload the page
    window.location.reload();
  };

  const handleRestart = () => {
    setCurrentPoseIndex(0);
    setSessionState('transition');
    setOverlayText('');
  };

  return (
    <div className="app-container">
      <Header onQuit={handleQuit} />
      <div className="main-container">
        <LiveFeed overlayText={overlayText} />
        <ReferencePose 
          pose={poseSequence[currentPoseIndex]} 
        />
      </div>
      {sessionState === 'complete' && (
        <CompletionScreen onRestart={handleRestart} />
      )}
    </div>
  );
}

export default App;
