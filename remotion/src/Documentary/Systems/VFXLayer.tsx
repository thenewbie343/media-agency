import React from 'react';
import { useCurrentFrame, AbsoluteFill, random } from 'remotion';

export const VFXLayer: React.FC<{
  isColdTheme?: boolean;
  isGlitch?: boolean;
}> = ({ isColdTheme = false, isGlitch = false }) => {
  const frame = useCurrentFrame();

  const randomGlitchShift = isGlitch && frame % 10 === 0 ? random(frame) * 10 - 5 : 0;

  return (
    <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 20 }}>
      {/* VHS Scanline Overlay */}
      {isGlitch && (
        <AbsoluteFill
          style={{
            background: 'repeating-linear-gradient(0deg, rgba(0,0,0,0.15), rgba(0,0,0,0.15) 2px, transparent 2px, transparent 4px)',
            pointerEvents: 'none',
            transform: `translateY(${randomGlitchShift}px)`,
            opacity: 0.7
          }}
        />
      )}

      {/* Film Grain Overlay - 3% Master Filter */}
      <AbsoluteFill style={{ pointerEvents: 'none', opacity: 0.03, mixBlendMode: 'overlay' }}>
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <filter id="noiseFilter">
            <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" stitchTiles="stitch" />
          </filter>
          <rect width="100%" height="100%" filter="url(#noiseFilter)" />
        </svg>
      </AbsoluteFill>

      {/* Cinematic Vignette - Outer 15% Darkened */}
      <AbsoluteFill
        style={{
          background: 'radial-gradient(circle, rgba(0,0,0,0) 65%, rgba(0,0,0,0.85) 100%)',
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};
