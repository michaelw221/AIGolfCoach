import React from 'react';

const ResultsDisplay = ({ status, results, error }) => {
  // 1. Prioritize displaying the explicit error from the App.js state
  if (error) {
    return (
      <article className="error">
        <header><h3>Error</h3></header>
        <p>{error}</p>
      </article>
    );
  }

  // 2. Check if the 'results' object itself contains an error from the Celery worker
  if (results?.error) {
    return (
      <article className="error">
        <header><h3>Pipeline Error</h3></header>
        <p>{results.error}</p>
      </article>
    );
  }

  // 3. Render the normal results if everything is successful
  return (
    <article>
      <header>
        <h3>Analysis Results</h3>
      </header>
      <p><strong>Status:</strong> {status}</p>

      {results && (
        <div>
          <h4>Diagnosed Faults:</h4>
          {/* Use optional chaining (?.) to prevent crashes if key is missing */}
          {results.diagnosed_faults?.length > 0 ? (
            <ul>
              {results.diagnosed_faults.map((fault, index) => (
                <li key={index}>
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
                <td>{results.metrics?.spine_angle_change_at_impact?.toFixed(1) || "N/A"}°</td>
              </tr>
              <tr>
                <td>Max Head Sway in Backswing</td>
                <td>{results.metrics?.max_head_sway_cm?.toFixed(1) || "N/A"} cm</td>
              </tr>
              <tr>
                <td>Backswing Length (Arm Angle)</td>
                <td>{results.metrics?.backswing_length_angle?.toFixed(1) || "N/A"}°</td>
              </tr>
              <tr>
                <td>Lead Arm Angle at Impact</td>
                <td>{results.metrics?.lead_arm_angle_impact?.toFixed(1) || "N/A"}°</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
};

export default ResultsDisplay;