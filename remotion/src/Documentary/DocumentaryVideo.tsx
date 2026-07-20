import { AbsoluteFill, Composition, getInputProps } from 'remotion';
import { DocumentaryScene } from './DocumentaryScene';

// Define the shape of our input props (from the Python pipeline)
export type SceneData = {
  scene: number;
  voiceover: string;
  caption: string;
  visual_type: string;
  video_file?: string;
  duration_hint: number;
};

export const DocumentaryVideo: React.FC<{ scenes: SceneData[] }> = ({ scenes }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: 'black' }}>
      {/* We iterate over the scenes and calculate their start frames */}
      {scenes.map((scene, index) => {
        // Calculate start frame based on sum of previous durations (assuming 30fps)
        const startFrame = scenes
          .slice(0, index)
          .reduce((acc, curr) => acc + Math.round(curr.duration_hint * 30), 0);
        const durationFrames = Math.round(scene.duration_hint * 30);

        return (
          <DocumentaryScene
            key={scene.scene}
            scene={scene}
            startFrame={startFrame}
            durationFrames={durationFrames}
          />
        );
      })}
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
      duration_hint: 4
    }
  ];

  const scenes = (inputProps.scenes as SceneData[]) || defaultScenes;

  // Calculate total duration
  const totalDuration = scenes.reduce(
    (acc, curr) => acc + Math.round(curr.duration_hint * 30),
    0
  );

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
