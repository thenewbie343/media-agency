import React from 'react';
import { useCurrentFrame, interpolate, AbsoluteFill } from 'remotion';

export const CameraSystem: React.FC<{
  cameraMotion?: string;
  durationFrames: number;
  shotIndex: number;
  children: React.ReactNode;
}> = ({ cameraMotion, durationFrames, shotIndex, children }) => {
  const frame = useCurrentFrame();

  let movement = 'none';
  if (cameraMotion) {
    const cleaned = cameraMotion.replace('ken_burns_', '').toLowerCase();
    movement = cleaned;
  }

  let scale = 1;
  let translateX = 0;
  let translateY = 0;

  switch (movement) {
    case 'zoom_in':
      scale = interpolate(frame, [0, durationFrames], [1.0, 1.25], { extrapolateRight: 'clamp' });
      break;
    case 'pan_left':
      scale = 1.18;
      translateX = interpolate(frame, [0, durationFrames], [6, -6], { extrapolateRight: 'clamp' });
      break;
    case 'zoom_out':
      scale = interpolate(frame, [0, durationFrames], [1.25, 1.0], { extrapolateRight: 'clamp' });
      break;
    case 'pan_right':
      scale = 1.18;
      translateX = interpolate(frame, [0, durationFrames], [-6, 6], { extrapolateRight: 'clamp' });
      break;
    case 'pan_up':
      scale = 1.18;
      translateY = interpolate(frame, [0, durationFrames], [6, -6], { extrapolateRight: 'clamp' });
      break;
    case 'pan_down':
      scale = 1.18;
      translateY = interpolate(frame, [0, durationFrames], [-6, 6], { extrapolateRight: 'clamp' });
      break;
    case 'none':
    default:
      // Completely stable camera by default, as requested.
      scale = 1.0;
      translateX = 0;
      translateY = 0;
      break;
  }

  return (
    <AbsoluteFill
      style={{
        transform: `scale(${scale}) translateX(${translateX * 0.5}%) translateY(${translateY * 0.5}%)`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
