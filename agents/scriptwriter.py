import json
from .base_agent import BaseAgent

class ScriptwriterAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def write_script(self, fact_sheet, outline):
        """Takes the fact sheet and outline and writes the voiceover & captions."""
        print("[*] ScriptwriterAgent writing scene-by-scene script...")
        
        system_prompt = """You are an elite YouTube Documentary Scriptwriter.
Your job is to take a Fact Sheet and an Outline, and write the actual voiceover and captions for each scene.

LANGUAGE:
- The `voiceover` MUST BE IN PURE HINDI (Devanagari script), perfect for a Hindi TTS engine. Use dramatic tone.
- The `caption` MUST BE IN HINGLISH (Roman script) (max 3-4 words per scene), to be displayed on screen.

RULES:
1. Break the video into 10 to 15 scenes.
2. Follow the 3-Act structure from the Outline.
3. Write highly engaging voiceover. Don't be boring.

Output JSON strictly matching this schema (an array of scenes):
[
  {
    "scene_number": 1,
    "purpose": "hook",
    "voiceover": "2018 में, मार्केट रातों-रात गिर गया...",
    "caption": "Market Collapsed Overnight"
  },
  {
    "scene_number": 2,
    "purpose": "context",
    "voiceover": "लेकिन ये सब शुरू कैसे हुआ?",
    "caption": "But How?"
  }
]"""
        
        prompt = f"Fact Sheet:\n{fact_sheet}\n\nOutline:\n{outline}\n\nWrite the Script."
        
        return self.call_llm(prompt, system_prompt)
