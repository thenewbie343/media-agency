# Original User Request

## 2026-08-23T18:29:46Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Execute the Master Cinematic Documentary Director Overhaul v2.0 with VisualSequenceDirector
> Requested team: Full Director & Editorial Refactor Team

Implement the Master Cinematic Documentary Director Overhaul (Version 2.0) across the automated YouTube documentary generation pipeline, transforming it from a narrated slideshow generator into an authoritative, editorial documentary director engine with an explicit VisualSequenceDirector layer.

Working directory: c:\Users\Asus\Downloads\assets\media-agency
Integrity mode: development

## Requirements

### R1. Deep Investigative Research Architecture (`DocumentaryResearchPackage`)
Upgrade `agents/researcher.py` and `agents/schema.py` to produce a complete `DocumentaryResearchPackage`. The package must identify: `central_question`, `documentary_thesis`, `central_contradiction`, `audience_initial_belief`, `what_the_audience_thinks_is_true`, `what_is_actually_more_complicated`, `protagonist_or_human_anchor`, `antagonistic_force_or_system`, `stakes`, `historical_context`, `turning_points`, `major_reveals`, `final_payoff`, `evidence_items` (specific documents, telexes, logs, photos), `people`, `locations`, `physical_objects`, `numbers` (with visual experience treatments), `dates`, `archival_opportunities`, `reconstruction_opportunities`, `motion_graphic_opportunities`, `visual_motifs`, and `ending_image_opportunity`.

### R2. Macro Narrative Architecture & Hook Engine
Update `agents/head_writer.py`, `agents/scriptwriter.py`, and `agents/director.py` to formulate a `DocumentaryVision` before writing scenes. The narrative arc must follow: `HOOK` (first 20-30s strictly creates a Question, Contradiction, Shock, Mystery, or Visual Anomaly before revealing context) → `CENTRAL_QUESTION` → `CONTEXT` → `FIRST_DISCOVERY` → `COMPLICATION` → `ESCALATION` → `REVELATION` → `CONSEQUENCE` → `DEEPER_REVELATION` → `FINAL_CONTRADICTION` → `PAYOFF`. Every 30–90 seconds must form a mini-arc (`SETUP` → `BUILD` → `COMPLICATION` → `REVEAL` → `CONSEQUENCE`).

### R3. Visual Sequence Director (`VisualSequenceDirector` Layer)
Introduce `agents/visual_sequence_director.py` between `EditorialBeat[]` and `Shot[]`. It must formulate a `VisualSequencePlan` before selecting individual assets. The plan designs: `intention`, `visual_argument` (e.g., `industry_value_growth vs animator_wage_stagnation`), `withholding_strategy` (anticipation > immediate noun illustration), `memorable_image` (a visually distinctive key anchor shot representing the central idea of the act), `sequence_ending_statement` (final visual statement transitioning into the next beat), and sequence quality metrics (`information_change`, `emotional_change`, `visual_change`, `scale_change`).
Enforce the **Anti-Literal Rule & Mute Test**: The sequence must communicate a visual argument even if muted.
Enforce **No-Generic-B-Roll Fallback Cascade**: Priority: 1. Alternative visual interpretation → 2. Motion graphic diagram → 3. AI Reconstruction → 4. Archival document → 5. Generic B-roll (last resort only).

