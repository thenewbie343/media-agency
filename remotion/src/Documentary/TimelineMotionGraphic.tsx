import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { colors, typography, fontWeights, borders, shadows } from '../editorialTheme';

const hashString = (str: string) => {
  if (!str) return 0;
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
};

const extractYear = (text?: string): number | null => {
  if (!text) return null;
  const matches = text.match(/\b(17|18|19|20)\d{2}\b/);
  if (matches) return parseInt(matches[0], 10);
  return null;
};

export const TimelineMotionGraphic: React.FC<{ shot: any }> = ({ shot }) => {
  const frame = useCurrentFrame();

  const title = shot.text_overlay || shot.caption || 'HISTORICAL TIMELINE';
  const seed = hashString(title);

  // 1. Extract Target Year
  const targetYear = extractYear(shot.text_overlay) || 
                     extractYear(shot.caption) || 
                     extractYear(shot.continuity?.time_period) || 
                     (1985 + (seed % 35)); // default to modern era (1985 - 2020)

  // Calculate timeline bounds
  const startYear = targetYear - 15;
  const yearRange = 15;
  
  // Progress fill (0% to 100%)
  const progressPercent = interpolate(frame, [0, 90], [0, 100], { extrapolateRight: 'clamp' });

  // Year Counter Animation ticking from startYear to targetYear
  const currentYear = Math.floor(interpolate(frame, [0, 90], [startYear, targetYear], { extrapolateRight: 'clamp' }));

  // Generate 4 sequential years for timeline markers
  const step = Math.floor(yearRange / 3);
  const milestoneYears = [
    startYear,
    startYear + step,
    startYear + step * 2,
    targetYear
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: colors.darkCharcoal, overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      
      {/* 1. Background Parchment Grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `radial-gradient(rgba(212, 175, 55, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(140, 123, 107, 0.03) 1px, transparent 1px), linear-gradient(0deg, rgba(140, 123, 107, 0.03) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
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

      {/* Frame Notches */}
      <div style={{ position: 'absolute', top: '24px', left: '24px', width: '15px', height: '15px', borderTop: borders.goldMedium, borderLeft: borders.goldMedium, opacity: 0.6 }} />
      <div style={{ position: 'absolute', top: '24px', right: '24px', width: '15px', height: '15px', borderTop: borders.goldMedium, borderRight: borders.goldMedium, opacity: 0.6 }} />
      <div style={{ position: 'absolute', bottom: '24px', left: '24px', width: '15px', height: '15px', borderBottom: borders.goldMedium, borderLeft: borders.goldMedium, opacity: 0.6 }} />
      <div style={{ position: 'absolute', bottom: '24px', right: '24px', width: '15px', height: '15px', borderBottom: borders.goldMedium, borderRight: borders.goldMedium, opacity: 0.6 }} />

      {/* 2. Top Header HUD */}
      <div
        style={{
          position: 'absolute',
          top: '50px',
          color: colors.mutedSepia,
          fontFamily: typography.serifHeader,
          fontWeight: fontWeights.serifHeaderMin,
          fontSize: '13px',
          letterSpacing: '3px',
          textTransform: 'uppercase',
          zIndex: 5,
        }}
      >
        Chronological Timeline Sequence
      </div>

      {/* 3. Central Big Editorial Counter */}
      <div style={{ zIndex: 10, textAlign: 'center', marginBottom: '60px' }}>
        <span
          style={{
            fontFamily: typography.serifHeader,
            fontWeight: fontWeights.serifHeaderMin,
            color: colors.warmGold,
            fontSize: '20px',
            letterSpacing: '3px',
            textTransform: 'uppercase',
          }}
        >
          {shot.continuity?.time_period || 'HISTORICAL RECORD'}
        </span>
        <div
          style={{
            fontFamily: typography.serifHeader,
            fontWeight: fontWeights.bold,
            fontSize: '110px',
            color: colors.parchment,
            textShadow: shadows.goldDrop,
            marginTop: '8px',
            lineHeight: 1.1,
          }}
        >
          {currentYear} <span style={{ fontSize: '48px', color: colors.warmGold, fontWeight: fontWeights.serifHeaderMin }}>AD</span>
        </div>
      </div>

      {/* 4. Horizontal Axis */}
      <div
        style={{
          width: '75%',
          height: '4px',
          backgroundColor: 'rgba(140, 123, 107, 0.2)',
          position: 'relative',
          zIndex: 10,
          border: borders.sepiaThin,
          borderRadius: '2px',
        }}
      >
        {/* Animated Axis Line */}
        <div
          style={{
            width: `${progressPercent}%`,
            height: '100%',
            backgroundColor: colors.warmGold,
            boxShadow: shadows.goldGlow,
            borderRadius: '2px',
          }}
        />

        {/* Milestone Nodes */}
        {[0, 33, 66, 100].map((nodePos, i) => {
          const isActive = progressPercent >= nodePos;
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                top: '-10px',
                left: `${nodePos}%`,
                transform: 'translateX(-50%)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}
            >
              {/* Node Circle */}
              <div
                style={{
                  width: '22px',
                  height: '22px',
                  borderRadius: '50%',
                  backgroundColor: isActive ? colors.warmGold : colors.darkCharcoal,
                  border: isActive ? `3px solid ${colors.parchment}` : borders.sepiaMedium,
                  boxShadow: isActive ? shadows.goldGlow : 'none',
                  transition: 'background-color 0.2s, box-shadow 0.2s',
                }}
              />
              {/* Year Label */}
              <span
                style={{
                  marginTop: '16px',
                  fontFamily: typography.serifHeader,
                  fontWeight: fontWeights.serifHeaderMin,
                  fontSize: '16px',
                  color: isActive ? colors.warmGold : colors.mutedSepia,
                  letterSpacing: '1px',
                }}
              >
                {milestoneYears[i]}
              </span>
            </div>
          );
        })}
      </div>

      {/* 5. Details Caption overlay under the axis */}
      <div
        style={{
          position: 'absolute',
          bottom: '70px',
          width: '60%',
          textAlign: 'center',
          color: colors.parchment,
          fontFamily: typography.body,
          fontSize: '15px',
          lineHeight: '1.6',
          opacity: 0.85,
          letterSpacing: '0.5px',
        }}
      >
        {shot.text_overlay || shot.caption}
      </div>

    </AbsoluteFill>
  );
};
