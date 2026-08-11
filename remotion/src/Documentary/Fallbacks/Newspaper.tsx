import React from 'react';
import { AbsoluteFill } from 'remotion';
import { typography, fontWeights } from '../../editorialTheme';

export const Newspaper: React.FC<{
  caption?: string;
  title?: string;
}> = ({ caption = '', title = 'BREAKING HEADLINES' }) => {
  let text = caption || '';
  if (caption.length > 200) {
    text = caption.slice(0, 197) + '...';
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#e9e5db',
        overflow: 'hidden',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '60px',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `repeating-linear-gradient(0deg, rgba(0,0,0,0.03), rgba(0,0,0,0.03) 1px, transparent 1px, transparent 4px)`,
          opacity: 0.6,
        }}
      />

      <div
        style={{
          position: 'relative',
          zIndex: 10,
          width: '100%',
          maxWidth: '1000px',
          borderTop: '6px solid #111',
          borderBottom: '6px solid #111',
          padding: '40px 0',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '30px',
        }}
      >
        <div
          style={{
            fontFamily: typography.serifHeader,
            fontWeight: fontWeights.bold,
            fontSize: '72px',
            color: '#111',
            letterSpacing: '0px',
            textAlign: 'center',
            lineHeight: '1.1',
          }}
        >
          {title.toUpperCase()}
        </div>

        <div style={{ display: 'flex', width: '100%', borderTop: '2px solid #111', borderBottom: '2px solid #111', padding: '10px 0', justifyContent: 'space-between', fontFamily: typography.serifHeader, fontSize: '18px', fontWeight: fontWeights.semiBold, color: '#333', textTransform: 'uppercase' }}>
          <span>VOL. CXLIV ... No. 50,000</span>
          <span>THE GLOBAL CHRONICLE</span>
          <span>SPECIAL EDITION</span>
        </div>

        <div
          style={{
            columnCount: 2,
            columnGap: '40px',
            fontFamily: typography.body,
            fontSize: '22px',
            lineHeight: '1.7',
            color: '#222',
            textAlign: 'justify',
            wordBreak: 'break-word',
          }}
        >
          <span style={{ fontSize: '48px', float: 'left', lineHeight: '48px', paddingRight: '8px', fontFamily: typography.serifHeader }}>{text.charAt(0)}</span>
          {text.slice(1)}
          {' '}Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
        </div>
      </div>
    </AbsoluteFill>
  );
};
