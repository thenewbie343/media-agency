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
- The `caption` MUST BE the FULL Romanized Hinglish equivalent of the voiceover, to be displayed on screen as subtitles. (CRITICAL: USE ENGLISH ALPHABET ONLY. NO DEVANAGARI. NO EMOJIS. If you use Hindi script in the caption, the font will render as boxes).

RULES:
1. MUST output EXACTLY {target_scenes} scenes. Write detailed, immersive Hindi voiceover (3-4 full sentences, ~10-12 seconds of narration per scene) so that all {target_scenes} scenes combined reach a total duration of EXACTLY {duration_minutes} minutes!
2. NARRATIVE FLOW (CRITICAL): Do NOT write bullet points, fragmented keywords, or "word salad". You MUST write a cohesive story, connecting one idea to the next using logic, cause, and effect.
3. Follow the 3-Act structure from the Outline.
4. Write highly engaging voiceover. Don't be short or rushed. Provide rich story details in every scene.

Output JSON strictly matching this schema (an array of EXACTLY {target_scenes} scenes):
[
  {{
    "scene_number": 1,
    "purpose": "hook",
    "voiceover": "2018 में, मार्केट रातों-रात गिर गया। किसी को समझ नहीं आया कि यह कैसे हुआ।",
    "caption": "2018 mein, market raaton-raat gir gaya. Kisi ko samajh nahi aaya ki yeh kaise hua."
  }}
]"""
        
        prompt = f"Fact Sheet:\n{fact_sheet}\n\nOutline:\n{outline}\n\nTarget Scenes: {target_scenes} ({duration_minutes} min).\nWrite ALL {target_scenes} Scenes."
        
        return self.call_llm(prompt, system_prompt)
