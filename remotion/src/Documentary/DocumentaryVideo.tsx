import { AbsoluteFill, Composition, getInputProps, Audio, staticFile, Sequence } from 'remotion';
import { ShotRenderer } from './ShotRenderer';
import { TransitionSeries, linearTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { Fragment } from 'react';

// Define the shape of our input props (from the Python pipeline)
export type ShotData = {
  shot_id: string;
  duration_mode: "ratio" | "fixed";
  duration_ratio?: number;
  duration_seconds?: number;
  actual_duration: number; // calculated precise duration in seconds
  visual_type: string;
  visual_query?: string;
  ai_prompt?: string;
  camera_motion?: string;
  overlay?: string;
  lut?: string;
  asset?: {
    path?: string;
    source?: string;
    status?: string;
    bg_file?: string;
    fg_file?: string;
    fallback_used?: boolean;
  };
  caption?: string; // Passed down from the parent block for rendering
};

export type NarrationBlockData = {
  block_id: string;
  voiceover: string;
  audio_file?: string;
  strategic_silence?: {
    duration_seconds?: number;
    visual_behavior?: string;
  };
  music_ducking?: {
    duck_to_percentage?: number;
    ramp_duration_seconds?: number;
  };
  shots: ShotData[];
  actual_voice_duration: number;
  total_block_duration: number;
  caption?: string; // Raw caption, passed to shots
};

export type StoryBeatData = {
  beat_id: string;
  intent: string;
  narration_blocks: NarrationBlockData[];
};

export type ScriptManifest = {
  schema_version: string;
  project_meta: any;
  story_beats: StoryBeatData[];
};

export const DocumentaryVideo: React.FC<{ manifest: ScriptManifest }> = ({ manifest }) => {
  if (!manifest || !manifest.story_beats) {
    return <AbsoluteFill style={{ backgroundColor: 'black' }} />;
  }

  // Flatten the shots from the hierarchy for the visual timeline
  const allShots: ShotData[] = [];
  manifest.story_beats.forEach(beat => {
    beat.narration_blocks.forEach(block => {
      block.shots.forEach(shot => {
        allShots.push({ ...shot, caption: block.caption });
      });
    });
  });

  // Collect the audio timeline data
  const audioBlocks: { file: string; startFrame: number }[] = [];
  let currentFrame = 0;

  manifest.story_beats.forEach(beat => {
    beat.narration_blocks.forEach(block => {
      // Calculate block duration in frames
      const blockDurationFrames = Math.ceil(block.total_block_duration * 30);
      
      // If there's an audio file, add it to our Audio timeline array
      if (block.audio_file) {
        audioBlocks.push({
          file: block.audio_file,
          startFrame: currentFrame,
        });
      }
      
      currentFrame += blockDurationFrames;
    });
  });

  return (
    <AbsoluteFill style={{ backgroundColor: 'black' }}>
      
      {/* 1. VISUAL TIMELINE */}
      <TransitionSeries>
        {allShots.map((shot, index) => {
          // Precise calculated shot duration
          const durationFrames = Math.ceil((shot.actual_duration || 4) * 30);

          return (
            <Fragment key={shot.shot_id || index}>
              {index > 0 && (
                <TransitionSeries.Transition
                  presentation={fade()}
                  timing={linearTiming({ durationInFrames: 15 })}
                />
              )}
              <TransitionSeries.Sequence durationInFrames={durationFrames}>
                <ShotRenderer
                  shot={shot}
                  durationFrames={durationFrames}
                  shotIndex={index}
                />
              </TransitionSeries.Sequence>
            </Fragment>
          );
        })}
      </TransitionSeries>
      
      {/* 2. AUDIO TIMELINE */}
      {audioBlocks.map((audio, i) => (
        <Sequence key={`audio-${i}`} from={audio.startFrame}>
          <Audio 
            src={staticFile(`assets/${audio.file}`)} 
            volume={1} 
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

// Remotion requires a Root component that registers the compositions
export const RemotionRoot: React.FC = () => {
  const inputProps = getInputProps();
  
  // Default fallback data for when running in the Remotion Studio preview
  const defaultManifest: ScriptManifest = {
    schema_version: "2.0",
    project_meta: { topic: "Test", length_minutes: 1 },
    story_beats: [
      {
        beat_id: "test",
        intent: "test",
        narration_blocks: [
          {
            block_id: "b1",
            voiceover: "Testing the new visual timeline.",
            caption: "Testing the new visual timeline.",
            actual_voice_duration: 3,
            total_block_duration: 4,
            shots: [
              {
                shot_id: "s1",
                duration_mode: "fixed",
                duration_seconds: 4,
                actual_duration: 4,
                visual_type: "motion_graphics"
              }
            ]
          }
        ]
      }
    ]
  };

  const manifest = (inputProps.scenes ? { story_beats: [], ...inputProps, schema_version: "2.0" } : inputProps) as ScriptManifest;
  const activeManifest = manifest.story_beats ? manifest : defaultManifest;

  // Calculate total duration (accounting for transitions overlap)
  let baseDuration = 0;
  let totalShotsCount = 0;
  
  activeManifest.story_beats.forEach(beat => {
    beat.narration_blocks.forEach(block => {
      block.shots.forEach(shot => {
        baseDuration += Math.ceil((shot.actual_duration || 4) * 30);
        totalShotsCount++;
      });
    });
  });
  
  const transitionOverlap = totalShotsCount > 1 ? (totalShotsCount - 1) * 15 : 0;
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
          manifest: activeManifest,
        }}
      />
    </>
  );
};
