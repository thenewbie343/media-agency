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

  2. WORD WEIGHT & FLUID PACING:
     To give words gravity, write natural, flowing sentences. 
     DO NOT chop up your sentences with periods every 2 or 3 words! It breaks the TTS engine and makes the voiceover sound like a stammering robot.
     YES (Fluid & dramatic): "But that night, one man refused to press the button."
     NOT (Choppy & robotic): "But that night. One man. Refused to press the button."
     NOT (Stammering): "The loss... two hundred... billion dollars... gone."
  
  3. DRAMATIC PAUSES & STRATEGIC DASHES:
     - Use commas (,) for natural breathing within flowing sentences.
     - Use an em-dash (—) ONLY at critical, high-impact moments right before a major reveal, shocking number, or climax (1-2 per scene max).
       YES: "और वो दस्तावेज़ — तीस सालों तक छुपा रहा।"
       YES: "The lost document was classified — for thirty years."
     - Only use periods (.) at the actual end of a complete thought. Never force choppy 2-word stops.

4. RHYTHMIC PUNCH PATTERNS:
   Alternate between investigation sentences and brutal short punches:
   Long: "For three decades, the CIA had been running a covert operation across fourteen countries."
   Punch: "Nobody knew."
   Long: "The documents revealed payments totaling over forty million dollars to foreign officials."
   Punch: "Every single one — classified."

5. ONE-SENTENCE PARAGRAPHS FOR IMPACT:
   When you want maximum weight, give a sentence its own block:
   "He had twenty-three minutes."
   (Let that hang. Let the silence do the work.)

============================================================
BANNED PHRASES (INSTANT SCRIPT REJECTION)
============================================================
- "In the world of..."
- "Little did they know..."
- "Let's delve deeper..."
- "It's worth noting that..."
- "In a shocking turn of events..."
- "This begs the question..."
- "At the end of the day..."
- "The landscape of..."
- "Nestled in..."
- "Buckle up" / "Strap in"
- "Imagine..." as an opening
- "But here's the thing..." (overused)
- "Fast forward to..." (lazy transition)
- Any sentence that reads like a Wikipedia introduction

