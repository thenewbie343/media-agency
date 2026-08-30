import json
import logging
from typing import Dict, Any, List, Optional, Union
from .base_agent import BaseAgent
from .schema import (
    DocumentaryResearchPackage,
    DocumentaryVision,
    NarrativeIntent,
    MiniArcPhase,
)

log = logging.getLogger("agency")


class ScriptwriterAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    def _normalize_input(self, data: Any) -> Any:
        if hasattr(data, "model_dump"):
            return data.model_dump()
        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception:
                return data
        return data

    def write_script(
        self,
        fact_sheet: Union[Dict[str, Any], str, DocumentaryResearchPackage],
        outline: Union[Dict[str, Any], str],
        vision: Optional[Union[Dict[str, Any], str, DocumentaryVision]] = None,
        duration_minutes: int = 1,
        target_scenes: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Takes the research package, outline, and optional vision, and writes the complete scene-by-scene script
        with calibrated Hindi voiceover, Hinglish captions, macro narrative intents, and mini-arc phases.
        """
        target_words_total = int(duration_minutes * 130)
        target_words_per_scene = max(25, target_words_total // max(1, target_scenes))
        print(f"[*] ScriptwriterAgent writing scene-by-scene script ({duration_minutes}m -> {target_scenes} scenes, ~{target_words_total} total words)...")
        log.info(f"Writing script: {duration_minutes}m, {target_scenes} scenes, ~{target_words_total} words.")

        research_pkg = self._normalize_input(fact_sheet)
        outline_data = self._normalize_input(outline)
        vision_data = self._normalize_input(vision)

        system_prompt = f"""You are the Lead Master Scriptwriter for visceral, emotionally devastating YouTube documentaries.
You write like a fusion of Lemmino, MagnatesMedia, Dhruv Rathee, and HBO True Crime.
Your scripts make people FEEL — dread, curiosity, rage, awe — not just learn facts.

============================================================
THE GOLDEN RULE: YOU ARE A STORYTELLER, NOT A TEXTBOOK
============================================================
Every line you write must pass this test:
"Would a human narrator pause here, lower their voice, and lean in?"
If not, rewrite it.

============================================================
DHRUV RATHEE / GAURAV THAKUR PACING MANDATE
============================================================
The voiceover must sound like a real human speaking with WEIGHT and BREATHING ROOM:

1. SENTENCE BREATHING: After every major statement, there is a natural breath.
   Write SHORT sentences. Then pause. Then deliver the next blow.
   NOT: "The system was designed by engineers in 1983 and it monitored satellite data for incoming nuclear threats using infrared sensors."
   YES: "1983. Soviet engineers built a system. One job — detect American nuclear missiles. The machine watched the sky. Day and night. Without blinking."

  2. WORD WEIGHT:
       To give words gravity, DO NOT put dashes or ellipses between every word! DO NOT write single word sentences! It breaks the TTS engine.
       YES: "But that night, one man refused to press the button."
       NOT: "But that night. One man. Refused to press the button."
       NOT: "But that night — one man — refused to press the button."
    
  3. DRAMATIC PACING:
       Use natural punctuation. Avoid artificial pauses that sound like stammering.
       "And when they opened the file, everything changed."

4. RHYTHMIC PUNCH PATTERNS:
   Long sentence, then: "Nobody knew." / "Every page — a lie." / "Twenty-three minutes."

5. ONE-SENTENCE PARAGRAPHS for maximum weight.

BANNED PHRASES: "In the world of", "Little did they know", "Let's delve deeper", "It's worth noting", "Buckle up", "Imagine...", "Fast forward to", Wikipedia-style introductions.

VISCERAL MANDATE: Every scene needs ONE physical sensation, ONE environmental detail, ONE human internal state.

EMOTIONAL CURVE: Every scene must include `viewer_emotion`, `vocal_intensity`, `pacing_note`.

LANGUAGE:
- `voiceover`: NATURAL, DRAMATIC HINDI (Devanagari), written like Dhruv Rathee speaks — conversational and authoritative.
- `caption`: FULL Romanized Hinglish (ENGLISH ALPHABET ONLY. NO DEVANAGARI. NO EMOJIS).

RULES:
1. EXACTLY {target_scenes} scenes for this Act.
2. Target: ~{target_words_per_act} Hindi words across {target_scenes} scenes. Each voiceover ~{target_words_per_scene} to {target_words_per_scene + 10} words.
3. Continue seamlessly from previous acts. Do NOT restart or re-introduce.
4. Every scene: `narrative_intent`, `mini_arc_phase`, `viewer_emotion`, `vocal_intensity`, `pacing_note`.

Output JSON (array of EXACTLY {target_scenes} scenes):
[
  {{
    "scene_number": 1,
    "narrative_intent": "HOOK",
    "mini_arc_phase": "SETUP",
    "purpose": "hook",
    "dramatic_tension": 0.95,
    "viewer_emotion": "dread",
    "vocal_intensity": "grave",
    "pacing_note": "slow_and_heavy",
    "voiceover": "26 September, 1983. Midnight. Ek Soviet officer — apni screen ko ghoor raha tha.",
    "caption": "26 September, 1983. Midnight. Ek Soviet officer — apni screen ko ghoor raha tha.",
    "visual_cue": "Dark bunker, green CRT glow on sweating face",
    "withholding_element": "Withhold identity and decision"
  }}
]"""

        prompt = f"""Documentary Research Package:
{json.dumps(research_pkg, indent=2)}

Act {act_number} Outline:
{json.dumps(outline_data, indent=2)}

Documentary Vision:
{json.dumps(vision_data, indent=2) if vision_data else "Pacing and vision aligned with research."}

Context from Previous Acts (Do NOT repeat or restart these events):
{context_so_far}

Target Scenes for THIS Act: {target_scenes} (~{target_words_per_act} words).
Write ALL {target_scenes} Scenes."""

        raw_output = self.call_llm(prompt, system_prompt)

        if isinstance(raw_output, str):
            try:
                raw_output = json.loads(raw_output)
            except Exception as e:
                log.error(f"Failed to parse Scriptwriter Act LLM JSON: {e}")
                raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        if not isinstance(raw_output, list):
            if isinstance(raw_output, dict) and "scenes" in raw_output:
                raw_output = raw_output["scenes"]
            else:
                raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        print(f"[*] ScriptwriterAgent: Act {act_number} ({len(raw_output)} scenes) completed!")
        return raw_output

