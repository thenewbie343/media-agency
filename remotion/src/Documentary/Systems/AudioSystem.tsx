import React from 'react';
import { Audio, staticFile, Sequence } from 'remotion';

export const AudioSystem: React.FC<{
  soundDesign?: string;
  volume?: number;
  events?: any[];
  durationFrames?: number;
}> = ({ soundDesign, volume = 0.5, events = [], durationFrames = 90 }) => {
  const sfxEvents = events.filter(e => e.type === 'SFX' || e.type === 'IMPACT');
  
  return (
    <>
      {soundDesign && (
        <Audio 
          src={staticFile(`assets/${soundDesign}.mp3`)} 
          volume={volume} 
          startFrom={0}
        />
      )}
      {sfxEvents.map((evt, idx) => {
        // Calculate start frame based on timing_percent
        const timingPct = evt.timing_percent !== undefined ? evt.timing_percent : 0;
        const delayFrames = Math.floor((timingPct / 100) * durationFrames);
        const evtVolume = evt.intensity ? evt.intensity * 0.8 : volume;
        return (
          <Sequence key={idx} from={delayFrames}>
            <Audio 
              src={staticFile(`assets/${evt.cue}.mp3`)} 
              volume={evtVolume} 
              startFrom={0}
            />
          </Sequence>
        );
      })}
    </>
  );
};
