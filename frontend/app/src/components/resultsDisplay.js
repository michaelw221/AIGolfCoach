// src/components/ResultsDisplay.js
import React from 'react';

const ResultsDisplay = ({ status, results, error }) => {
  return (
    <article>
      <header>
        <h3>Analysis Results</h3>
      </header>
      <p><strong>Status:</strong> {status}</p>

      {error && (
        <pre className="error"><code>Error: {error}</code></pre>
      )}
      
      {results && (
        <div>
          <h4>Diagnosed Faults:</h4>
          {results.diagnosed_faults.length > 0 ? (
            <ul>
              {results.diagnosed_faults.map((fault) => (
                <li key={fault.name}>
                  <strong>{fault.name}:</strong> {fault.detail}
                </li>
              ))}
            </ul>
          ) : (
            <p>No major faults detected. Good swing!</p>
          )}

          <hr />

          <h4>Key Metrics:</h4>
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Spine Angle Change at Impact</td>
                <td>{results.metrics.spine_angle_change_at_impact.toFixed(1)}°</td>
              </tr>
              <tr>
                <td>Max Head Sway in Backswing</td>
                <td>{results.metrics.max_head_sway_cm.toFixed(1)} cm</td>
              </tr>
              <tr>
                <td>Backswing Length (Arm Angle)</td>
                <td>{results.metrics.backswing_length_angle.toFixed(1)}°</td>
              </tr>
              <tr>
                <td>Lead Arm Angle at Impact</td>
                <td>{results.metrics.lead_arm_angle_impact.toFixed(1)}°</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
};

export default ResultsDisplay;