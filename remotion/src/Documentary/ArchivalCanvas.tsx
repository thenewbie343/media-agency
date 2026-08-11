import React from 'react';
import { AbsoluteFill } from 'remotion';
import { colors, typography, fontWeights, borders, shadows } from '../editorialTheme';

export const ArchivalCanvas: React.FC<{
  caption?: string;
  title?: string;
  caseNumber?: string;
}> = ({ caption = '', title = 'ARCHIVAL DOSSIER', caseNumber = 'CASE FILE #8492-DOC' }) => {
  // Strict 120-character truncation for LLM-generated captions so historical case file layout never suffers overflow clipping
  let text = caption || '';
  if (caption.length > 120) {
    text = caption.slice(0, 117) + '...';
  }

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.parchment,
        overflow: 'hidden',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '60px',
      }}
    >
      {/* 1. Historical Parchment Texture Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `radial-gradient(rgba(140, 123, 107, 0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(212, 175, 55, 0.05) 1px, transparent 1px)`,
          backgroundSize: '40px 40px, 80px 80px',
          opacity: 0.7,
        }}
      />

      {/* Decorative Outer Sepia & Gold Frame Borders */}
      <div
        style={{
          position: 'absolute',
          inset: '30px',
          border: borders.goldMedium,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: '38px',
          border: borders.sepiaThin,
          pointerEvents: 'none',
        }}
      />

      {/* 2. Historical Case File Document Container */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          width: '100%',
          maxWidth: '1000px',
          backgroundColor: colors.sepia,
          border: borders.goldMedium,
          boxShadow: shadows.deepSoft,
          padding: '50px 60px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          boxSizing: 'border-box',
        }}
      >
        {/* Header Row: Case File Reference & Vintage Stamp */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div
              style={{
                fontFamily: typography.serifHeader,
                fontWeight: fontWeights.serifHeaderMin,
                fontSize: '16px',
                color: colors.mutedSepia,
                letterSpacing: '3px',
                textTransform: 'uppercase',
              }}
            >
              {caseNumber}
            </div>
            <h2
              style={{
                margin: '6px 0 0 0',
                fontFamily: typography.serifHeader,
                fontWeight: fontWeights.bold,
                fontSize: '36px',
                color: colors.darkCharcoal,
                letterSpacing: '1px',
              }}
            >
              {title}
            </h2>
          </div>

          {/* Historical Case File Stamp */}
          <div
            style={{
              padding: '8px 18px',
              border: `2px solid ${colors.warmAccent}`,
              color: colors.warmAccent,
              fontFamily: typography.serifHeader,
              fontWeight: fontWeights.bold,
              fontSize: '16px',
              letterSpacing: '2px',
              textTransform: 'uppercase',
              transform: 'rotate(-4deg)',
              borderRadius: '2px',
              backgroundColor: 'rgba(184, 134, 11, 0.08)',
              boxShadow: shadows.subtlePaper,
            }}
          >
            CLASSIFIED RECORD
          </div>
        </div>

        {/* Gold Accent Divider Line */}
        <div style={{ width: '100%', height: '2px', backgroundColor: colors.warmGold }} />

        {/* Caption Body Text Box (Dynamic Wrapping & 120-Char Truncation Guaranteed) */}
        <div
          style={{
            fontFamily: typography.body,
            fontSize: '26px',
            lineHeight: '1.6',
            color: colors.charcoal,
            wordBreak: 'break-word',
            overflowWrap: 'break-word',
            backgroundColor: 'rgba(245, 242, 235, 0.6)',
            padding: '24px 30px',
            borderLeft: `4px solid ${colors.warmGold}`,
            borderRadius: '2px',
          }}
        >
          {text ? `"${text}"` : '"No transcript caption provided for this archival entry."'}
        </div>

        {/* Footer Meta Row */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
          <div
            style={{
              fontFamily: typography.serifHeader,
              fontWeight: fontWeights.serifHeaderMin,
              fontSize: '14px',
              color: colors.mutedSepia,
              letterSpacing: '2px',
            }}
          >
            DOCUMENTARY ARCHIVE REGISTRY • DEPT. OF HISTORICAL EVIDENCE
          </div>
          <div
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: colors.warmGold,
              boxShadow: shadows.goldDrop,
            }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
