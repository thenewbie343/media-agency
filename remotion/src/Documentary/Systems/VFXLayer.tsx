import React from 'react';
import { useCurrentFrame, AbsoluteFill, random } from 'remotion';

export const VFXLayer: React.FC<{
  isColdTheme?: boolean;
  overlay?: string;
  events?: any[];
  durationFrames?: number;
}> = ({ isColdTheme = false, overlay, events = [], durationFrames = 90 }) => {
  const frame = useCurrentFrame();

  const isGlitch = overlay === 'vhs_glitch';
  const isGrain = overlay === 'film_grain' || overlay === 'dust_scratches';
  const isLeaks = overlay === 'light_leaks';

  const randomGlitchShift = isGlitch && frame % 10 === 0 ? random(frame) * 10 - 5 : 0;
  
  // Dynamic light leaks based on frame
  const leakX = Math.sin(frame / 30) * 100;
  const leakOpacity = 0.3 + Math.abs(Math.sin(frame / 15)) * 0.2;

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
      
      {/* Light Leaks */}
      {isLeaks && (
        <AbsoluteFill
          style={{
            background: `radial-gradient(ellipse at ${50 + leakX}% 10%, rgba(255, 100, 50, ${leakOpacity}), transparent 60%)`,
            pointerEvents: 'none',
            mixBlendMode: 'screen'
          }}
        />
      )}

      {/* Film Grain Overlay - Master Filter */}
      <AbsoluteFill style={{ pointerEvents: 'none', opacity: isGrain ? 0.08 : 0.03, mixBlendMode: 'overlay' }}>
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <filter id="noiseFilter">
            <feTurbulence type="fractalNoise" baseFrequency={isGrain ? "0.9" : "0.8"} numOctaves="3" stitchTiles="stitch" />
          </filter>
          <rect width="100%" height="100%" filter="url(#noiseFilter)" />
        </svg>
      </AbsoluteFill>
      
      {/* Dynamic Editorial Events (OVERLAY) */}
      {events.filter(e => e.type === 'OVERLAY').map((evt, idx) => {
        const timingPct = evt.timing_percent !== undefined ? evt.timing_percent : 0;
        const delayFrames = Math.floor((timingPct / 100) * durationFrames);
        const eventDuration = evt.duration ? Math.floor(evt.duration * 30) : 15;
        
        if (frame >= delayFrames && frame < delayFrames + eventDuration) {
           const progress = (frame - delayFrames) / eventDuration;
           if (evt.cue === 'flash' || evt.cue === 'white_flash') {
              const opacity = (1 - progress) * 0.85;
              return <AbsoluteFill key={idx} style={{ backgroundColor: 'white', opacity, pointerEvents: 'none', zIndex: 50, mixBlendMode: 'screen' }} />;
           } else if (evt.cue === 'light_leak') {
              const opacity = Math.sin(progress * Math.PI) * 0.5;
              return <AbsoluteFill key={idx} style={{ background: 'radial-gradient(circle at 80% 20%, rgba(255, 140, 50, 0.8), transparent 70%)', opacity, pointerEvents: 'none', zIndex: 45, mixBlendMode: 'screen' }} />;
           } else if (evt.cue === 'vhs_glitch') {
              const offset = (random(frame) * 16 - 8);
              return <AbsoluteFill key={idx} style={{ background: 'repeating-linear-gradient(0deg, rgba(255,0,0,0.1), rgba(0,255,255,0.1) 3px, transparent 3px, transparent 6px)', transform: `translateY(${offset}px)`, pointerEvents: 'none', zIndex: 45 }} />;
           } else if (evt.cue === 'red_tint' || evt.cue === 'alert') {
              const opacity = Math.sin(progress * Math.PI) * 0.35;
              return <AbsoluteFill key={idx} style={{ backgroundColor: 'rgba(220, 20, 20, 0.4)', opacity, pointerEvents: 'none', zIndex: 45, mixBlendMode: 'color-burn' }} />;
           }
        }
        return null;
      })}

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
