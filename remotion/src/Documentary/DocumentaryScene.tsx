import { AbsoluteFill, Sequence, useVideoConfig, useCurrentFrame, interpolate, spring, Img, Video, staticFile } from 'remotion';
import { SceneData } from './DocumentaryVideo';
import { Fragment } from 'react';

export const DocumentaryScene: React.FC<{
  scene: SceneData;
  startFrame: number;
  durationFrames: number;
}> = ({ scene, startFrame, durationFrames }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  // A subtle ken burns effect (zoom in slightly over time)
  const scale = interpolate(
    frame,
    [0, durationFrames],
    [1, 1.1],
    { extrapolateRight: 'clamp' }
  );

  // Spring animation for text pop-in
  const textScale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 90, mass: 0.5 },
  });

  return (
    <Sequence from={startFrame} durationInFrames={durationFrames}>
      <AbsoluteFill style={{ overflow: 'hidden' }}>
        {/* Background Visual (Image or Video) */}
        <AbsoluteFill style={{ transform: `scale(${scale})` }}>
          {scene.video_file ? (
            scene.video_file.endsWith('.mp4') ? (
              <Video src={staticFile(`assets/${scene.video_file}`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <Img src={staticFile(`assets/${scene.video_file}`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )
          ) : (
            // Placeholder if no visual found
            <div style={{ width: '100%', height: '100%', backgroundColor: '#1a1a1a' }} />
          )}
        </AbsoluteFill>

        {/* Cinematic Vignette */}
        <AbsoluteFill
          style={{
            background: 'radial-gradient(circle, rgba(0,0,0,0) 30%, rgba(0,0,0,0.9) 100%)',
          }}
        />

        {/* Kinetic Center Typography */}
        {scene.caption && (
          <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
            <div
              style={{
                transform: `scale(${textScale})`,
                color: '#ffcc00',
                fontFamily: 'Impact, sans-serif',
                fontSize: '120px',
                fontWeight: '900',
                textTransform: 'uppercase',
                textAlign: 'center',
                maxWidth: '90%',
                lineHeight: '1.1',
                textShadow: '6px 6px 0px #000, -2px -2px 0px #000, 2px -2px 0px #000, -2px 2px 0px #000, 2px 2px 0px #000, 10px 10px 20px rgba(0,0,0,0.8)',
                WebkitTextStroke: '3px black'
              }}
            >
              {scene.caption.split('\n').map((line, i) => (
                <Fragment key={i}>
                  {line}
                  <br />
                </Fragment>
              ))}
            </div>
          </AbsoluteFill>
        )}
      </AbsoluteFill>
    </Sequence>
  );
};
