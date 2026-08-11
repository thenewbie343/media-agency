import React from 'react';
import { AbsoluteFill } from 'remotion';
import { colors, typography, fontWeights, borders, shadows } from '../../editorialTheme';

export const PortraitCard: React.FC<{
  caption?: string;
  title?: string;
}> = ({ caption = '', title = 'HISTORICAL DOSSIER' }) => {
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
      {/* Background Parchment Grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `radial-gradient(rgba(212, 175, 55, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(140, 123, 107, 0.03) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
          opacity: 0.8,
        }}
      />

      {/* Frame Border */}
      <div
        style={{
          position: 'absolute',
          inset: '24px',
          border: borders.goldThin,
          pointerEvents: 'none',
          opacity: 0.35,
        }}
      />

      {/* Main Portrait Card */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          width: '540px',
          backgroundColor: colors.charcoal,
          border: borders.goldMedium,
          borderRadius: '8px',
          boxShadow: shadows.deepSoft,
          padding: '36px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Archival Portrait Frame */}
        <div
          style={{
            width: '180px',
            height: '220px',
            borderRadius: '4px',
            border: `2px solid ${colors.warmGold}`,
            backgroundColor: 'rgba(140, 123, 107, 0.15)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            marginBottom: '24px',
            boxShadow: shadows.subtlePaper,
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Archival Silhouette Vector Icon */}
          <svg width="120" height="150" viewBox="0 0 100 120" fill="none">
            {/* Head Silhouette */}
            <circle cx="50" cy="40" r="28" fill={colors.warmGold} opacity="0.85" />
            {/* Shoulders Silhouette */}
            <path d="M 10 120 C 10 80 90 80 90 120 Z" fill={colors.warmGold} opacity="0.85" />
          </svg>

          {/* Vignette Overlay over portrait */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              boxShadow: 'inset 0 0 20px rgba(18, 16, 14, 0.8)',
            }}
          />
        </div>

        {/* Person Title / Subject Name */}
        <div
          style={{
            fontFamily: typography.serifHeader,
            fontWeight: fontWeights.bold,
            fontSize: '26px',
            color: colors.warmGold,
            letterSpacing: '2px',
            textTransform: 'uppercase',
            textAlign: 'center',
            marginBottom: '12px',
          }}
        >
          {title}
        </div>

        <div style={{ width: '60px', height: '2px', backgroundColor: colors.warmGold, opacity: 0.5, marginBottom: '16px' }} />

        {/* Caption Info */}
        <div
          style={{
            fontFamily: typography.body,
            fontSize: '17px',
            color: colors.parchment,
            textAlign: 'center',
            lineHeight: '1.5',
            opacity: 0.9,
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
