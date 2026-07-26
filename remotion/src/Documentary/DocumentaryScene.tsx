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
    // 2.5D Parallax Depth Engine
    scale = interpolate(frame, [0, durationFrames], [1.05, 1.22], { extrapolateRight: 'clamp' });
    translateX = interpolate(frame, [0, durationFrames], [0, -8], { extrapolateRight: 'clamp' });
  }

  // 2. Thugesh Cinematic Master Color Grade (Warm Golden Hour + High Contrast Shadows)
  let cssFilter = 'sepia(0.18) saturate(1.25) contrast(1.15) brightness(0.95)';
  if (scene.lut === 'dark_noir') {
    cssFilter = 'grayscale(1) contrast(1.3) brightness(0.8)';
  } else if (scene.lut === 'neon_pink' || scene.lut === 'vintage') {
    cssFilter = 'sepia(0.8) hue-rotate(-30deg) saturate(2.5) contrast(1.2)';
  }

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
        
        {/* Visual Layer (Image/Video) with 2.5D Parallax Movement & Thugesh Golden-Hour Color Grade */}
        <AbsoluteFill 
          style={{ 
            transform: `scale(${parallaxBgScale}) translateX(${translateX * 0.5}%) translateY(${translateY}%)`,
            filter: cssFilter
          }}
        >
          {scene.video_file ? (
            scene.video_file.endsWith('.mp4') ? (
              <Video src={staticFile(`assets/${scene.video_file}`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <Img src={staticFile(`assets/${scene.video_file}`)} style={{ width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${parallaxFgScale / parallaxBgScale}) translateX(${translateX * 0.5}%)` }} />
            )
          ) : (
            // 30% Remotion Motion Graphics Grid & Blueprint Card
            <div style={{ width: '100%', height: '100%', backgroundColor: '#080c14', backgroundImage: 'radial-gradient(#1e293b 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '40px 40px, 80px 80px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
              <div style={{ width: '80%', height: '3px', backgroundColor: '#e2e8f0', boxShadow: '0 0 15px #38bdf8', marginBottom: '20px', transform: `scaleX(${Math.min(1, frame / 15)})` }} />
              <span style={{ fontFamily: 'monospace', color: '#38bdf8', letterSpacing: '6px', fontSize: '24px', textTransform: 'uppercase' }}>[ SYSTEM DOCUMENTATION • HISTORICAL METRICS ]</span>
            </div>
          )}
        </AbsoluteFill>

        {/* 20% Real Evidence Archival Stamp */}
        {(scene.visual_type === 'real_photo' || scene.visual_type === 'stock_video') && (
          <div style={{ position: 'absolute', top: '40px', left: '40px', display: 'flex', alignItems: 'center', gap: '12px', zIndex: 10 }}>
            <div style={{ width: '14px', height: '14px', borderRadius: '50%', backgroundColor: '#ef4444', boxShadow: '0 0 10px #ef4444', animation: 'pulse 1s infinite' }} />
            <span style={{ fontFamily: 'Impact, sans-serif', fontSize: '24px', color: '#ffffff', letterSpacing: '3px', textShadow: '2px 2px 4px rgba(0,0,0,0.9)', textTransform: 'uppercase' }}>
              ARCHIVAL EVIDENCE • DOCUMENTED RECORD
            </span>
          </div>
        )}

        {/* 30% Remotion Motion Graphics: Custom Maps, Timelines & UI Overlays */}
        {(scene.visual_type === 'motion_graphics' || scene.visual_type === 'text_stat') && (
          <Fragment>
            {/* Custom Interactive Map Radar & Target Overlay */}
            <div style={{ position: 'absolute', top: '40px', right: '40px', padding: '12px 20px', backgroundColor: 'rgba(8, 12, 20, 0.85)', border: '1px solid #38bdf8', borderRadius: '6px', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', gap: '12px', zIndex: 10 }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#38bdf8', boxShadow: '0 0 12px #38bdf8' }} />
              <span style={{ fontFamily: 'monospace', fontSize: '18px', color: '#38bdf8', letterSpacing: '2px' }}>
                GEOGRAPHIC RADAR • LOCATION MAP
              </span>
            </div>

            {/* Animated Timeline & Progress Bar */}
            <div style={{ position: 'absolute', bottom: '120px', left: '60px', right: '60px', height: '4px', backgroundColor: 'rgba(255, 255, 255, 0.15)', borderRadius: '2px', zIndex: 10 }}>
              <div style={{ width: `${Math.min(100, (frame / durationFrames) * 100)}%`, height: '100%', backgroundColor: '#f59e0b', boxShadow: '0 0 12px #f59e0b', borderRadius: '2px' }} />
            </div>

            {/* Glassmorphic Data Callout Card & Metric Badge */}
            <div style={{ position: 'absolute', bottom: '50px', left: '60px', padding: '14px 24px', backgroundColor: 'rgba(15, 23, 42, 0.9)', borderLeft: '6px solid #f59e0b', backdropFilter: 'blur(10px)', borderRadius: '4px', zIndex: 10, display: 'flex', alignItems: 'center', gap: '16px' }}>
              <span style={{ fontFamily: 'sans-serif', fontSize: '20px', fontWeight: 'bold', color: '#f59e0b', letterSpacing: '2px', textTransform: 'uppercase' }}>
                DOCUMENTARY CHRONOLOGY • KEY METRIC
              </span>
            </div>

            {/* High-Impact CTA Bell & Subscribe Popup (triggers on scene 5+) */}
            {scene.scene_number && scene.scene_number >= 5 && (
              <div style={{ position: 'absolute', top: '40px', left: '40px', padding: '10px 20px', backgroundColor: 'rgba(220, 38, 38, 0.9)', borderRadius: '30px', boxShadow: '0 0 15px rgba(220, 38, 38, 0.6)', zIndex: 10, display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '18px' }}>🔔</span>
                <span style={{ fontFamily: 'Impact, sans-serif', fontSize: '20px', color: '#ffffff', letterSpacing: '2px', textTransform: 'uppercase' }}>
                  SUBSCRIBE FOR PART 2
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

        {/* Film Grain Overlay */}
        <AbsoluteFill
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.08'/%3E%3C/svg%3E")`,
            pointerEvents: 'none',
            mixBlendMode: 'overlay',
            opacity: 0.5,
          }}
        />

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
