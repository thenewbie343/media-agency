import React from 'react';
import { Audio, staticFile, Sequence } from 'remotion';

const resolveAudioSrc = (cue?: string): string => {
  if (!cue) return '';
  if (cue.startsWith('http://') || cue.startsWith('https://')) return cue;
  if (cue.startsWith('assets/')) return staticFile(cue);
  if (cue.includes('.')) {
    if (cue.startsWith('sfx/')) return staticFile(`assets/${cue}`);
    return staticFile(`assets/sfx/${cue}`);
  }
  return staticFile(`assets/${cue}.mp3`);
};

export const AudioSystem: React.FC<{
  soundDesign?: string;
  volume?: number;
  events?: any[];
  durationFrames?: number;
}> = ({ soundDesign, volume = 0.6, events = [], durationFrames = 90 }) => {
  const sfxEvents = events.filter(e => e.type === 'SFX' || e.type === 'IMPACT');
  
  return (
    <>
      {soundDesign && (
        <Audio 
          src={resolveAudioSrc(soundDesign)} 
          volume={volume} 
          startFrom={0}
        />
      )}
      {sfxEvents.map((evt, idx) => {
        // Calculate start frame based on timing_percent
        const timingPct = evt.timing_percent !== undefined ? evt.timing_percent : 0;
        const delayFrames = Math.floor((timingPct / 100) * durationFrames);
        const evtVolume = evt.intensity ? evt.intensity * 0.96 : volume;
        return (
          <Sequence key={idx} from={delayFrames}>
            <Audio 
              src={resolveAudioSrc(evt.cue)} 
              volume={evtVolume} 
              startFrom={0}
            />
          </Sequence>
        );
      })}
    </>
  );
};
