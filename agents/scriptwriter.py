import json
from .base_agent import BaseAgent

class ScriptwriterAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def write_script(self, fact_sheet, outline, duration_minutes=1, target_scenes=4):
        """Takes the fact sheet and outline and writes the voiceover & captions targeting specified duration."""
        target_words_total = int(duration_minutes * 130)
        target_words_per_scene = max(25, target_words_total // max(1, target_scenes))
        print(f"[*] ScriptwriterAgent writing scene-by-scene script ({duration_minutes}m -> {target_scenes} scenes, ~{target_words_total} total words)...")
        
        system_prompt = f"""You are an elite YouTube Documentary Scriptwriter.
Your job is to take a Fact Sheet and an Outline, and write the actual voiceover and captions for a {duration_minutes}-minute video.

LANGUAGE:
- The `voiceover` MUST BE IN PURE HINDI (Devanagari script), perfect for a Hindi TTS engine. Use dramatic tone.
- The `caption` MUST BE the FULL Romanized Hinglish equivalent of the voiceover, to be displayed on screen as subtitles. (CRITICAL: USE ENGLISH ALPHABET ONLY. NO DEVANAGARI. NO EMOJIS. If you use Hindi script in the caption, the font will render as boxes).

RULES:
1. MUST output EXACTLY {target_scenes} scenes.
2. DURATION & PACING CALIBRATION:
   - Target total video duration: {duration_minutes} minutes (~{target_words_total} total Hindi words).
   - Each `voiceover` MUST be approximately {target_words_per_scene} to {target_words_per_scene + 10} words (2-4 natural sentences).
   - Do NOT write overly long paragraphs that cause the video to exceed {duration_minutes} minutes.
3. NARRATIVE FLOW: Do NOT write bullet points or fragmented keywords. You MUST write a cohesive, engaging story connecting ideas through logic, cause, and effect.
4. Follow the 3-Act structure from the Outline.

Output JSON strictly matching this schema (an array of EXACTLY {target_scenes} scenes):
[
  {{
    "scene_number": 1,
    "purpose": "hook",
    "voiceover": "2018 में, मार्केट रातों-रात गिर गया। किसी को समझ नहीं आया कि यह कैसे हुआ।",
    "caption": "2018 mein, market raaton-raat gir gaya. Kisi ko samajh nahi aaya ki yeh kaise hua."
  }}
]"""
        
        prompt = f"Fact Sheet:\n{fact_sheet}\n\nOutline:\n{outline}\n\nTarget Scenes: {target_scenes} ({duration_minutes} min, ~{target_words_total} words total).\nWrite ALL {target_scenes} Scenes."
        
        return self.call_llm(prompt, system_prompt)

    def write_act(self, fact_sheet, act_number, act_outline, target_scenes=4, duration_minutes=1, context_so_far=""):
        """Writes the voiceover & captions for a SINGLE act with calibrated pacing."""
        target_words_total = int(duration_minutes * 130)
        target_words_per_act = max(50, target_words_total // 3)
        target_words_per_scene = max(25, target_words_per_act // max(1, target_scenes))
        print(f"[*] ScriptwriterAgent writing Act {act_number} ({target_scenes} scenes, ~{target_words_per_act} words for Act {act_number})...")
        
        system_prompt = f"""You are an elite YouTube Documentary Scriptwriter.
Your job is to write Act {act_number} of a 3-Act documentary based on the provided Fact Sheet and Act Outline.

LANGUAGE:
- The `voiceover` MUST BE IN PURE HINDI (Devanagari script), perfect for a Hindi TTS engine. Use dramatic tone.
- The `caption` MUST BE the FULL Romanized Hinglish equivalent of the voiceover, to be displayed on screen as subtitles. (CRITICAL: USE ENGLISH ALPHABET ONLY. NO DEVANAGARI).

RULES:
1. MUST output EXACTLY {target_scenes} scenes for this Act.
2. DURATION & PACING CALIBRATION:
   - Target for Act {act_number}: ~{target_words_per_act} total Hindi words across {target_scenes} scenes.
   - Each `voiceover` MUST be approximately {target_words_per_scene} to {target_words_per_scene + 10} words (2-3 natural sentences).
   - Keep pacing tight and cinematic so the full 3-Act documentary accurately hits the {duration_minutes}-minute target.
3. NARRATIVE FLOW & CONTINUITY:
   - You MUST write a cohesive, linear story that continues from the previous acts.
   - Do NOT restart the story. Do NOT re-introduce characters or facts already explained in "Context from Previous Acts".
   - Pick up the narrative exactly where the previous act left off.

Output JSON strictly matching this schema (an array of EXACTLY {target_scenes} scenes):
[
  {{
    "scene_number": 1,
    "purpose": "hook",
    "voiceover": "2018 में, मार्केट रातों-रात गिर गया। किसी को समझ नहीं आया कि यह कैसे हुआ।",
    "caption": "2018 mein, market raaton-raat gir gaya. Kisi ko samajh nahi aaya ki yeh kaise hua."
  }}
]"""
        
        prompt = f"Fact Sheet:\n{fact_sheet}\n\nAct {act_number} Outline:\n{act_outline}\n\nContext from Previous Acts (Do NOT repeat or restart these events):\n{context_so_far}\n\nTarget Scenes for THIS Act: {target_scenes} (~{target_words_per_act} words).\nWrite ALL {target_scenes} Scenes."
        
        return self.call_llm(prompt, system_prompt)
