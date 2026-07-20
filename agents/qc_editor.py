import json
from .base_agent import BaseAgent

class QCEditorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def review_script(self, director_script):
        """Reviews the director's script to ensure it meets quality standards."""
        print("[*] QCEditorAgent reviewing final script...")
        
        system_prompt = """You are the brutal Editor-in-Chief of a massive YouTube Documentary channel.
Your job is to review a Director's JSON script and decide if it is APPROVED or REJECTED.

REJECTION CRITERIA:
1. Boring Visuals: If important historical facts use `broll_video` instead of `real_photo` or `motion_graphics`.
2. Bad Pacing: If there are no `strategic_silence_seconds` in the entire script.
3. Weak Conflict: If the hook doesn't set up a problem.

Output JSON strictly matching this schema:
{
  "status": "APPROVED", // or "REJECTED"
  "feedback": "...", // Give specific reasons if rejected, or "Looks good" if approved.
  "fixed_script": [] // ONLY if rejected, provide the fixed, corrected JSON array of scenes here. If approved, leave empty.
}"""
        
        prompt = f"Director Script to Review:\n{json.dumps(director_script, ensure_ascii=False, indent=2)}\n\nReview it."
        
        return self.call_llm(prompt, system_prompt)
