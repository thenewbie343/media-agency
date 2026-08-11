import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { colors, typography, fontWeights } from '../../editorialTheme';

export const CaptionSystem: React.FC<{
  caption?: string;
  highlight?: { keyword: string; style: string; importance: string };
  durationFrames: number;
}> = ({ caption, highlight, durationFrames }) => {
  const frame = useCurrentFrame();

  if (!caption) return null;

  const words = caption.split(' ');
  const framesPerWord = words.length > 0 ? (durationFrames * 0.8) / words.length : 10;
  
  // Clean punctuation for matching highlight keyword
  const highlightWordClean = highlight?.keyword?.toLowerCase().replace(/[^a-z0-9]/g, '');

  return (
    <div style={{ position: 'absolute', bottom: '30px', width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 30, pointerEvents: 'none' }}>
      <div
        style={{
          fontFamily: typography.body,
          fontSize: '32px',
          fontWeight: fontWeights.bold,
          textTransform: 'uppercase',
          textAlign: 'center',
          maxWidth: '85%',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: 'rgba(18, 16, 14, 0.75)',
          padding: '10px 24px',
          borderRadius: '4px',
          borderLeft: `4px solid ${colors.warmGold}`,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(4px)',
        }}
      >
        {words.map((word: string, i: number) => {
          const wordStartFrame = i * framesPerWord;
          const opacity = interpolate(
            frame - wordStartFrame,
            [0, 5],
            [0.3, 1],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );
          
          const cleanWord = word.toLowerCase().replace(/[^a-z0-9]/g, '');
          const isHighlightWord = highlightWordClean && cleanWord === highlightWordClean;
          
          // Apply highlight style
          let wordColor: string = colors.parchment;
          let textDecoration = 'none';
          let backgroundColor = 'transparent';
          let padding = '0';
          
          if (isHighlightWord) {
            if (highlight?.style === 'marker') {
              backgroundColor = 'rgba(212, 175, 55, 0.3)';
              wordColor = colors.warmGold;
              padding = '0 6px';
            } else if (highlight?.style === 'underline') {
              textDecoration = `underline ${colors.warmGold} 4px`;
              wordColor = colors.warmGold;
            } else if (highlight?.style === 'glow') {
              wordColor = '#fff';
            } else {
              wordColor = colors.warmGold;
            }
          }

          return (
            <span
              key={i}
              style={{
                opacity,
                color: wordColor,
                backgroundColor,
                textDecoration,
                padding,
                display: 'inline-block',
                textShadow: isHighlightWord && highlight?.style === 'glow' ? `0 0 12px ${colors.warmGold}` : '0 2px 4px rgba(0,0,0,0.8)',
                borderRadius: '2px',
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
