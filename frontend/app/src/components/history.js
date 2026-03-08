import React, { useEffect, useState } from 'react';
import { getAuthHeader } from '../services/auth';

function History({ onSelectJob }) {
  const [swings, setSwings] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/swings', { headers: getAuthHeader() })
      .then(res => res.json())
      .then(data => setSwings(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="history-section">
      <h3>Your Swing History</h3>
      {swings.length === 0 ? <p>No swings analyzed yet.</p> : (
        <table>
          <thead>
            <tr><th>Date</th><th>Status</th><th>Action</th></tr>
          </thead>
          <tbody>
            {swings.map(s => (
              <tr key={s.id}>
                <td>{new Date(s.created_at).toLocaleDateString()}</td>
                <td>{s.status}</td>
                <td>
                  <button onClick={() => onSelectJob(s.id)}>View Results</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default History;