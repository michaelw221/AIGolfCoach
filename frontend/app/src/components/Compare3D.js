import React, { useState } from 'react';
import Skeleton3D from './Skeleton3D';

export default function Compare3D({ userSequence, proSequence }) {
  const [progress, setProgress] = useState(0);

  // 1. Find the maximum frames for both sequences
  const userMaxFrames = userSequence && userSequence.length > 0 ? userSequence.length - 1 : 0;
  const validProSequence = proSequence && proSequence.length > 0 ? proSequence : userSequence;
  const proMaxFrames = validProSequence.length - 1;

  // 2. Map the 0-100% progress to the specific frame index for each golfer
  const userCurrentFrame = Math.floor((progress / 100) * userMaxFrames);
  const proCurrentFrame = Math.floor((progress / 100) * proMaxFrames);

  return (
    <div style={{ marginTop: '2rem' }}>
      <h3 style={{ textAlign: 'center' }}>3D Motion Analysis</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '1rem' }}>
        
        {/* User View */}
        <div>
          <h4 style={{ textAlign: 'center', color: 'var(--text-main)' }}>Your Swing</h4>
          <Skeleton3D sequence={userSequence} currentFrame={userCurrentFrame} color="white" />
        </div>

        {/* Pro View */}
        <div>
          <h4 style={{ textAlign: 'center', color: 'var(--accent)' }}>Pro Reference</h4>
          <Skeleton3D sequence={validProSequence} currentFrame={proCurrentFrame} color="#10b981" />
        </div>

      </div>

      {/* Timeline Slider Controls */}
      <div style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <span style={{ fontWeight: 'bold' }}>Swing Timeline</span>
          <span>{progress}% Complete</span>
        </div>
        
        <input 
          type="range" 
          min="0" 
          max="100" 
          value={progress} 
          onChange={(e) => setProgress(parseInt(e.target.value))}
          style={{ width: '100%', cursor: 'pointer' }}
        />
        
        <p style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--text-light)', marginTop: '1rem' }}>
          🖱️ <strong>Tip:</strong> Click and drag the 3D models above to rotate the camera. Scroll to zoom in/out.
        </p>
      </div>
    </div>
  );
}