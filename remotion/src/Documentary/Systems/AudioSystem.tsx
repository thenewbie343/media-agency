import React from 'react';
import { Audio, staticFile } from 'remotion';

export const AudioSystem: React.FC<{
  soundDesign?: string;
  volume?: number;
}> = ({ soundDesign, volume = 0.5 }) => {
  if (!soundDesign) return null;

  return (
    <Audio 
      src={staticFile(`assets/${soundDesign}.mp3`)} 
      volume={volume} 
      startFrom={0}
    />
  );
};
