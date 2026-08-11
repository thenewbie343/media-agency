import React from 'react';
import { AbsoluteFill } from 'remotion';
import { typography } from '../../editorialTheme';

export const EvidenceBoard: React.FC<{
  caption?: string;
  title?: string;
}> = ({ caption = '', title = 'INVESTIGATION BOARD' }) => {
  let text = caption || '';
  if (caption.length > 120) {
    text = caption.slice(0, 117) + '...';
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#3a332d', // Cork board color
        backgroundImage: `url('data:image/svg+xml,%3Csvg width="100" height="100" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noise"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100" height="100" filter="url(%23noise)" opacity="0.15"/%3E%3C/svg%3E')`,
        overflow: 'hidden',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '60px',
      }}
    >
      {/* Red string elements */}
      <div style={{ position: 'absolute', top: '30%', left: '20%', width: '60%', height: '2px', backgroundColor: '#d9381e', transform: 'rotate(15deg)', boxShadow: '0 2px 4px rgba(0,0,0,0.5)' }} />
      <div style={{ position: 'absolute', top: '60%', left: '30%', width: '50%', height: '2px', backgroundColor: '#d9381e', transform: 'rotate(-25deg)', boxShadow: '0 2px 4px rgba(0,0,0,0.5)' }} />

      {/* Main Evidence Card */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          width: '700px',
          backgroundColor: '#ffffe0', // Yellow legal pad color
          boxShadow: '2px 5px 15px rgba(0,0,0,0.4)',
          padding: '40px',
          transform: 'rotate(-2deg)',
        }}
      >
        {/* Red Pin */}
        <div style={{ position: 'absolute', top: '15px', left: '50%', transform: 'translateX(-50%)', width: '16px', height: '16px', borderRadius: '50%', backgroundColor: '#cc0000', boxShadow: 'inset -2px -2px 5px rgba(0,0,0,0.5), 0 3px 5px rgba(0,0,0,0.4)' }} />

        <h3 style={{ margin: '20px 0 10px 0', fontFamily: 'Courier New, monospace', fontSize: '24px', color: '#111', textDecoration: 'underline' }}>
          {title}
        </h3>
        
        <p style={{ margin: 0, fontFamily: typography.body, color: '#222', fontSize: '28px', lineHeight: '1.4' }}>
          {text}
        </p>
      </div>
    </AbsoluteFill>
  );
};
