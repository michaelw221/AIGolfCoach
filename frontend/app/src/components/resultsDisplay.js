import React from 'react';

function ResultsDisplay({ status, results, error }) {
  // 1. Handle error state
  if (error) {
    return (
      <div className="error" style={{ backgroundColor: '#fee2e2', color: '#b91c1c', padding: '1rem', borderRadius: '5px', marginTop: '1rem' }}>
        <strong>Error:</strong> {error}
      </div>
    );
  }

  // 2. Handle loading/empty state
  if (!results) return null;

  // 3. Safely extract data
  const faults = results.diagnosed_faults || [];
  const debugImages = results.debug_images || {}; // New: get the images

  return (
    <div className="results-container" style={{ marginTop: '2rem' }}>
      <h3>Analysis Results</h3>
      <p><strong>Status:</strong> {status}</p>

      {/* NEW: Visual Verification Section */}
      {Object.keys(debugImages).length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h4>Key Frame Visualization</h4>
          {Object.entries(debugImages).map(([view, phases]) => (
            <div key={view} style={{ marginBottom: '1.5rem' }}>
              <h5>{view.toUpperCase()} View</h5>
              <div style={{ display: 'flex', gap: '15px', overflowX: 'auto' }}>
                {Object.entries(phases).map(([phase, imgData]) => (
                  <div key={phase} style={{ textAlign: 'center' }}>
                    <p style={{ fontSize: '0.8rem', margin: '0' }}>{phase.toUpperCase()}</p>
                    <img 
                      src={`data:image/jpeg;base64,${imgData}`} 
                      alt={`${view}-${phase}`} 
                      style={{ width: '200px', border: '2px solid #ddd', borderRadius: '4px' }} 
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <h4>Diagnosed Faults:</h4>
      {faults.length === 0 ? (
        <p style={{ color: '#10b981', fontWeight: 'bold' }}>
          ✅ No major faults detected. Great swing!
        </p>
      ) : (
        <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
          {faults.map((fault, index) => (
            <li key={index} style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #ef4444', borderRadius: '5px', backgroundColor: '#fef2f2' }}>
              <strong style={{ color: '#b91c1c', fontSize: '1.1rem' }}>{fault.name}</strong>
              <p style={{ margin: '0.5rem 0 0 0', color: '#7f1d1d' }}>{fault.detail}</p>
            </li>
          ))}
        </ul>
      )}

      <h4 style={{ marginTop: '2rem' }}>Key Metrics:</h4>
      <pre style={{ fontSize: '0.8rem', backgroundColor: '#1a212c', color: '#e2e8f0', padding: '1rem', borderRadius: '5px', overflowX: 'auto' }}>
        {JSON.stringify(results.metrics, null, 2)}
      </pre>
    </div>
  );
}

export default ResultsDisplay;