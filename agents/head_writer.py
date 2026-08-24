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

        system_prompt = f"""You are the Master Head Writer for authoritative, cinematic investigative YouTube documentaries (style of MagnatesMedia, James Jani, Vox, Johnny Harris).
Your task is to take a Deep Documentary Research Package and Documentary Vision, and construct a comprehensive Macro Narrative Arc Outline for a {duration_minutes}-minute film ({target_scenes} target scenes).

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

OUTPUT JSON STRUCTURE (STRICTLY REQUIRED):
{{
  "title_idea": "The Grand Title: The Subtitle",
  "title": "The Grand Title: The Subtitle",
  "documentary_thesis": "The central investigative argument...",
  "hook_strategy": {{
    "hook_type": "CONTRADICTION",
    "target_duration_seconds": 25.0,
    "anomaly_description": "Immediate shocking metric or contradiction...",
    "withholding_element": "What context is strictly withheld during the opening 25 seconds...",
    "opening_visual_cue": "Specific opening frame description..."
  }},
  "macro_narrative_arc": [
    {{"phase": "HOOK", "target_beat_index": 0, "narrative_goal": "...", "attention_target": 0.85, "key_evidence_or_reveal": "..."}},
    {{"phase": "CENTRAL_QUESTION", "target_beat_index": 1, "narrative_goal": "...", "attention_target": 0.75, "key_evidence_or_reveal": "..."}},
    {{"phase": "CONTEXT", "target_beat_index": 2, "narrative_goal": "...", "attention_target": 0.65, "key_evidence_or_reveal": "..."}},
    {{"phase": "FIRST_DISCOVERY", "target_beat_index": 3, "narrative_goal": "...", "attention_target": 0.80, "key_evidence_or_reveal": "..."}},
    {{"phase": "COMPLICATION", "target_beat_index": 4, "narrative_goal": "...", "attention_target": 0.75, "key_evidence_or_reveal": "..."}},
    {{"phase": "ESCALATION", "target_beat_index": 5, "narrative_goal": "...", "attention_target": 0.85, "key_evidence_or_reveal": "..."}},
    {{"phase": "REVELATION", "target_beat_index": 6, "narrative_goal": "...", "attention_target": 0.95, "key_evidence_or_reveal": "..."}},
    {{"phase": "CONSEQUENCE", "target_beat_index": 7, "narrative_goal": "...", "attention_target": 0.85, "key_evidence_or_reveal": "..."}},
    {{"phase": "DEEPER_REVELATION", "target_beat_index": 8, "narrative_goal": "...", "attention_target": 0.90, "key_evidence_or_reveal": "..."}},
    {{"phase": "FINAL_CONTRADICTION", "target_beat_index": 9, "narrative_goal": "...", "attention_target": 0.80, "key_evidence_or_reveal": "..."}},
    {{"phase": "PAYOFF", "target_beat_index": 10, "narrative_goal": "...", "attention_target": 0.90, "key_evidence_or_reveal": "..."}}
  ],
  "macro_phases": [
    {{"phase": "HOOK", "scene_number": 1, "description": "...", "mini_arc_phase": "SETUP"}},
    {{"phase": "CENTRAL_QUESTION", "scene_number": 2, "description": "...", "mini_arc_phase": "BUILD"}},
    {{"phase": "CONTEXT", "scene_number": 3, "description": "...", "mini_arc_phase": "COMPLICATION"}},
    {{"phase": "FIRST_DISCOVERY", "scene_number": 4, "description": "...", "mini_arc_phase": "REVEAL"}},
    {{"phase": "COMPLICATION", "scene_number": 5, "description": "...", "mini_arc_phase": "CONSEQUENCE"}},
    {{"phase": "ESCALATION", "scene_number": 6, "description": "...", "mini_arc_phase": "SETUP"}},
    {{"phase": "REVELATION", "scene_number": 7, "description": "...", "mini_arc_phase": "REVEAL"}},
    {{"phase": "CONSEQUENCE", "scene_number": 8, "description": "...", "mini_arc_phase": "CONSEQUENCE"}},
    {{"phase": "DEEPER_REVELATION", "scene_number": 9, "description": "...", "mini_arc_phase": "REVEAL"}},
    {{"phase": "FINAL_CONTRADICTION", "scene_number": 10, "description": "...", "mini_arc_phase": "COMPLICATION"}},
    {{"phase": "PAYOFF", "scene_number": 11, "description": "...", "mini_arc_phase": "PAYOFF"}}
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
      "key_evidence": "..."
    }},
    {{
      "scene_number": 2,
      "scene_desc": "...",
      "narrative_intent": "CENTRAL_QUESTION",
      "mini_arc_phase": "BUILD",
      "purpose": "question",
      "dramatic_tension": 0.75,
      "key_evidence": "..."
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
      "key_evidence": "..."
    }},
    {{
      "scene_number": 4,
      "scene_desc": "...",
      "narrative_intent": "REVELATION",
      "mini_arc_phase": "REVEAL",
      "purpose": "revelation",
      "dramatic_tension": 0.95,
      "key_evidence": "..."
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
      "key_evidence": "..."
    }},
    {{
      "scene_number": 6,
      "scene_desc": "...",
      "narrative_intent": "PAYOFF",
      "mini_arc_phase": "PAYOFF",
      "purpose": "payoff",
      "dramatic_tension": 0.90,
      "key_evidence": "..."
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


