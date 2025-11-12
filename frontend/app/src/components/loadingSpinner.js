// src/components/LoadingSpinner.js
import React from 'react';
import './css/loadingSpinner.css';

const LoadingSpinner = () => {
  return (
    <div className="spinner-container">
      <div className="loading-spinner"></div>
      <p>Analyzing... Please wait.</p>
    </div>
  );
};

export default LoadingSpinner;