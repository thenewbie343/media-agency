import React from 'react';
import { AbsoluteFill } from 'remotion';
import { colors, typography, fontWeights, borders, shadows } from '../../editorialTheme';

export const TechnicalDiagram: React.FC<{
  caption?: string;
  title?: string;
}> = ({ caption = '', title = 'OBJECT SCHEMATIC' }) => {
  let text = caption || '';
  if (caption.length > 120) {
    text = caption.slice(0, 117) + '...';
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.darkCharcoal,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {/* Blueprint Grid Network */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `linear-gradient(rgba(212, 175, 55, 0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(212, 175, 55, 0.07) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
          opacity: 0.9,
        }}
      />

      {/* Frame Border with Corner Accents */}
      <div style={{ position: 'absolute', inset: '24px', border: borders.goldThin, pointerEvents: 'none', opacity: 0.35 }} />
      <div style={{ position: 'absolute', top: '24px', left: '24px', width: '16px', height: '16px', borderTop: borders.goldMedium, borderLeft: borders.goldMedium, opacity: 0.7 }} />
      <div style={{ position: 'absolute', top: '24px', right: '24px', width: '16px', height: '16px', borderTop: borders.goldMedium, borderRight: borders.goldMedium, opacity: 0.7 }} />
      <div style={{ position: 'absolute', bottom: '24px', left: '24px', width: '16px', height: '16px', borderBottom: borders.goldMedium, borderLeft: borders.goldMedium, opacity: 0.7 }} />
      <div style={{ position: 'absolute', bottom: '24px', right: '24px', width: '16px', height: '16px', borderBottom: borders.goldMedium, borderRight: borders.goldMedium, opacity: 0.7 }} />

      {/* Technical Schematic Drawing SVG */}
      <svg style={{ position: 'absolute', width: '800px', height: '500px', opacity: 0.4 }}>
        {/* Outer Isometric Box / Blueprint Shape */}
        <rect x="200" y="100" width="400" height="280" fill="none" stroke={colors.warmGold} strokeWidth="1.5" strokeDasharray="8 4" />
        <rect x="240" y="140" width="320" height="200" fill="none" stroke={colors.parchment} strokeWidth="1" />
        
        {/* Dimension Lines */}
        <line x1="160" y1="100" x2="160" y2="380" stroke={colors.warmGold} strokeWidth="1" />
        <line x1="150" y1="100" x2="170" y2="100" stroke={colors.warmGold} strokeWidth="1" />
        <line x1="150" y1="380" x2="170" y2="380" stroke={colors.warmGold} strokeWidth="1" />
        
        {/* Center Target Circles */}
        <circle cx="400" cy="240" r="60" fill="none" stroke={colors.warmGold} strokeWidth="1.5" />
        <circle cx="400" cy="240" r="8" fill={colors.warmGold} />
        
        {/* Crosshair Lines */}
        <line x1="300" y1="240" x2="500" y2="240" stroke={colors.warmGold} strokeWidth="1" strokeDasharray="4 2" />
        <line x1="400" y1="140" x2="400" y2="340" stroke={colors.warmGold} strokeWidth="1" strokeDasharray="4 2" />
      </svg>

      {/* Foreground Callout Box */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          backgroundColor: 'rgba(18, 16, 14, 0.88)',
          borderLeft: `4px solid ${colors.warmGold}`,
          borderTop: borders.sepiaThin,
          borderRight: borders.sepiaThin,
          borderBottom: borders.sepiaThin,
          padding: '24px 32px',
          width: '720px',
          textAlign: 'center',
          boxShadow: shadows.deepSoft,
          backdropFilter: 'blur(6px)',
        }}
      >
        <div style={{ fontFamily: typography.serifHeader, fontSize: '13px', color: colors.mutedSepia, letterSpacing: '3px', textTransform: 'uppercase', marginBottom: '8px' }}>
          TECHNICAL SPECIFICATION
        </div>

        <div style={{ fontFamily: typography.serifHeader, fontWeight: fontWeights.bold, fontSize: '28px', color: colors.warmGold, letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '12px' }}>
          {title}
        </div>

        <p style={{ margin: 0, fontFamily: typography.body, color: colors.parchment, fontSize: '18px', lineHeight: '1.5', opacity: 0.95 }}>
          {text}
        </p>
      </div>
    </AbsoluteFill>
  );
};
