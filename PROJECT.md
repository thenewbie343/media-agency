# Project: Master Cinematic Documentary Director Overhaul v2.0 with VisualSequenceDirector

## Architecture
Transform the automated YouTube documentary generation pipeline into an authoritative, editorial documentary director engine with an explicit VisualSequenceDirector layer.

```
[Deep Research Package] (R1)
         │
         ▼
[DocumentaryVision & Macro Narrative Arc] (R2)
         │
         ▼
[Scriptwriter & Editorial Beats] (R2)
         │
         ▼
[VisualSequenceDirector] (R3) ──> Formulates VisualSequencePlan (Anti-Literal, Mute Test, Fallback Cascade)
         │
         ▼
[VisualStoryPlanner] (R4, R5) ──> 20 Visual Jobs, 12 Shot Relationships, 7D Contrast, Motifs, Numbers
         │
         ▼
[Cinematic QC & Reviewers] (R6) ──> 17 Validation Metrics, Score >= 8.0/10.0
         │
         ▼
[Remotion VFX & Audio Compositor] (R7) ──> Hindi Voice (+20%), Contextual VFX, LUTs, Final Master
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | `DocumentaryResearchPackage` Schema | Pydantic v2 model with all 24 investigative fields and sub-models | M1 (DONE) | R1 |
| 2 | `DocumentaryVision` & Narrative Arc Schema | 11-phase macro arc & 30-90s mini-arc schemas | M1 (DONE) | R2 |
| 3 | `VisualSequencePlan` Schema | Sequence intention, visual argument, withholding, memorable image, metrics | M1 (DONE) | R3 |
| 4 | 20 Editorial Visual Jobs Schema | Enum & validation for 20 visual jobs | M1 (DONE) | R4 |
| 5 | 12 Shot Relationships Schema | Enum & validation for 12 shot relationships | M1 (DONE) | R4 |
| 6 | Deep Investigative Research Engine | Upgraded ResearcherAgent with multi-pass search & package output | M2 (DONE) | R1 |
| 7 | Macro Narrative Vision & Hook Engine | HeadWriter & Scriptwriter 11-phase arc with 20-30s hook withholding | M2 (DONE) | R2 |
| 8 | 30-90s Mini-Arc Engine | Scriptwriter & Director mini-arc progression | M2 (DONE) | R2 |
| 9 | Director Manifest Intent Preservation | DirectorAgent normalizes without down-mapping macro intents | M2 (DONE) | R2 |
| 10 | `VisualSequenceDirector` Layer | Formulates VisualSequencePlan per beat before shot selection | M3 (DONE) | R3 |
| 11 | Anti-Literal Rule & Mute Test Engine | Visual dialectic validation ensuring visual argument communicates when muted | M3 (DONE) | R3 |
| 12 | 5-Stage Fallback Cascade | Interpretation -> Motion Graphic -> AI Reconstruction -> Archival -> B-Roll | M3 (DONE) | R3 |
| 13 | 12 Shot Relationships Engine | `agents/shot_relationship.py` relational grammar enforcement | M3 (DONE) | R4 |
| 14 | 20 Visual Jobs Decomposition | `agents/visual_story_planner.py` assigning 20 semantic jobs | M3 (DONE) | R4 |
| 15 | 7-Dimensional Visual Contrast Engine | Pacing, Motion/Static, Scale, Medium, Sound/Silence, Light, Density | M3 (DONE) | R5 |
| 16 | Dramatic Number Typography Punctuation | Numbers formatted as editorial kinetic typography + NUMBER_TO_SCALE | M3 (DONE) | R5 |
| 17 | Motif Escalation & Human Anchors | Cross-chapter motif tracking in DirectorMemory + HUMANIZE shots | M3 (DONE) | R5 |
| 18 | 17 Validation Metrics Calculation | `agents/cinematic_qc.py` calculating all 17 validation metrics | M4 | R6 |
| 19 | Director Score & Reject Thresholds | Overall score >= 8.0/10.0, rejection of generic B-roll and literal illustrations | M4 | R6 |
| 20 | QC Manifest & Editor Upgrades | `manifest_reviewer.py` & `qc_editor.py` metric verification | M4 | R6 |
| 21 | Core Systems Preservation | Word budgeting (130wpm), post-TTS decomposition, <=5s shots, LUTs, VFX | M5 | R7 |
| 22 | Audio & TTS Preservation | Kokoro Hindi (+20% volume), SFX cooldowns, Remotion audio ducking | M5 | R7 |
| 23 | Architecture Test Matrix Runner | `test_director_architecture.py` computing 17 metrics and >= 8.0 score | M5 | Acceptance |
| 24 | Comprehensive Pytest Suite | 4-tier deterministic offline test suite (Tiers 1-4) with 100% pass | M5 | Acceptance |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Schema & Core Data Models | `agents/schema.py`, `agents/base_agent.py` | none | DONE |
| 2 | M2: Deep Research & Macro Narrative Engine | `agents/researcher.py`, `agents/head_writer.py`, `agents/scriptwriter.py`, `agents/director.py` | M1 | DONE |
| 3 | M3: Visual Sequence Director Layer & Planner | `agents/visual_sequence_director.py`, `agents/shot_relationship.py`, `agents/visual_story_planner.py`, `agents/director_memory.py`, `agents/visual_intent.py` | M1, M2 | DONE |
| 4 | M4: 17 Cinematic QC Metrics & Reviewers | `agents/cinematic_qc.py`, `agents/manifest_reviewer.py`, `agents/qc_editor.py` | M1, M3 | IN_PROGRESS |
| 5 | M5: Core Preservation & Architecture Test Suite | `test_director_architecture.py`, `pipeline.py`, `tests/` | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### M1 ↔ M2 (Research & Narrative to Schema)
- `ResearcherAgent.research_topic(topic)` -> returns `DocumentaryResearchPackage`
- `HeadWriterAgent.write_outline(research_package, vision)` -> returns structured outline with 11 macro phases
- `DirectorAgent.formulate_vision(research_package)` -> returns `DocumentaryVision`

### M2 ↔ M3 (Narrative Beats to Visual Sequence Director)
- `VisualSequenceDirector.plan_visual_sequence(story_beat, research_package, vision)` -> returns `VisualSequencePlan`
- `StoryBeat.visual_sequence_plan: Optional[VisualSequencePlan]`
- `VisualStoryPlanner.decompose_narration_block(block, duration, sequence_plan, ...)` -> returns `List[Shot]` with 20 visual jobs and 12 shot relationships

### M3 ↔ M4 (Visual Planning to Cinematic QC)
- `CinematicQCEngine.evaluate_manifest_director_score(manifest)` -> returns `{"overall_score": float, "verdict": str, "metrics": Dict[str, Any]}` covering all 17 validation metrics.

### M4 ↔ M5 (QC to Test Architecture)
- `test_director_architecture.py` imports `CinematicQCEngine`, `VisualSequenceDirector`, `VisualStoryPlanner`, `ResearcherAgent`, `DirectorAgent` and asserts all 17 metrics are generated and overall director score >= 8.0/10.0.

## Code Layout
- `agents/schema.py`: Exclusive to M1 Worker (DONE)
- `agents/base_agent.py`: Exclusive to M1 Worker (DONE)
- `agents/researcher.py`: Exclusive to M2 Worker (DONE)
- `agents/head_writer.py`: Exclusive to M2 Worker (DONE)
- `agents/scriptwriter.py`: Exclusive to M2 Worker (DONE)
- `agents/director.py`: Exclusive to M2 Worker (DONE)
- `agents/visual_sequence_director.py`: Exclusive to M3 Worker (DONE)
- `agents/shot_relationship.py`: Exclusive to M3 Worker (DONE)
- `agents/visual_story_planner.py`: Exclusive to M3 Worker (DONE)
- `agents/director_memory.py`: Exclusive to M3 Worker (DONE)
- `agents/visual_intent.py`: Exclusive to M3 Worker (DONE)
- `agents/cinematic_qc.py`: Exclusive to M4 Worker
- `agents/manifest_reviewer.py`: Exclusive to M4 Worker
- `agents/qc_editor.py`: Exclusive to M4 Worker
- `test_director_architecture.py`: Exclusive to M5 Worker
- `tests/`: Exclusive to M5 Worker
- `pipeline.py`: Exclusive to M5 Worker
