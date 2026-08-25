import React, { Fragment } from 'react';
import { AbsoluteFill, Img, OffthreadVideo, staticFile, useCurrentFrame, interpolate } from 'remotion';
import { MapMotionGraphic } from './MapMotionGraphic';
import { TimelineMotionGraphic } from './TimelineMotionGraphic';
import { SemanticFallback } from './Fallbacks';
import { CameraSystem } from './Systems/CameraSystem';
import { CaptionSystem } from './Systems/CaptionSystem';
import { VFXLayer } from './Systems/VFXLayer';
import { AudioSystem } from './Systems/AudioSystem';
import { EvidenceCard } from './Systems/EvidenceCard';
import { colors } from '../editorialTheme';

export const ShotRenderer: React.FC<{
  shot: any;
  durationFrames: number;
  shotIndex?: number;
}> = ({ shot, durationFrames, shotIndex }) => {
  const frame = useCurrentFrame();
  const vType = shot.visual_type || '';
  const isEvidence = vType.startsWith('EVIDENCE') || vType === 'evidence' || shot.fallback_type === 'EvidenceCard';
  const isBlackHold = vType === 'BLACK_HOLD';
  const isTypographyReveal = vType === 'TYPOGRAPHY_REVEAL';
  const isMotionGraphics = vType === 'motion_graphics' || vType === 'text_stat' || vType === 'MOTION_GRAPHIC';
  
  const searchStr = (shot.visual_query || '') + ' ' + (shot.ai_prompt || '') + ' ' + (shot.visual_description || '');
  const searchLower = searchStr.toLowerCase();
  
  const isMapScene = isMotionGraphics && (searchLower.includes('map') || searchLower.includes('location') || searchLower.includes('geograph') || searchLower.includes('trajectory'));
  const isColdTheme = searchLower.includes('thriller') || searchLower.includes('history') || searchLower.includes('dark') || searchLower.includes('soviet') || searchLower.includes('bunker');
  
  let cssFilter = 'none';
  if (shot.lut_filter === 'warm_cinema') {
    cssFilter = 'sepia(0.3) saturate(1.35) contrast(1.15) brightness(0.96) hue-rotate(5deg)';
  } else if (shot.lut_filter === 'teal_orange') {
    cssFilter = 'sepia(0.2) saturate(1.45) contrast(1.25) hue-rotate(18deg) brightness(0.92)';
  } else if (shot.lut_filter === 'sepia') {
    cssFilter = 'sepia(0.9) saturate(0.8) contrast(1.25) brightness(0.9)';
  } else if (shot.lut_filter === 'vintage_film') {
    cssFilter = 'sepia(0.45) saturate(0.8) contrast(1.35) brightness(0.85)';
  } else if (shot.lut_filter === 'noir') {
    cssFilter = 'grayscale(1) contrast(1.6) brightness(0.82)';
  } else if (shot.lut_filter === 'neon_cyberpunk') {
    cssFilter = 'saturate(2.2) hue-rotate(180deg) contrast(1.3) brightness(0.95)';
  } else if (shot.lut_filter === 'high_contrast') {
    cssFilter = 'contrast(1.6) saturate(1.25) brightness(0.92)';
  }

  const videoFile = shot.asset?.path;
  const bgFile = shot.asset?.bg_file;
  const fgFile = shot.asset?.fg_file;
  const fallbackUsed = shot.asset?.fallback_used;

  // Typography Reveal Animation
  const textOpacity = interpolate(frame, [10, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const textScale = interpolate(frame, [0, durationFrames], [0.96, 1.04]);

  return (
    <AbsoluteFill style={{ overflow: 'hidden', backgroundColor: colors.darkCharcoal }}>
      
      <CameraSystem 
        cameraMotion={shot.camera_motion} 
        durationFrames={durationFrames} 
        shotIndex={shotIndex || 1}
      >
        <AbsoluteFill style={{ filter: cssFilter }}>
          {isBlackHold ? (
            /* CINEMATIC BLACK / STRATEGIC SILENCE HOLD */
            <AbsoluteFill style={{ backgroundColor: '#050505', justifyContent: 'center', alignItems: 'center' }}>
              {shot.text_overlay && (
                <div style={{
                  fontFamily: 'monospace',
                  fontSize: 28,
                  letterSpacing: '0.3em',
                  color: 'rgba(255, 255, 255, 0.4)',
                  textTransform: 'uppercase'
                }}>
                  {shot.text_overlay}
                </div>
              )}
            </AbsoluteFill>
          ) : isTypographyReveal ? (
            /* MAJOR EDITORIAL TYPOGRAPHY REVEAL */
            <AbsoluteFill style={{ 
              backgroundColor: colors.darkCharcoal, 
              justifyContent: 'center', 
              alignItems: 'center', 
              padding: 80 
            }}>
              <div style={{
                opacity: textOpacity,
                transform: `scale(${textScale})`,
                textAlign: 'center',
                maxWidth: '85%'
              }}>
                <div style={{
                  fontFamily: 'serif',
                  fontSize: 48,
                  fontWeight: 900,
                  color: colors.parchment,
                  lineHeight: 1.3,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  borderTop: `2px solid ${colors.warmGold}`,
                  borderBottom: `2px solid ${colors.warmGold}`,
                  padding: '30px 20px',
                  boxShadow: '0 0 40px rgba(0,0,0,0.9)'
                }}>
                  {shot.text_overlay || shot.visual_description}
                </div>
              </div>
            </AbsoluteFill>
          ) : isEvidence ? (
            /* FIRST-CLASS EVIDENCE RENDERING */
            <EvidenceCard shot={shot} durationFrames={durationFrames} />
          ) : fallbackUsed ? (
            <SemanticFallback shot={shot} seed={shotIndex || 1} />
          ) : isMotionGraphics ? (
            isMapScene ? (
              <MapMotionGraphic shot={shot} />
            ) : (
              <TimelineMotionGraphic shot={shot} />
            )
          ) : videoFile ? (
            videoFile.endsWith('.mp4') ? (
              <OffthreadVideo 
                src={staticFile(`assets/${videoFile}`)} 
                style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                pauseWhenBuffering
              />
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

      <VFXLayer isColdTheme={isColdTheme} overlay={shot.overlay} events={shot.editorial_events} durationFrames={durationFrames} />
      <CaptionSystem caption={shot.caption} highlight={shot.highlight} durationFrames={durationFrames} />
      <AudioSystem soundDesign={shot.sound_design} events={shot.editorial_events} durationFrames={durationFrames} />
      
      {/* AUTHENTIC PROVENANCE BADGE */}
      {shot.asset_provenance && !isBlackHold && (
        <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'flex-end', padding: 35, pointerEvents: 'none' }}>
          <div style={{
            color: 'rgba(255, 255, 255, 0.45)',
            fontFamily: 'monospace',
            fontSize: '15px',
            textTransform: 'uppercase',
            letterSpacing: '0.2em',
            backgroundColor: 'rgba(0, 0, 0, 0.4)',
            padding: '4px 12px',
            borderRadius: '2px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            textShadow: '0 2px 4px rgba(0,0,0,0.8)'
          }}>
            [ {shot.asset_provenance.replace(/_/g, ' ')} ]
          </div>
        </AbsoluteFill>
      )}
      
    </AbsoluteFill>
  );
};
