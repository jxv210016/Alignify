// src/components/Header.js
import React from 'react';

function Header({ onQuit }) {
  return (
    <header className="header">
      <button onClick={onQuit} className="quit-button">
        Quit
      </button>
    </header>
  );
}

export default Header;
