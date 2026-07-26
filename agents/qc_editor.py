import json
from .base_agent import BaseAgent

class QCEditorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def review_script(self, director_script):
        """Reviews the director's script to ensure it meets quality standards."""
        total_scenes = len(director_script)
        print(f"[*] QCEditorAgent reviewing final script ({total_scenes} scenes)...")
        
        system_prompt = f"""You are the brutal Editor-in-Chief of a massive YouTube Documentary channel.
Your job is to review a Director's JSON script of {total_scenes} scenes and decide if it is APPROVED or REJECTED.

VISUAL RATIO TO RESPECT (30% motion_graphics / 25% ai_video / 20% real_photo/stock_video / 15% ai_image / 10% broll_video).
CRITICAL RULE 1: Do NOT replace `ai_video` scenes with `stock_video`. Keep `ai_video` scenes intact for Colab AnimateDiff generation.
CRITICAL RULE 2: If REJECTED, fixed_script MUST PRESERVE ALL {total_scenes} SCENES! DO NOT TRUNCATE OR DROP SCENES!

REJECTION CRITERIA:
1. Boring Visuals: If important historical facts use `broll_video` everywhere instead of adhering to the visual ratio.
2. Bad Pacing: If there are no `strategic_silence_seconds` in the entire script.
3. Weak Conflict: If the hook doesn't set up a problem.

Output JSON strictly matching this schema:
{{
  "status": "APPROVED", // or "REJECTED"
  "feedback": "...", // Give specific reasons if rejected, or "Looks good" if approved.
  "fixed_script": [] // ONLY if rejected, provide the fixed, corrected JSON array containing ALL {total_scenes} scenes here. If approved, leave empty.
}}"""
        
        prompt = f"Director Script ({total_scenes} scenes) to Review:\n{json.dumps(director_script, ensure_ascii=False, indent=2)}\n\nReview it. Keep all {total_scenes} scenes."
        
        return self.call_llm(prompt, system_prompt)