============================================================
VISCERAL SENSORY WRITING MANDATE
============================================================
Every scene MUST contain at least ONE:
- Physical sensation (cold sweat, trembling hands, the weight of a phone receiver)
- Environmental detail (fluorescent hum, ticking wall clock, distant sirens)
- Human internal state (his stomach dropped, her mind raced, he couldn't breathe)

============================================================
EMOTIONAL CURVE PER SCENE
============================================================
Every scene JSON must include:
- "viewer_emotion": What the viewer should FEEL (dread, curiosity, disbelief, rage, awe, relief)
- "vocal_intensity": How the narrator delivers this (whisper, measured, urgent, grave, explosive)
- "pacing_note": Speed guidance for TTS (slow_and_heavy, building, rapid_fire, dead_pause)

CRITICAL HOOK ENGINE RULE (THE 20-30 SECOND WITHHOLDING LAW):
- SCENE 1 (THE OPENING 20-30s) MUST BE `narrative_intent: "HOOK"` and `mini_arc_phase: "SETUP"`.
- STRICT ANTI-CONTEXT MANDATE: You are STRICTLY FORBIDDEN from starting with biographical background, birthdates, company founding stories, or status quo summaries.
- IMMEDIATE CRISIS: Open on the single most terrifying moment. The viewer must feel their pulse quicken within 5 seconds.

LANGUAGE RULES:
- `voiceover`: MUST BE IN NATURAL, DRAMATIC, PRECISE HINDI (Devanagari script), formatted for high-end neural TTS.
- Write Hindi the way Dhruv Rathee speaks — conversational, authoritative, with strategic pauses.
- `caption`: MUST BE the FULL Romanized Hinglish equivalent (ENGLISH ALPHABET ONLY. NO DEVANAGARI. NO EMOJIS).

RULES:
1. MUST output EXACTLY {target_scenes} scenes.
2. DURATION & PACING: {duration_minutes} minutes (~{target_words_total} total Hindi words). Each voiceover ~{target_words_per_scene} to {target_words_per_scene + 10} words.
3. NARRATIVE FLOW: Cohesive dramatic investigation with causal logic.
4. Every scene MUST specify `narrative_intent`, `mini_arc_phase`, `viewer_emotion`, `vocal_intensity`, and `pacing_note`.

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
    "voiceover": "26 September, 1983. Midnight. Moscow se 200 kilometer door, ek bunker mein — ek aadmi baitha tha. Uske saamne ek screen thi. Aur us screen pe... paanch nuclear missiles.",
    "caption": "26 September, 1983. Midnight. Moscow se 200 kilometer door, ek bunker mein — ek aadmi baitha tha. Uske saamne ek screen thi. Aur us screen pe... paanch nuclear missiles.",
    "visual_cue": "Dark bunker, single green CRT monitor casting eerie glow on a man's sweating face",
    "withholding_element": "Withhold who this man is and what he decided — maximum suspense"
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
You write like a fusion of Lemmino, MagnatesMedia, Dhruv Rathee, and HBO True Crime.
{hook_rule}

============================================================
DHRUV RATHEE / GAURAV THAKUR PACING MANDATE
============================================================
1. SENTENCE BREATHING: After every major statement, there is a natural breath.
   Write SHORT sentences. Then pause. Then deliver the next blow.
   NOT: "The system was designed by engineers in 1983 and it monitored satellite data for incoming nuclear threats using infrared sensors."
   YES: "1983. Soviet engineers built a system. One job — detect American nuclear missiles. The machine watched the sky. Day and night. Without blinking."

  2. WORD WEIGHT & FLUID PACING:
     To give words gravity, write natural, flowing sentences. 
     DO NOT chop up your sentences with periods every 2 or 3 words! It breaks the TTS engine and makes the voiceover sound like a stammering robot.
     YES (Fluid & dramatic): "But that night, one man refused to press the button."
     NOT (Choppy & robotic): "But that night. One man. Refused to press the button."
     NOT (Stammering): "The loss... two hundred... billion dollars... gone."
  
  3. DRAMATIC PAUSES & STRATEGIC DASHES:
     - Use commas (,) for natural breathing within flowing sentences.
     - Use an em-dash (—) ONLY at critical, high-impact moments right before a major reveal, shocking number, or climax (1-2 per scene max).
       YES: "और वो दस्तावेज़ — तीस सालों तक छुपा रहा।"
       YES: "The lost document was classified — for thirty years."
     - Only use periods (.) at the actual end of a complete thought. Never force choppy 2-word stops.

4. RHYTHMIC PUNCH PATTERNS:
   Alternate between investigation sentences and brutal short punches:
   Long: "For three decades, the CIA had been running a covert operation across fourteen countries."
   Punch: "Nobody knew."
   Long: "The documents revealed payments totaling over forty million dollars to foreign officials."
   Punch: "Every single one — classified."

5. ONE-SENTENCE PARAGRAPHS FOR IMPACT:
   When you want maximum weight, give a sentence its own block:
   "He had twenty-three minutes."
   (Let that hang. Let the silence do the work.)
  
  BANNED PHRASES: "In the world of", "Little did they know", "Let's delve deeper", "It's worth noting", "Buckle up", "Imagine...", "Fast forward to", Wikipedia-style introductions.
  
  ============================================================
  NATIVE SCRIPT MANDATE (CRITICAL FOR TTS ENGINES)
  ============================================================
  If the target language or topic is Hindi (or requested in Hinglish), you MUST output the voiceover text EXCLUSIVELY in the native Devanagari script (e.g., "मुंबई का सच" instead of "mumbai ka sach"). Do NOT write Hindi words using the English/Latin alphabet. Our TTS engine will read Latin characters with a heavy American accent. You must use native Devanagari characters so the Hindi voice model reads it natively. Do NOT use English loan words unless absolutely necessary. If you must use English words (like "Subscribe", "Channel", "Computer"), you MUST transliterate them into Devanagari script (e.g. "सब्सक्राइब", "चैनल", "कंप्यूटर"). There must be ZERO A-Z English characters in the voiceover field. Even the sign-off must be 100% Devanagari.

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


