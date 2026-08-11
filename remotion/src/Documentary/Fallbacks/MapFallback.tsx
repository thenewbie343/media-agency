import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { colors, typography } from '../../editorialTheme';

export const MapFallback: React.FC<{
  caption?: string;
  title?: string;
}> = ({ caption = '', title = 'GEOGRAPHIC ANALYSIS' }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  let text = caption || '';
  if (caption.length > 120) {
    text = caption.slice(0, 117) + '...';
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.darkCharcoal,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `linear-gradient(rgba(212, 175, 55, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(212, 175, 55, 0.1) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
          opacity: 0.8,
        }}
      />
      
      {/* Radar sweep */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          width: '800px',
          height: '800px',
          transform: 'translate(-50%, -50%)',
          borderRadius: '50%',
          border: `1px solid ${colors.warmGold}`,
          boxShadow: `inset 0 0 50px rgba(212, 175, 55, 0.2)`,
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            width: '50%',
            height: '2px',
            backgroundColor: colors.warmGold,
            transformOrigin: '0% 50%',
            transform: `rotate(${(frame / fps) * 45}deg)`,
            background: `linear-gradient(90deg, transparent, ${colors.warmGold})`,
            boxShadow: `0 0 20px ${colors.warmGold}`,
          }}
        />
      </div>

      <div
        style={{
          position: 'absolute',
          bottom: '100px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(18, 16, 14, 0.9)',
          borderLeft: `4px solid ${colors.warmGold}`,
          padding: '24px 32px',
          width: '800px',
          textAlign: 'center',
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
        }}
      >
        <h3 style={{ margin: '0 0 12px 0', fontFamily: typography.serifHeader, color: colors.warmGold, letterSpacing: '3px' }}>
          {title.toUpperCase()}
        </h3>
        <p style={{ margin: 0, fontFamily: typography.body, color: colors.parchment, fontSize: '24px', lineHeight: '1.5' }}>
          {text}
        </p>
      </div>
    </AbsoluteFill>
  );
};
