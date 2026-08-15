import json
from pydantic_core import ValidationError
from .base_agent import BaseAgent
from .schema import ScriptManifest
import logging

log = logging.getLogger(__name__)

class DirectorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
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
        log.warning(f"Schema Validation Failed. Attempting targeted schema repair...")
        
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
        """Programmatically enforce rules that the LLM might miss."""
        import copy, math
        
        manifest = copy.deepcopy(raw_manifest)
        
        for beat in manifest.get("story_beats", []):
            for block in beat.get("narration_blocks", []):
                block_dur = block.get("total_block_duration", block.get("actual_voice_duration", 4.0))
                new_shots = []
                for shot in block.get("shots", []):
                    # 1. ENFORCE CINEMATOGRAPHY
                    if not shot.get("shot_size") or shot.get("shot_size", "").upper() == "N/A" or str(shot.get("shot_size")).lower() == "null":
                        shot["shot_size"] = "medium_shot"
                    if not shot.get("camera_angle") or shot.get("camera_angle", "").upper() == "N/A" or str(shot.get("camera_angle")).lower() == "null":
                        shot["camera_angle"] = "eye_level"
                    if not shot.get("lens") or shot.get("lens", "").upper() == "N/A" or str(shot.get("lens")).lower() == "null":
                        shot["lens"] = "standard_lens"
                    if not shot.get("composition") or shot.get("composition", "").upper() == "N/A" or str(shot.get("composition")).lower() == "null":
                        shot["composition"] = "rule_of_thirds"
                        
                    # 2. ENFORCE 4.5S HARD SPLIT
                    mode = shot.get("duration_mode", "ratio")
                    if mode == "fixed" and shot.get("duration_seconds"):
                        dur = float(shot.get("duration_seconds"))
                        ratio = 1.0 # placeholder
                    else:
                        ratio = float(shot.get("duration_ratio", 1.0))
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
                            
                            # vary camera motion slightly on duplicates
                            if i % 2 == 1:
                                if sub.get("camera_motion") == "zoom_in":
                                    sub["camera_motion"] = "pan_right"
                                elif sub.get("camera_motion") == "pan_right":
                                    sub["camera_motion"] = "zoom_out"
                                    
                            new_shots.append(sub)
                    else:
                        new_shots.append(shot)
                
                block["shots"] = new_shots
                
        return manifest

    def add_metadata(self, raw_script):
        """Acts as the Video Director, adding visual and audio metadata to the hierarchical script."""
        print("[*] DirectorAgent adding cinematic metadata (v2.0 Schema)...")
        
        schema_json = json.dumps(ScriptManifest.model_json_schema(), indent=2)
        
        system_prompt = f"""You are an elite Video Director for YouTube documentaries.
Your job is to take a basic script (array of scenes) and upgrade it into a professional cinematic shot manifest following a strict hierarchical architecture:
Story Beat -> Narration Block -> Shots[].

CRITICAL DIRECTIVES:

1. VISUAL DIVERSITY & ASSET PROVENANCE RULES (CRITICAL):
   Do NOT default to `ai_video` for everything. You MUST select the most authentic and high-quality `asset_provenance` and `visual_type`.
   If `visual_job` is `SHOW_PERSON` or `SHOW_EVIDENCE`, you MUST use `real_photo` and provide a highly specific `visual_query` (e.g. "Vijay Mallya portrait 2012").

2. BAN CLICHÉ DOCUMENTARY VISUALS:
   Do NOT use generic symbolic visuals (e.g. champagne pouring, generic handcuffs, scales of justice, generic gavel, generic businessman, money raining, generic rising graph).
   Before accepting a shot, ensure it: shows real evidence, explains information, shows a real place/event, establishes specific environment, or creates tension. If none, REJECT.

3. FIX LOCATION-SPECIFIC VISUALS:
   For historical events, named place + year + specific event must be reflected. 
   BAD: "dark international airport"
   GOOD: "Delhi airport departure environment, 2016, night, Indian airport architecture appropriate to the period"

4. ALLOWED NARRATIVE_INTENT ENUMS (STRICT):
   `narrative_intent` MUST ONLY be one of: HOOK, EVIDENCE, MYSTERY, EXPLANATION, CONFLICT, RESOLUTION, LOCATION_ESTABLISH.
   Separate narrative intent from shot role. Keep narrative intent simple. Use `shot_role` for detailed cinematic grammar (e.g. Intent: CONFLICT, Role: EVIDENCE).

5. HARD DURATION LIMITS (CRITICAL):
   NO SHOT MAY EXCEED 4.5 SECONDS. NEVER.
   If a NarrationBlock's `duration_hint` is > 4.5 seconds, you MUST split it into multiple distinct shots by adjusting `duration_ratio`.
   Example: If duration is 9s, create Shot A (ratio 0.5) and Shot B (ratio 0.5).

6. DETAILED AI PROMPTS & CONTINUITY:
   `ai_prompt` MUST be highly descriptive (MINIMUM 20 WORDS). Detail the lighting, atmosphere, lens feeling, colors, and specific subject action.
   BAD: "Vijay Mallya on a yacht"
   GOOD: "Cinematic medium shot of an Indian billionaire in a tailored suit relaxing on a luxury white yacht, 2005 era, Arabian Sea near Goa, golden hour sunset lighting, warm colors, anamorphic lens flare"

7. STOCK FOOTAGE & EVIDENCE:
   Provide a clean `visual_query` for stock footage. If citing evidence, populate `source_name` and `source_date`.
   
8. AESTHETICS (LUTS & OVERLAYS):
   Use `lut_filter` (e.g. 'sepia', 'vintage_film', 'noir', 'neon_cyberpunk', 'high_contrast') to color grade shots.
   Use `overlay` (e.g. 'vhs_glitch', 'film_grain', 'dust_scratches', 'light_leaks', 'scanlines') to add texture.

9. STRICT CINEMATOGRAPHY & FATIGUE RULES:
   - YOU MUST NEVER use "N/A" or "null" or empty strings for `shot_size`, `camera_angle`, `lens`, or `composition`. They are strictly required for every single shot.
   - You MUST vary `camera_motion` across consecutive shots. Do NOT use "zoom_in" repeatedly. Alternate with "pan_right", "slow_push_in", "pan_left", "static", "dolly_out", etc.
   - `cut_reason` MUST be highly descriptive (e.g. "Cutting to wide shot to reveal the massive scale of the mansion" instead of just "To show the mansion").

You must return a valid JSON object matching this exact JSON schema:
{schema_json}
"""
        
        prompt = f"Raw Script:\n{json.dumps(raw_script, ensure_ascii=False, indent=2)}\n\nGenerate the complete ScriptManifest JSON."
        
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
