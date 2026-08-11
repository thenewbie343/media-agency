import React from 'react';
import { Audio, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';

export interface AnimatedHighlightProps {
  text: string;
  highlightWords?: string[];
  startFrame?: number;
  durationInFrames?: number;
  highlightColor?: string;
  strokeOpacity?: number;
  playSfx?: boolean;
  sfxVolume?: number;
  sfxSrc?: string;
  style?: React.CSSProperties;
  textStyle?: React.CSSProperties;
  highlightStyle?: React.CSSProperties;
  fontSize?: number | string;
  textColor?: string;
}

export const AnimatedHighlight: React.FC<AnimatedHighlightProps> = ({
  text,
  highlightWords,
  startFrame = 0,
  durationInFrames = 15,
  highlightColor = '#facc15',
  strokeOpacity = 0.55,
  playSfx = true,
  sfxVolume = 0.10, // -20dB volume scale
  sfxSrc = staticFile('assets/sfx/Whooshes/Cinematic Whoosh.mp3'),
  style,
  textStyle,
  highlightStyle,
  fontSize,
  textColor = '#ffffff',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const animFrame = Math.max(0, frame - startFrame);
  const progress = spring({
    frame: animFrame,
    fps,
    config: { damping: 14, stiffness: 110, mass: 0.5 },
  });

  const widthPercent = interpolate(progress, [0, 1], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const shouldHighlightWord = (word: string): boolean => {
    if (!highlightWords || highlightWords.length === 0) return true;
    const cleanWord = word.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
    return highlightWords.some(hw => {
      const cleanHw = hw.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
      return cleanWord === cleanHw || cleanWord.includes(cleanHw) || cleanHw.includes(cleanWord);
    });
  };

  const words = text.split(' ');

  return (
    <div
      style={{
        position: 'relative',
        display: 'inline-flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: '6px',
        fontSize: fontSize || '32px',
        color: textColor,
        ...style,
      }}
    >
      {/* Swoosh Sound Effect Triggered at startFrame */}
      {playSfx && animFrame >= 0 && (
        <Sequence from={startFrame} durationInFrames={durationInFrames}>
          <Audio src={sfxSrc} volume={sfxVolume} />
        </Sequence>
      )}

      {words.map((word, idx) => {
        const isHighlighted = shouldHighlightWord(word);

        if (!isHighlighted) {
          return (
            <span key={idx} style={{ position: 'relative', zIndex: 2, ...textStyle }}>
              {word}
            </span>
          );
        }

        return (
          <span
            key={idx}
            style={{
              position: 'relative',
              display: 'inline-block',
              padding: '2px 6px',
              zIndex: 2,
              ...highlightStyle,
            }}
          >
            {/* Physical Yellow Marker Stroke background drawing across word */}
            <span
              style={{
                position: 'absolute',
                top: '12%',
                bottom: '10%',
                left: 0,
                width: `${widthPercent}%`,
                backgroundColor: highlightColor,
                opacity: strokeOpacity,
                borderRadius: '3px 9px 4px 7px',
                transform: 'rotate(-0.8deg) skewX(-4deg)',
                boxShadow: `0 0 10px ${highlightColor}66`,
                pointerEvents: 'none',
                zIndex: 1,
              }}
            />
            <span style={{ position: 'relative', zIndex: 2, ...textStyle }}>
              {word}
            </span>
          </span>
        );
      })}
    </div>
  );
};
