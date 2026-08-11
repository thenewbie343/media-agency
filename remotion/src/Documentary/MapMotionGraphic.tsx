import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { colors, typography, fontWeights, borders, shadows } from '../editorialTheme';

const hashString = (str: string) => {
  if (!str) return 0;
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash);
};

export const MapMotionGraphic: React.FC<{ shot: any }> = ({ shot }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();

  // 1. Resolve Location Name
  const locationName = shot.continuity?.location || shot.visual_query || 'TACTICAL POSITION';
  const seed = hashString(locationName);

  // 2. Generate Coordinates based on Location Name
  const lat = ((seed % 700000) / 10000 + 8.0).toFixed(4); // India Latitude range: 8N to 37N
  const lon = ((seed % 300000) / 10000 + 68.0).toFixed(4); // India Longitude range: 68E to 97E

  // 3. Calculate unique start/end points for the route
  const startX = 200 + (seed % 300);
  const startY = 600 + ((seed >> 2) % 200);
  
  const endX = 1000 + ((seed >> 4) % 500);
  const endY = 300 + ((seed >> 6) % 300);
  
  const ctrlX = (startX + endX) / 2 + ((seed >> 8) % 300 - 150);
  const ctrlY = Math.min(startY, endY) - 150 - ((seed >> 10) % 100);

  // Route drawing progression (frames 0 to 60)
  const routeProgress = interpolate(frame, [0, 60], [1200, 0], { extrapolateRight: 'clamp' });

  // Compass Rotation
  const compassRotation = (frame * 0.4) % 360;

  // Spring animations for Pin and Compass Rose
  const pinScale = spring({ frame: frame - 45, fps, config: { damping: 11, stiffness: 80 } });
  const compassScale = spring({ frame, fps, config: { damping: 15, stiffness: 50 } });

  // Generate unique topographical contour lines using SVG curves based on seed
  const generateContour = (offsetY: number, amplitude: number, index: number) => {
    const waveSeed = (seed + index * 12345) % 1000;
    const y1 = offsetY + (waveSeed % amplitude);
    const y2 = offsetY - ((waveSeed >> 2) % amplitude);
    const y3 = offsetY + ((waveSeed >> 4) % amplitude);
    const controlX1 = width * 0.25;
    const controlX2 = width * 0.75;
    return `M 0,${y1} C ${controlX1},${y1 + 100} ${controlX2},${y2 - 100} ${width},${y3}`;
  };

  return (
    <AbsoluteFill style={{ backgroundColor: colors.darkCharcoal, overflow: 'hidden' }}>
      
      {/* 1. Topographical Contour Lines (Seeded Background) */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.15 }}>
        {[0, 1, 2, 3, 4].map((i) => (
          <path
            key={i}
            d={generateContour(150 + i * 180, 80, i)}
            fill="none"
            stroke={colors.warmGold}
            strokeWidth={1 + i * 0.5}
            strokeDasharray="6 4"
          />
        ))}
      </svg>

      {/* 2. Grid Network (Parchment Overlay) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `radial-gradient(rgba(212, 175, 55, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(140, 123, 107, 0.03) 1px, transparent 1px), linear-gradient(0deg, rgba(140, 123, 107, 0.03) 1px, transparent 1px)`,
          backgroundSize: '80px 80px, 80px 80px, 80px 80px',
          opacity: 0.85,
        }}
      />

      {/* Elegant Editorial Outer Frame Border */}
      <div
        style={{
          position: 'absolute',
          inset: '24px',
          border: borders.goldThin,
          pointerEvents: 'none',
          opacity: 0.3,
        }}
      />

      {/* Outer corner notches to enhance the premium HUD look */}
      <div style={{ position: 'absolute', top: '24px', left: '24px', width: '20px', height: '20px', borderTop: borders.goldMedium, borderLeft: borders.goldMedium, opacity: 0.6 }} />
      <div style={{ position: 'absolute', top: '24px', right: '24px', width: '20px', height: '20px', borderTop: borders.goldMedium, borderRight: borders.goldMedium, opacity: 0.6 }} />
      <div style={{ position: 'absolute', bottom: '24px', left: '24px', width: '20px', height: '20px', borderBottom: borders.goldMedium, borderLeft: borders.goldMedium, opacity: 0.6 }} />
      <div style={{ position: 'absolute', bottom: '24px', right: '24px', width: '20px', height: '20px', borderBottom: borders.goldMedium, borderRight: borders.goldMedium, opacity: 0.6 }} />

      {/* 3. Coordinates & Location Info Box (Header HUD) */}
      <div
        style={{
          position: 'absolute',
          top: '50px',
          left: '60px',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 5,
        }}
      >
        <span
          style={{
            fontFamily: typography.serifHeader,
            fontWeight: fontWeights.serifHeaderMin,
            color: colors.warmGold,
            fontSize: '22px',
            letterSpacing: '2px',
            textTransform: 'uppercase',
          }}
        >
          {locationName}
        </span>
        <span
          style={{
            fontFamily: typography.body,
            fontSize: '13px',
            color: colors.mutedSepia,
            marginTop: '4px',
            letterSpacing: '1px',
          }}
        >
          COORD: {lat}° N / {lon}° E | RELIABILITY: 98.4%
        </span>
      </div>

      <div
        style={{
          position: 'absolute',
          top: '50px',
          right: '60px',
          color: colors.mutedSepia,
          fontFamily: typography.serifHeader,
          fontWeight: fontWeights.serifHeaderMin,
          fontSize: '14px',
          letterSpacing: '3px',
          textTransform: 'uppercase',
        }}
      >
        Strategic Cartography
      </div>

      {/* 4. Animated Route Trajectory */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 3 }}>
        <defs>
          <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#8c7b6b" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#d4af37" stopOpacity="1" />
          </linearGradient>
        </defs>
        
        {/* Shadow glow under path */}
        <path
          d={`M ${startX},${startY} Q ${ctrlX},${ctrlY} ${endX},${endY}`}
          fill="none"
          stroke="rgba(212,175,55,0.25)"
          strokeWidth="6"
          strokeLinecap="round"
        />
        
        {/* Animated main route */}
        <path
          d={`M ${startX},${startY} Q ${ctrlX},${ctrlY} ${endX},${endY}`}
          fill="none"
          stroke="url(#goldGrad)"
          strokeWidth="3"
          strokeDasharray="1200"
          strokeDashoffset={routeProgress}
          strokeLinecap="round"
        />
      </svg>

      {/* 5. Start Point (Origin Marker) */}
      <div
        style={{
          position: 'absolute',
          left: startX,
          top: startY,
          transform: 'translate(-50%, -50%)',
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          backgroundColor: '#8c7b6b',
          border: '2px solid rgba(245, 242, 235, 0.6)',
          zIndex: 4,
        }}
      />

      {/* 6. Compass Rose (Positioned on the side, scaling up elegantly) */}
      <div
        style={{
          position: 'absolute',
          bottom: '60px',
          left: '60px',
          width: '140px',
          height: '140px',
          opacity: 0.45,
          transform: `scale(${compassScale})`,
          zIndex: 2,
        }}
      >
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 200 200"
          style={{ transform: `rotate(${compassRotation}deg)` }}
        >
          <circle cx="100" cy="100" r="90" fill="none" stroke={colors.warmGold} strokeWidth="1" />
          <circle cx="100" cy="100" r="82" fill="none" stroke={colors.mutedSepia} strokeWidth="0.5" strokeDasharray="2 2" />
          
          {/* Compass Needles */}
          <polygon points="100,15 106,100 100,110 94,100" fill={colors.warmGold} />
          <polygon points="100,185 106,100 100,90 94,100" fill={colors.mutedSepia} />
          <polygon points="15,100 100,106 110,100 100,94" fill={colors.warmGold} />
          <polygon points="185,100 100,106 90,100 100,94" fill={colors.mutedSepia} />
          
          <text x="100" y="32" textAnchor="middle" fill={colors.warmGold} fontSize="12" fontFamily={typography.serifHeader}>N</text>
        </svg>
      </div>

      {/* 7. Target Destination Pin (Spring scales in at target endX, endY) */}
      <div
        style={{
          position: 'absolute',
          left: endX,
          top: endY,
          transform: `translate(-50%, -50%) scale(${Math.max(0, pinScale)})`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          zIndex: 10,
        }}
      >
        {/* Pulsing Gold Glow behind Pin */}
        <div
          style={{
            position: 'absolute',
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            backgroundColor: colors.warmGold,
            opacity: 0.35 + Math.sin(frame * 0.15) * 0.15,
            transform: 'scale(1.3)',
            boxShadow: shadows.goldGlow,
          }}
        />

        {/* Gold Pin Outer */}
        <div
          style={{
            width: '18px',
            height: '18px',
            borderRadius: '50%',
            backgroundColor: colors.warmGold,
            border: `3px solid ${colors.darkCharcoal}`,
            boxShadow: shadows.deepSoft,
          }}
        />

        {/* Gold Dropdown Line */}
        <div
          style={{
            width: '1.5px',
            height: '30px',
            backgroundColor: colors.warmGold,
          }}
        />

        {/* Location Text Banner Box */}
        <div
          style={{
            padding: '6px 14px',
            backgroundColor: colors.charcoal,
            color: colors.parchment,
            fontFamily: typography.serifHeader,
            fontWeight: fontWeights.serifHeaderMin,
            fontSize: '15px',
            letterSpacing: '1px',
            borderRadius: '4px',
            border: borders.goldMedium,
            boxShadow: shadows.deepSoft,
            whiteSpace: 'nowrap',
            marginTop: '-5px',
          }}
        >
          {locationName}
        </div>
      </div>

    </AbsoluteFill>
  );
};
