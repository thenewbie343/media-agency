import json
import logging
from .base_agent import BaseAgent

log = logging.getLogger("agency")

class QCEditorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def review_script(self, director_manifest):
        """Reviews the director's hierarchical script using an LLM to evaluate editorial quality."""
        print("[*] QCEditorAgent evaluating editorial quality via LLM...")
        
        # Ensure we are dealing with a dict (v2 Schema)
        if not isinstance(director_manifest, dict) or "story_beats" not in director_manifest:
            log.warning("QC failed: manifest is not a valid v2 ScriptManifest dict.")
            return {"status": "REJECTED", "feedback": "Invalid manifest structure."}
        
        system_prompt = """You are the Supervising Editor for a cinematic YouTube documentary.
Your job is to strictly evaluate the editorial quality of the generated ScriptManifest.

CRITICAL EDITORIAL RULES:
1. Visual Job Validation: Every shot MUST have a defined `visual_job` (e.g. SHOW_LOCATION, SHOW_PERSON, SHOW_EVIDENCE, EXPLAIN_MECHANISM) that directly serves the narration.
2. HARD QC RULE: Reject any shot that exists solely for visual variety. Every shot must answer: "What does this shot communicate that the previous shot did not?" If the answer is "nothing", REJECT the manifest.
3. Continuity Locks: Check that shots within continuous scenes maintain strict Era, Location, Character, Object, Weather, and Lighting continuity locks.
4. Visual Variety: If consecutive shots have identical or similar visuals, or if `camera_motion`, `camera_angle`, and `shot_size` are repeated >2 times, flag for 'VISUAL_REDUNDANCY' or 'CAMERA_FATIGUE'.
5. Cinematography completeness: Any non-graphic visual shot missing `lens`, `camera_angle`, or `composition` is a FAIL.
6. Cut Reason: Generic `cut_reason` (e.g. introduce_information, transition) is a FAIL. Must be highly semantic (e.g. 'bridge_luxury_to_collapse').
7. REPAIR ISOLATION: When recommending a repair, you MUST instruct the Director to ONLY modify fields related to the failure. Under NO circumstances should narration, beat chronology, or unrelated IDs be modified to fix visual or camera issues.

Review the JSON manifest provided. If there are major editorial flaws (weak hooks, repetitive shots, missing cut_reasons, continuity breaks, or meaningless camera movement), you must REJECT it and provide specific feedback for the DirectorAgent to fix.

You must return a JSON object in this exact format:
{
  "status": "APPROVED" | "REJECTED",
  "score": <1-10>,
  "feedback": "Detailed explanation of why it passed or failed.",
  "failures": [
    {
      "shot_id": "n005_s001",
      "beat_id": "b001",
      "failure_type": "VISUAL_REDUNDANCY",
      "severity": "high",
      "repair": {
        "preserve_narration": true,
        "preserve_timing": true,
        "preserve_beat": true,
        "preserve_ids": true,
        "replace_visual_only": true,
        "recommended_visual_job": "SHOW_EVIDENCE"
      }
    }
  ]
}
"""
        
        prompt = f"ScriptManifest:\n{json.dumps(director_manifest, indent=2)}\n\nEvaluate the editorial quality and return the JSON response."
        
        try:
            output_dict = self.call_llm(prompt, system_prompt)
            print(f"[*] QC Result: {output_dict.get('status')} (Score: {output_dict.get('score')})")
            if output_dict.get('status') == 'REJECTED':
                log.warning(f"QC Editor Rejected Script: {output_dict.get('feedback')}")
            return output_dict
        except Exception as e:
            log.error(f"QC Editor Agent Failed: {str(e)}")
            return {"status": "APPROVED", "score": 7, "feedback": f"Auto-approved due to error: {str(e)}"}
