import json
import logging
import copy
import random
import math
from typing import Dict, Any, List, Optional, Union
from pydantic_core import ValidationError
from .base_agent import BaseAgent
from .schema import (
    ScriptManifest,
    DocumentaryVision,
    DocumentaryResearchPackage,
    HookStrategy,
    NarrativePhasePlan,
    MiniArcPlan,
    NarrativeIntent,
    MiniArcPhase,
    VisualJob,
    ShotRelationship,
    ProjectMeta,
    VisualBible,
    StoryBeat,
    NarrationBlock,
    Shot,
    TimeContext,
    StrategicSilence,
    AudioMetadata,
    ContinuityMetadata,
)
from .style_profiles import get_style_profile, select_profile_for_topic
from .director_memory import DirectorMemory
from .shot_relationship import ShotRelationshipEngine
from .visual_intent import VisualIntentEngine

log = logging.getLogger(__name__)


class DirectorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.memory = DirectorMemory()
        self.relationship_engine = ShotRelationshipEngine()
        self.intent_engine = VisualIntentEngine()

    def _normalize_input(self, data: Any) -> Any:
        if hasattr(data, "model_dump"):
            return data.model_dump()
        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception:
                return data
        return data

    def formulate_vision(
        self,
        research_package: Union[Dict[str, Any], str, DocumentaryResearchPackage],
        duration_minutes: int = 1,
    ) -> Dict[str, Any]:
        """
        Formulates the comprehensive DocumentaryVision from the DocumentaryResearchPackage
        before outline generation and scene writing.
        """
        print(f"[*] DirectorAgent formulating DocumentaryVision ({duration_minutes}m)...")
        log.info(f"Formulating DocumentaryVision for {duration_minutes}m film.")

        pkg_data = self._normalize_input(research_package)
        if not isinstance(pkg_data, dict):
            pkg_data = {"topic": str(research_package)}

        topic = pkg_data.get("topic", "Investigative Documentary")
        style_profile_name = select_profile_for_topic(topic)

        schema_json = json.dumps(DocumentaryVision.model_json_schema(), indent=2)

        system_prompt = f"""You are the Master Cinematic Documentary Director (style of David Fincher, Alex Gibney, Ken Burns).
Your mission is to formulate an authoritative 'DocumentaryVision' defining the directorial philosophy, hook strategy, 11-phase macro narrative arc, 30-90s mini-arcs, recurring visual motifs, and ending image.

THE 11 MACRO NARRATIVE ARC PHASES (MANDATORY IN `macro_narrative_arc`):
1. `HOOK`: 20-30s shock, contradiction, or visual anomaly without prior context.
2. `CENTRAL_QUESTION`: Core investigative question.
3. `CONTEXT`: Historical/geopolitical setting.
4. `FIRST_DISCOVERY`: Initial hard evidence or crack.
5. `COMPLICATION`: Initial assumptions break down.
6. `ESCALATION`: Tension multiplies, stakes escalate.
7. `REVELATION`: Smoking gun document or covert memo.
8. `CONSEQUENCE`: Catastrophic aftermath or collapse.
9. `DEEPER_REVELATION`: Systemic rot behind individual actors.
10. `FINAL_CONTRADICTION`: Haunting unresolved irony.
11. `PAYOFF`: Philosophical conclusion and climactic lingering image.

JSON SCHEMA:
{schema_json}"""

        prompt = f"""Documentary Research Package:
{json.dumps(pkg_data, indent=2)}

Target Duration: {duration_minutes} minutes.
Selected Style Profile: {style_profile_name}

Generate the complete DocumentaryVision JSON."""

        raw_output = self.call_llm(prompt, system_prompt)

        if isinstance(raw_output, str):
            try:
                raw_output = json.loads(raw_output)
            except Exception as e:
                log.error(f"Failed to parse DocumentaryVision LLM JSON: {e}")
                raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        if not isinstance(raw_output, dict):
            raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        # In mock fallback for DirectorAgent, extract documentary_vision if full manifest returned
        if "documentary_vision" in raw_output and "story_beats" in raw_output:
            raw_output = raw_output["documentary_vision"]

        try:
            vision = DocumentaryVision.model_validate(raw_output)
            print("[*] DirectorAgent: DocumentaryVision successfully formulated and validated!")
            return vision.model_dump()
        except ValidationError as val_err:
            log.warning(f"DocumentaryVision validation error: {val_err}. Repairing...")
            repaired = self.repair_schema_error(raw_output, val_err)
            if "documentary_vision" in repaired and "story_beats" in repaired:
                repaired = repaired["documentary_vision"]
            try:
                vision = DocumentaryVision.model_validate(repaired)
                return vision.model_dump()
            except Exception as e:
                log.error(f"Vision validation repair failed: {e}. Synthesizing valid vision.")
                fallback = self._get_mock_fallback(prompt, system_prompt, True)
                if "documentary_vision" in fallback:
                    fallback = fallback["documentary_vision"]
                vision = DocumentaryVision.model_validate(fallback)
                return vision.model_dump()

    def normalize_manifest(self, data: Any) -> Any:
        """
        Normalizes manifest strings and preserves all 11 Macro Narrative Arc intents
        and 5 mini-arc phases without down-mapping them.
        """
        if isinstance(data, dict):
            for k, v in list(data.items()):
                if k == "narrative_intent" and isinstance(v, str):
                    v_up = v.upper().strip()
                    # Safe alias recovery map (do NOT down-map canonical phases)
                    alias_map = {
                        "THE_PROBLEM": "COMPLICATION",
                        "PROBLEM": "COMPLICATION",
                        "SETUP": "CONTEXT",
                        "DISCOVERY": "FIRST_DISCOVERY",
                        "AFTERMATH": "CONSEQUENCE",
                        "LOCATION": "LOCATION_ESTABLISH",
                        "BACKGROUND": "CONTEXT",
                        "INTRODUCTION": "HOOK",
                        "CLIMAX": "REVELATION",
                    }
                    if v_up in alias_map:
                        data[k] = alias_map[v_up]
                    elif v_up in NarrativeIntent.__members__:
                        data[k] = v_up
                elif k == "mini_arc_phase" and isinstance(v, str):
                    v_up = v.upper().strip()
                    if v_up in MiniArcPhase.__members__:
                        data[k] = v_up
                elif isinstance(v, (dict, list)):
                    self.normalize_manifest(v)
        elif isinstance(data, list):
            for item in data:
                self.normalize_manifest(item)
        return data

    def repair_schema_error(self, output_dict, error):
        """Targeted repair for Pydantic ValidationError."""
        log.warning("Schema Validation Failed. Attempting targeted schema repair...")
        
        prompt = f"""You generated a JSON that failed schema validation.
Error details:
{str(error)}

Here is the broken JSON:
{json.dumps(output_dict, indent=2)}

Please fix ONLY the invalid fields and return the FULL corrected JSON matching the schema."""

        system = "You are a JSON schema repair assistant. You only output valid JSON. Fix the exact fields mentioned in the error."
        try:
            fixed_dict = self.call_llm(prompt, system)
            fixed_dict = self.normalize_manifest(fixed_dict)
            return fixed_dict
        except Exception as e:
            log.error(f"Targeted schema repair call failed: {e}")
            return output_dict
            
    def repair_manifest_section(self, broken_snippet, qc_failures):
        """Targeted surgical repair for QC failures."""
        log.info(f"Targeted Surgical Repair for {len(qc_failures)} failures...")
        
        system = """You are an elite Video Director executing a surgical repair on a broken ScriptManifest section.
You will be given a JSON snippet (a beat, block, or shot) and a list of QC failures.
You MUST fix the JSON snippet to address the QC failures while STRICTLY PRESERVING all global IDs (beat_id, block_id, shot_id).
Do NOT regenerate unaffected shots. 
Ensure:
- Diverse camera movements (NOT zoom_in repeatedly; use slow_push_in, pan_left, pan_right, static, dolly_in).
- Highly semantic cut_reason (e.g. 'bridge_luxury_to_collapse', 'reveal_anomaly_detail').
- Varied camera angles (use eye_level, low_angle, overhead_shot; Dutch angle at most once).
Return the corrected JSON snippet."""

        prompt = f"""Broken JSON Snippet:
{json.dumps(broken_snippet, indent=2)}

QC Failures:
{json.dumps(qc_failures, indent=2)}

Fix the snippet to address the failures and return the corrected JSON."""
        
        try:
            fixed_dict = self.call_llm(prompt, system)
            return fixed_dict
        except Exception as e:
            log.error(f"Surgical repair call failed: {e}")
            return broken_snippet

    def enforce_strict_rules(self, raw_manifest):
        """Programmatically enforce cinematic variety and eliminate camera fatigue."""
        from .visual_story_planner import VisualStoryPlanner
        planner = VisualStoryPlanner()
        
        manifest = copy.deepcopy(raw_manifest)
        
        sizes = ["establishing_shot", "wide", "medium", "close", "extreme_close"]
        angles = ["eye_level", "low_angle", "high_angle", "overhead_shot", "dutch_angle"]
        lenses = ["wide_angle_lens", "standard_lens", "telephoto_lens", "macro_lens"]
        comps = ["rule_of_thirds", "center_framed", "leading_lines", "symmetry"]
        motions = ["slow_push_in", "pan_left", "pan_right", "dolly_in", "static", "zoom_out", "crane_up"]
        
        semantic_cut_reasons = {
            "HOOK": ["establish_shocking_anomaly", "hook_viewer_with_scale", "contrast_normalcy_with_disaster", "isolate_initial_paradox"],
            "CENTRAL_QUESTION": ["frame_core_investigative_mystery", "pose_central_contradiction", "question_official_narrative", "interrogate_hidden_motives"],
            "CONTEXT": ["establish_historical_baseline", "reveal_preconditions_and_setting", "situate_geopolitical_backdrop", "trace_economic_landscape"],
            "FIRST_DISCOVERY": ["reveal_first_hard_evidence", "expose_initial_anomaly_log", "uncover_hidden_document_crack", "highlight_critical_discrepancy"],
            "COMPLICATION": ["dramatize_systemic_friction", "expose_conflicting_account", "shatter_simple_explanation", "reveal_technical_obstacle"],
            "ESCALATION": ["accelerate_investigative_tension", "dramatize_mounting_pressure", "bridge_friction_to_crisis", "amplify_institutional_panic"],
            "REVELATION": ["expose_smoking_gun_document", "reveal_hidden_mastermind_record", "unmask_covert_mechanism", "unveil_critical_memo"],
            "CONSEQUENCE": ["frame_immediate_catastrophe", "document_institutional_reaction", "quantify_irreversible_damage", "capture_market_evaporation"],
            "DEEPER_REVELATION": ["uncover_systemic_root_cause", "expose_structural_culpability", "reveal_wider_network_scope", "unmask_underlying_culture"],
            "FINAL_CONTRADICTION": ["illuminate_haunting_irony", "contrast_ultimate_gain_and_loss", "isolate_unresolved_paradox", "frame_lasting_dilemma"],
            "PAYOFF": ["close_investigative_inquiry", "deliver_lasting_philosophical_verdict", "linger_on_climactic_final_image", "punctuate_enduring_lesson"],
            "EVIDENCE": ["reveal_official_case_record", "highlight_critical_discrepancy", "expose_hidden_transaction_log"],
            "CONFLICT": ["dramatize_system_breakdown", "accelerate_investigative_tension", "bridge_luxury_to_collapse"],
            "MYSTERY": ["deepen_unanswered_question", "isolate_unidentified_operator", "reveal_encrypted_communication"],
            "EXPLANATION": ["visualize_underlying_mechanism", "trace_interconnected_network", "map_chronological_sequence"],
            "RESOLUTION": ["contemplate_irreversible_aftermath", "frame_long_term_consequences", "close_investigative_inquiry"],
            "LOCATION_ESTABLISH": ["establish_geographic_epicenter", "anchor_investigative_setting", "reveal_institutional_stronghold"]
        }
        
        s_idx, a_idx, l_idx, c_idx, m_idx = 0, 0, 0, 0, 0
        last_motion = None
        last_angle = None
        dutch_count = 0
        seen_queries = set()
        
        for beat in manifest.get("story_beats", []):
            time_mode = beat.get("time_context", {}).get("mode", "historical")
            intent = beat.get("narrative_intent", "EXPLANATION")
            attention = float(beat.get("attention_intensity", 0.5))
            
            # Establish visual chapter language
            if not beat.get("chapter_color_language"):
                beat["chapter_color_language"] = planner.determine_chapter_color(intent, time_mode)
                
            for block in beat.get("narration_blocks", []):
                block_dur = block.get("total_block_duration") or block.get("actual_voice_duration") or 4.0
                new_shots = []
                for shot in block.get("shots", []):
                    shot = planner.enforce_editorial_restraint(shot, attention)
                    
                    # 1. ENFORCE CINEMATOGRAPHY VARIANCE
                    if not shot.get("shot_size") or shot.get("shot_size", "").upper() == "N/A" or str(shot.get("shot_size")).lower() == "null":
                        shot["shot_size"] = sizes[s_idx % len(sizes)]; s_idx += 1
                    
                    # Prevent Dutch angle overuse (max 1 per act/beat)
                    current_angle = shot.get("camera_angle")
                    if not current_angle or current_angle.upper() == "N/A" or str(current_angle).lower() == "null" or (current_angle.lower() == "dutch_angle" and dutch_count >= 1):
                        safe_angles = [a for a in angles if a != "dutch_angle" and a != last_angle]
                        shot["camera_angle"] = safe_angles[a_idx % len(safe_angles)]; a_idx += 1
                    if shot.get("camera_angle", "").lower() == "dutch_angle":
                        dutch_count += 1
                    last_angle = shot.get("camera_angle")

                    if not shot.get("lens") or shot.get("lens", "").upper() == "N/A" or str(shot.get("lens")).lower() == "null":
                        shot["lens"] = lenses[l_idx % len(lenses)]; l_idx += 1
                    if not shot.get("composition") or shot.get("composition", "").upper() == "N/A" or str(shot.get("composition")).lower() == "null":
                        shot["composition"] = comps[c_idx % len(comps)]; c_idx += 1
                        
                    # 2. ELIMINATE CAMERA FATIGUE (STRICTLY BAN ZOOM_IN REPETITION)
                    motion = shot.get("camera_motion", "static")
                    if motion == "zoom_in" or motion == last_motion or not motion:
                        available_motions = [m for m in motions if m != last_motion and m != "zoom_in"]
                        shot["camera_motion"] = available_motions[m_idx % len(available_motions)]
                        m_idx += 1
                    last_motion = shot["camera_motion"]
                    
                    # 3. SANITIZE GENERIC CUT REASONS
                    cut_reason = (shot.get("cut_reason") or "").lower()
                    generic_triggers = ["introduce", "transition", "show_fact", "change_scene", "next_shot", "conflict", "information"]
                    if not cut_reason or any(g in cut_reason for g in ["introduce_conflict", "introduce_information", "transition", "next_scene"]) or len(cut_reason) < 10:
                        reason_pool = semantic_cut_reasons.get(intent, semantic_cut_reasons["EXPLANATION"])
                        shot["cut_reason"] = reason_pool[s_idx % len(reason_pool)]
                        
                    # 4. PREVENT VISUAL QUERY / PROMPT DUPLICATION
                    query = (shot.get("visual_query") or "").strip()
                    if query in seen_queries:
                        unique_suffix = f" {shot.get('shot_size', 'detail')} {shot.get('camera_angle', 'angle')}"
                        shot["visual_query"] = f"{query}{unique_suffix}"
                    seen_queries.add(shot.get("visual_query", ""))

                    # 5. ENFORCE 4.5S HARD SPLIT
                    mode = shot.get("duration_mode") or "ratio"
                    if mode == "fixed" and shot.get("duration_seconds"):
                        dur = float(shot.get("duration_seconds") or 4.0)
                        ratio = 1.0
                    else:
                        ratio = float(shot.get("duration_ratio") or 1.0)
                        dur = block_dur * ratio
                    
                    if dur > 4.5:
                        splits = math.ceil(dur / 4.5)
                        new_ratio = ratio / splits
                        for i in range(splits):
                            sub = copy.deepcopy(shot)
                            sub["shot_id"] = f"{shot.get('shot_id', 's')}_part{i}"
                            
                            if mode == "fixed" and sub.get("duration_seconds"):
                                sub["duration_seconds"] = dur / splits
                            else:
                                sub["duration_ratio"] = new_ratio
                            
                            # vary camera motion and scale on split parts
                            available_motions = [m for m in motions if m != last_motion and m != "zoom_in"]
                            sub["camera_motion"] = available_motions[m_idx % len(available_motions)]
                            m_idx += 1
                            last_motion = sub["camera_motion"]
                            
                            if i > 0:
                                sub["shot_size"] = "close" if shot.get("shot_size") == "medium" else "medium"
                                sub["cut_reason"] = f"magnify_{shot.get('cut_reason', 'detail')}"
                                sub["visual_query"] = f"{sub.get('visual_query', '')} forensic angle part{i+1}"
                                    
                            new_shots.append(sub)
                    else:
                        new_shots.append(shot)
                
                block["shots"] = new_shots
                
        return manifest

    def add_metadata(
        self,
        raw_script: List[Dict[str, Any]],
        research_package: Optional[Union[Dict[str, Any], str, DocumentaryResearchPackage]] = None,
        vision: Optional[Union[Dict[str, Any], str, DocumentaryVision]] = None,
    ) -> Dict[str, Any]:
        """Acts as the Video Director, adding visual and audio metadata to the hierarchical script."""
        print("[*] DirectorAgent adding cinematic metadata (v2.0 Schema)...")
        log.info(f"Adding metadata to script ({len(raw_script)} scenes)...")

        research_pkg_data = self._normalize_input(research_package) if research_package else None
        vision_data = self._normalize_input(vision) if vision else None

        schema_json = json.dumps(ScriptManifest.model_json_schema(), indent=2)

        system_prompt = f"""You are an elite Video Director for YouTube documentaries (Masterclass / Vox / Frontline style).
Your job is to take a basic script (array of scenes) and upgrade it into a professional cinematic shot manifest following a strict hierarchical architecture:
Story Beat -> Narration Block -> Shots[].

CRITICAL DIRECTIVES:

0. SCENE PRESERVATION & INTENT FIDELITY: 
   The raw script contains an array of scenes with `narrative_intent` and `mini_arc_phase`.
   You MUST create exactly one NarrationBlock for EVERY SINGLE SCENE in the raw script. 
   Do NOT merge scenes together. Preserve the scene's `narrative_intent` (one of the 11 Macro Narrative Arc phases) and `mini_arc_phase`!

1. VISUAL DIVERSITY & ASSET PROVENANCE:
   Do NOT default to generic stock visuals or AI video for everything. Select authentic `asset_provenance` (AUTHENTIC_PHOTO, ARCHIVAL_FOOTAGE, DOCUMENT, MOTION_GRAPHIC, AI_RECONSTRUCTION, STOCK).
   If showing people, evidence, or records, use authentic documents, photos, or diagrams.

2. BAN CLICHÉ DOCUMENTARY VISUALS:
   Do NOT use generic metaphors (e.g. champagne glasses, generic handcuffs, scales of justice, generic businessman shaking hands, money falling from sky).
   Every shot must show specific real evidence, specific environments, technical diagrams, or authentic archival records.

3. STRICT CAMERA DIVERSITY & NO CAMERA FATIGUE:
   - DO NOT USE `zoom_in` repeatedly. Distribute camera movements: `slow_push_in`, `pan_left`, `pan_right`, `dolly_in`, `static`, `zoom_out`.
   - Rotate camera angles: `eye_level`, `low_angle`, `high_angle`, `overhead_shot`. Use `dutch_angle` at most ONCE per video.
   - Varied shot sizes: alternate `establishing_shot`, `wide`, `medium`, `close`, `extreme_close`.

4. 20 VISUAL JOBS & 12 SHOT RELATIONSHIPS:
   - Assign one of the 20 canonical `visual_job` enums to each shot (ESTABLISH_WORLD, INTRODUCE_CHARACTER, INTRODUCE_OBJECT, SHOW_EVIDENCE, EXAMINE_EVIDENCE, VISUALIZE_ABSTRACT_CONCEPT, SHOW_SCALE, SHOW_COMPARISON, RECONSTRUCT_EVENT, BUILD_MYSTERY, WITHHOLD_INFORMATION, ESCALATE, INTERRUPT, CONTRAST, HUMANIZE, CONSEQUENCE, REVEAL, PAYOFF).
   - Assign `shot_relationship` to transition shots (CONTINUATION, CONTRAST, CAUSE_TO_EFFECT, QUESTION_TO_ANSWER, DETAIL_TO_CONTEXT, CONTEXT_TO_DETAIL, BEFORE_TO_AFTER, EXPECTATION_TO_SUBVERSION, OBJECT_TO_PERSON, PERSON_TO_CONSEQUENCE, NUMBER_TO_SCALE, EVIDENCE_TO_REVEAL).

5. SEMANTIC CUT REASONS (MANDATORY):
   `cut_reason` MUST describe a causal editorial shift.
   GOOD: 'bridge_luxury_to_collapse', 'reveal_critical_typo_discrepancy', 'contrast_public_image_with_covert_log', 'isolate_central_instigator'.
   BANNED: 'introduce_conflict', 'introduce_information', 'transition', 'next_shot', 'change_scene'.

6. HARD DURATION LIMITS:
   NO SHOT MAY EXCEED 4.5 SECONDS.

You must return a valid JSON object matching this exact JSON schema:
{schema_json}
"""

        prompt = f"""Raw Script:
{json.dumps(raw_script, ensure_ascii=False, indent=2)}

Documentary Research Package:
{json.dumps(research_pkg_data, indent=2) if research_pkg_data else "None"}

Documentary Vision:
{json.dumps(vision_data, indent=2) if vision_data else "None"}

Generate the complete ScriptManifest JSON."""

        output_dict = self.call_llm(prompt, system_prompt)
        output_dict = self.normalize_manifest(output_dict)

        # If LLM returned mock fallback or missing scenes, dynamically synthesize beats from raw_script
        raw_scenes_count = len(raw_script) if isinstance(raw_script, list) else 0
        manifest_scenes_count = sum(len(b.get("narration_blocks", [])) for b in output_dict.get("story_beats", [])) if isinstance(output_dict, dict) else 0
        
        if raw_scenes_count > 0 and (manifest_scenes_count != raw_scenes_count or not self.model):
            from .visual_story_planner import VisualStoryPlanner
            from .visual_sequence_director import VisualSequenceDirector
            planner = VisualStoryPlanner()
            vsd = VisualSequenceDirector()
            
            synthesized_beats = []
            for s_idx, scene in enumerate(raw_script):
                beat_id = f"b{s_idx+1:03d}"
                block_id = f"n{s_idx+1:03d}"
                intent = scene.get("narrative_intent", "EXPLANATION")
                mini_phase = scene.get("mini_arc_phase", "SETUP")
                vo = scene.get("voiceover", "")
                cap = scene.get("caption", "")
                
                block = {
                    "block_id": block_id,
                    "voiceover": vo,
                    "caption": cap,
                    "duration_hint": max(3.5, len(vo.split()) / 2.5),
                    "strategic_silence": {
                        "duration_seconds": 0.5 if intent in ["REVELATION", "FINAL_CONTRADICTION", "HOOK"] else 0.0,
                        "position": "end",
                        "ambient_level": -35,
                        "visual_behavior": "hold_frame"
                    },
                    "audio_metadata": {
                        "music_energy": 0.8 if intent in ["HOOK", "ESCALATION", "REVELATION"] else 0.5,
                        "music_duck_amount": -15
                    },
                    "mini_arc_phase": mini_phase,
                    "shots": []
                }
                
                # Decompose into dynamic visual sequence
                decomposed_shots = planner.decompose_narration_block(
                    block,
                    actual_duration=block["duration_hint"],
                    beat_intent=intent,
                    attention_intensity=0.85 if intent in ["HOOK", "REVELATION"] else 0.5
                )
                block["shots"] = decomposed_shots
                
                # Plan visual sequence
                seq_plan = vsd.plan_visual_sequence(
                    beat={"narrative_intent": intent, "description": cap, "narration_blocks": [block]},
                    research_package=research_pkg_data,
                    vision=vision_data
                )
                
                beat_obj = {
                    "beat_id": beat_id,
                    "time_context": {
                        "year": "2000s",
                        "mode": "historical",
                        "location": "Global",
                        "transition_reason": f"Investigative progression into {intent}"
                    },
                    "narrative_intent": intent,
                    "mini_arc_phase": mini_phase,
                    "visual_sequence_plan": seq_plan.model_dump() if hasattr(seq_plan, "model_dump") else seq_plan,
                    "description": cap[:80],
                    "attention_intensity": 0.85 if intent in ["HOOK", "REVELATION"] else 0.5,
                    "chapter_color_language": "cool noir tones" if intent in ["COMPLICATION", "CONFLICT"] else "warm archival",
                    "narration_blocks": [block]
                }
                synthesized_beats.append(beat_obj)
            
            output_dict["story_beats"] = synthesized_beats

        if "project_meta" not in output_dict or not output_dict.get("project_meta"):
            output_dict["project_meta"] = {
                "topic": "Cinematic Documentary",
                "genre": "documentary",
                "style_profile": "DOCUMENTARY_INVESTIGATIVE",
                "language": "hindi",
                "visual_bible": {
                    "era": "2000s",
                    "locations": ["Global"],
                    "lighting": "low-key, cold, cinematic",
                    "color_language": "cool noir tones",
                    "film_texture": "subtle grain, 35mm"
                }
            }
        elif "visual_bible" not in output_dict["project_meta"] or not output_dict["project_meta"].get("visual_bible"):
            output_dict["project_meta"]["visual_bible"] = {
                "era": "2000s",
                "locations": ["Global"],
                "lighting": "low-key, cold, cinematic",
                "color_language": "cool noir tones",
                "film_texture": "subtle grain, 35mm"
            }

        # If research_package or vision were provided, attach them to manifest if missing
        if isinstance(output_dict, dict):
            if research_pkg_data and ("research_package" not in output_dict or not output_dict.get("research_package")):
                output_dict["research_package"] = research_pkg_data
            if vision_data and ("documentary_vision" not in output_dict or not output_dict.get("documentary_vision")):
                output_dict["documentary_vision"] = vision_data

        print("[*] Validating output against Pydantic schema...")
        try:
            manifest = ScriptManifest.model_validate(output_dict)
            print("[*] Schema validation successful!")
            return self.enforce_strict_rules(manifest.model_dump())
        except ValidationError as e:
            repaired_dict = self.repair_schema_error(output_dict, e)
            if research_pkg_data and ("research_package" not in repaired_dict or not repaired_dict.get("research_package")):
                repaired_dict["research_package"] = research_pkg_data
            if vision_data and ("documentary_vision" not in repaired_dict or not repaired_dict.get("documentary_vision")):
                repaired_dict["documentary_vision"] = vision_data
            try:
                manifest = ScriptManifest.model_validate(repaired_dict)
                print("[*] Schema repair validation successful!")
                return self.enforce_strict_rules(manifest.model_dump())
            except ValidationError as e2:
                log.error("Schema repair failed twice. Hard failing.")
                raise e2

