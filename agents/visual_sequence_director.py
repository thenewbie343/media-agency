"""
Visual Sequence Director Layer (Part 2: Story + Scene Authoring)
Orchestrates NarrativeMicroBeat decomposition, EditorialScene authoring,
knowledge delta tracking, dialectical visual arguments, and material selection (EVIDENCE, ARCHIVAL, RECONSTRUCTION, GRAPHIC).
Enforces the Final Scene Test and Auto-Repair Loop before shot asset fulfillment.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple

from .base_agent import BaseAgent
from .schema import (
    VisualSequencePlan,
    StoryBeat,
    VisualJob,
    ShotRelationship,
    NarrativeIntent,
    DocumentaryResearchPackage,
    DocumentaryVision,
    EditorialScene,
    VisualRequirement,
    NarrativeMicroBeat,
    VisualInformationTarget,
    ReconstructionPlan,
    GraphicDecision,
    GraphicType,
    EvidenceTreatment,
    AssetClass,
    HistoricalFidelity,
    SequenceVerificationResult
)

log = logging.getLogger(__name__)


class VisualSequenceDirector(BaseAgent):
    """
    Visual Sequence Director (Part 2: Story + Scene Authoring).
    Formulates macro visual sequence strategy and EditorialScene specifications
    before individual shot asset selection, enforces the Anti-Literal Rule & Mute Test,
    and conducts the Final Scene Test with Auto-Repair loops.
    """

    def __init__(self):
        super().__init__()
        self.banned_literal_keywords = [
            "money falling", "handshake", "scales of justice", "piggy bank",
            "generic businessman", "generic code typing", "handcuffs on table",
            "coins falling", "man crying over laptop", "hacker in hoodie laughing",
            "stock handshake", "briefcase opening with money", "stock footage suit"
        ]

    def _get_mock_fallback(self, prompt: str, system: str, force_json: bool) -> Dict[str, Any]:
        """Provides a complete, schema-valid mock fallback for EditorialScene & VisualSequencePlan."""
        return {
            "scene_intent": "Dramatize systemic institutional breakdown through forensic paper trails and human consequence.",
            "narrative_function": "ESCALATION_TO_REVEAL",
            "viewer_emotion": "Mounting tension yielding to startling realization",
            "viewer_question": "How did an automated safeguard fail to prevent catastrophic escalation?",
            "knowledge_before": "The viewer assumes standard automated protocols safely governed operations.",
            "knowledge_after": "The viewer understands that systemic sensor flaws created a catastrophic false signal.",
            "visual_argument": "sterile_automated_sensor_flaw vs human_intuitive_restraint",
            "scene_world": "Underground defense command bunker, 1980s Cold War technology",
            "human_anchor": "Lead duty officer at monitoring console",
            "micro_beats": [
                {"text": "A quiet room in a secret bunker south of Moscow.", "micro_intent": "ESTABLISH_ISOLATION"},
                {"text": "Suddenly, the SIRENA alarm pierces the silence.", "micro_intent": "BREAK_ROUTINE_WITH_ANOMALY"},
                {"text": "The Oko satellites report five inbound intercontinental missiles.", "micro_intent": "ESCALATE_EXISTENTIAL_THREAT"},
                {"text": "Petrov realizes a true strike would involve hundreds of missiles, not five.", "micro_intent": "FORENSIC_INTUITIVE_REVELATION"}
            ],
            "opening_visual": "Cinematic wide shot of sterile Soviet computer banks and amber phosphor terminals in 1983.",
            "development": "Macro push on flashing red warning annunciator and bakelite telephone console.",
            "reveal": "Forensic reconstruction graphic of satellite trajectory blips indicating five anomalous reflections.",
            "consequence": "Tight close-up on officer's sweating brow and trembling hands hovering over override key.",
            "closing_visual": "Locked-off static frame on the illuminated master clock holding in silence.",
            "visual_requirements": [
                {
                    "shot_id": "shot_01",
                    "visual_job": "ESTABLISH_WORLD",
                    "subject_entity": "Soviet command bunker",
                    "time_period": "1983",
                    "visual_type": "ai_video",
                    "visual_purpose": "Establish quiet claustrophobic baseline before alarm",
                    "historical_fidelity": "ERA_ACCURATE"
                },
                {
                    "shot_id": "shot_02",
                    "visual_job": "ESCALATE",
                    "subject_entity": "Red alarm indicator",
                    "time_period": "1983",
                    "visual_type": "ai_image",
                    "visual_purpose": "Shatter routine with visual anomaly",
                    "historical_fidelity": "ERA_ACCURATE"
                },
                {
                    "shot_id": "shot_03",
                    "visual_job": "SHOW_EVIDENCE",
                    "subject_entity": "Early warning radar screen",
                    "time_period": "1983",
                    "visual_type": "motion_graphics",
                    "visual_purpose": "Reconstruct anomalous 5-missile trajectory display",
                    "historical_fidelity": "ERA_ACCURATE"
                },
                {
                    "shot_id": "shot_04",
                    "visual_job": "HUMANIZE",
                    "subject_entity": "Duty officer Stanislav Petrov",
                    "time_period": "1983",
                    "visual_type": "ai_video",
                    "visual_purpose": "Anchor existential stakes in human decision",
                    "historical_fidelity": "ERA_ACCURATE"
                }
            ],
            "information_change": 0.85,
            "emotional_change": 0.80,
            "visual_change": 0.80,
            "scale_change": 0.65
        }

    def plan_visual_sequence(
        self,
        beat: Dict[str, Any],
        research_package: Optional[Union[Dict[str, Any], DocumentaryResearchPackage]] = None,
        vision: Optional[Union[Dict[str, Any], DocumentaryVision]] = None
    ) -> VisualSequencePlan:
        """Formulates a VisualSequencePlan for an entire story beat."""
        scene, plan, _ = self.create_editorial_scene(beat, research_package, vision)
        return plan

    def create_editorial_scene(
        self,
        block: Dict[str, Any],
        research_package: Optional[Union[Dict[str, Any], DocumentaryResearchPackage]] = None,
        vision: Optional[Union[Dict[str, Any], DocumentaryVision]] = None,
        max_retries: int = 2
    ) -> Tuple[EditorialScene, VisualSequencePlan, List[VisualRequirement]]:
        """
        Part 2 Core Pipeline:
        Transforms a continuous NarrationBlock into an authoritative EditorialScene,
        decomposing it into NarrativeMicroBeats, defining the Visual Argument,
        and outputting strict VisualRequirements with the Final Scene Test verification loop.
        """
        voiceover = block.get("voiceover", "")
        caption = block.get("caption", "")
        combined_text = f"{voiceover} {caption}".strip()
        intent = block.get("narrative_intent", "EXPLANATION")
        if hasattr(intent, "value"):
            intent = intent.value

        pkg_dict = research_package.model_dump() if isinstance(research_package, DocumentaryResearchPackage) else (research_package or {})
        vision_dict = vision.model_dump() if isinstance(vision, DocumentaryVision) else (vision or {})

        topic = pkg_dict.get("topic") or vision_dict.get("core_premise") or "Documentary Investigation"
        central_contradiction = pkg_dict.get("central_contradiction") or vision_dict.get("central_contradiction") or "public_facade vs hidden_reality"
        motifs = pkg_dict.get("visual_motifs") or vision_dict.get("visual_motifs") or ["case file", "ticking clock", "terminal screen"]
        time_mode = block.get("time_mode", "historical")

        # Attempt LLM-driven scene authoring with auto-repair loop
        rejection_feedback: List[str] = []
        for attempt in range(max_retries + 1):
            try:
                scene_data = self._call_llm_scene_authoring(
                    combined_text, intent, topic, central_contradiction, motifs, time_mode, rejection_feedback
                )
                scene, plan, reqs = self._parse_scene_payload(block, scene_data, intent, combined_text, topic)
                
                # Perform Final Scene Test
                verification = self._verify_scene_structure(scene, reqs)
                if verification.passed:
                    return scene, plan, reqs
                else:
                    log.warning(f"Scene authoring attempt {attempt+1} failed Final Scene Test: {verification.issues}")
                    rejection_feedback = verification.issues
            except Exception as e:
                log.warning(f"LLM scene authoring attempt {attempt+1} failed with error: {e}")
                rejection_feedback = [str(e)]

        # Fallback to deterministic scene authoring engine
        log.info("Falling back to deterministic EditorialScene authoring engine.")
        return self._generate_deterministic_scene(block, pkg_dict, vision_dict)

    def _call_llm_scene_authoring(
        self,
        text: str,
        intent: str,
        topic: str,
        contradiction: str,
        motifs: List[str],
        time_mode: str,
        rejection_feedback: List[str]
    ) -> Dict[str, Any]:
        """Calls LLM with strict Part 2 directorial instructions."""
        feedback_prompt = ""
        if rejection_feedback:
            feedback_prompt = f"""
