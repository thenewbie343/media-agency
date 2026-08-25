import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame, interpolate, spring } from 'remotion';
import { colors } from '../../editorialTheme';

export const EvidenceCard: React.FC<{
  shot: any;
  durationFrames?: number;
}> = ({ shot, durationFrames = 150 }) => {
  const frame = useCurrentFrame();
  const asset = shot.asset || {};
  const sourceName = asset.source_name || shot.source_name || 'CENTRAL ARCHIVES';
  const confidence = asset.confidence || shot.confidence || 0.99;
  const title = asset.title || shot.text_overlay || 'DECLASSIFIED EVIDENCE RECORD';
  const excerpt = asset.relevant_excerpt || shot.visual_description || '';
  const date = asset.publication_date || shot.source_date || '1983-09-26';
  const publisher = asset.publisher || sourceName;
  const treatment = asset.visual_treatment || (
    shot.visual_type === 'EVIDENCE_ARTICLE' ? 'article_clipping' :
    shot.visual_type === 'EVIDENCE_QUOTE' ? 'quote_highlight' :
    shot.visual_type === 'EVIDENCE_PHOTO' ? 'photo_pan' : 'document_inspection'
  );

  // Entrance spring
  const scale = spring({
    frame,
    fps: 30,
    config: { damping: 14, mass: 0.9 },
    durationInFrames: 25,
  });

  // Slow inspection drift
  const yOffset = interpolate(frame, [0, durationFrames], [8, -8]);
  const rotation = interpolate(frame, [0, durationFrames], [-0.5, 0.5]);

  // Marker highlight progress
  const highlightProgress = interpolate(frame, [15, 45], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // ARTICLE CLIPPING TREATMENT
  if (treatment === 'article_clipping' || shot.visual_type === 'EVIDENCE_ARTICLE') {
    return (
      <AbsoluteFill style={{ 
        backgroundColor: colors.darkCharcoal,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 50
      }}>
        <div style={{
          backgroundColor: '#fbf8f1',
          width: '85%',
          height: '85%',
          boxShadow: '0 25px 60px rgba(0,0,0,0.7)',
          display: 'flex',
          flexDirection: 'column',
          padding: '50px 60px',
          transform: `scale(${scale}) translateY(${yOffset}px) rotate(${rotation}deg)`,
          position: 'relative',
          border: '1px solid #e0d8c3'
        }}>
          {/* Newspaper Masthead */}
          <div style={{ borderBottom: '3px double #1c1917', paddingBottom: 15, marginBottom: 25, textAlign: 'center' }}>
            <div style={{ fontFamily: 'serif', fontSize: 38, fontWeight: 900, letterSpacing: '0.1em', textTransform: 'uppercase', color: colors.charcoal }}>
              {publisher}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, fontFamily: 'monospace', color: '#666', marginTop: 8 }}>
              <span>HISTORICAL DISPATCH</span>
              <span>DATE: {date}</span>
              <span>ARCHIVE REF: {(confidence * 100).toFixed(0)}% AUTHENTIC</span>
            </div>
          </div>

          {/* Headline */}
          <div style={{ fontFamily: 'serif', fontSize: 32, fontWeight: 800, color: colors.charcoal, marginBottom: 25, lineHeight: 1.2 }}>
            {title}
          </div>

          {/* Body & Excerpt Highlight */}
          <div style={{ flex: 1, position: 'relative' }}>
            <div style={{ 
              fontFamily: 'serif', 
              fontSize: 26, 
              lineHeight: 1.5, 
              color: '#2a2825',
              position: 'relative',
              display: 'inline',
              background: `linear-gradient(90deg, rgba(212, 175, 55, 0.4) ${highlightProgress}%, transparent ${highlightProgress}%)`
            }}>
              "{excerpt}"
            </div>
          </div>

          {/* Archival Corner Seal */}
          <div style={{
            position: 'absolute',
            bottom: 35,
            right: 40,
            border: '2px solid #8c7b6b',
            padding: '6px 16px',
            fontFamily: 'monospace',
            fontSize: 14,
            color: '#8c7b6b',
            letterSpacing: 2
          }}>
            EXHIBIT RECORD // {sourceName.toUpperCase()}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // QUOTE HIGHLIGHT TREATMENT
  if (treatment === 'quote_highlight' || shot.visual_type === 'EVIDENCE_QUOTE') {
    return (
      <AbsoluteFill style={{ 
        backgroundColor: colors.darkCharcoal,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 60
      }}>
        <div style={{
          width: '80%',
          display: 'flex',
          flexDirection: 'column',
          transform: `scale(${scale}) translateY(${yOffset}px)`,
          position: 'relative'
        }}>
          <div style={{ fontFamily: 'serif', fontSize: 120, color: colors.warmGold, opacity: 0.6, lineHeight: 0.5, marginBottom: 20 }}>
            “
          </div>
          <div style={{
            fontFamily: 'serif',
            fontSize: 42,
            lineHeight: 1.4,
            color: colors.parchment,
            fontStyle: 'italic',
            marginBottom: 35,
            textShadow: '0 4px 15px rgba(0,0,0,0.8)'
          }}>
            {excerpt || title}
          </div>
          <div style={{ borderTop: `2px solid ${colors.warmGold}`, paddingTop: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontFamily: 'serif', fontSize: 24, fontWeight: 'bold', color: colors.warmGold }}>
                {sourceName}
              </div>
              <div style={{ fontFamily: 'sans-serif', fontSize: 16, color: '#aaa', marginTop: 4 }}>
                {title} // {date}
              </div>
            </div>
            <div style={{ fontFamily: 'monospace', fontSize: 16, color: '#888', border: '1px solid #444', padding: '6px 12px' }}>
              PRIMARY SOURCE EVIDENCE
            </div>
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // PHOTO TREATMENT
  if (treatment === 'photo_pan' || shot.visual_type === 'EVIDENCE_PHOTO') {
    return (
      <AbsoluteFill style={{ 
        backgroundColor: colors.darkCharcoal,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 40
      }}>
        <div style={{
          backgroundColor: '#eae5d9',
          padding: 20,
          boxShadow: '0 25px 50px rgba(0,0,0,0.8)',
          transform: `scale(${scale}) translateY(${yOffset}px) rotate(${rotation}deg)`,
          width: '80%',
          height: '85%',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{ flex: 1, backgroundColor: '#000', overflow: 'hidden', position: 'relative' }}>
            {asset.path || asset.fg_file ? (
              <Img 
                src={staticFile(`assets/${asset.path || asset.fg_file}`)} 
                style={{ width: '100%', height: '100%', objectFit: 'contain' }} 
              />
            ) : (
              <div style={{ width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#fff', fontFamily: 'serif', fontSize: 28 }}>
                [HISTORICAL PHOTOGRAPH RECORD]
              </div>
            )}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 15 }}>
            <div style={{ fontFamily: 'serif', fontSize: 20, color: colors.charcoal, fontWeight: 'bold' }}>
              {title}
            </div>
            <div style={{ fontFamily: 'monospace', fontSize: 14, color: '#666' }}>
              {sourceName} • {date}
            </div>
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // DEFAULT: CLASSIFIED DOCUMENT INSPECTION
  return (
    <AbsoluteFill style={{ 
      backgroundColor: colors.darkCharcoal,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 40
    }}>
      {asset.bg_file && (
        <Img src={staticFile(`assets/${asset.bg_file}`)} style={{
          position: 'absolute', width: '100%', height: '100%', objectFit: 'cover', opacity: 0.25
        }} />
      )}

      <div style={{
        backgroundColor: colors.parchment,
        width: '80%',
        height: '85%',
        boxShadow: '0 25px 60px rgba(0,0,0,0.8)',
        display: 'flex',
        flexDirection: 'column',
        padding: '50px 60px',
        transform: `scale(${scale}) translateY(${yOffset}px) rotate(${rotation}deg)`,
        position: 'relative',
        border: '1px solid #dcd3be'
      }}>
        {/* Header */}
        <div style={{ 
          borderBottom: `2px solid ${colors.warmGold}`, 
          paddingBottom: '16px',
          marginBottom: '25px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end'
        }}>
          <div>
            <div style={{ fontFamily: 'sans-serif', fontSize: 16, color: '#777', letterSpacing: 2, textTransform: 'uppercase' }}>
              ARCHIVAL SOURCE RECORD
            </div>
            <div style={{ fontFamily: 'serif', fontSize: 30, color: colors.charcoal, fontWeight: 'bold' }}>
              {sourceName}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontFamily: 'sans-serif', fontSize: 14, color: '#888' }}>VERIFICATION</div>
            <div style={{ fontFamily: 'monospace', fontSize: 20, color: confidence >= 0.95 ? '#2e7d32' : colors.warmGold }}>
              {(confidence * 100).toFixed(0)}% AUTHENTIC
            </div>
          </div>
        </div>

        {/* Content Scan or Text */}
        {asset.fg_file || asset.path ? (
          <Img src={staticFile(`assets/${asset.fg_file || asset.path}`)} style={{ 
            width: '100%', flex: 1, objectFit: 'contain', border: '1px solid #ccc'
          }} />
        ) : (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            border: '1px dashed #b8ad99',
            padding: 30,
            backgroundColor: 'rgba(255,255,255,0.4)'
          }}>
            <div style={{ fontFamily: 'serif', fontSize: 34, fontWeight: 'bold', color: colors.charcoal, textAlign: 'center', marginBottom: 15 }}>
              {title}
            </div>
            {excerpt && (
              <div style={{ 
                fontFamily: 'monospace', 
                fontSize: 22, 
                color: '#333', 
                textAlign: 'center',
                backgroundColor: 'rgba(212, 175, 55, 0.25)',
                padding: '10px 20px',
                borderLeft: `4px solid ${colors.warmGold}`
              }}>
                "{excerpt}"
              </div>
            )}
          </div>
        )}

        {/* Declassified Stamp */}
        <div style={{
          position: 'absolute',
          bottom: 35,
          right: 40,
          border: '4px solid #b71c1c',
          color: '#b71c1c',
          fontFamily: 'sans-serif',
          fontSize: 26,
          fontWeight: 900,
          padding: '8px 18px',
          transform: 'rotate(-12deg)',
          opacity: 0.85,
          letterSpacing: 2
        }}>
          DECLASSIFIED // СОВЕРШЕННО СЕКРЕТНО
        </div>
      </div>
    </AbsoluteFill>
  );
};
