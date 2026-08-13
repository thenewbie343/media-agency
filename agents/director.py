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

5. LOOPS & SHOT-SPLITTING LIMITS:
   No single shot may cover more than 4.5 seconds. If a block is > 4.5s, define MULTIPLE shots (using `duration_ratio`) so visuals alternate.

6. DETAILED AI PROMPTS & CONTINUITY:
   `ai_prompt` MUST be formatted exactly as: [SUBJECT], [ERA], [LOCATION], [ENVIRONMENT], [LIGHTING], [CAMERA ANGLE].

7. STOCK FOOTAGE & EVIDENCE:
   Provide a clean `visual_query` for stock footage. If citing evidence, populate `source_name` and `source_date`.

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
            return manifest.model_dump()
        except ValidationError as e:
            repaired_dict = self.repair_schema_error(output_dict, e)
            try:
                manifest = ScriptManifest.model_validate(repaired_dict)
                print("[*] Schema repair validation successful!")
                return manifest.model_dump()
            except ValidationError as e2:
                log.error("Schema repair failed twice. Hard failing.")
                raise e2
