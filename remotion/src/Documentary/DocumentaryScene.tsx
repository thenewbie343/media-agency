import React, { Fragment } from 'react';
import { useVideoConfig, useCurrentFrame, interpolate, spring, AbsoluteFill, Img, Video, staticFile } from 'remotion';
import { MapMotionGraphic } from './MapMotionGraphic';
import { TimelineMotionGraphic } from './TimelineMotionGraphic';
import { SceneData } from './DocumentaryVideo';

// Advanced Motion Graphic Engine for YouTube Documentaries
export const DocumentaryScene: React.FC<{
  scene: SceneData;
  durationFrames: number;
}> = ({ scene, durationFrames }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const isMotionGraphics = scene.visual_type === 'motion_graphics' || scene.visual_type === 'text_stat';
  
  const searchStr = (scene.visual_search || '') + ' ' + (scene.ai_prompt || '');
  const searchLower = searchStr.toLowerCase();
  
  const isMapScene = isMotionGraphics && (searchLower.includes('map') || searchLower.includes('location') || searchLower.includes('geograph'));
  const isTimelineScene = isMotionGraphics && !isMapScene && (searchLower.includes('timeline') || searchLower.includes('chronolog') || searchLower.includes('history') || searchLower.includes('date'));
  const isDataScene = isMotionGraphics && !isMapScene && !isTimelineScene;

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
    // 2.5D Parallax Depth Engine
    scale = interpolate(frame, [0, durationFrames], [1.05, 1.22], { extrapolateRight: 'clamp' });
    translateX = interpolate(frame, [0, durationFrames], [0, -8], { extrapolateRight: 'clamp' });
  }

  // 2. Universal Master Filter (Global Color Grade)
  // Instead of conditional LUTs per scene that break unity, we apply one universal cinematic grade.
  const isColdTheme = searchLower.includes('thriller') || searchLower.includes('history') || searchLower.includes('dark');
  const cssFilter = isColdTheme ? 'sepia(0.2) saturate(1.1) contrast(1.15) brightness(0.9) hue-rotate(-15deg)' : 'sepia(0.25) saturate(1.2) contrast(1.15) brightness(0.9) hue-rotate(5deg)';

  // 3. VHS Glitch / Scanline effect
  const isGlitch = scene.overlay === 'vhs_glitch';
  const randomGlitchShift = isGlitch && frame % 10 === 0 ? Math.random() * 10 - 5 : 0;
  
  // 4. Kinetic Typography (Word-by-Word revealing)
  const words = scene.caption ? scene.caption.split(' ') : [];
  const framesPerWord = words.length > 0 ? (durationFrames * 0.8) / words.length : 10;

  // 2.5D Parallax background/foreground scale differential
  const parallaxBgScale = scale * 0.96;
  const parallaxFgScale = scale * 1.08;

  return (
      <AbsoluteFill style={{ overflow: 'hidden', backgroundColor: '#000' }}>
        
        {/* Visual Layer (Image/Video or Full-Screen Remotion Motion Graphics Canvas) */}
        <AbsoluteFill 
          style={{ 
            transform: `scale(${parallaxBgScale}) translateX(${translateX * 0.5}%) translateY(${translateY}%)`,
            filter: cssFilter
          }}
        >
          {isMotionGraphics ? (
            isMapScene ? (
              <MapMotionGraphic title={scene.caption?.slice(0, 30) || 'TACTICAL MAP TARGET'} />
            ) : (
              <TimelineMotionGraphic title={scene.caption?.slice(0, 30) || 'CHRONOLOGY ANALYSIS'} />
            )
          ) : scene.video_file ? (
            scene.video_file.endsWith('.mp4') ? (
              <Video src={staticFile(`assets/${scene.video_file}`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : scene.fg_file && scene.bg_file ? (
              <Fragment>
                {/* 2.5D Parallax Background */}
                <Img src={staticFile(`assets/${scene.bg_file}`)} style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${parallaxBgScale}) translateX(${translateX * 0.3}%)` }} />
                {/* 2.5D Parallax Foreground Subject */}
                <Img src={staticFile(`assets/${scene.fg_file}`)} style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${parallaxFgScale}) translateX(${translateX * 0.8}%)` }} />
              </Fragment>
            ) : (
              <Img src={staticFile(`assets/${scene.video_file}`)} style={{ width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${parallaxFgScale / parallaxBgScale}) translateX(${translateX * 0.5}%)` }} />
            )
          ) : (
            <TimelineMotionGraphic title="SYSTEM DATA METRICS" />
          )}
        </AbsoluteFill>

        {/* 30% Remotion Motion Graphics: Custom Maps, Timelines & UI Overlays */}
        {(scene.visual_type === 'motion_graphics' || scene.visual_type === 'text_stat') && (
          <Fragment>
            {/* Custom Interactive Map Radar & Target Overlay */}
            {isMapScene && (
              <div style={{ position: 'absolute', top: '40px', right: '40px', padding: '12px 20px', backgroundColor: 'rgba(8, 12, 20, 0.85)', border: '1px solid #38bdf8', borderRadius: '6px', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', gap: '12px', zIndex: 10 }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#38bdf8', boxShadow: '0 0 12px #38bdf8' }} />
                <span style={{ fontFamily: 'monospace', fontSize: '18px', color: '#38bdf8', letterSpacing: '2px' }}>
                  GEOGRAPHIC RADAR • LOCATION MAP
                </span>
              </div>
            )}

            {/* Animated Timeline & Progress Bar */}
            {isTimelineScene && (
              <div style={{ position: 'absolute', bottom: '120px', left: '60px', right: '60px', height: '4px', backgroundColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '2px', zIndex: 10 }}>
                <div style={{ width: `${Math.min(100, (frame / durationFrames) * 100)}%`, height: '100%', backgroundColor: '#f59e0b', boxShadow: '0 0 12px #f59e0b', borderRadius: '2px' }} />
              </div>
            )}

            {/* Glassmorphic Data Callout Card & Metric Badge */}
            {(isDataScene || isTimelineScene) && (
              <div style={{ position: 'absolute', top: '40px', left: '40px', padding: '14px 24px', backgroundColor: 'rgba(15, 23, 42, 0.9)', borderLeft: '6px solid #f59e0b', backdropFilter: 'blur(10px)', borderRadius: '4px', zIndex: 10, display: 'flex', alignItems: 'center', gap: '16px' }}>
                <span style={{ fontFamily: 'sans-serif', fontSize: '20px', fontWeight: 'bold', color: '#f59e0b', letterSpacing: '2px', textTransform: 'uppercase' }}>
                  {isTimelineScene ? 'DOCUMENTARY CHRONOLOGY' : 'SYSTEM DATA METRICS'}
                </span>
              </div>
            )}

          </Fragment>
        )}

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

        {/* Atmospheric Layering (Dust Motes) */}
        <AbsoluteFill style={{ pointerEvents: 'none', opacity: 0.6, zIndex: 20 }}>
          {Array.from({ length: 20 }).map((_, i) => {
            const startX = (i * 17) % 100;
            const delay = (i * 13) % 100;
            const size = 2 + (i % 4);
            const moveY = interpolate(frame - delay, [0, 300], [100, -20], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
            return (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: `${startX}%`,
                  bottom: `${moveY}%`,
                  width: `${size}px`,
                  height: `${size}px`,
                  backgroundColor: 'rgba(255,255,255,0.4)',
                  borderRadius: '50%',
                  boxShadow: '0 0 10px rgba(255,255,255,0.5)',
                  transform: `translateX(${Math.sin((frame + delay) / 30) * 20}px)`,
                }}
              />
            );
          })}
        </AbsoluteFill>

        {/* Film Grain Overlay - 3% Master Filter */}
        <AbsoluteFill
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.03'/%3E%3C/svg%3E")`,
            pointerEvents: 'none',
            mixBlendMode: 'overlay',
            opacity: 1,
          }}
        />

        {/* Cinematic Vignette - Outer 15% Darkened */}
        <AbsoluteFill
          style={{
            background: 'radial-gradient(circle, rgba(0,0,0,0) 65%, rgba(0,0,0,0.85) 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Modern Non-Intrusive Lower-Third Captions */}
        {scene.caption && (
          <div style={{ position: 'absolute', bottom: '30px', width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 30, pointerEvents: 'none' }}>
            <div
              style={{
                fontFamily: '"Noto Sans Devanagari", Inter, system-ui, -apple-system, sans-serif',
                fontSize: '32px',
                fontWeight: '800',
                textTransform: 'uppercase',
                textAlign: 'center',
                maxWidth: '85%',
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: 'rgba(5, 8, 16, 0.65)',
                padding: '10px 24px',
                borderRadius: '8px',
                border: 'none',
                boxShadow: '0 10px 40px rgba(0, 0, 0, 0.9)',
                backdropFilter: 'blur(4px)',
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

                // Highlight key emphasis words in gold vs white
                const isYellow = index % 2 === 0;

                return (
                  <span
                    key={index}
                    style={{
                      transform: `scale(${wordScale})`,
                      color: isYellow ? '#f59e0b' : '#ffffff',
                      textShadow: '0 2px 8px rgba(0,0,0,0.9)',
                      letterSpacing: '1px'
                    }}
                  >
                    {word}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </AbsoluteFill>
  );
};
