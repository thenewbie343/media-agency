import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

export const MapMotionGraphic: React.FC<{ title?: string }> = ({ title }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Animated Radar Rotation
  const radarRotation = (frame * 2) % 360;

  // Route Draw Animation (0 to 100%)
  const routeProgress = interpolate(frame, [0, 60], [1000, 0], { extrapolateRight: 'clamp' });

  // Spring scale for target pin
  const pinScale = spring({ frame: frame - 15, fps, config: { damping: 12 } });

  return (
    <AbsoluteFill style={{ backgroundColor: '#050811', overflow: 'hidden' }}>
      {/* 1. Animated Tech Grid */}
      <div
        style={{
          width: '100%',
          height: '100%',
          backgroundImage: 'radial-gradient(rgba(56, 189, 248, 0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
          backgroundSize: '50px 50px, 100px 100px',
          opacity: 0.8,
        }}
      />

      {/* 2. Top-Right Strategic Coordinates HUD */}
      <div style={{ position: 'absolute', top: '50px', right: '60px', color: '#38bdf8', fontFamily: 'monospace', fontSize: '20px', letterSpacing: '4px', textAlign: 'right' }}>
        <div>[ GEOGRAPHIC TACTICAL RADAR ]</div>
        <div style={{ fontSize: '14px', opacity: 0.7, marginTop: '4px' }}>LAT: 19.8136° N | LON: 85.8312° E</div>
      </div>

      {/* 3. Central Rotating Tactical Radar Reticle */}
      <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: '600px', height: '600px', borderRadius: '50%', border: '1px solid rgba(56, 189, 248, 0.3)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ width: '400px', height: '400px', borderRadius: '50%', border: '1px dashed rgba(56, 189, 248, 0.5)', transform: `rotate(${radarRotation}deg)` }} />
        
        {/* Radar Sweep Line */}
        <div
          style={{
            position: 'absolute',
            width: '300px',
            height: '300px',
            top: '0',
            left: '300px',
            background: 'conic-gradient(from 0deg, rgba(56, 189, 248, 0.4) 0deg, transparent 60deg)',
            transformOrigin: '0% 100%',
            transform: `rotate(${radarRotation}deg)`,
            borderRadius: '0 100% 0 0',
          }}
        />

        {/* Pulsating Target Pin */}
        <div
          style={{
            transform: `scale(${Math.max(0, pinScale)})`,
            position: 'absolute',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: '#ef4444', boxShadow: '0 0 25px #ef4444' }} />
          <div style={{ marginTop: '10px', padding: '6px 14px', backgroundColor: 'rgba(239, 68, 68, 0.9)', color: '#ffffff', fontFamily: 'Impact, sans-serif', fontSize: '18px', letterSpacing: '2px', borderRadius: '4px' }}>
            {title || 'TARGET LOCATION DETECTED'}
          </div>
        </div>
      </div>

      {/* 4. Animated Connecting Map Route Line SVG */}
      <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <path
          d="M 300 700 Q 600 300 960 540 T 1600 300"
          fill="none"
          stroke="#38bdf8"
          strokeWidth="4"
          strokeDasharray="1000"
          strokeDashoffset={routeProgress}
          style={{ filter: 'drop-shadow(0px 0px 8px #38bdf8)' }}
        />
      </svg>
    </AbsoluteFill>
  );
};
