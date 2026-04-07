import React from 'react';
import Compare3D from './Compare3D';

const FAULT_DESCRIPTIONS = {
  "Early Extension (Loss of Posture)": "Your hips moved closer to the golf ball during the downswing, causing your torso to stand up. This eliminates the space your arms need to swing freely, leading to inconsistent strikes, blocks, and hooks.",
  "Sway": "Your upper body drifted too far laterally away from the target during the backswing. This makes it incredibly difficult to return to a solid impact position and causes a severe loss of power.",
  "Excessive Slide": "Your lower body shifted too far forward toward the target during the downswing without rotating. This gets the club 'stuck' behind you, forcing your hands to flip at the ball to square the clubface.",
  "Over-swinging": "The club traveled well past parallel at the top of your swing. This loss of structural integrity makes it difficult to sequence the downswing correctly and reduces your overall control.",
  "Bent Lead Arm at Impact (Chicken Wing)": "Your lead elbow broke down and bent as you hit the ball. This 'chicken wing' motion prevents full extension through impact, robbing you of significant distance and accuracy.",
  "Poor Separation": "Your hips and shoulders rotated together as one single unit. For maximum power, your lower body needs to lead the downswing to create a 'stretch' (X-Factor) against your upper body.",
  "Loss of Knee Flex": "Your lead knee straightened too early or locked out during the backswing. Maintaining dynamic flex in your knees is essential for a stable, powerful base to rotate around.",
  "Over the Top": "Your hands and shoulders initiated the downswing by throwing the club outward over the correct plane. This creates an out-to-in swing path, resulting in weak slices or pull-hooks."
};

let proData =[];
try {
  proData = require('../assets/pro_swing.json');
} catch (e) {
  console.log("Pro data not found yet.");
}

// Dynamic Scoring Engine
const calculateScores = (metrics) => {
  const clamp = (val) => Math.max(1.0, Math.min(10.0, val));

  // 1. Posture (Spine Angle) - Loses 1 point for every 2 degrees of change
  const spine = Math.abs(metrics.spine_angle_change_at_impact || 0);
  const postureScore = clamp(10.0 - (spine / 2));

  // 2. Stability (Sway) - Loses 1 point for every 8cm of sway
  const sway = Math.abs(metrics.max_head_sway_cm || 0);
  const stabilityScore = clamp(10.0 - (sway / 8));

  // 3. Power (X-Factor) - Perfect 10 is 30+ degrees of separation
  const xFactor = Math.abs(metrics.x_factor_angle || 0);
  const powerScore = clamp((xFactor / 25) * 10);

  // 4. Swing Plane (Hand Path / Over the Top) - Loses 1 pt per 6 degrees outward
  const path = Math.abs(metrics.initial_hand_path_angle || 0);
  const planeScore = clamp(10.0 - (path / 6));

  const overall = (postureScore + stabilityScore + powerScore + planeScore) / 4;

  return {
    overall: overall.toFixed(1),
    posture: postureScore.toFixed(1),
    stability: stabilityScore.toFixed(1),
    power: powerScore.toFixed(1),
    plane: planeScore.toFixed(1)
  };
};

// Helper for dynamic colors
const getScoreColor = (score) => {
  if (score >= 8.0) return '#10b981';
  if (score >= 5.0) return '#f59e0b';
  return '#ef4444';
};

