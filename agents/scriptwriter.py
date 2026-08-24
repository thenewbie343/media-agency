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

        system_prompt = f"""You are the Lead Master Scriptwriter for high-end cinematic investigative YouTube documentaries (style of MagnatesMedia, Frontline, James Jani).
Your mission is to write an electrifying, authoritative script matching the 11-Phase Macro Narrative Arc and 30-90s Mini-Arc Engine for a {duration_minutes}-minute video.

CRITICAL HOOK ENGINE RULE (THE 20-30 SECOND WITHHOLDING LAW):
- SCENE 1 (THE OPENING 20-30s) MUST BE `narrative_intent: "HOOK"` and `mini_arc_phase: "SETUP"`.
- STRICT ANTI-CONTEXT MANDATE: You are STRICTLY FORBIDDEN from starting with biographical background, birthdates, company founding stories, or status quo summaries (e.g. NEVER write "X company was founded in 1985..." or "In the world of technology...").
- IMMEDIATE ANOMALY: The opening scene MUST present an immediate Question, Contradiction, Shock, Mystery, or Visual Anomaly before any context is revealed. Deliberately withhold background to create intense curiosity!

LANGUAGE & DRAMATIC PACING:
- `voiceover`: MUST BE IN NATURAL, DRAMATIC, PRECISE HINDI (Devanagari script), formatted for high-end neural TTS.
- STRATEGIC MICRO-PAUSES: Use ellipses (`...`) or em-dashes (`—`) with targeted restraint (1–2 times per scene):
  * Immediately before a key revelation, shocking fact, or anomaly (e.g. "और तब जांचकर्ताओं को दिखा... एक छोटी सी टाइपिंग की गलती।")
  * Immediately before a major financial or statistical scale (e.g. "लेकिन अकाउंट से गायब हो चुके थे — पूरे 81 मिलियन डॉलर।")
  * At the conclusion of an introductory hook or major narrative section before transitioning.
- `caption`: MUST BE the FULL Romanized Hinglish equivalent of the voiceover, to be displayed on screen as subtitles (CRITICAL: USE ENGLISH ALPHABET ONLY. NO DEVANAGARI. NO EMOJIS).

RULES:
1. MUST output EXACTLY {target_scenes} scenes.
2. DURATION & PACING CALIBRATION:
   - Target total video duration: {duration_minutes} minutes (~{target_words_total} total Hindi words).
   - Each `voiceover` MUST be approximately {target_words_per_scene} to {target_words_per_scene + 10} words (2-4 natural sentences).
   - Do NOT write overly long paragraphs that cause the video to exceed {duration_minutes} minutes.
3. NARRATIVE FLOW: Write a cohesive, dramatic investigation connecting facts through causal logic.
4. MACRO INTENT & MINI-ARC ASSIGNMENT:
   Every scene MUST specify its `narrative_intent` (one of: HOOK, CENTRAL_QUESTION, CONTEXT, FIRST_DISCOVERY, COMPLICATION, ESCALATION, REVELATION, CONSEQUENCE, DEEPER_REVELATION, FINAL_CONTRADICTION, PAYOFF)
   and its `mini_arc_phase` (one of: SETUP, BUILD, COMPLICATION, REVEAL, CONSEQUENCE).

Output JSON strictly matching this schema (an array of EXACTLY {target_scenes} scenes):
[
  {{
    "scene_number": 1,
    "narrative_intent": "HOOK",
    "mini_arc_phase": "SETUP",
    "purpose": "hook",
    "dramatic_tension": 0.85,
    "voiceover": "2007 में दुनिया का हर दूसरा स्मार्टफोन नोकिया का था। लेकिन सिर्फ पांच सालों के अंदर, ढाई सौ अरब डॉलर का यह साम्राज्य... पूरी तरह खाक हो गया।",
    "caption": "2007 mein duniya ka har doosra smartphone Nokia ka tha. Lekin sirf paanch saalon ke andar, dhai sau arab dollar ka yeh samrajya... poori tarah khaak ho gaya.",
    "visual_cue": "Extreme macro close-up of a cracked glowing Nokia blue screen",
    "withholding_element": "Withhold founding history to open purely on the sudden catastrophic collapse"
  }}
]"""

        prompt = f"""Documentary Research Package:
{json.dumps(research_pkg, indent=2)}

Macro Narrative Outline:
{json.dumps(outline_data, indent=2)}

Documentary Vision Directives:
{json.dumps(vision_data, indent=2) if vision_data else "Execute calibrated documentary pacing."}

Target Scenes: {target_scenes} ({duration_minutes} min, ~{target_words_total} words total).
Write ALL {target_scenes} Scenes."""

        raw_output = self.call_llm(prompt, system_prompt)

        if isinstance(raw_output, str):
            try:
                raw_output = json.loads(raw_output)
            except Exception as e:
                log.error(f"Failed to parse Scriptwriter LLM JSON: {e}")
                raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        if not isinstance(raw_output, list):
            if isinstance(raw_output, dict) and "scenes" in raw_output:
                raw_output = raw_output["scenes"]
            else:
                raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        print(f"[*] ScriptwriterAgent: {len(raw_output)} scenes generated successfully!")
        return raw_output

    def write_act(
        self,
        fact_sheet: Union[Dict[str, Any], str, DocumentaryResearchPackage],
        act_number: int,
        act_outline: Union[Dict[str, Any], str, List[Any]],
        vision: Optional[Union[Dict[str, Any], str, DocumentaryVision]] = None,
        target_scenes: int = 4,
        duration_minutes: int = 1,
        context_so_far: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Writes the voiceover & captions for a SINGLE act with calibrated pacing,
        enforcing macro narrative intents, mini-arcs, and opening hook withholding.
        """
        target_words_total = int(duration_minutes * 130)
        target_words_per_act = max(50, target_words_total // 3)
        target_words_per_scene = max(25, target_words_per_act // max(1, target_scenes))
        print(f"[*] ScriptwriterAgent writing Act {act_number} ({target_scenes} scenes, ~{target_words_per_act} words for Act {act_number})...")
        log.info(f"Writing Act {act_number}: {target_scenes} scenes, ~{target_words_per_act} words.")

        research_pkg = self._normalize_input(fact_sheet)
        outline_data = self._normalize_input(act_outline)
        vision_data = self._normalize_input(vision)

        hook_rule = ""
        if act_number == 1:
            hook_rule = """
CRITICAL HOOK ENGINE RULE (ACT 1 SCENE 1 WITHHOLDING LAW):
- SCENE 1 MUST BE `narrative_intent: "HOOK"` and `mini_arc_phase: "SETUP"`.
- STRICT ANTI-CONTEXT MANDATE: Absolutely NO biography, founding history, or status quo summaries in Scene 1.
- Open immediately on the core paradox, anomaly, or shock metric!"""

        system_prompt = f"""You are an elite Documentary Scriptwriter writing Act {act_number} of a 3-Act documentary.
{hook_rule}

LANGUAGE & DRAMATIC PACING:
- The `voiceover` MUST BE IN NATURAL, DRAMATIC HINDI (Devanagari script), optimized for neural TTS.
- STRATEGIC MICRO-PAUSES: Use ellipses (`...`) or em-dashes (`—`) with targeted restraint (1–2 times per scene):
  * Immediately before a key revelation, shocking fact, or anomaly (e.g. "और तब जांचकर्ताओं को दिखा... एक छोटी सी टाइपिंग की गलती।")
  * Immediately before a major financial or statistical scale (e.g. "लेकिन अकाउंट से गायब हो चुके थे — पूरे 81 मिलियन डॉलर।")
  * At the conclusion of an introductory hook or major narrative section before transitioning.
- The `caption` MUST BE the FULL Romanized Hinglish equivalent of the voiceover, to be displayed on screen as subtitles (CRITICAL: USE ENGLISH ALPHABET ONLY. NO DEVANAGARI. NO EMOJIS).

RULES:
1. MUST output EXACTLY {target_scenes} scenes for this Act.
2. DURATION & PACING CALIBRATION:
   - Target for Act {act_number}: ~{target_words_per_act} total Hindi words across {target_scenes} scenes.
   - Each `voiceover` MUST be approximately {target_words_per_scene} to {target_words_per_scene + 10} words (2-3 natural sentences).
   - Keep pacing tight and cinematic.
3. NARRATIVE FLOW & CONTINUITY:
   - Continue seamlessly from previous acts. Do NOT restart the story or re-introduce characters already explained in "Context from Previous Acts".
4. INTENTS & MINI-ARCS:
   - Each scene MUST include `narrative_intent` (e.g. HOOK, CENTRAL_QUESTION, CONTEXT, FIRST_DISCOVERY, COMPLICATION, ESCALATION, REVELATION, CONSEQUENCE, DEEPER_REVELATION, FINAL_CONTRADICTION, PAYOFF)
   - and `mini_arc_phase` (SETUP, BUILD, COMPLICATION, REVEAL, CONSEQUENCE).

Output JSON strictly matching this schema (an array of EXACTLY {target_scenes} scenes):
[
  {{
    "scene_number": 1,
    "narrative_intent": "HOOK",
    "mini_arc_phase": "SETUP",
    "purpose": "hook",
    "dramatic_tension": 0.85,
    "voiceover": "2007 में दुनिया का हर दूसरा स्मार्टफोन नोकिया का था। लेकिन सिर्फ पांच सालों के अंदर, ढाई सौ अरब डॉलर का यह साम्राज्य... पूरी तरह खाक हो गया।",
    "caption": "2007 mein duniya ka har doosra smartphone Nokia ka tha. Lekin sirf paanch saalon ke andar, dhai sau arab dollar ka yeh samrajya... poori tarah khaak ho gaya.",
    "visual_cue": "Macro shot of cracked Nokia screen",
    "withholding_element": "Withhold early origins"
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

