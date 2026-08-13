import React, { Fragment } from 'react';
import { AbsoluteFill, Img, Video, staticFile } from 'remotion';
import { MapMotionGraphic } from './MapMotionGraphic';
import { TimelineMotionGraphic } from './TimelineMotionGraphic';
import { SemanticFallback } from './Fallbacks';
import { CameraSystem } from './Systems/CameraSystem';
import { CaptionSystem } from './Systems/CaptionSystem';
import { VFXLayer } from './Systems/VFXLayer';
import { AudioSystem } from './Systems/AudioSystem';
import { colors } from '../editorialTheme';

export const ShotRenderer: React.FC<{
  shot: any;
  durationFrames: number;
  shotIndex?: number;
}> = ({ shot, durationFrames, shotIndex }) => {
  const isMotionGraphics = shot.visual_type === 'motion_graphics' || shot.visual_type === 'text_stat';
  
  const searchStr = (shot.visual_query || '') + ' ' + (shot.ai_prompt || '');
  const searchLower = searchStr.toLowerCase();
  
  const isMapScene = isMotionGraphics && (searchLower.includes('map') || searchLower.includes('location') || searchLower.includes('geograph'));
  const isColdTheme = searchLower.includes('thriller') || searchLower.includes('history') || searchLower.includes('dark');
  const cssFilter = isColdTheme ? 'sepia(0.2) saturate(1.1) contrast(1.15) brightness(0.9) hue-rotate(-15deg)' : 'sepia(0.25) saturate(1.2) contrast(1.15) brightness(0.9) hue-rotate(5deg)';

  const videoFile = shot.asset?.path;
  const bgFile = shot.asset?.bg_file;
  const fgFile = shot.asset?.fg_file;
  const fallbackUsed = shot.asset?.fallback_used;

  return (
    <AbsoluteFill style={{ overflow: 'hidden', backgroundColor: colors.darkCharcoal }}>
      
      <CameraSystem 
        cameraMotion={shot.camera_motion} 
        durationFrames={durationFrames} 
        shotIndex={shotIndex || 1}
      >
        <AbsoluteFill style={{ filter: cssFilter }}>
          {fallbackUsed ? (
            <SemanticFallback shot={shot} seed={shotIndex || 1} />
          ) : isMotionGraphics ? (
            isMapScene ? (
              <MapMotionGraphic shot={shot} />
            ) : (
              <TimelineMotionGraphic shot={shot} />
            )
          ) : videoFile ? (
            videoFile.endsWith('.mp4') ? (
              /* eslint-disable-next-line @remotion/no-object-fit-on-media-video */
              <Video src={staticFile(`assets/${videoFile}`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} loop />
            ) : fgFile && bgFile ? (
              <Fragment>
                <Img src={staticFile(`assets/${bgFile}`)} style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover' }} />
                <Img src={staticFile(`assets/${fgFile}`)} style={{ position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', transform: 'scale(1.12)' }} />
              </Fragment>
            ) : (
              <Img src={staticFile(`assets/${videoFile}`)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )
          ) : (
            <SemanticFallback shot={shot} seed={shotIndex || 1} />
          )}
        </AbsoluteFill>
      </CameraSystem>

      <VFXLayer isColdTheme={isColdTheme} isGlitch={shot.overlay === 'vhs_glitch'} />
      <CaptionSystem caption={shot.caption} highlight={shot.highlight} durationFrames={durationFrames} />
      <AudioSystem soundDesign={shot.sound_design} />
      
      {shot.asset_provenance && (
        <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'flex-end', padding: 40, pointerEvents: 'none' }}>
          <div style={{
            color: 'rgba(255, 255, 255, 0.4)',
            fontFamily: 'serif',
            fontSize: '22px',
            textTransform: 'uppercase',
            letterSpacing: '0.15em',
            textShadow: '0 2px 4px rgba(0,0,0,0.8)'
          }}>
            {shot.asset_provenance.replace(/_/g, ' ')}
          </div>
        </AbsoluteFill>
      )}
      
    </AbsoluteFill>
  );
};
