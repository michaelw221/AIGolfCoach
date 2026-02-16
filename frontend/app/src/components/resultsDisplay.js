// src/components/resultsDisplay.js
import React from 'react';

const ResultsDisplay = ({ status, results, error }) => {
  return (
    <article>
      <header>
        <h3>Analysis Results</h3>
      </header>
      
      <p><strong>Status:</strong> {status}</p>

      {/* 1. Display specific Pipeline Errors (Wrong Angle, No Person, etc.) */}
      {error && (
        <div style={{ 
          padding: '1rem', 
          backgroundColor: '#ffeeee', 
          color: '#bb0000', 
          border: '1px solid #ffcccc',
          borderRadius: '8px',
          marginBottom: '1rem' 
        }}>
          <strong>⚠️ Pipeline Error:</strong> {error}
        </div>
      )}

      {/* 2. Display actual analysis if no error and results exist */}
      {!error && results && (
        <div>
           {/* Your existing metrics table and faults list code here */}
           <h4>Diagnosed Faults:</h4>
           {/* ... */}
        </div>
      )}
    </article>
  );
};

export default ResultsDisplay;