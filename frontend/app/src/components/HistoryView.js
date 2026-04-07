import React, { useState, useEffect } from 'react';
import { getAuthHeader } from '../services/auth';

export default function HistoryView({ onViewResults }) {
  const [swings, setSwings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/swings', {
          headers: getAuthHeader()
        });
        if (!response.ok) {
          throw new Error('Failed to fetch history. Please log in again.');
        }
        const data = await response.json();
        setSwings(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', marginTop: '4rem' }}>Loading your swing history...</div>;
  }

  if (error) {
    return <div className="card" style={{ color: 'var(--error)', textAlign: 'center' }}>Error: {error}</div>;
  }

  return (
    <div className="card" style={{ maxWidth: '800px', margin: '2rem auto' }}>
      <h2 style={{ marginBottom: '2rem' }}>Your Swing History</h2>
      
      {swings.length === 0 ? (
        <p style={{ color: 'var(--text-light)' }}>You haven't analyzed any swings yet. Run a "New Analysis" to get started!</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {swings.map((swing) => (
            <div key={swing.id} style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              padding: '1.5rem', 
              border: '1px solid var(--border)', 
              borderRadius: '8px',
              backgroundColor: '#fafafa'
            }}>
              <div>
                <strong style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>
                  Analysis from {new Date(swing.created_at).toLocaleDateString()}
                </strong>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem', color: swing.status === 'complete' ? 'var(--success)' : (swing.status === 'failed' ? 'var(--error)' : 'var(--text-light)')}}>
                  Status: {swing.status}
                </p>
              </div>
              <button 
                className="btn-dark" 
                onClick={() => onViewResults(swing.analysis_results)}
                disabled={swing.status !== 'complete' || !swing.analysis_results}
              >
                View Results
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}