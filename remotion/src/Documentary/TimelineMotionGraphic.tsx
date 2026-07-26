import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';

export const TimelineMotionGraphic: React.FC<{ title?: string }> = ({ title }) => {
  const frame = useCurrentFrame();

  // Progress Bar fill (0% to 100%)
  const progressPercent = interpolate(frame, [0, 90], [0, 100], { extrapolateRight: 'clamp' });

  // Year Counter Animation
  const year = Math.floor(interpolate(frame, [0, 90], [1198, 2026], { extrapolateRight: 'clamp' }));

  return (
    <AbsoluteFill style={{ backgroundColor: '#070a14', overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      {/* Background Film Grain Blueprint Grid */}
      <div
        style={{
          width: '100%',
          height: '100%',
          backgroundImage: 'linear-gradient(rgba(245, 158, 11, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(245, 158, 11, 0.1) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          opacity: 0.6,
        }}
      />

      {/* Central Year Counter Badge */}
      <div style={{ zIndex: 10, textAlign: 'center', marginBottom: '60px' }}>
        <span style={{ fontFamily: 'monospace', color: '#f59e0b', fontSize: '24px', letterSpacing: '6px', textTransform: 'uppercase' }}>
          [ HISTORICAL CHRONOLOGY TIMELINE ]
        </span>
        <div style={{ fontFamily: 'Impact, sans-serif', fontSize: '140px', color: '#ffffff', textShadow: '0 0 30px rgba(245, 158, 11, 0.8)', marginTop: '-10px' }}>
          {year} AD
        </div>
      </div>

      {/* Horizontal Animated Timeline Bar */}
      <div style={{ width: '80%', height: '8px', backgroundColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '4px', position: 'relative', zIndex: 10 }}>
        {/* Animated Active Fill Line */}
        <div
          style={{
            width: `${progressPercent}%`,
            height: '100%',
            backgroundColor: '#f59e0b',
            boxShadow: '0 0 20px #f59e0b',
            borderRadius: '4px',
          }}
        />

        {/* Milestone Nodes */}
        {[0, 33, 66, 100].map((nodePos, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              top: '-8px',
              left: `${nodePos}%`,
              transform: 'translateX(-50%)',
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              backgroundColor: progressPercent >= nodePos ? '#f59e0b' : '#1e293b',
              border: '3px solid #ffffff',
              boxShadow: progressPercent >= nodePos ? '0 0 15px #f59e0b' : 'none',
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};
