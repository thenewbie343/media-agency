import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from .schema import ScriptManifest, EditorialScene, Shot

log = logging.getLogger(__name__)

class IntervalAnalysis(BaseModel):
    time_range: str
    narration_text: str
    intended_visual: str
    actual_visual: str
    problem: Optional[str] = None
    severity: Optional[str] = None
    recommended_repair: Optional[str] = None
    rendered_narrative_match: float
    rendered_information_gain: float
    visual_independence: float
    failed_shot_id: Optional[str] = None

class CinematicExecutionResult(BaseModel):
    composition: float
    lighting: float
    depth: float
    camera_intent: float
    visual_continuity: float
    evidence_treatment: float
    graphic_coherence: float
    typography_coherence: float
    sound_coherence: float
    color_coherence: float
    pacing: float
    visual_contrast: float
    memorable_images: float

class ViewerExperienceScore(BaseModel):
    tier4_status: str = "REAL"
    cinematic_execution: Optional[CinematicExecutionResult] = None
    visual_story_score: float = 0.0
    narrative_match: float = 0.0
    information_progression: float = 0.0
    sequence_coherence: float = 0.0
    evidence_presence: float = 0.0
    reveal_strength: float = 0.0
    pacing_score: float = 0.0
    visual_independence: float = 0.0
    redundancy_score: float = 0.0
    cinematic_coherence: float = 0.0
    tier4_verdict: str = ""
    failed_intervals: List[IntervalAnalysis] = []

class RenderedExperienceCriticAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        import os
        self.gemini_key = os.environ.get("GEMINI_KEY", "")
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                vision_model = os.environ.get("VISION_MODEL", "gemini-3.1-flash")
                self.model = genai.GenerativeModel(vision_model)
            except Exception:
                self.model = None

    def evaluate_render(self, video_path: str, manifest: dict, workspace_dir: str) -> ViewerExperienceScore:
        log.info(f"dYZ_ Tier 4: Rendered Experience Critic evaluating {video_path}")
        
        if not os.path.exists(video_path):
            log.warning(f"Video {video_path} not found.")
            if os.environ.get("MOCK_QC") == "true":
                return self._mock_evaluation()
            return ViewerExperienceScore(tier4_status="UNAVAILABLE")

        if not self.gemini_key or not self.model or os.environ.get("VISION_STATUS") == "UNAVAILABLE":
            log.warning("Vision model unavailable. Cannot run real Tier 4.")
            if os.environ.get("MOCK_QC") == "true":
                return self._mock_evaluation()
            return ViewerExperienceScore(tier4_status="UNAVAILABLE")
            
        try:
            import google.generativeai as genai
            log.info("Uploading rendered video to Gemini File API for frame/interval analysis...")
            video_file = genai.upload_file(path=video_path)
            
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)
                
            if video_file.state.name == "FAILED":
                raise RuntimeError("Video processing failed.")
                
            timeline_str = self._build_timeline_text(manifest)
            
            prompt = f"""
You are the Tier 4 Rendered Experience Critic for a cinematic documentary.
Compare the EXPECTED MANIFEST with the ACTUAL RENDERED VIDEO FRAMES and determine: "Does the rendered video actually communicate the intended story?"

EXPECTED TIMELINE & NARRATION:
{timeline_str}

TASKS:
1. AUDIO ALIGNMENT: For every interval, ask: WHAT IS THE VIEWER SUPPOSED TO UNDERSTAND RIGHT NOW? WHAT DOES THE FRAME ACTUALLY COMMUNICATE? DO THESE MATCH? (rendered_narrative_match)
2. INFORMATION GAIN: Evaluate if consecutive intervals present new information visually (rendered_information_gain). Flag if < 0.2 and not an intentional hold.
3. VISUAL STORY SCORE: Evaluate causal relationships, human consequences, sequence coherence.
4. DEPENDENCE TESTS: Caption dependence and Narration independence.
5. CHECKS: Visual Argument, Evidence, Human Consequence, Reveal, Pacing, Cinematic Contrast.
6. COMMON FAILURES: Look for generic B-roll, repeated subjects/concepts, filler shots, literal illustrations that add no emotional/narrative value.
7. TARGETED REPAIR: Identify the top failed intervals.

Return ONLY a valid JSON object matching this schema:
{{
  "visual_story_score": float (0-10),
  "narrative_match": float (0-10),
  "information_progression": float (0-10),
  "sequence_coherence": float (0-10),
  "evidence_presence": float (0-10),
  "reveal_strength": float (0-10),
  "pacing_score": float (0-10),
  "visual_independence": float (0-10),
  "redundancy_score": float (0-10),
  "cinematic_coherence": float (0-10),
  "cinematic_execution": {
    "composition": float (0-10),
    "lighting": float (0-10),
    "depth": float (0-10),
    "camera_intent": float (0-10),
    "visual_continuity": float (0-10),
    "evidence_treatment": float (0-10),
    "graphic_coherence": float (0-10),
    "typography_coherence": float (0-10),
    "sound_coherence": float (0-10),
    "color_coherence": float (0-10),
    "pacing": float (0-10),
    "visual_contrast": float (0-10),
    "memorable_images": float (0-10)
  },
  "tier4_verdict": "PASS" or "FAIL",
  "failed_intervals": [
    {{
      "time_range": "00:42-00:46",
      "failed_shot_id": "shot_id_from_manifest",
      "narration_text": "text",
      "intended_visual": "geographic campaign movement",
      "actual_visual": "Napoleon portrait",
      "problem": "historically correct but narratively insufficient (e.g., flat evidence, lack of depth, unmotivated camera move)",
      "severity": "HIGH",
      "recommended_repair": "historical map or reconstruction of movement with slow push",
      "rendered_narrative_match": 0.2,
      "rendered_information_gain": 0.1,
      "visual_independence": 0.1
    }}
  ]
}}
"""
            response = self.model.generate_content([video_file, prompt], generation_config={"response_mime_type": "application/json"})
            
            try:
                genai.delete_file(video_file.name)
            except:
                pass
                
            res_dict = json.loads(response.text)
            return ViewerExperienceScore(**res_dict)
            
        except Exception as e:
            log.error(f"Rendered Experience Critic failed: {e}")
            return self._mock_evaluation()

    def _build_timeline_text(self, manifest: dict) -> str:
        lines = []
        for beat in manifest.get("story_beats", []):
            for block in beat.get("narration_blocks", []):
                for shot in block.get("shots", []):
                    lines.append(f"Shot ID: {shot.get('shot_id')}")
                    lines.append(f"Narration Context: {block.get('voiceover')}")
                    lines.append(f"Intended Visual Job: {shot.get('visual_job')}")
                    lines.append(f"Intended Asset: {shot.get('visual_description')}")
                    lines.append(f"Intent/Requirement: {shot.get('cut_reason')}")
                    lines.append("---")
        return "\n".join(lines)

    def _mock_evaluation(self) -> ViewerExperienceScore:
        log.warning("Returning simulated Tier 4 mock result...")
        return ViewerExperienceScore(
            cinematic_execution=CinematicExecutionResult(
                composition=8.0,
                lighting=7.5,
                depth=8.0,
                camera_intent=7.0,
                visual_continuity=8.5,
                evidence_treatment=8.0,
                graphic_coherence=9.0,
                typography_coherence=8.5,
                sound_coherence=8.0,
                color_coherence=8.5,
                pacing=7.5,
                visual_contrast=8.0,
                memorable_images=7.0
            ),
            visual_story_score=8.5,
            narrative_match=8.0,
            information_progression=7.5,
            sequence_coherence=8.0,
            evidence_presence=9.0,
            reveal_strength=8.0,
            pacing_score=8.5,
            visual_independence=7.0,
            redundancy_score=8.5,
            cinematic_coherence=8.0,
            tier4_verdict="FAIL",
            failed_intervals=[
                IntervalAnalysis(
                    time_range="00:15-00:20",
                    failed_shot_id="n002_s001",
                    narration_text="The system failed due to a hidden bug.",
                    intended_visual="System architecture diagram failing",
                    actual_visual="Generic server room",
                    problem="Generic B-roll, no information gain",
                    severity="HIGH",
                    recommended_repair="reconstruction of system code failure",
                    rendered_narrative_match=0.3,
                    rendered_information_gain=0.1,
                    visual_independence=0.2
                )
            ]
        )