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
1. MUST output EXACTLY {target_scenes} scenes. Write detailed, immersive Hindi voiceover so that all {target_scenes} scenes combined reach a total duration of EXACTLY {duration_minutes} minutes!
2. MINIMUM WORD COUNT (CRITICAL): Each `voiceover` MUST be at least 45 words (3-5 full sentences). If you write short 1-sentence voiceovers, the final video will be way too short and the viewer will be disappointed.
3. NARRATIVE FLOW: Do NOT write bullet points, fragmented keywords, or "word salad". You MUST write a cohesive story, connecting one idea to the next using logic, cause, and effect.
4. Follow the 3-Act structure from the Outline.
5. Write highly engaging voiceover. Don't be short or rushed. Provide rich story details in every scene.

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

    def write_act(self, fact_sheet, act_number, act_outline, target_scenes=8, context_so_far=""):
        """Writes the voiceover & captions for a SINGLE act to prevent LLM truncation."""
        print(f"[*] ScriptwriterAgent writing Act {act_number} ({target_scenes} scenes)...")
        
        system_prompt = f"""You are an elite YouTube Documentary Scriptwriter.
Your job is to write Act {act_number} of a 3-Act documentary based on the provided Fact Sheet and Act Outline.

LANGUAGE:
- The `voiceover` MUST BE IN PURE HINDI (Devanagari script), perfect for a Hindi TTS engine. Use dramatic tone.
- The `caption` MUST BE the FULL Romanized Hinglish equivalent of the voiceover, to be displayed on screen as subtitles. (CRITICAL: USE ENGLISH ALPHABET ONLY. NO DEVANAGARI).

RULES:
1. MUST output EXACTLY {target_scenes} scenes for this Act.
2. MINIMUM WORD COUNT (CRITICAL): Each `voiceover` MUST be at least 45 words (3-5 full sentences).
3. NARRATIVE FLOW: Do NOT write bullet points or "word salad". You MUST write a cohesive story, connecting one idea to the next.
4. Ensure continuity with previous acts (if provided).
5. Write highly engaging voiceover. Don't be short or rushed.

Output JSON strictly matching this schema (an array of EXACTLY {target_scenes} scenes):
[
  {{
    "scene_number": 1,
    "purpose": "hook",
    "voiceover": "2018 में, मार्केट रातों-रात गिर गया। किसी को समझ नहीं आया कि यह कैसे हुआ।",
    "caption": "2018 mein, market raaton-raat gir gaya. Kisi ko samajh nahi aaya ki yeh kaise hua."
  }}
]"""
        
        prompt = f"Fact Sheet:\n{fact_sheet}\n\nAct {act_number} Outline:\n{act_outline}\n\nContext from Previous Acts:\n{context_so_far}\n\nTarget Scenes for THIS Act: {target_scenes}.\nWrite ALL {target_scenes} Scenes."
        
        return self.call_llm(prompt, system_prompt)
