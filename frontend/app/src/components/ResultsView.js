import React from 'react';
import Compare3D from './Compare3D';

export default function ResultsView({ results }) {
  if (!results) return null;

  const faults = results.diagnosed_faults?.faults || [];
  const drills = results.diagnosed_faults?.recommended_drills ||[];
  const user3DData = results.keypoints_3d ||[];

  const getEmbedUrl = (url) => {
    try { 
      return `https://www.youtube.com/embed/${url.split('v=')[1].split('&')[0]}`; 
    } catch { 
      return url; 
    }
  };

  return (
    <div>
      {/* SECTION 1: 3D Visualization */}
      <div style={{ minHeight: '80vh' }}>
        
        <Compare3D 
            userSequence={user3DData} 
            proSequence={user3DData} 
        />

        <div style={{ textAlign: 'center', marginTop: '4rem', cursor: 'pointer' }} onClick={() => document.getElementById('analysis-section').scrollIntoView({ behavior: 'smooth' })}>
            <p style={{ color: 'var(--text-light)', fontWeight: '600' }}>Scroll for Analysis & Drills</p>
            <div style={{ width: '20px', height: '20px', borderRight: '3px solid var(--accent)', borderBottom: '3px solid var(--accent)', transform: 'rotate(45deg)', margin: '0 auto' }}></div>
        </div>
      </div>

      {/* SECTION 2: Faults and Drills */}
      <div id="analysis-section" style={{ paddingTop: '3rem' }}>
        <h2>Analysis Breakdown</h2>
        {faults.length === 0 ? (
          <div className="card" style={{ borderColor: 'var(--success)', backgroundColor: '#ecfdf5', color: '#065f46' }}>
            <h3>✅ No major faults detected!</h3>
            <p>Your biomechanical metrics are within professional ranges.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '3rem' }}>
            {faults.map((f, i) => (
              <div key={i} className="fault-card">
                <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--error)' }}>{f.name}</h3>
                <p style={{ margin: 0 }}>{f.detail}</p>
                <small style={{ color: '#991b1b', fontWeight: 'bold', display: 'block', marginTop: '0.5rem' }}>
                  Severity Score: {f.severity ? f.severity.toFixed(2) : 'N/A'}
                </small>
              </div>
            ))}
          </div>
        )}

        <h2>Recommended Drills</h2>
        <div className="visual-grid" style={{ gap: '20px' }}>
          {drills.map((drill, index) => (
            <div key={index} className="drill-card">
              <iframe
                width="100%" height="200" src={getEmbedUrl(drill.url)} frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen
              ></iframe>
              <div className="drill-card-body">
                <h4 style={{ margin: '0 0 0.5rem 0' }}>{drill.title}</h4>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}