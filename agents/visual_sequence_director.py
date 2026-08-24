"""
Visual Sequence Director Layer
Operates between EditorialBeat[] and Shot[] to formulate a VisualSequencePlan,
enforce the Anti-Literal Rule & Mute Test, and execute the No-Generic-B-Roll Fallback Cascade.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union

from .base_agent import BaseAgent
from .schema import (
    VisualSequencePlan,
    StoryBeat,
    VisualJob,
    ShotRelationship,
    NarrativeIntent,
    DocumentaryResearchPackage,
    DocumentaryVision
)

log = logging.getLogger(__name__)


class VisualSequenceDirector(BaseAgent):
    """
    Visual Sequence Director (R3).
    Formulates macro visual sequence strategy before individual shot asset selection,
    ensures sequences pass the Mute Test with dialectical visual arguments,
    and enforces the 5-stage No-Generic-B-Roll fallback cascade.
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
        """Provides a complete, schema-valid mock fallback for VisualSequencePlan."""
        return {
            "intention": "Dramatize systemic institutional breakdown through forensic paper trails and human consequence.",
            "visual_argument": "exponential_financial_flow vs human_vulnerability_and_denial",
            "withholding_strategy": "Withhold full smoking gun document until escalating transaction discrepancies establish high stakes.",
            "memorable_image": "Extreme macro close-up of a forged signature on official telex paper under harsh tungsten desk lamp.",
            "sequence_ending_statement": "Locked-off static frame on empty executive boardroom transitioning to irreversible aftermath.",
            "information_change": 0.80,
            "emotional_change": 0.75,
            "visual_change": 0.85,
            "scale_change": 0.65
        }

    def plan_visual_sequence(
        self,
        beat: Dict[str, Any],
        research_package: Optional[Union[Dict[str, Any], DocumentaryResearchPackage]] = None,
        vision: Optional[Union[Dict[str, Any], DocumentaryVision]] = None
    ) -> VisualSequencePlan:
        """
        Formulates a VisualSequencePlan for an entire story beat before shot decomposition.
        """
        intent = beat.get("narrative_intent", "EXPLANATION")
        if hasattr(intent, "value"):
            intent = intent.value
        desc = beat.get("description", "")
        blocks = beat.get("narration_blocks", [])
        combined_text = " ".join(
            [b.get("voiceover", "") + " " + b.get("caption", "") for b in blocks]
        ).strip()

        # Extract research and vision context
        pkg_dict = research_package.model_dump() if isinstance(research_package, DocumentaryResearchPackage) else (research_package or {})
        vision_dict = vision.model_dump() if isinstance(vision, DocumentaryVision) else (vision or {})

        topic = pkg_dict.get("topic") or vision_dict.get("core_premise") or "Cinematic Documentary"
        central_contradiction = pkg_dict.get("central_contradiction") or vision_dict.get("central_contradiction") or "public_facade vs hidden_reality"
        motifs = pkg_dict.get("visual_motifs") or vision_dict.get("visual_motifs") or []

        prompt = f"""You are the Visual Sequence Director for an elite cinematic documentary.
Formulate the overarching VisualSequencePlan for this story beat before any individual shots are generated.

TOPIC: {topic}
STORY BEAT:
- Narrative Intent: {intent}
- Beat Description: {desc}
- Combined Narration: {combined_text}
- Central Contradiction: {central_contradiction}
- Key Visual Motifs: {motifs}

DIRECTIVES (Master Documentary Director Standards):
1. intention: Define the overarching editorial intention of this sequence (what the audience must experience).
2. visual_argument: State the dialectical tension/contradiction (e.g. 'industry_value_growth vs animator_wage_stagnation', 'exponential_market_cap vs internal_system_decay').
3. withholding_strategy: How do we delay the central reveal to build anticipation rather than instantly illustrating words?
4. memorable_image: Describe ONE iconic, visually distinctive anchor shot representing the act's thesis.
5. sequence_ending_statement: Describe the final transitional visual statement leading into the next beat.
6. 4 Change Metrics (0.0 to 1.0):
   - information_change: rate of new forensic/narrative facts introduced
   - emotional_change: shift in tension/gravity
   - visual_change: diversity of visual framing and medium
   - scale_change: progression from micro detail to macro context (or reverse)

Return strictly valid JSON matching the VisualSequencePlan schema."""

        system = "You are an elite cinematic documentary director. Return strictly valid JSON."

        try:
            plan_dict = self.call_llm(prompt, system)
            if not isinstance(plan_dict, dict) or "visual_argument" not in plan_dict:
                raise ValueError("Incomplete LLM output for VisualSequencePlan")
            return VisualSequencePlan.model_validate(plan_dict)
        except Exception as e:
            log.warning(f"LLM visual sequence planning fell back to deterministic plan: {e}")
            return self._generate_deterministic_plan(intent, desc, combined_text, pkg_dict, vision_dict)

    def _generate_deterministic_plan(
        self,
        intent: str,
        desc: str,
        text: str,
        pkg: Dict[str, Any],
        vision: Dict[str, Any]
    ) -> VisualSequencePlan:
        """
        Generates a rich, context-aware, dialectical VisualSequencePlan deterministically.
        """
        intent_upper = str(intent).upper()
        topic = pkg.get("topic") or vision.get("core_premise") or "The Investigation"
        contradiction = pkg.get("central_contradiction") or "institutional_power vs human_vulnerability"
        motifs = pkg.get("visual_motifs") or ["official telex document", "ticking control room clock", "dimly lit trading floor"]
        selected_motif = motifs[0] if motifs else "forensic case file"

        # Dialectical Visual Arguments per Macro Intent Phase
        dialectics = {
            "HOOK": f"surface_normalcy vs impending_catastrophe ({contradiction})",
            "CENTRAL_QUESTION": "official_narrative vs undeniable_forensic_discrepancy",
            "CONTEXT": "architectural_grandeur vs foundational_instability",
            "FIRST_DISCOVERY": "routine_paperwork vs fatal_smoking_gun_detail",
            "COMPLICATION": "frictionless_automation vs human_operator_panic",
            "ESCALATION": "exponential_system_pressure vs crumbling_institutional_denial",
            "REVELATION": "concealed_mastermind_record vs unvarnished_evidence_exposure",
            "CONSEQUENCE": "abstract_financial_figures vs devastating_human_fallout",
            "DEEPER_REVELATION": "individual_scapegoat vs systemic_cultural_corruption",
            "FINAL_CONTRADICTION": "colossal_superficial_wealth vs hollowed_core_aftermath",
            "PAYOFF": "historical_oblivion vs permanent_structural_lesson",
            "EVIDENCE": "official_press_release vs unredacted_audit_logs",
            "CONFLICT": "escalating_system_pressure vs desperate_containment",
            "MYSTERY": "known_anomalies vs unidentified_covert_operators",
            "EXPLANATION": "abstract_technical_mechanism vs physical_chain_reaction",
            "RESOLUTION": "momentary_hubris vs permanent_silence"
        }

        visual_arg = dialectics.get(intent_upper, f"systemic_process vs real_world_consequence ({contradiction})")

        withholdings = {
            "HOOK": "Conceal the identity of the central subject; present only the visual anomaly and immediate aftermath.",
            "CENTRAL_QUESTION": "Present contradictory data logs before revealing the source of the investigation.",
            "CONTEXT": "Establish institutional scale before exposing the micro fracture in the infrastructure.",
            "FIRST_DISCOVERY": "Withhold full document page; focus on macro close-up of the single anomalous typo.",
            "COMPLICATION": "Show server alerts and operator reactions before revealing the failed failover protocol.",
            "ESCALATION": "Delay showing executive response; build tension through mounting transaction backlogs.",
            "REVELATION": "Hold frame on preceding silence before cutting to the unredacted classified memo.",
            "CONSEQUENCE": "Withhold corporate headquarters; show empty worker desks and foreclosed storefronts.",
            "DEEPER_REVELATION": "Conceal the final network diagram until every intermediary node has been exposed.",
            "FINAL_CONTRADICTION": "Juxtapose the celebratory launch footage with silent contemporary ruins.",
            "PAYOFF": "Linger on the symbolic motif in silence before delivering the final title card."
        }

        withholding = withholdings.get(
            intent_upper,
            "Conceal decisive evidence until preceding contextual framing establishes high stakes."
        )

        memorable_images = {
            "HOOK": f"High-contrast opening frame of {selected_motif} isolated under cold noir rim lighting in {topic}.",
            "CENTRAL_QUESTION": f"Forensic split-screen comparing official ledger against {selected_motif}.",
            "CONTEXT": f"Sweeping architectural low-angle establishing shot of {topic} headquarters at dusk.",
            "FIRST_DISCOVERY": f"Extreme macro lens pushing into the red-ink discrepancy on {selected_motif}.",
            "COMPLICATION": f"Close-up of trembling hands hovering over emergency terminal keys in {topic}.",
            "ESCALATION": f"Towering kinetic typography chart showing exponential divergence of {contradiction}.",
            "REVELATION": f"Locked-off static frame on unredacted confidential memo with bold black redactions.",
            "CONSEQUENCE": f"Haunting medium shot of an abandoned workstation illuminated only by a blinking error light.",
            "DEEPER_REVELATION": f"Cinematic network diagram revealing interconnected offshore shell entities.",
            "FINAL_CONTRADICTION": f"Archival photograph of triumphant founders juxtaposed against empty demolished factory.",
            "PAYOFF": f"Iconic static hold on {selected_motif} gathering dust in archived basement storage."
        }

        memorable = memorable_images.get(
            intent_upper,
            f"Visually distinctive anchor shot capturing {contradiction} in {desc[:50]}."
        )

        ending_statements = {
            "HOOK": "Sudden visual cut to black punctuated by anomalous audio cue.",
            "CENTRAL_QUESTION": "Static wide shot holding on the unanswered forensic discrepancy.",
            "CONTEXT": "Smooth camera tilt transitioning from skyward architecture to underground cables.",
            "FIRST_DISCOVERY": "Macro hold on the highlighted document discrepancy fading to next act.",
            "COMPLICATION": "Harsh cold rim lighting settling on the unresolved system error.",
            "ESCALATION": "Rapid cadence of data charts resolving into a tense locked-off hold.",
            "REVELATION": "Static 4-second hold on the smoking gun document in absolute silence.",
            "CONSEQUENCE": "Slow pull-back revealing human consequence across the landscape.",
            "DEEPER_REVELATION": "Visual shift from warm archival tones to cold contemporary noir.",
            "FINAL_CONTRADICTION": "Dual framing illustrating the permanent gulf between gain and loss.",
            "PAYOFF": "Long static hold on the central motif as room tone naturally decays."
        }

        ending_stmt = ending_statements.get(
            intent_upper,
            "Deliberate static frame on physical artifact transitioning to the next narrative phase."
        )

        # Dynamic Quality Change Metrics based on Intent
        info_change = 0.85 if intent_upper in ["FIRST_DISCOVERY", "REVELATION", "DEEPER_REVELATION"] else 0.70
        emo_change = 0.90 if intent_upper in ["HOOK", "REVELATION", "CONSEQUENCE", "PAYOFF"] else 0.65
        vis_change = 0.80 if intent_upper in ["HOOK", "COMPLICATION", "FINAL_CONTRADICTION"] else 0.75
        scale_change = 0.85 if intent_upper in ["CONTEXT", "ESCALATION", "CONSEQUENCE"] else 0.55

        return VisualSequencePlan(
            intention=f"Cinematically convey {intent.lower()} through dialectical progression: {desc[:70]}",
            visual_argument=visual_arg,
            withholding_strategy=withholding,
            memorable_image=memorable,
            sequence_ending_statement=ending_stmt,
            information_change=info_change,
            emotional_change=emo_change,
            visual_change=vis_change,
            scale_change=scale_change
        )

    def evaluate_mute_test(
        self,
        shots: List[Dict[str, Any]],
        sequence_plan: Optional[VisualSequencePlan] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether the visual sequence communicates its narrative argument when completely muted.
        Checks for:
        1. Narrative Arc Progression: Setup -> Development -> Climax/Consequence
        2. Visual Job Diversity (>= 2 distinct visual jobs)
        3. Rejection of Literal Clichés / Stock B-roll
        4. Presence of Visual Restraint / Holding Frames
        """
        if not shots:
            return {
                "mute_test_passed": False,
                "score": 0.0,
                "verdict": "FAILED",
                "reasons": ["No shots provided in sequence"]
            }

        jobs = [str(s.get("visual_job", "")) for s in shots]
        queries = [(s.get("visual_query") or s.get("ai_prompt") or "").lower() for s in shots]

        has_setup = any(
            j in [
                VisualJob.ESTABLISH_WORLD.value,
                VisualJob.INTRODUCE_CHARACTER.value,
                VisualJob.INTRODUCE_OBJECT.value,
                VisualJob.BUILD_MYSTERY.value,
                VisualJob.WITHHOLD_INFORMATION.value,
                VisualJob.SHOW_EVIDENCE.value,
                VisualJob.EXAMINE_EVIDENCE.value,
                "ESTABLISH_WORLD", "INTRODUCE_CHARACTER", "INTRODUCE_OBJECT", "BUILD_MYSTERY",
                "WITHHOLD_INFORMATION", "SHOW_EVIDENCE", "EXAMINE_EVIDENCE", "ESTABLISH"
            ] for j in jobs
        )

        has_development = any(
            j in [
                VisualJob.SHOW_EVIDENCE.value,
                VisualJob.EXAMINE_EVIDENCE.value,
                VisualJob.VISUALIZE_ABSTRACT_CONCEPT.value,
                VisualJob.SHOW_SCALE.value,
                VisualJob.SHOW_COMPARISON.value,
                VisualJob.RECONSTRUCT_EVENT.value,
                VisualJob.ESCALATE.value,
                VisualJob.CONTRAST.value,
                VisualJob.FOLLOW_OBJECT.value,
                "SHOW_EVIDENCE", "EXAMINE_EVIDENCE", "VISUALIZE_ABSTRACT_CONCEPT", "SHOW_SCALE",
                "SHOW_COMPARISON", "RECONSTRUCT_EVENT", "ESCALATE", "CONTRAST", "FOLLOW_OBJECT"
            ] for j in jobs
        )

        has_climax_or_consequence = any(
            j in [
                VisualJob.REVEAL.value,
                VisualJob.REVEAL_DETAIL.value,
                VisualJob.CONSEQUENCE.value,
                VisualJob.HUMANIZE.value,
                VisualJob.PAYOFF.value,
                VisualJob.INTERRUPT.value,
                "REVEAL", "REVEAL_DETAIL", "CONSEQUENCE", "HUMANIZE", "PAYOFF", "INTERRUPT"
            ] for j in jobs
        )

        # Check for literal cliché violations
        literal_violations = []
        for i, q in enumerate(queries):
            for banned in self.banned_literal_keywords:
                if banned in q:
                    literal_violations.append(f"Shot {i+1} contains banned cliché: '{banned}'")

        distinct_jobs = len(set(jobs))
        has_restraint = any(s.get("is_restrained", False) or s.get("camera_motion") == "static" for s in shots)

        # Calculate Mute Test Director Score (0.0 to 10.0)
        score = 4.0
        if has_setup:
            score += 2.0
        if has_development:
            score += 2.0
        if has_climax_or_consequence:
            score += 2.0
        if distinct_jobs >= 3:
            score += 1.0
        if has_restraint:
            score += 0.5
        if literal_violations:
            score -= (len(literal_violations) * 2.5)

        score = max(0.0, min(10.0, score))
        passed = (
            (has_setup or has_development)
            and (has_climax_or_consequence or (has_setup and has_development))
            and len(literal_violations) == 0
            and (distinct_jobs >= 2 or len(shots) == 1)
        )

        return {
            "mute_test_passed": passed,
            "score": round(score, 2),
            "verdict": "PASSED" if passed else "FAILED",
            "has_setup": has_setup,
            "has_development": has_development,
            "has_climax_or_consequence": has_climax_or_consequence,
            "distinct_visual_jobs": distinct_jobs,
            "has_restraint": has_restraint,
            "literal_violations": literal_violations
        }

    def is_literal_illustration(self, shot: Dict[str, Any], voiceover: str = "") -> bool:
        """
        Detects if a shot is a lazy, literal noun-matching cliché.
        """
        query = (shot.get("visual_query") or shot.get("ai_prompt") or "").lower()
        for banned in self.banned_literal_keywords:
            if banned in query:
                return True
        return False

    def apply_fallback_cascade(
        self,
        visual_job: Union[VisualJob, str],
        intent_info: Optional[Dict[str, Any]] = None,
        available_assets: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        No-Generic-B-Roll Fallback Cascade (5 Priority Levels):
        Level 1: Alternative Visual Interpretation (Metaphorical / forensic framing)
        Level 2: Motion Graphic Diagram (Kinetic data, map, timeline, typography)
        Level 3: AI Reconstruction (Period drama recreation, atmospheric reconstruction)
        Level 4: Archival Document (Authentic case file, telex, newspaper React fallback)
        Level 5: Generic B-roll (Strict last resort only, <15% of total documentary)
        """
        job_str = visual_job.value if isinstance(visual_job, VisualJob) else str(visual_job)
        info = intent_info or {}
        assets = available_assets or {}

        # ── Level 1: Alternative Visual Interpretation ──
        if (
            assets.get("has_metaphorical_photo")
            or job_str in [VisualJob.HUMANIZE.value, VisualJob.CONTRAST.value, "HUMANIZE", "CONTRAST"]
            or info.get("has_human_anchor")
        ):
            return {
                "cascade_level": 1,
                "strategy": "ALTERNATIVE_INTERPRETATION",
                "visual_type": "real_photo",
                "asset_provenance": "AUTHENTIC_PHOTO",
                "fallback_type": "PortraitCard",
                "priority_score": 1.0
            }

        # ── Level 2: Motion Graphic Diagram ──
        if (
            assets.get("can_render_diagram")
            or info.get("has_statistic")
            or info.get("has_process")
            or info.get("has_timestamp")
            or job_str in [
                VisualJob.SHOW_SCALE.value,
                VisualJob.SHOW_COMPARISON.value,
                VisualJob.VISUALIZE_ABSTRACT_CONCEPT.value,
                "SHOW_SCALE", "SHOW_COMPARISON", "VISUALIZE_ABSTRACT_CONCEPT"
            ]
        ):
            return {
                "cascade_level": 2,
                "strategy": "MOTION_GRAPHIC_DIAGRAM",
                "visual_type": "motion_graphics" if not info.get("has_statistic") else "text_stat",
                "asset_provenance": "MOTION_GRAPHIC",
                "fallback_type": "TechnicalDiagram" if not info.get("has_statistic") else "CinematicText",
                "priority_score": 0.9
            }

        # ── Level 3: AI Reconstruction ──
        if (
            assets.get("has_ai_generator")
            or info.get("has_cyber")
            or job_str in [
                VisualJob.RECONSTRUCT_EVENT.value,
                VisualJob.BUILD_MYSTERY.value,
                VisualJob.ESCALATE.value,
                "RECONSTRUCT_EVENT", "BUILD_MYSTERY", "ESCALATE"
            ]
        ):
            return {
                "cascade_level": 3,
                "strategy": "AI_RECONSTRUCTION",
                "visual_type": "ai_video" if job_str in [VisualJob.ESCALATE.value, "ESCALATE"] else "ai_image",
                "asset_provenance": "AI_RECONSTRUCTION",
                "fallback_type": "EvidenceBoard",
                "priority_score": 0.8
            }

        # ── Level 4: Archival Document ──
        if (
            assets.get("has_archival_doc")
            or info.get("has_anomaly")
            or info.get("has_evidence")
            or job_str in [
                VisualJob.SHOW_EVIDENCE.value,
                VisualJob.EXAMINE_EVIDENCE.value,
                VisualJob.REVEAL_DETAIL.value,
                VisualJob.REVEAL.value,
                VisualJob.PAYOFF.value,
                "SHOW_EVIDENCE", "EXAMINE_EVIDENCE", "REVEAL_DETAIL", "REVEAL", "PAYOFF"
            ]
        ):
            return {
                "cascade_level": 4,
                "strategy": "ARCHIVAL_DOCUMENT",
                "visual_type": "real_photo",
                "asset_provenance": "ARCHIVAL_FOOTAGE",
                "fallback_type": "ArchivalDocument" if not info.get("has_anomaly") else "ClassifiedFile",
                "priority_score": 0.7
            }

        # ── Level 5: Generic B-roll (Strict Last Resort) ──
        return {
            "cascade_level": 5,
            "strategy": "GENERIC_BROLL",
            "visual_type": "broll_video",
            "asset_provenance": "STOCK",
            "fallback_type": "PhotoWall",
            "priority_score": 0.3
        }