export default function ResultsView({ results }) {
  if (!results) return null;

  const faults = results.diagnosed_faults?.faults ||[];
  const drills = results.diagnosed_faults?.recommended_drills ||[];
  const user3DData = results.keypoints_3d ||[];
  const scores = calculateScores(results.metrics || {});

  const getEmbedUrl = (url) => {
    try { 
      return `https://www.youtube.com/embed/${url.split('v=')[1].split('&')[0]}`; 
    } catch { 
      return url; 
    }
  };

  return (
    <div>
      <div style={{ backgroundColor: 'var(--primary-dark)', color: 'white', borderRadius: '12px', padding: '2rem', marginBottom: '3rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', boxShadow: '0 10px 25px rgba(0,0,0,0.1)' }}>
        
        {/* Left Side: Massive Overall Score */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', borderRight: '1px solid #555' }}>
          <h2 style={{ margin: '0 0 0.5rem 0', color: '#585757', fontSize: '1.2rem', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '1px' }}>Overall Swing Score</h2>
          <div style={{ fontSize: '4.5rem', fontWeight: '700', color: getScoreColor(scores.overall), textShadow: '0 2px 10px rgba(0,0,0,0.3)' }}>
            {scores.overall} <span style={{ fontSize: '2rem', color: '#575757' }}>/ 10</span>
          </div>
          <p style={{ color: '#5a5a5a', marginTop: '0.5rem' }}>Based on 4 core biomechanical pillars</p>
        </div>

        {/* Right Side: Score Breakdown Bars */}
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '1.2rem', paddingRight: '1rem' }}>
          
          {[
            { label: 'Posture (Spine Stability)', value: scores.posture },
            { label: 'Stability (Head Sway)', value: scores.stability },
            { label: 'Power (X-Factor Separation)', value: scores.power },
            { label: 'Swing Plane (Hand Path)', value: scores.plane }
          ].map((stat, idx) => (
            <div key={idx}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem', fontSize: '0.9rem', color: '#5a5a5a' }}>
                <span style={{ fontWeight: '600' }}>{stat.label}</span>
                <span style={{ fontWeight: 'bold', color: getScoreColor(stat.value) }}>{stat.value} / 10</span>
              </div>
              <div style={{ width: '100%', height: '8px', backgroundColor: '#333', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ width: `${stat.value * 10}%`, height: '100%', backgroundColor: getScoreColor(stat.value), borderRadius: '4px', transition: 'width 1s ease-in-out' }}></div>
              </div>
            </div>
          ))}

        </div>
      </div>

      {/* SECTION 1: 3D Visualization */}
      <div style={{ minHeight: '80vh' }}>
        <Compare3D userSequence={user3DData} proSequence={proData} />

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
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(2, 1fr)', 
            gap: '2rem', 
            marginBottom: '3rem' 
          }}>
            {faults.map((f, i) => (
              <div key={i} className="fault-card" style={{ 
                display: 'flex', flexDirection: 'column', gap: '0.8rem', margin: 0, height: '100%' 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                  <h3 style={{ margin: 0, color: 'var(--error)', fontSize: '1.2rem', lineHeight: '1.2' }}>{f.name}</h3>
                  <span style={{ fontSize: '0.75rem', backgroundColor: '#fee2e2', padding: '4px 10px', borderRadius: '12px', color: '#b91c1c', fontWeight: 'bold', border: '1px solid #f87171', whiteSpace: 'nowrap' }}>
                    SEVERITY: {f.severity ? f.severity.toFixed(2) : 'N/A'}
                  </span>
                </div>

                <p style={{ margin: 0, color: 'var(--text-main)', lineHeight: '1.6', flex: 1 }}>
                  {FAULT_DESCRIPTIONS[f.name] || "A biomechanical inefficiency was detected in your swing."}
                </p>

                <div style={{ backgroundColor: '#ffffff', padding: '0.8rem', borderRadius: '6px', border: '1px dashed #fca5a5', marginTop: 'auto' }}>
                  <strong style={{ color: '#991b1b', fontSize: '0.85rem', textTransform: 'uppercase' }}>AI Measurement: </strong>
                  <span style={{ color: '#7f1d1d', fontSize: '0.9rem' }}>{f.detail}</span>
                </div>
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
                <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: 'var(--primary)' }}>{drill.title}</h4>
              </div>
            </div>
          ))}
        </div>
        
        {/* Raw Metrics Toggle */}
        <details style={{ marginTop: '4rem' }}>
          <summary style={{ cursor: 'pointer', color: 'var(--text-light)', fontSize: '0.85rem' }}>View Developer Metrics (Raw JSON)</summary>
          <pre style={{ fontSize: '0.75rem', backgroundColor: '#1e293b', color: '#e2e8f0', padding: '1rem', borderRadius: '8px', marginTop: '1rem', overflowX: 'auto' }}>
            {JSON.stringify(results.metrics, null, 2)}
          </pre>
        </details>

      </div>
    </div>
  );
}