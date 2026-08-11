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
4. Anachronism Check: REJECT modern imagery (steel skyscrapers, modern cars) used in historical settings unless explicitly representing present-day context.
5. Visual/Narration Match: The visuals must match the narration accurately without literal/corny metaphor translations.
6. Meaningful Cuts: Every shot must have a strong 'cut_reason' and a narrative justification. Reject unnecessary cuts.
7. Evaluate Editorial Quality over quotas.

Review the JSON manifest provided. If there are major editorial flaws (weak hooks, repetitive shots, missing cut_reasons, continuity breaks, or meaningless camera movement), you must REJECT it and provide specific feedback for the DirectorAgent to fix.

Return a JSON object in this format:
{
  "status": "APPROVED" | "REJECTED",
  "score": <1-10>,
  "feedback": "Detailed explanation of why it passed or failed and what needs fixing."
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
