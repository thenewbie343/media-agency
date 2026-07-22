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

VISUAL TYPES ALLOWED:
- `ai_video` (For high-end cinematic recreations of historical events or conceptual footage where real footage doesn't exist)
- `ai_image` (For generating specific historical or conceptual imagery)
- `motion_graphics` (For abstract concepts, numbers, stock charts, animated text)
- `real_photo` (For specific people, companies, historical evidence)
- `broll_video` (Generic cinematic filler)

TRANSITIONS ALLOWED:
- `j_cut` (Audio starts before video)
- `fade` (Standard crossfade)
- `hard_cut` (Immediate cut)

For `visual_query`, if `real_photo`, give a specific Google Image Search term (e.g., "Vijay Shekhar Sharma Paytm CEO").

Output JSON strictly matching this schema (an array of scenes, extending the input script):
[
  {
    "scene_number": 1,
    "voiceover": "...",
    "caption": "...",
    "visual_type": "motion_graphics",
    "visual_query": "Stock market crashing red line graph",
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
