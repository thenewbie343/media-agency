import React from 'react';
import { useCurrentFrame, interpolate, AbsoluteFill } from 'remotion';

export const CameraSystem: React.FC<{
  cameraMotion?: string;
  durationFrames: number;
  shotIndex: number;
  children: React.ReactNode;
}> = ({ cameraMotion, durationFrames, shotIndex, children }) => {
  const frame = useCurrentFrame();

  const pattern = ['zoom_in', 'pan_left', 'zoom_out', 'pan_right', 'pan_up'] as const;
  const activeIdx = Math.max(0, shotIndex);
  
  let movement = pattern[activeIdx % pattern.length] as string;
  if (cameraMotion) {
    const cleaned = cameraMotion.replace('ken_burns_', '').toLowerCase();
    if ((pattern as readonly string[]).includes(cleaned)) {
      movement = cleaned;
    }
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
    default:
      scale = interpolate(frame, [0, durationFrames], [1.05, 1.22], { extrapolateRight: 'clamp' });
      translateX = interpolate(frame, [0, durationFrames], [0, -6], { extrapolateRight: 'clamp' });
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
