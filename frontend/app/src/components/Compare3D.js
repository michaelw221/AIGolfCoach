import React, { useState } from 'react';
import Skeleton3D from './Skeleton3D';

export default function Compare3D({ userSequence, proSequence }) {
  const [currentFrame, setCurrentFrame] = useState(0);

  // Use the length of the user's video as the max frame count
  const maxFrames = userSequence ? userSequence.length - 1 : 100;

  return (
    <div style={{ marginTop: '2rem' }}>
      <h3 style={{ textAlign: 'center' }}>3D Motion Analysis</h3>
      
      {/* 1. Side-by-side Canvases */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '1rem' }}>
        
        {/* User View */}
        <div>
          <h4 style={{ textAlign: 'center', color: 'var(--text-main)' }}>Your Swing</h4>
          <Skeleton3D sequence={userSequence} currentFrame={currentFrame} color="white" />
        </div>

        {/* Pro View */}
        <div>
          <h4 style={{ textAlign: 'center', color: 'var(--accent)' }}>Pro Reference</h4>
          <Skeleton3D sequence={proSequence} currentFrame={currentFrame} color="#10b981" />
        </div>

      </div>

      {/* 2. Timeline Slider Controls */}
      <div style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <span style={{ fontWeight: 'bold' }}>Timeline</span>
          <span>Frame: {currentFrame} / {maxFrames}</span>
        </div>
        
        <input 
          type="range" 
          min="0" 
          max={maxFrames} 
          value={currentFrame} 
          onChange={(e) => setCurrentFrame(parseInt(e.target.value))}
          style={{ width: '100%', cursor: 'pointer' }}
        />
        
        <p style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-light)', marginTop: '1rem' }}>
          🖱️ <strong>Tip:</strong> Click and drag the 3D models above to rotate the camera. Scroll to zoom in/out.
        </p>
      </div>
    </div>
  );
}