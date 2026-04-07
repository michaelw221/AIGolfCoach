import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Line, Sphere, Tube } from '@react-three/drei';
import * as THREE from 'three';

const H36M_CONNECTIONS = [
  // Legs connect to Pelvis (0)
  [0, 1], [1, 2], [2, 3], // Right Leg
  [0, 4], [4, 5], [5, 6], // Left Leg
  // Torso connects to Pelvis (0)
  [0, 7], [7, 8], [8, 9], [9, 10], 
  // Arms connect to Thorax (8)
  [8, 11], [11, 12], [12, 13], 
  [8, 14], [14, 15], [15, 16]
];

const SCALE = 1.5;

const mapPoint = (pt) => {
  if (!pt || (pt[0] === 0 && pt[1] === 0 && pt[2] === 0)) return null;
  return new THREE.Vector3(pt[0] * SCALE, -pt[1] * SCALE, -pt[2] * SCALE);
};

function Limb({ p1, p2, color }) {
  const points = [p1, p2];
  const curve = new THREE.CatmullRomCurve3(points);
  return <Tube args={[curve, 8, 0.02, 8, false]}><meshStandardMaterial color={color} roughness={0.3} /></Tube>;
}

function SkeletonModel({ frameData, color }) {
  if (!frameData) return null;
  return (
    <group position={[0, 0, 0]}>
      {H36M_CONNECTIONS.map(([startIdx, endIdx], i) => {
        const p1 = mapPoint(frameData[startIdx]);
        const p2 = mapPoint(frameData[endIdx]);
        if (!p1 || !p2) return null;
        return <Limb key={i} p1={p1} p2={p2} color={color} />;
      })}
      {frameData.map((point, i) => {
        const mappedPt = mapPoint(point);
        if (!mappedPt) return null;
        return <Sphere key={i} position={mappedPt} args={[0.03, 16, 16]}><meshStandardMaterial color={color} /></Sphere>;
      })}
    </group>
  );
}

function SwingPath({ sequence, currentFrame }) {
  const pathPoints = useMemo(() => {
    if (!sequence) return [];
    let points = [];
    
    // Extract raw midpoints first
    for (let i = 0; i <= currentFrame; i++) {
      const frame = sequence[i];
      if (frame && frame[13] && frame[16]) {
        const mid = [
            (frame[13][0] + frame[16][0]) / 2,
            (frame[13][1] + frame[16][1]) / 2,
            (frame[13][2] + frame[16][2]) / 2
        ];
        points.push(mid);
      }
    }

    if (points.length > 11) {
        return points.map((p, i) => {
            if (i < 2 || i > points.length - 3) return mapPoint(p);
            const avgX = (points[i-2][0] + points[i-1][0] + p[0] + points[i+1][0] + points[i+2][0]) / 5;
            const avgY = (points[i-2][1] + points[i-1][1] + p[1] + points[i+1][1] + points[i+2][1]) / 5;
            const avgZ = (points[i-2][2] + points[i-1][2] + p[2] + points[i+1][2] + points[i+2][2]) / 5;
            return mapPoint([avgX, avgY, avgZ]);
        });
    }
    return points.map(mapPoint).filter(p => p !== null);
  }, [sequence, currentFrame]);

  if (pathPoints.length < 2) return null;
  return <Line points={pathPoints} color="#ef4444" lineWidth={4} />;
}

export default function Skeleton3D({ sequence, currentFrame, color }) {
  const frameData = sequence && sequence.length > 0 ? sequence[currentFrame] : [];

  return (
    <div style={{ width: '100%', height: '400px', backgroundColor: '#1e293b', borderRadius: '8px' }}>
      <Canvas camera={{ position: [0, 1.5, 4], fov: 45 }}>
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        
        <SkeletonModel frameData={frameData} color={color || '#0ea5e9'} />
        <SwingPath sequence={sequence} currentFrame={currentFrame} />
        
        <gridHelper args={[10, 10, "#475569", "#334155"]} position={[0, -1.5, 0]} />
        <OrbitControls target={[0, 0, 0]} />
      </Canvas>
    </div>
  );
}