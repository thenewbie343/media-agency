import { AbsoluteFill, Sequence, useVideoConfig, useCurrentFrame, interpolate, spring, Img, Video } from 'remotion';
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

  return (
    <Sequence from={startFrame} durationInFrames={durationFrames}>
      <AbsoluteFill style={{ overflow: 'hidden' }}>
        {/* Background Visual (Image or Video) */}
        <AbsoluteFill style={{ transform: `scale(${scale})` }}>
          {scene.video_file ? (
            scene.video_file.endsWith('.mp4') ? (
              <Video src={`file://${scene.video_file}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <Img src={`file://${scene.video_file}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )
          ) : (
            // Placeholder if no visual found
            <div style={{ width: '100%', height: '100%', backgroundColor: '#1a1a1a' }} />
          )}
        </AbsoluteFill>

        {/* Cinematic Vignette */}
        <AbsoluteFill
          style={{
            background: 'radial-gradient(circle, rgba(0,0,0,0) 40%, rgba(0,0,0,0.8) 100%)',
          }}
        />

        {/* Lower Thirds Captions */}
        {scene.caption && (
          <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'center', paddingBottom: '100px' }}>
            <div
              style={{
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                padding: '20px 40px',
                borderRadius: '10px',
                borderLeft: '8px solid #ffcc00',
                color: 'white',
                fontFamily: 'sans-serif',
                fontSize: '50px',
                fontWeight: 'bold',
                textShadow: '2px 2px 4px rgba(0,0,0,0.5)',
                textAlign: 'center',
                maxWidth: '80%',
              }}
            >
              {scene.caption}
            </div>
          </AbsoluteFill>
        )}
      </AbsoluteFill>
    </Sequence>
  );
};
