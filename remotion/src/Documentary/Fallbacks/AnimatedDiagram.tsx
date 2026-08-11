import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { colors, typography, fontWeights, borders, shadows } from '../../editorialTheme';

export const AnimatedDiagram: React.FC<{
  caption?: string;
  title?: string;
}> = ({ caption = '', title = 'PROCESS MECHANISM' }) => {
  const frame = useCurrentFrame();

  let text = caption || '';
  if (caption.length > 120) {
    text = caption.slice(0, 117) + '...';
  }

  // Dashoffset animation for active schematic flow
  const dashOffset = (frame * 2) % 40;

  // Node scale spring animations
  const node1Opacity = interpolate(frame, [0, 15], [0.3, 1], { extrapolateRight: 'clamp' });
  const node2Opacity = interpolate(frame, [15, 30], [0.3, 1], { extrapolateRight: 'clamp' });
  const node3Opacity = interpolate(frame, [30, 45], [0.3, 1], { extrapolateRight: 'clamp' });

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
      {/* Background Radial Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `radial-gradient(rgba(212, 175, 55, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(140, 123, 107, 0.03) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
          opacity: 0.8,
        }}
      />

      <div style={{ position: 'absolute', inset: '24px', border: borders.goldThin, pointerEvents: 'none', opacity: 0.3 }} />

      {/* Process Flow Diagram (3 Animated Connected Nodes) */}
      <div style={{ position: 'relative', width: '800px', height: '200px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', zIndex: 5, marginBottom: '40px' }}>
        
        {/* Animated Connecting Line SVG */}
        <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
          <line x1="140" y1="100" x2="660" y2="100" stroke={colors.warmGold} strokeWidth="3" strokeDasharray="10 10" strokeDashoffset={-dashOffset} opacity="0.8" />
        </svg>

        {/* Node 1 */}
        <div style={{ opacity: node1Opacity, display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 10 }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: colors.charcoal, border: `2px solid ${colors.warmGold}`, boxShadow: shadows.goldGlow, display: 'flex', justifyContent: 'center', alignItems: 'center', color: colors.parchment, fontFamily: typography.serifHeader, fontSize: '20px', fontWeight: fontWeights.bold }}>
            01
          </div>
          <span style={{ marginTop: '10px', color: colors.mutedSepia, fontFamily: typography.serifHeader, fontSize: '13px', letterSpacing: '2px' }}>INPUT</span>
        </div>

        {/* Node 2 */}
        <div style={{ opacity: node2Opacity, display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 10 }}>
          <div style={{ width: '100px', height: '100px', borderRadius: '50%', backgroundColor: colors.charcoal, border: `3px solid ${colors.warmGold}`, boxShadow: shadows.goldGlow, display: 'flex', justifyContent: 'center', alignItems: 'center', color: colors.warmGold, fontFamily: typography.serifHeader, fontSize: '24px', fontWeight: fontWeights.bold }}>
            PROCESS
          </div>
          <span style={{ marginTop: '10px', color: colors.warmGold, fontFamily: typography.serifHeader, fontSize: '13px', letterSpacing: '2px' }}>MECHANISM</span>
        </div>

        {/* Node 3 */}
        <div style={{ opacity: node3Opacity, display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 10 }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: colors.charcoal, border: `2px solid ${colors.warmGold}`, boxShadow: shadows.goldGlow, display: 'flex', justifyContent: 'center', alignItems: 'center', color: colors.parchment, fontFamily: typography.serifHeader, fontSize: '20px', fontWeight: fontWeights.bold }}>
            03
          </div>
          <span style={{ marginTop: '10px', color: colors.mutedSepia, fontFamily: typography.serifHeader, fontSize: '13px', letterSpacing: '2px' }}>OUTCOME</span>
        </div>

      </div>

      {/* Caption Box */}
      <div
        style={{
          position: 'relative',
          zIndex: 10,
          backgroundColor: 'rgba(18, 16, 14, 0.9)',
          borderLeft: `4px solid ${colors.warmGold}`,
          borderTop: borders.sepiaThin,
          borderRight: borders.sepiaThin,
          borderBottom: borders.sepiaThin,
          padding: '20px 32px',
          width: '720px',
          textAlign: 'center',
          boxShadow: shadows.deepSoft,
        }}
      >
        <div style={{ fontFamily: typography.serifHeader, fontSize: '13px', color: colors.mutedSepia, letterSpacing: '3px', textTransform: 'uppercase', marginBottom: '6px' }}>
          SYSTEMIC ANALYSIS
        </div>
        <div style={{ fontFamily: typography.serifHeader, fontWeight: fontWeights.bold, fontSize: '24px', color: colors.warmGold, letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '10px' }}>
          {title}
        </div>
        <p style={{ margin: 0, fontFamily: typography.body, color: colors.parchment, fontSize: '18px', lineHeight: '1.5' }}>
          {text}
        </p>
      </div>

    </AbsoluteFill>
  );
};