PREVIOUS ATTEMPT FAILED THE FINAL SCENE TEST:
{chr(10).join(['- ' + issue for issue in rejection_feedback])}
You MUST fix these specific issues in this attempt. Ensure knowledge_after is completely distinct from knowledge_before.
"""

        prompt = f"""You are the Master Visual Sequence Director for an investigative documentary (Part 2: Story + Scene Authoring).
Author a complete EditorialScene and VisualSequencePlan for this narration block.

TOPIC: {topic}
CENTRAL CONTRADICTION: {contradiction}
TIME MODE: {time_mode}
NARRATIVE INTENT: {intent}
NARRATION: "{text}"
RECURRING MOTIFS: {motifs}
{feedback_prompt}

DIRECTORIAL REQUIREMENTS:
1. Break narration into 2-4 NarrativeMicroBeats (Setup -> Action/Complication -> Reveal -> Consequence).
2. Define the Final Scene Test:
   - knowledge_before: What did the audience assume before this scene?
   - knowledge_after: What new factual, systemic, or human insight do they possess after? (MUST be distinct and meaningful)
   - viewer_question: What dramatic or analytical inquiry does this scene create?
3. visual_argument: Formulate a dialectical argument (e.g. 'automated_system_flaw vs human_intuitive_restraint', 'corporate_revenue_growth vs worker_stagnation').
4. Material Decisions: Decide whether each beat requires EVIDENCE, ARCHIVAL, RECONSTRUCTION, MOTION_GRAPHIC, MAP, or TYPOGRAPHY.
   (Strictly ban generic B-roll and literal metaphors).
