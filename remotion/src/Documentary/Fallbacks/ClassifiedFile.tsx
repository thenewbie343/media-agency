import React from 'react';
import { AbsoluteFill } from 'remotion';
import { colors, typography, fontWeights, borders, shadows } from '../../editorialTheme';

export const ClassifiedFile: React.FC<{
  caption?: string;
  title?: string;
  caseNumber?: string;
}> = ({ caption = '', title = 'CLASSIFIED INTELLIGENCE', caseNumber = 'FILE #8492-DOC' }) => {
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
        justifyContent: 'center',
        alignItems: 'center',
        padding: '60px',
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: '30px',
          border: borders.charcoalThin,
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          position: 'relative',
          zIndex: 10,
          width: '100%',
          maxWidth: '1000px',
          backgroundColor: '#2a2624',
          border: borders.goldMedium,
          boxShadow: shadows.deepSoft,
          padding: '50px 60px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div
              style={{
                fontFamily: typography.serifHeader,
                fontWeight: fontWeights.serifHeaderMin,
                fontSize: '16px',
                color: colors.warmGold,
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
                color: colors.parchment,
                letterSpacing: '1px',
              }}
            >
              {title}
            </h2>
          </div>

          <div
            style={{
              padding: '8px 18px',
              border: `2px solid #ff4444`,
              color: '#ff4444',
              fontFamily: typography.serifHeader,
              fontWeight: fontWeights.bold,
              fontSize: '18px',
              letterSpacing: '2px',
              textTransform: 'uppercase',
              transform: 'rotate(-4deg)',
              borderRadius: '2px',
              backgroundColor: 'rgba(255, 68, 68, 0.08)',
            }}
          >
            TOP SECRET
          </div>
        </div>

        <div style={{ width: '100%', height: '2px', backgroundColor: colors.mutedSepia }} />

        <div
          style={{
            fontFamily: typography.body,
            fontSize: '26px',
            lineHeight: '1.6',
            color: colors.sepia,
            wordBreak: 'break-word',
            overflowWrap: 'break-word',
            backgroundColor: 'rgba(28, 25, 23, 0.6)',
            padding: '24px 30px',
            borderLeft: `4px solid ${colors.warmGold}`,
            borderRadius: '2px',
          }}
        >
          {text ? `"${text}"` : '"[REDACTED]"'}
        </div>

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
            DEPARTMENT OF COVERT AFFAIRS
          </div>
          <div
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: '#ff4444',
            }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
