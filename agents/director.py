import json
import logging
import copy
import random
import math
from pydantic_core import ValidationError
from .base_agent import BaseAgent
from .schema import ScriptManifest
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
        
    def normalize_manifest(self, data):
        """Map common LLM hallucinated Enums to safe schema Enums."""
        if isinstance(data, dict):
            for k, v in data.items():
                if k == "narrative_intent" and isinstance(v, str):
                    v_up = v.upper().strip()
                    mapping = {
                        "THE_PROBLEM": "CONFLICT",
                        "ESCALATION": "CONFLICT",
                        "SETUP": "EXPLANATION",
                        "DISCOVERY": "EVIDENCE",
                        "AFTERMATH": "RESOLUTION",
                        "LOCATION": "LOCATION_ESTABLISH",
                        "BACKGROUND": "EXPLANATION",
                        "INTRODUCTION": "HOOK"
                    }
                    if v_up in mapping:
                        data[k] = mapping[v_up]
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
            "HOOK": ["establish_shocking_anomaly", "hook_viewer_with_scale", "contrast_normalcy_with_disaster"],
            "EVIDENCE": ["reveal_official_case_record", "highlight_critical_discrepancy", "expose_hidden_transaction_log"],
            "CONFLICT": ["dramatize_system_breakdown", "accelerate_investigative_tension", "bridge_luxury_to_collapse"],
            "MYSTERY": ["deepen_unanswered_question", "isolate_unidentified_operator", "reveal_encrypted_communication"],
            "EXPLANATION": ["visualize_underlying_mechanism", "trace_interconnected_network", "map_chronological_sequence"],
            "RESOLUTION": ["contemplate_irreversible_aftermath", "frame_long_term_consequences", "close_investigative_inquiry"]
        }
        
        s_idx, a_idx, l_idx, c_idx, m_idx = 0, 0, 0, 0, 0
        last_motion = None
        last_angle = None
        dutch_count = 0
        
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
                        
                    # 4. ENFORCE 4.5S HARD SPLIT
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
                                    
                            new_shots.append(sub)
                    else:
                        new_shots.append(shot)
                
                block["shots"] = new_shots
                
        return manifest

    def add_metadata(self, raw_script):
        """Acts as the Video Director, adding visual and audio metadata to the hierarchical script."""
        print("[*] DirectorAgent adding cinematic metadata (v2.0 Schema)...")
        
        schema_json = json.dumps(ScriptManifest.model_json_schema(), indent=2)
        
        system_prompt = f"""You are an elite Video Director for YouTube documentaries (Masterclass / Vox style).
Your job is to take a basic script (array of scenes) and upgrade it into a professional cinematic shot manifest following a strict hierarchical architecture:
Story Beat -> Narration Block -> Shots[].

CRITICAL DIRECTIVES:

0. SCENE PRESERVATION (ABSOLUTE MANDATE): 
   The raw script contains an array of scenes. You MUST create exactly one NarrationBlock for EVERY SINGLE SCENE in the raw script. 
   Do NOT merge scenes together. Do NOT drop or summarize scenes. The total number of NarrationBlocks in your final JSON MUST EXACTLY MATCH the total number of scenes in the raw script!

1. VISUAL DIVERSITY & ASSET PROVENANCE:
   Do NOT default to generic stock visuals or AI video for everything. Select authentic `asset_provenance` (AUTHENTIC_PHOTO, ARCHIVAL_FOOTAGE, DOCUMENT, DATA_VISUALIZATION, AI_RECONSTRUCTION).
   If showing people, evidence, or records, use `real_photo` with high-detail queries.

2. BAN CLICHÉ DOCUMENTARY VISUALS:
   Do NOT use generic metaphors (e.g. champagne glasses, generic handcuffs, scales of justice, generic businessman shaking hands, money falling from sky).
   Every shot must show specific real evidence, specific environments, technical diagrams, or authentic archival records.

3. STRICT CAMERA DIVERSITY & NO CAMERA FATIGUE:
   - DO NOT USE `zoom_in` repeatedly. Distribute camera movements: `slow_push_in`, `pan_left`, `pan_right`, `dolly_in`, `static`, `zoom_out`.
   - Rotate camera angles: `eye_level`, `low_angle`, `high_angle`, `overhead_shot`. Use `dutch_angle` at most ONCE per video.
   - Varied shot sizes: alternate `establishing_shot`, `wide`, `medium`, `close`, `extreme_close`.

4. SEMANTIC CUT REASONS (MANDATORY):
   `cut_reason` MUST describe a causal editorial shift. 
   GOOD: 'bridge_luxury_to_collapse', 'reveal_critical_typo_discrepancy', 'contrast_public_image_with_covert_log', 'isolate_central_instigator'.
   BANNED: 'introduce_conflict', 'introduce_information', 'transition', 'next_shot', 'change_scene'.

5. HARD DURATION LIMITS:
   NO SHOT MAY EXCEED 4.5 SECONDS.
   If a NarrationBlock is > 4.5s, split into multiple distinct shots with complementary angles.

You must return a valid JSON object matching this exact JSON schema:
{schema_json}
"""
        
        prompt = f"""Raw Script:
{json.dumps(raw_script, ensure_ascii=False, indent=2)}

Generate the complete ScriptManifest JSON."""
        
        output_dict = self.call_llm(prompt, system_prompt)
        output_dict = self.normalize_manifest(output_dict)
        
        print("[*] Validating output against Pydantic schema...")
        try:
            manifest = ScriptManifest.model_validate(output_dict)
            print("[*] Schema validation successful!")
            return self.enforce_strict_rules(manifest.model_dump())
        except ValidationError as e:
            repaired_dict = self.repair_schema_error(output_dict, e)
            try:
                manifest = ScriptManifest.model_validate(repaired_dict)
                print("[*] Schema repair validation successful!")
                return self.enforce_strict_rules(manifest.model_dump())
            except ValidationError as e2:
                log.error("Schema repair failed twice. Hard failing.")
                raise e2
