import json
from .base_agent import BaseAgent

class DirectorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def add_metadata(self, raw_script):
        """Acts as the Video Director, adding visual and audio metadata to each scene."""
        print("[*] DirectorAgent adding cinematic metadata...")
        
        system_prompt = """You are an elite Video Director for YouTube documentaries.
Your job is to take a basic script (array of scenes) and upgrade it by adding precise visual and audio metadata to every scene.

VISUAL TYPES RATIO (CRITICAL - YOU MUST DISTRIBUTE VISUAL TYPES ACROSS SCENES ACCORDING TO THIS EXACT RATIO):
- 30% `motion_graphics` / `text_stat` (Remotion maps, timelines, stock charts, animated text overlays)
- 25% `ai_video` (AnimateDiff AI Video for atmospheric B-roll and hero shots)
- 20% `real_photo` / `stock_video` (Real evidence on screen, specific company/person photos)
- 15% `ai_image` (Pollinations 4K + Ken Burns FX for historical/conceptual illustrations)
- 10% `broll_video` (Real archival B-roll stock footage)

AI PROMPT STRUCTURE FOR `ai_video`:
MUST follow 4 parts: [Simple Subject] + [Environment] + [Camera Movement] + [Art Style].
Example: "a lone officer sitting at a radar desk, dimly lit bunker, slow camera zoom in, retro 80s aesthetic". Rule: MOVE THE CAMERA, NOT THE SUBJECT. Max 1 action verb.

TRANSITIONS ALLOWED:
- `j_cut` (Audio starts before video)
- `fade` (Standard crossfade)
- `hard_cut` (Immediate cut)

Output JSON strictly matching this schema (an array of scenes, extending the input script):
[
  {
    "scene_number": 1,
    "voiceover": "...",
    "caption": "...",
    "visual_type": "ai_video",
    "visual_query": "Stock market crashing red line graph",
    "ai_prompt": "a glowing digital stock chart plunging downward, dark moody trading floor, slow camera zoom in, cinematic 8k",
    "camera_movement": "ken_burns_zoom_in",
    "lut": "dark_noir",
    "overlay": "vhs_glitch",
    "sfx": "deep_impact",
    "bgm_mood": "dark suspense",
    "strategic_silence_seconds": 1.5,
    "transition_in": "hard_cut",
    "duration_hint": 4.5
  }
]"""
        
        prompt = f"Raw Script:\n{json.dumps(raw_script, ensure_ascii=False, indent=2)}\n\nAdd Director Metadata."
        
        return self.call_llm(prompt, system_prompt)
