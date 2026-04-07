import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Line, Sphere } from '@react-three/drei';

// Human3.6M format used by VideoPose3D
const H36M_CONNECTIONS = [
  [0, 1], [1, 2], [2, 3],       // Right Leg
  [0, 4], [4, 5], [5, 6],       // Left Leg
  [0, 7], [7, 8], [8, 9],[9, 10], // Spine, Thorax, Neck, Head
  [8, 11],[11, 12], [12, 13],  // Left Arm[8, 14], [14, 15], [15, 16]   // Right Arm
];

const SCALE = 2; 

// Helper to map coordinates correctly for Three.js
const mapPoint = (pt) => {
  if (!pt || (pt[0] === 0 && pt[1] === 0)) return null;
  return [pt[0] * SCALE, -pt[1] * SCALE, -pt[2] * SCALE];
};

function SkeletonModel({ frameData, color }) {
  if (!frameData || frameData.length === 0) return null;

  return (
    <group position={[0, 1, 0]}>
      {/* 1. Draw the Lines (Bones) */}
      {H36M_CONNECTIONS.map(([startIdx, endIdx], i) => {
        const p1 = mapPoint(frameData[startIdx]);
        const p2 = mapPoint(frameData[endIdx]);
        
        if (!p1 || !p2) return null;

        return (
          <Line key={`line-${i}`} points={[p1, p2]} color={color || "white"} lineWidth={4} />
        );
      })}

      {/* 2. Draw the Spheres (Joints) */}
      {frameData.map((point, i) => {
        const mappedPt = mapPoint(point);
        if (!mappedPt) return null;
        
        return (
          <Sphere key={`joint-${i}`} position={mappedPt} args={[0.04, 16, 16]}>
            <meshStandardMaterial color={color === "white" ? "#0ea5e9" : color} />
          </Sphere>
        );
      })}
    </group>
  );
}

// --- NEW FEATURE: Swing Path Trace ---
function SwingPath({ sequence, currentFrame }) {
  // Extract the wrist positions up to the current frame to draw a trail
  const pathPoints = useMemo(() => {
    if (!sequence) return [];
    const points =[];
    // Index 13 is Left Wrist, 16 is Right Wrist. We trace the midpoint.
    for (let i = 0; i <= currentFrame; i++) {
      const frame = sequence[i];
      if (frame && frame[13] && frame[16]) {
        const lw = frame[13];
        const rw = frame[16];
        // Calculate midpoint of hands and map it
        const midX = (lw[0] + rw[0]) / 2;
        const midY = (lw[1] + rw[1]) / 2;
        const midZ = (lw[2] + rw[2]) / 2;
        
        const pt = mapPoint([midX, midY, midZ]);
        if (pt) points.push(pt);
      }
    }
    return points;
  }, [sequence, currentFrame]);

  if (pathPoints.length < 2) return null;

  return (
    <group position={[0, 1, 0]}>
      <Line points={pathPoints} color="#ef4444" lineWidth={3} dashed={false} />
    </group>
  );
}

export default function Skeleton3D({ sequence, currentFrame, color }) {
  const frameData = sequence && sequence.length > 0 ? sequence[currentFrame] :[];

  return (
    <div style={{ width: '100%', height: '400px', backgroundColor: '#1e293b', borderRadius: '8px', overflow: 'hidden' }}>
      <Canvas camera={{ position: [0, 1.5, 5], fov: 45 }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        
        {/* Draw the Golfer */}
        <SkeletonModel frameData={frameData} color={color} />
        
        {/* Draw the red trace line behind the hands */}
        <SwingPath sequence={sequence} currentFrame={currentFrame} />
        
        {/* Controls */}
        <OrbitControls target={[0, 1, 0]} enableDamping dampingFactor={0.1} />
        
        {/* Floor Grid */}
        <gridHelper args={[10, 10, "#475569", "#334155"]} position={[0, -1, 0]} />
      </Canvas>
    </div>
  );
}