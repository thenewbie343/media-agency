import json
import logging
from typing import Dict, Any, List, Optional, Union
from .base_agent import BaseAgent
from .schema import (
    DocumentaryResearchPackage,
    DocumentaryVision,
    HookStrategy,
    NarrativePhasePlan,
    MiniArcPlan,
    NarrativeIntent,
    MiniArcPhase,
)

log = logging.getLogger("agency")


class HeadWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    def write_outline(
        self,
        fact_sheet: Union[Dict[str, Any], str, DocumentaryResearchPackage],
        vision: Optional[Union[Dict[str, Any], str, DocumentaryVision]] = None,
        duration_minutes: int = 1,
        target_scenes: int = 8,
    ) -> Dict[str, Any]:
        """
        Drafts a Macro Narrative Outline executing the 11-phase arc and 30-90s mini-arcs,
        informed by the DocumentaryResearchPackage and DocumentaryVision.
        """
        print(f"[*] HeadWriterAgent drafting 11-Phase Macro Narrative Outline ({duration_minutes}m -> target {target_scenes} scenes)...")
        log.info(f"Drafting outline for {duration_minutes}m video with {target_scenes} target scenes.")

        # Normalize inputs
        research_pkg_data = fact_sheet
        if isinstance(fact_sheet, str):
            try:
                research_pkg_data = json.loads(fact_sheet)
            except Exception:
                research_pkg_data = {"topic": fact_sheet}
        elif hasattr(fact_sheet, "model_dump"):
            research_pkg_data = fact_sheet.model_dump()

        vision_data = vision
        if isinstance(vision, str):
            try:
                vision_data = json.loads(vision)
            except Exception:
                vision_data = None
        elif hasattr(vision, "model_dump"):
            vision_data = vision.model_dump()

        system_prompt = f"""You are the Master Head Writer for visceral, emotionally devastating investigative YouTube documentaries.
You are NOT an encyclopedia. You are NOT a textbook. You are a psychological warfare architect who engineers viewer addiction through DRAMATIC HUMAN STORIES.

Your style fuses:
- Lemmino / MagnatesMedia: Character-first stakes, dramatic irony, sensory immersion
- Vox / Johnny Harris: Curiosity loops, forensic hypothesis-testing, punchy inquisition
- Netflix / HBO True Crime: Atmospheric suspense, psychological dread, extended silences
- Dhruv Rathee / Gaurav Thakur: Conversational authority, weight on pivotal words, measured pacing

============================================================
THE 5-BEAT PSYCHOLOGICAL RETENTION BLUEPRINT (MANDATORY)
============================================================

Every documentary MUST follow this exact emotional architecture:

BEAT 1 — COLD ANOMALY HOOK (First 20-30s):
- Open on the SINGLE most terrifying, shocking, or impossible moment of the story.
- ZERO biography. ZERO founding history. ZERO "In the world of..." context.
- The viewer must feel: "WHAT? How is this possible?"
- Example: "26 September 1983. Midnight. A Soviet officer stares at his screen. Five nuclear missiles are heading toward Moscow. He has 23 minutes to decide if humanity lives or dies."

BEAT 2 — THE HIDDEN PARADOX (20-45s):
- Reveal the gap between what the public believed and the horrifying reality.
- Create cognitive dissonance: "Everyone thought X... but the truth was Y."
- The viewer must feel: "Wait, I was wrong about this my whole life?"

BEAT 3 — FORENSIC ESCALATION (45-70s):
- Drip-feed evidence, documents, and escalating stakes.
- Each new fact must make the situation MORE dangerous, MORE urgent, MORE personal.
- Build a curiosity loop: answer one question, immediately pose a bigger one.
- The viewer must feel: "This is worse than I thought."

BEAT 4 — THE SILENT CLIMAX (70-85s):
- The moment of maximum tension where everything hangs in the balance.
- Music drops to dead silence. A heartbeat. A ticking clock.
- One person. One decision. One moment that changes everything.
- The viewer must feel their chest tighten.

BEAT 5 — PHILOSOPHICAL PAYOFF (85-90s):
- NOT a summary. NOT a recap.
- A universal truth that haunts the viewer after the video ends.
- A lingering image. A question with no easy answer.
- The viewer must feel: "I need to think about this."

============================================================
VISCERAL WRITING MANDATES (ANTI-AI-SLOP RULES)
============================================================

BANNED PHRASES (INSTANT REJECTION IF USED):
- "In the world of..."
- "Little did they know..."
- "Let's delve deeper..."
- "It's worth noting that..."
- "In a shocking turn of events..."
- "This begs the question..."
- "At the end of the day..."
- "It goes without saying..."
- "The landscape of..."
- "Nestled in..."
- Any variation of "buckle up" or "strap in"
- Any sentence starting with "Imagine..."

MANDATORY WRITING RULES:
1. SENSORY DETAILS: Every scene description must include at least ONE physical sensation (the hum of fluorescent lights, the weight of a telephone receiver, the smell of printer ink).
2. RHYTHMIC PUNCH: Alternate between long investigative sentences and brutal 1-3 word dramatic punches. Example: "The document was 847 pages long. Every single page was a lie."
3. HUMAN STAKES: Every abstract concept (economy, policy, technology) MUST be anchored to a specific human being with a name, a face, and something to lose.
4. DRAMATIC IRONY: The outline must identify at least 2 moments where the audience knows something the characters don't.
5. WITHHOLDING: Identify the single most important piece of information and specify EXACTLY when it should be revealed (not before Beat 4).

THE 11-PHASE MACRO NARRATIVE ARC (MANDATORY SEQUENCE):
1. `HOOK` (First 20-30s): Shock, anomaly, paradox, or visual contradiction. STRICT ANTI-CONTEXT RULE: Absolutely NO biography, founding backstory, or status quo summary.
2. `CENTRAL_QUESTION`: Explicitly articulate the core investigative mystery or central inquiry.
3. `CONTEXT`: Essential historical, economic, or technological backdrop explaining the world before the fracture.
4. `FIRST_DISCOVERY`: The first tangible piece of evidence, classified log, or early anomaly exposed.
5. `COMPLICATION`: Initial assumptions break down; friction, technical roadblocks, or mounting flaws emerge.
6. `ESCALATION`: The stakes multiply, competition closes in, institutional denial turns into panic.
7. `REVELATION`: The smoking-gun document, covert memo, or pivotal revelation exposed to light.
8. `CONSEQUENCE`: The immediate catastrophe, market collapse, indictment, or operational breakdown.
9. `DEEPER_REVELATION`: The systemic, cultural, or human rot beneath the individual crisis.
10. `FINAL_CONTRADICTION`: The unresolved paradox, haunting irony, or systemic double-standard.
11. `PAYOFF`: The lasting philosophical verdict, moral resonance, and final lingering image.

THE 30-90s MINI-ARC ENGINE:
Every scene cluster within each act must progress through 5 mini-arc dramatic phases:
- `SETUP`: Grounding circumstance and initial status.
- `BUILD`: Accumulating evidence and forward acceleration.
- `COMPLICATION`: Tension spike, unexpected flaw, or anomaly.
- `REVEAL`: The decisive discovery or payoff.
- `CONSEQUENCE`: The emotional and systemic aftermath transitioning into the next beat.

EMOTIONAL CURVE REQUIREMENT:
Each scene in the outline MUST specify:
- `viewer_emotion`: What the viewer should FEEL at this moment (dread, curiosity, disbelief, relief, rage, awe).
- `sensory_anchor`: One specific physical detail that grounds this scene (a sound, a texture, a temperature).
- `dramatic_irony_note`: What does the audience know that the subject doesn't? (null if not applicable)

OUTPUT JSON STRUCTURE (STRICTLY REQUIRED):
{{
  "title_idea": "The Grand Title: The Subtitle",
  "title": "The Grand Title: The Subtitle",
  "documentary_thesis": "The central investigative argument...",
  "emotional_throughline": "The dominant emotional journey: from X to Y",
  "hook_strategy": {{
    "hook_type": "CONTRADICTION",
    "target_duration_seconds": 25.0,
    "anomaly_description": "Immediate shocking metric or contradiction...",
    "withholding_element": "What context is strictly withheld during the opening 25 seconds...",
    "opening_visual_cue": "Specific opening frame description...",
    "sensory_detail": "The physical sensation that opens the film"
  }},
  "macro_narrative_arc": [
    {{"phase": "HOOK", "target_beat_index": 0, "narrative_goal": "...", "attention_target": 0.85, "key_evidence_or_reveal": "...", "viewer_emotion": "shock", "sensory_anchor": "..."}},
    {{"phase": "CENTRAL_QUESTION", "target_beat_index": 1, "narrative_goal": "...", "attention_target": 0.75, "key_evidence_or_reveal": "...", "viewer_emotion": "curiosity", "sensory_anchor": "..."}},
    {{"phase": "CONTEXT", "target_beat_index": 2, "narrative_goal": "...", "attention_target": 0.65, "key_evidence_or_reveal": "...", "viewer_emotion": "understanding", "sensory_anchor": "..."}},
    {{"phase": "FIRST_DISCOVERY", "target_beat_index": 3, "narrative_goal": "...", "attention_target": 0.80, "key_evidence_or_reveal": "...", "viewer_emotion": "intrigue", "sensory_anchor": "..."}},
    {{"phase": "COMPLICATION", "target_beat_index": 4, "narrative_goal": "...", "attention_target": 0.75, "key_evidence_or_reveal": "...", "viewer_emotion": "unease", "sensory_anchor": "..."}},
    {{"phase": "ESCALATION", "target_beat_index": 5, "narrative_goal": "...", "attention_target": 0.85, "key_evidence_or_reveal": "...", "viewer_emotion": "dread", "sensory_anchor": "..."}},
    {{"phase": "REVELATION", "target_beat_index": 6, "narrative_goal": "...", "attention_target": 0.95, "key_evidence_or_reveal": "...", "viewer_emotion": "disbelief", "sensory_anchor": "..."}},
    {{"phase": "CONSEQUENCE", "target_beat_index": 7, "narrative_goal": "...", "attention_target": 0.85, "key_evidence_or_reveal": "...", "viewer_emotion": "devastation", "sensory_anchor": "..."}},
    {{"phase": "DEEPER_REVELATION", "target_beat_index": 8, "narrative_goal": "...", "attention_target": 0.90, "key_evidence_or_reveal": "...", "viewer_emotion": "rage", "sensory_anchor": "..."}},
    {{"phase": "FINAL_CONTRADICTION", "target_beat_index": 9, "narrative_goal": "...", "attention_target": 0.80, "key_evidence_or_reveal": "...", "viewer_emotion": "bitter_irony", "sensory_anchor": "..."}},
    {{"phase": "PAYOFF", "target_beat_index": 10, "narrative_goal": "...", "attention_target": 0.90, "key_evidence_or_reveal": "...", "viewer_emotion": "haunted_reflection", "sensory_anchor": "..."}}
  ],
  "macro_phases": [
    {{"phase": "HOOK", "scene_number": 1, "description": "...", "mini_arc_phase": "SETUP", "viewer_emotion": "shock", "sensory_anchor": "..."}},
    {{"phase": "CENTRAL_QUESTION", "scene_number": 2, "description": "...", "mini_arc_phase": "BUILD", "viewer_emotion": "curiosity", "sensory_anchor": "..."}},
    {{"phase": "CONTEXT", "scene_number": 3, "description": "...", "mini_arc_phase": "COMPLICATION", "viewer_emotion": "understanding", "sensory_anchor": "..."}},
    {{"phase": "FIRST_DISCOVERY", "scene_number": 4, "description": "...", "mini_arc_phase": "REVEAL", "viewer_emotion": "intrigue", "sensory_anchor": "..."}},
    {{"phase": "COMPLICATION", "scene_number": 5, "description": "...", "mini_arc_phase": "CONSEQUENCE", "viewer_emotion": "unease", "sensory_anchor": "..."}},
    {{"phase": "ESCALATION", "scene_number": 6, "description": "...", "mini_arc_phase": "SETUP", "viewer_emotion": "dread", "sensory_anchor": "..."}},
    {{"phase": "REVELATION", "scene_number": 7, "description": "...", "mini_arc_phase": "REVEAL", "viewer_emotion": "disbelief", "sensory_anchor": "..."}},
    {{"phase": "CONSEQUENCE", "scene_number": 8, "description": "...", "mini_arc_phase": "CONSEQUENCE", "viewer_emotion": "devastation", "sensory_anchor": "..."}},
    {{"phase": "DEEPER_REVELATION", "scene_number": 9, "description": "...", "mini_arc_phase": "REVEAL", "viewer_emotion": "rage", "sensory_anchor": "..."}},
    {{"phase": "FINAL_CONTRADICTION", "scene_number": 10, "description": "...", "mini_arc_phase": "COMPLICATION", "viewer_emotion": "bitter_irony", "sensory_anchor": "..."}},
    {{"phase": "PAYOFF", "scene_number": 11, "description": "...", "mini_arc_phase": "PAYOFF", "viewer_emotion": "haunted_reflection", "sensory_anchor": "..."}}
  ],
  "mini_arcs": [
    {{
      "beat_id": "b001",
      "time_window": "0:00 - 0:45",
      "setup": "...",
      "build": "...",
      "complication": "...",
      "reveal": "...",
      "consequence": "..."
    }}
  ],
  "act_1_the_hook_and_rise": [
    {{
      "scene_number": 1,
      "scene_desc": "...",
      "narrative_intent": "HOOK",
      "mini_arc_phase": "SETUP",
      "purpose": "hook",
      "dramatic_tension": 0.85,
      "key_evidence": "...",
      "viewer_emotion": "shock",
      "sensory_anchor": "...",
      "dramatic_irony_note": null
    }}
  ],
  "act_2_the_conflict": [
    {{
      "scene_number": 3,
      "scene_desc": "...",
      "narrative_intent": "COMPLICATION",
      "mini_arc_phase": "COMPLICATION",
      "purpose": "the problem",
      "dramatic_tension": 0.80,
      "key_evidence": "...",
      "viewer_emotion": "unease",
      "sensory_anchor": "...",
      "dramatic_irony_note": "..."
    }}
  ],
  "act_3_the_fall_and_stakes": [
    {{
      "scene_number": 5,
      "scene_desc": "...",
      "narrative_intent": "CONSEQUENCE",
      "mini_arc_phase": "CONSEQUENCE",
      "purpose": "consequence",
      "dramatic_tension": 0.85,
      "key_evidence": "...",
      "viewer_emotion": "devastation",
      "sensory_anchor": "...",
      "dramatic_irony_note": null
    }}
  ]
}}"""

        prompt = f"""Documentary Research Package:
{json.dumps(research_pkg_data, indent=2)}

Documentary Vision Directives:
{json.dumps(vision_data, indent=2) if vision_data else "Formulate narrative outline directly from research package."}

Target Duration: {duration_minutes} min ({target_scenes} total scenes).
Generate the 11-Phase Macro Narrative Outline JSON."""

        raw_output = self.call_llm(prompt, system_prompt)

        if isinstance(raw_output, str):
            try:
                raw_output = json.loads(raw_output)
            except Exception as e:
                log.error(f"Failed to parse HeadWriter LLM JSON: {e}")
                raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        if not isinstance(raw_output, dict):
            raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        # Ensure backward-compatible act keys exist
        if "acts" in raw_output:
            acts_list = raw_output.get("acts", [])
            for act in acts_list:
                num = act.get("act_number", 1)
                scenes = act.get("scenes", [])
                if num == 1 and "act_1_the_hook_and_rise" not in raw_output:
                    raw_output["act_1_the_hook_and_rise"] = scenes
                elif num == 2 and "act_2_the_conflict" not in raw_output:
                    raw_output["act_2_the_conflict"] = scenes
                elif num == 3 and "act_3_the_fall_and_stakes" not in raw_output:
                    raw_output["act_3_the_fall_and_stakes"] = scenes

        if "act_1_the_hook_and_rise" not in raw_output and "act_1" in raw_output:
            raw_output["act_1_the_hook_and_rise"] = raw_output["act_1"]
        if "act_2_the_conflict" not in raw_output and "act_2" in raw_output:
            raw_output["act_2_the_conflict"] = raw_output["act_2"]
        if "act_3_the_fall_and_stakes" not in raw_output and "act_3" in raw_output:
            raw_output["act_3_the_fall_and_stakes"] = raw_output["act_3"]

        print("[*] HeadWriterAgent: 11-Phase Macro Narrative Outline successfully generated!")
        return raw_output