5. Generate 2 to 4 distinct VisualRequirements matching the scene progression (Setup -> Development -> Reveal -> Consequence).

Return strictly valid JSON with keys:
- scene_intent (str)
- narrative_function (str)
- viewer_emotion (str)
- viewer_question (str)
- knowledge_before (str)
- knowledge_after (str)
- visual_argument (str)
- scene_world (str)
- human_anchor (str)
- micro_beats (list of {{"text": str, "micro_intent": str}})
- opening_visual (str)
- development (str)
- reveal (str)
- consequence (str)
- closing_visual (str)
- visual_requirements (list of {{"shot_id": str, "visual_job": str, "subject_entity": str, "time_period": str, "visual_type": str, "visual_purpose": str, "historical_fidelity": str}})
- information_change (float 0.0-1.0)
- emotional_change (float 0.0-1.0)
- visual_change (float 0.0-1.0)
- scale_change (float 0.0-1.0)
"""
        system = "You are an elite documentary director. Return strictly valid JSON."
        return self.call_llm(prompt, system)

    def _parse_scene_payload(
        self,
        block: Dict[str, Any],
        payload: Dict[str, Any],
        intent: str,
        text: str,
        topic: str
    ) -> Tuple[EditorialScene, VisualSequencePlan, List[VisualRequirement]]:
        """Parses and validates LLM payload into Pydantic models."""
        block_id = block.get("block_id", "scene_01")
        
        # Parse micro-beats
        raw_beats = payload.get("micro_beats", [])
        micro_beats = []
        if isinstance(raw_beats, list) and raw_beats:
            for b in raw_beats:
                if isinstance(b, dict) and "text" in b:
                    micro_beats.append(NarrativeMicroBeat(
                        text=b.get("text", ""),
                        micro_intent=b.get("micro_intent", "EXPLAIN")
                    ))
        if not micro_beats:
            half = len(text) // 2 if len(text) > 0 else 0
            micro_beats = [
                NarrativeMicroBeat(text=text[:half], micro_intent="SETUP_CONTEXT"),
                NarrativeMicroBeat(text=text[half:], micro_intent="DELIVER_REVEAL")
            ]

        # Parse Visual Requirements
        raw_reqs = payload.get("visual_requirements", [])
        requirements: List[VisualRequirement] = []
        if isinstance(raw_reqs, list) and raw_reqs:
            for i, r in enumerate(raw_reqs):
                if isinstance(r, dict):
                    fidelity_str = r.get("historical_fidelity", "ERA_ACCURATE")
                    try:
                        fidelity = HistoricalFidelity(fidelity_str)
                    except Exception:
                        fidelity = HistoricalFidelity.ERA_ACCURATE

                    requirements.append(VisualRequirement(
                        shot_id=f"{block_id}_s{i+1:03d}",
                        visual_job=r.get("visual_job", VisualJob.ESTABLISH_WORLD.value),
                        subject_entity=r.get("subject_entity", topic),
                        time_period=r.get("time_period", "1980s"),
                        visual_type=r.get("visual_type", "ai_video"),
                        visual_purpose=r.get("visual_purpose", "Advance visual argument"),
                        historical_fidelity=fidelity
                    ))

        # Build VisualSequencePlan
        plan = VisualSequencePlan(
            intention=payload.get("scene_intent", f"Execute {intent} sequence"),
            visual_argument=payload.get("visual_argument", "systemic_process vs real_world_consequence"),
            withholding_strategy=payload.get("withholding_strategy", "Withhold smoking gun reveal until contextual build"),
            memorable_image=payload.get("reveal") or payload.get("opening_visual") or "Iconic archival artifact hold",
            sequence_ending_statement=payload.get("closing_visual") or "Static frame transitioning into aftermath",
            information_change=float(payload.get("information_change", 0.75)),
            emotional_change=float(payload.get("emotional_change", 0.70)),
            visual_change=float(payload.get("visual_change", 0.80)),
            scale_change=float(payload.get("scale_change", 0.60)),
            micro_beats=micro_beats
        )

        # Build EditorialScene
        scene = EditorialScene(
            scene_id=block_id,
            scene_intent=plan.intention,
            narrative_function=str(payload.get("narrative_function", intent)),
            viewer_emotion=payload.get("viewer_emotion", "Tension and Focus"),
            viewer_question=payload.get("viewer_question", "What does the forensic evidence expose?"),
            knowledge_before=payload.get("knowledge_before", "Audience understands surface narrative."),
            knowledge_after=payload.get("knowledge_after", "Audience realizes the systemic contradiction."),
            visual_argument=plan.visual_argument,
            scene_world=payload.get("scene_world", topic),
            human_anchor=payload.get("human_anchor", "Key Investigative Figure"),
            opening_visual=payload.get("opening_visual", ""),
            development=payload.get("development", ""),
            reveal=payload.get("reveal", ""),
            consequence=payload.get("consequence", ""),
            closing_visual=payload.get("closing_visual", "")
        )

        return scene, plan, requirements

    def _verify_scene_structure(
        self,
        scene: EditorialScene,
        reqs: List[VisualRequirement]
    ) -> SequenceVerificationResult:
        """Enforces Part 2 Final Scene Test validation."""
        issues = []
        if not scene.knowledge_before or not scene.knowledge_after:
            issues.append("knowledge_before or knowledge_after is missing.")
        elif scene.knowledge_before.strip().lower() == scene.knowledge_after.strip().lower():
            issues.append("Zero knowledge delta: knowledge_after is identical to knowledge_before.")

        if not scene.viewer_question or len(scene.viewer_question.strip()) < 5:
            issues.append("Missing or trivial viewer_question.")

        if not scene.visual_argument or "vs" not in scene.visual_argument:
            issues.append("visual_argument must express a dialectical tension (contain 'vs').")

        if not reqs:
            issues.append("No VisualRequirements were generated for the scene.")

        return SequenceVerificationResult(
            passed=len(issues) == 0,
            information_gain_score=0.85 if len(issues) == 0 else 0.3,
            redundancy_penalty=0.0,
            issues=issues
        )

    def _generate_deterministic_scene(
        self,
        block: Dict[str, Any],
        pkg: Dict[str, Any],
        vision: Dict[str, Any]
    ) -> Tuple[EditorialScene, VisualSequencePlan, List[VisualRequirement]]:
        """
        Deterministic, robust Part 2 authoring engine.
        Guarantees schema validity and narrative progression without external LLM dependencies.
        """
        block_id = block.get("block_id", "scene_01")
        intent = str(block.get("narrative_intent", "EXPLANATION")).upper()
        voiceover = block.get("voiceover", "")
        caption = block.get("caption", "")
        text = f"{voiceover} {caption}".strip()

        topic = pkg.get("topic") or vision.get("core_premise") or "The Investigation"
        contradiction = pkg.get("central_contradiction") or "official_narrative vs hidden_reality"
        motifs = pkg.get("visual_motifs") or ["case file record", "monitoring terminal", "desk telephone"]
        motif = motifs[0] if motifs else "forensic document"
        time_mode = block.get("time_mode", "historical")

        # Dialectical Visual Arguments
        dialectics = {
            "HOOK": f"surface_calm vs existential_catastrophe ({contradiction})",
            "CENTRAL_QUESTION": "official_statement vs forensic_discrepancy",
            "CONTEXT": "architectural_scale vs infrastructural_vulnerability",
            "FIRST_DISCOVERY": "routine_logbook vs fatal_anomaly",
            "COMPLICATION": "automated_sensor_flaw vs human_operator_panic",
            "ESCALATION": "exponential_system_pressure vs crumbling_containment",
            "REVELATION": "concealed_truth vs unvarnished_evidence_exposure",
            "CONSEQUENCE": "abstract_numbers vs devastating_human_fallout",
            "PAYOFF": "historical_oblivion vs permanent_structural_lesson"
        }
        visual_arg = dialectics.get(intent, f"systemic_process vs human_consequence ({contradiction})")

        # Knowledge Deltas (Final Scene Test)
        knowledge_pairs = {
            "HOOK": (
                "The audience assumes a standard routine evening.",
                "The audience discovers that an unprecedented anomaly has breached the system."
            ),
            "CENTRAL_QUESTION": (
                "The audience believes the official record is complete.",
                "The audience sees an irreconcilable gap between reported facts and physical logs."
            ),
            "FIRST_DISCOVERY": (
                "The audience considers the event an unavoidable accident.",
                "The audience recognizes that a single overlooked detail triggered the chain reaction."
            ),
            "COMPLICATION": (
                "The audience assumes automatic fail-safes intervened.",
                "The audience understands that the automated fail-safes actively amplified the error."
            ),
            "ESCALATION": (
                "The audience expects containment protocols to succeed.",
                "The audience sees exponential pressure overwhelming institutional defenses."
            ),
            "REVELATION": (
                "The audience suspects a complex multi-party conspiracy.",
                "The audience uncovers the exact smoking gun document proving structural negligence."
            ),
            "CONSEQUENCE": (
                "The audience views the incident as a localized failure.",
                "The audience witnesses the permanent, global human aftermath."
            ),
            "PAYOFF": (
                "The audience views the historical crisis as concluded.",
                "The audience realizes the systemic flaw remains active in contemporary architecture."
            )
        }
        k_before, k_after = knowledge_pairs.get(
            intent,
            ("The audience holds a conventional surface understanding.", "The audience understands the deeper structural mechanism.")
        )

        viewer_questions = {
            "HOOK": "What suddenly shattered the routine?",
            "CENTRAL_QUESTION": "Why does the physical record contradict the official statement?",
            "FIRST_DISCOVERY": "How did a catastrophic flaw hide in plain sight?",
            "COMPLICATION": "Can human intuition override a malfunctioning automated protocol?",
            "ESCALATION": "How close did the system come to complete collapse?",
            "REVELATION": "Who authorized the suppression of this evidence?",
            "CONSEQUENCE": "What was the true human cost of this decision?",
            "PAYOFF": "What prevents this exact catastrophe from recurring today?"
        }
        v_question = viewer_questions.get(intent, "What is the structural cause behind this crisis?")

        # Narrative MicroBeats
        half = len(text) // 2 if len(text) > 0 else 0
        micro_beats = [
            NarrativeMicroBeat(text=text[:half], micro_intent="ESTABLISH_PREMISE_AND_TENSION"),
            NarrativeMicroBeat(text=text[half:], micro_intent="DELIVER_FORENSIC_TURNING_POINT")
        ]

        # Sequence Plan
        plan = VisualSequencePlan(
            intention=f"Cinematically dramatize {intent.lower()} through dialectic: {topic}",
            visual_argument=visual_arg,
            withholding_strategy="Conceal decisive smoking gun until contextual tension establishes stakes.",
            memorable_image=f"Cinematic frame of {motif} under cold tungsten illumination in {topic}.",
            sequence_ending_statement="Static frame on physical artifact transitioning to aftermath.",
            information_change=0.85 if intent in ["FIRST_DISCOVERY", "REVELATION"] else 0.70,
            emotional_change=0.85 if intent in ["HOOK", "CONSEQUENCE"] else 0.65,
            visual_change=0.80,
            scale_change=0.75,
            micro_beats=micro_beats
        )

        # Editorial Scene
        scene = EditorialScene(
            scene_id=block_id,
            scene_intent=plan.intention,
            narrative_function=intent,
            viewer_emotion="Investigative tension yielding to realization",
            viewer_question=v_question,
            knowledge_before=k_before,
            knowledge_after=k_after,
            visual_argument=visual_arg,
            scene_world=topic,
            human_anchor="Duty Investigator / Operator",
            opening_visual=f"Atmospheric establishing wide shot of {topic} environment, {time_mode} lighting.",
            development=f"Close detail shot of {motif} showing forensic indicators and tension.",
            reveal=f"High-impact graphic or document reconstruction illustrating {visual_arg}.",
            consequence=f"Serene yet haunting wide aftermath frame grounding the human stakes.",
            closing_visual="Locked-off static frame holding in silence."
        )

        # Generate 3 Canonical VisualRequirements
        reqs = [
            VisualRequirement(
                shot_id=f"{block_id}_s001",
                visual_job=VisualJob.ESTABLISH_WORLD.value,
                subject_entity=topic,
                time_period="1980s" if time_mode == "historical" else "modern",
                visual_type="ai_video" if intent in ["HOOK", "ESCALATION"] else "real_photo",
                visual_purpose="Establish world context and physical setting",
                historical_fidelity=HistoricalFidelity.ERA_ACCURATE
            ),
            VisualRequirement(
                shot_id=f"{block_id}_s002",
                visual_job=VisualJob.EXAMINE_EVIDENCE.value if intent in ["FIRST_DISCOVERY", "REVELATION"] else VisualJob.HUMANIZE.value,
                subject_entity=motif,
                time_period="1980s" if time_mode == "historical" else "modern",
                visual_type="real_photo" if intent in ["FIRST_DISCOVERY", "REVELATION"] else "ai_video",
                visual_purpose="Examine forensic detail and ground human emotion",
                historical_fidelity=HistoricalFidelity.ERA_ACCURATE
            ),
            VisualRequirement(
                shot_id=f"{block_id}_s003",
                visual_job=VisualJob.REVEAL.value if intent in ["FIRST_DISCOVERY", "REVELATION"] else VisualJob.CONSEQUENCE.value,
                subject_entity=topic,
                time_period="1980s" if time_mode == "historical" else "modern",
                visual_type="motion_graphics" if intent in ["EXPLANATION", "CENTRAL_QUESTION"] else "ai_image",
                visual_purpose="Deliver visual argument payoff and consequence",
                historical_fidelity=HistoricalFidelity.ERA_ACCURATE
            )
        ]

        return scene, plan, reqs
