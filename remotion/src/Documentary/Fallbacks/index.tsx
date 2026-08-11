export { ArchivalCanvas as ArchivalDocument } from '../ArchivalCanvas';
export { ClassifiedFile } from './ClassifiedFile';
export { Newspaper } from './Newspaper';
export { MapFallback } from './MapFallback';
export { EvidenceBoard } from './EvidenceBoard';
export { PortraitCard } from './PortraitCard';
export { TechnicalDiagram } from './TechnicalDiagram';
export { AnimatedDiagram } from './AnimatedDiagram';

import React from 'react';
import { ArchivalCanvas as ArchivalDocument } from '../ArchivalCanvas';
import { ClassifiedFile } from './ClassifiedFile';
import { Newspaper } from './Newspaper';
import { MapFallback } from './MapFallback';
import { EvidenceBoard } from './EvidenceBoard';
import { PortraitCard } from './PortraitCard';
import { TechnicalDiagram } from './TechnicalDiagram';
import { AnimatedDiagram } from './AnimatedDiagram';
import { MapMotionGraphic } from '../MapMotionGraphic';
import { TimelineMotionGraphic } from '../TimelineMotionGraphic';

export const SemanticFallback: React.FC<{
  shot: any;
  seed?: number;
}> = ({ shot }) => {
  const job = shot?.visual_job;
  const fallbackType = shot?.fallback_type;
  const caption = shot?.caption;
  const title = shot?.text_overlay || shot?.visual_query || 'HISTORICAL RECONSTRUCTION';

  // 1. Direct Fallback Type Matching
  if (fallbackType === 'MapFallback') return <MapFallback caption={caption} title={title} />;
  if (fallbackType === 'ClassifiedFile') return <ClassifiedFile caption={caption} title={title} />;
  if (fallbackType === 'Newspaper') return <Newspaper caption={caption} title={title} />;
  if (fallbackType === 'EvidenceBoard') return <EvidenceBoard caption={caption} title={title} />;
  if (fallbackType === 'PortraitCard') return <PortraitCard caption={caption} title={title} />;
  if (fallbackType === 'TechnicalDiagram') return <TechnicalDiagram caption={caption} title={title} />;
  if (fallbackType === 'AnimatedDiagram') return <AnimatedDiagram caption={caption} title={title} />;
  if (fallbackType === 'Timeline') return <TimelineMotionGraphic shot={shot} />;

  // 2. Semantic Mapping based on visual_job
  if (job === 'SHOW_LOCATION') return <MapMotionGraphic shot={shot} />;
  if (job === 'SHOW_EVIDENCE') return <ClassifiedFile caption={caption} title={title} />;
  if (job === 'SHOW_PERSON') return <PortraitCard caption={caption} title={title} />;
  if (job === 'SHOW_OBJECT') return <TechnicalDiagram caption={caption} title={title} />;
  if (job === 'EXPLAIN_MECHANISM' || job === 'EXPLAIN_PROCESS') return <AnimatedDiagram caption={caption} title={title} />;
  if (job === 'SHOW_TIME') return <TimelineMotionGraphic shot={shot} />;
  if (job === 'CREATE_MYSTERY') return <ClassifiedFile caption={caption} title={title} />;

  // 3. General Fallback
  return <ArchivalDocument caption={caption} title={title} />;
};

export const DynamicFallback = SemanticFallback;