### R4. 20 Semantic Visual Jobs & 12 Shot Relationships
Expand `agents/schema.py`, `agents/visual_story_planner.py`, and `agents/shot_relationship.py` with:
- 20 Editorial Visual Jobs: `ESTABLISH_WORLD`, `INTRODUCE_CHARACTER`, `INTRODUCE_OBJECT`, `FOLLOW_OBJECT`, `SHOW_EVIDENCE`, `EXAMINE_EVIDENCE`, `REVEAL_DETAIL`, `VISUALIZE_ABSTRACT_CONCEPT`, `SHOW_SCALE`, `SHOW_COMPARISON`, `RECONSTRUCT_EVENT`, `BUILD_MYSTERY`, `WITHHOLD_INFORMATION`, `ESCALATE`, `INTERRUPT`, `CONTRAST`, `HUMANIZE`, `CONSEQUENCE`, `REVEAL`, `PAYOFF`.
- 12 Shot Relationships: `CONTINUATION`, `CONTRAST`, `CAUSE_TO_EFFECT`, `QUESTION_TO_ANSWER`, `DETAIL_TO_CONTEXT`, `CONTEXT_TO_DETAIL`, `BEFORE_TO_AFTER`, `EXPECTATION_TO_SUBVERSION`, `OBJECT_TO_PERSON`, `PERSON_TO_CONSEQUENCE`, `NUMBER_TO_SCALE`, `EVIDENCE_TO_REVEAL`.

### R5. Visual Contrast Engine, Memorable Images, Numbers, and Motifs
Update `agents/visual_story_planner.py` to:
- Enforce visual rhythm contrast (fast ↔ slow, moving ↔ still, wide ↔ detail, archival ↔ reconstruction, sound ↔ silence, dark ↔ light, complex ↔ simple).
- Treat numbers as dramatic visual events with selective editorial typography punctuation (e.g., `$81,000,000`, `11:47 AM`, `UNKNOWN USER`).
- Track and escalate recurring visual motifs across chapters.
- Anchor abstract systems to human consequence (hands, workspaces, reactions, physical artifacts).
- Eliminate filler shots and semantic redundancy.

### R6. 17 Validation Metrics & QC Overhaul
Expand `agents/cinematic_qc.py`, `agents/manifest_reviewer.py`, and `agents/qc_editor.py` to calculate and enforce:
1. `number_of_unique_visual_concepts`
2. `repeated_visual_concepts`
3. `repeated_queries`
4. `repeated_camera_movements`
5. `repeated_compositions`
6. `shots_with_no_editorial_reason`
7. `number_of_major_reveals`
8. `number_of_attention_peaks`
9. `number_of_silence_moments`
10. `number_of_typography_punctuation_events`
11. `number_of_graphic_explanations`
12. `number_of_human_anchor_moments`
13. `number_of_visual_motifs`
14. `number_of_visual_contrasts`
15. `number_of_contextual_overlays`
16. `sfx_per_minute`
17. `% shots that merely illustrate narration`
QC must reject generic B-roll and unmotivated literal noun illustrations, while welcoming static holds, longer shots, and silence as intentional cinematic grammar.

### R7. Preservation of Existing Core Systems
Strictly preserve requested-duration word budgeting, post-TTS visual decomposition, continuous narration per block, ≤ 5s individual visual shots, chapter-level LUT assignment, contextual overlays, restrained SFX, Kokoro Hindi voice consistency (+20% volume boost), Remotion VFX/LUT rendering, and Pexels 4K/HD retrieval.

## Acceptance Criteria

### Schema & Data Integrity
- [ ] `DocumentaryResearchPackage`, `DocumentaryVision`, and `VisualSequencePlan` schemas validate with Pydantic without errors.
- [ ] All 20 visual jobs and 12 shot relationships are registered in `agents/schema.py` and utilized in visual decomposition.

### Visual Sequence & Directorial Flow
- [ ] `VisualSequenceDirector` outputs a structured `VisualSequencePlan` for every editorial beat before shot asset selection.
- [ ] The Mute Test passes: visual sequences convey a clear visual argument (e.g. scale expansion, contradiction, human consequence) rather than literal noun-matching.
- [ ] Generic B-roll cascade adheres to the strict priority order (interpretation → motion graphic → reconstruction → archival → B-roll last).

### Quality Control & Testing
- [ ] `test_director_architecture.py` executes all test suites, calculating the 17-metric matrix with an overall score ≥ 8.0/10.0 (APPROVED).
- [ ] `python -m pytest` passes 100% of unit tests.
- [ ] Benchmark documentary generation runs end-to-end to final mastered MP4 without regression in Remotion rendering or audio sidechain ducking.
