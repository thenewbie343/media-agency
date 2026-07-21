import { AbsoluteFill, useVideoConfig, useCurrentFrame, interpolate, spring, Img, Video, staticFile } from 'remotion';
import { SceneData } from './DocumentaryVideo';
import { Fragment } from 'react';

// Advanced Motion Graphic Engine for YouTube Documentaries
export const DocumentaryScene: React.FC<{
  scene: SceneData;
  durationFrames: number;
}> = ({ scene, durationFrames }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  // 1. Dynamic Camera Movement (Ken Burns System)
  let scale = 1;
  let translateX = 0;
  let translateY = 0;

  if (scene.camera_movement === 'ken_burns_zoom_in') {
    scale = interpolate(frame, [0, durationFrames], [1, 1.2], { extrapolateRight: 'clamp' });
  } else if (scene.camera_movement === 'ken_burns_pan_right') {
    scale = 1.15; // Zoom in to allow panning room
    translateX = interpolate(frame, [0, durationFrames], [0, -10], { extrapolateRight: 'clamp' });
  } else {
    // Default dynamic movement (never static)
    scale = interpolate(frame, [0, durationFrames], [1.05, 1.15], { extrapolateRight: 'clamp' });
  }

  // 2. Cinematic Filters & LUTs mapping
  let cssFilter = 'none';
  if (scene.lut === 'dark_noir') {
    cssFilter = 'grayscale(1) contrast(1.3) brightness(0.8)';
  } else if (scene.lut === 'neon_pink' || scene.lut === 'vintage') {
    cssFilter = 'sepia(1) hue-rotate(-50deg) saturate(3) contrast(1.2)';
  }

  // 3. VHS Glitch / Scanline effect
  const isGlitch = scene.overlay === 'vhs_glitch';
  const randomGlitchShift = isGlitch && frame % 10 === 0 ? Math.random() * 10 - 5 : 0;
  
  // 4. Kinetic Typography (Word-by-Word revealing)
  const words = scene.caption ? scene.caption.split(' ') : [];
  // Calculate frames per word so they finish displaying slightly before the end of the scene
  const framesPerWord = words.length > 0 ? (durationFrames * 0.8) / words.length : 10;

  return (
      <AbsoluteFill style={{ overflow: 'hidden', backgroundColor: '#000' }}>
        
        {/* Visual Layer (Image/Video) with Camera Movement & Filter */}
        <AbsoluteFill 
          style={{ 
            transform: `scale(${scale}) translateX(${translateX}%) translateY(${translateY}%)`,
            filter: cssFilter
          }}
        >
          {scene.video_file ? (
            scene.video_file.endsWith('.mp4') ? (
              <Video src={staticFile(`assets/${scene.video_file}`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <Img src={staticFile(`assets/${scene.video_file}`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )
          ) : (
            // Animated Fallback Grid Background
            <div style={{ width: '100%', height: '100%', backgroundColor: '#0a0a0a', backgroundImage: 'linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)', backgroundSize: '50px 50px' }} />
          )}
        </AbsoluteFill>

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

        {/* Cinematic Vignette */}
        <AbsoluteFill
          style={{
            background: 'radial-gradient(circle, rgba(0,0,0,0) 30%, rgba(0,0,0,0.9) 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Word-by-Word Kinetic Typography */}
        {scene.caption && (
          <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
            <div
              style={{
                fontFamily: 'Impact, sans-serif',
                fontSize: '130px',
                fontWeight: '900',
                textTransform: 'uppercase',
                textAlign: 'center',
                maxWidth: '90%',
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '20px',
              }}
            >
              {words.map((word, index) => {
                // Determine the frame at which this word should appear
                const appearanceFrame = index * framesPerWord;
                // Pop animation for the word
                const wordScale = spring({
                  frame: frame - appearanceFrame,
                  fps,
                  config: { damping: 12, stiffness: 100, mass: 0.5 },
                });

                // If the current frame is before the word's appearance frame, don't render it (or scale 0)
                if (frame < appearanceFrame) {
                  return <div key={index} style={{ opacity: 0 }}>{word}</div>;
                }

                // Alternate colors for emphasis (Yellow vs White)
                const isYellow = index % 2 === 0;

                return (
                  <div
                    key={index}
                    style={{
                      transform: `scale(${wordScale})`,
                      color: isYellow ? '#ffcc00' : '#ffffff',
                      textShadow: '6px 6px 0px #000, -2px -2px 0px #000, 2px -2px 0px #000, -2px 2px 0px #000, 2px 2px 0px #000, 15px 15px 30px rgba(0,0,0,0.9)',
                      WebkitTextStroke: '4px black',
                      lineHeight: '1.2'
                    }}
                  >
                    {word}
                  </div>
                );
              })}
            </div>
          </AbsoluteFill>
        )}
      </AbsoluteFill>
  );
};
