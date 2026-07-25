import json
from .base_agent import BaseAgent

class ScriptwriterAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def write_script(self, fact_sheet, outline, duration_minutes=1, target_scenes=8):
        """Takes the fact sheet and outline and writes the voiceover & captions targeting specified duration."""
        print(f"[*] ScriptwriterAgent writing scene-by-scene script ({duration_minutes}m -> {target_scenes} scenes)...")
        
        system_prompt = f"""You are an elite YouTube Documentary Scriptwriter.
Your job is to take a Fact Sheet and an Outline, and write the actual voiceover and captions for a {duration_minutes}-minute video.

LANGUAGE:
- The `voiceover` MUST BE IN PURE HINDI (Devanagari script), perfect for a Hindi TTS engine. Use dramatic tone.
- The `caption` MUST BE IN HINGLISH (Roman script) (max 3-4 words per scene), to be displayed on screen.

RULES:
1. MUST output EXACTLY {target_scenes} scenes. Write detailed, immersive Hindi voiceover (2-3 full sentences, ~8-10 seconds of narration per scene) so that all {target_scenes} scenes combined reach a total duration of EXACTLY {duration_minutes} minutes!
2. Follow the 3-Act structure from the Outline.
3. Write highly engaging voiceover. Don't be short or rushed. Provide rich story details in every scene.

Output JSON strictly matching this schema (an array of EXACTLY {target_scenes} scenes):
[
  {{
    "scene_number": 1,
    "purpose": "hook",
    "voiceover": "2018 में, मार्केट रातों-रात गिर गया...",
    "caption": "Market Collapsed Overnight"
  }}
]"""
        
        prompt = f"Fact Sheet:\n{fact_sheet}\n\nOutline:\n{outline}\n\nTarget Scenes: {target_scenes} ({duration_minutes} min).\nWrite ALL {target_scenes} Scenes."
        
        return self.call_llm(prompt, system_prompt)
