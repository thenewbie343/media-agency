import { AbsoluteFill, Composition, getInputProps } from 'remotion';
import { DocumentaryScene } from './DocumentaryScene';
import { TransitionSeries, linearTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { Fragment } from 'react';

// Define the shape of our input props (from the Python pipeline)
export type SceneData = {
  scene: number;
  voiceover: string;
  caption: string;
  visual_type: string;
  video_file?: string;
  actual_duration?: number;
  duration_hint: number;
};

export const DocumentaryVideo: React.FC<{ scenes: SceneData[] }> = ({ scenes }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: 'black' }}>
      <TransitionSeries>
        {scenes.map((scene, index) => {
          // Use exact actual_duration for precision audio sync
          const durationFrames = Math.ceil((scene.actual_duration || scene.duration_hint) * 30);

          return (
            <Fragment key={index}>
              {index > 0 && (
                <TransitionSeries.Transition
                  presentation={fade()}
                  timing={linearTiming({ durationInFrames: 15 })}
                />
              )}
              <TransitionSeries.Sequence durationInFrames={durationFrames}>
                <DocumentaryScene
                  scene={scene}
                  durationFrames={durationFrames}
                />
              </TransitionSeries.Sequence>
            </Fragment>
          );
        })}
      </TransitionSeries>
    </AbsoluteFill>
  );
};

// Remotion requires a Root component that registers the compositions
export const RemotionRoot: React.FC = () => {
  const inputProps = getInputProps();
  
  // Default fallback data for when running in the Remotion Studio preview
  const defaultScenes = [
    {
      scene: 1,
      voiceover: "Testing",
      caption: "This is a test caption",
      visual_type: "motion_graphics",
      duration_hint: 4,
      actual_duration: 4
    }
  ];

  const scenes = (inputProps.scenes as SceneData[]) || defaultScenes;

  // Calculate total duration (accounting for transitions overlap)
  const baseDuration = scenes.reduce(
    (acc, curr) => acc + Math.round(curr.duration_hint * 30),
    0
  );
  
  const transitionOverlap = scenes.length > 1 ? (scenes.length - 1) * 15 : 0;
  const totalDuration = baseDuration - transitionOverlap;

  return (
    <>
      <Composition
        id="DocumentaryVideo"
        component={DocumentaryVideo}
        durationInFrames={totalDuration || 30}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          scenes: scenes,
        }}
      />
    </>
  );
};
