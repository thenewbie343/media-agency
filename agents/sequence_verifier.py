"""
Sequence Verifier Engine (Part 2: Story + Scene Authoring)
Enforces the Final Scene Test, calculates per-shot information gain,
detects narrative and subject redundancies, and validates visual dialectic progression.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from agents.schema import Shot, EditorialScene, SequenceVerificationResult, VisualRequirement, HistoricalFidelity

log = logging.getLogger(__name__)


def _get_val(obj: Union[Dict[str, Any], Any], key: str, default: Any = None) -> Any:
    """Helper to get value from either dict or Pydantic model."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class SequenceVerifier:
    """
    Sequence Verifier Engine.
    Executes the Final Scene Test and Shot-to-Shot Relational Grammar Checks.
    """

    def verify_visual_sequence(
        self,
        scene: EditorialScene,
        shots: List[Union[Shot, Dict[str, Any]]],
        requirements: Optional[List[VisualRequirement]] = None
    ) -> SequenceVerificationResult:
        """
        Executes the Final Scene Test:
        1. Knowledge Delta: knowledge_after must be meaningfully different from knowledge_before.
        2. Viewer Inquiry: viewer_question must be present and non-trivial.
        3. Visual Dialectic: visual_argument must specify a dialectical tension ('vs').
        4. Information Gain: Each shot must have information_gain >= 0.2 (unless transitional/hold).
        5. Redundancy Detection: No consecutive unmotivated duplicate entities or visual concepts.
        6. Material Integrity: Banned generic stock footage on historical/evidence shots.
        """
        issues: List[str] = []
        passed = True
        redundancy_penalty = 0.0
        total_information_gain = 0.0

        # ── 1. Final Scene Test (Scene Level) ──
        if not scene.knowledge_before or not scene.knowledge_after:
            issues.append("Scene lacks defined knowledge_before and knowledge_after states.")
            passed = False
        elif scene.knowledge_before.strip().lower() == scene.knowledge_after.strip().lower():
            issues.append("Zero sequence-level knowledge delta: knowledge_after is identical to knowledge_before.")
            passed = False

        if not scene.viewer_question or len(scene.viewer_question.strip()) < 5:
            issues.append("Scene lacks an active viewer_question.")
            passed = False

        if not scene.visual_argument or "vs" not in scene.visual_argument.lower():
            issues.append("Scene visual_argument must define a dialectical tension (contain 'vs').")
            passed = False

        if not shots:
            issues.append("Sequence contains no shots.")
            return SequenceVerificationResult(
                passed=False,
                information_gain_score=0.0,
                redundancy_penalty=1.0,
                issues=issues
            )

        # ── 2. Shot-to-Shot Relational Dynamics & Information Gain ──
        previous_subjects = []
        previous_jobs = []

        for i, shot in enumerate(shots):
            shot_id = _get_val(shot, "shot_id", f"s_{i}")
            info_gain = float(_get_val(shot, "information_gain", 0.5))
            shot_role = str(_get_val(shot, "shot_role", "EXPLANATION"))
            total_information_gain += info_gain

            # Low information gain penalty
            if info_gain < 0.2 and shot_role not in ["TRANSITION", "HOLD"]:
                issues.append(f"Shot {shot_id} has insufficient information gain ({info_gain:.2f} < 0.20).")
                passed = False

            # Redundancy check: Repeated visual subject
            req = _get_val(shot, "visual_requirement")
            req_subject = _get_val(req, "subject_entity") if req else None
            vis_desc = str(_get_val(shot, "visual_description", _get_val(shot, "ai_prompt", "")))
            current_subject = req_subject or vis_desc[:30]

            if current_subject and current_subject in previous_subjects[-2:]:
                rel = _get_val(shot, "relationship_to_previous") or _get_val(shot, "shot_relationship")
                valid_relational_justifications = {
                    "CONTINUATION", "DETAIL_TO_CONTEXT", "CONTEXT_TO_DETAIL",
                    "CAUSE_TO_EFFECT", "BEFORE_TO_AFTER", "NUMBER_TO_SCALE",
                    "EVIDENCE_TO_REVEAL", "QUESTION_TO_ANSWER", "CONTRAST",
                    "EXPECTATION_TO_SUBVERSION", "OBJECT_TO_PERSON", "PERSON_TO_CONSEQUENCE"
                }
                rel_str = rel.value if hasattr(rel, "value") else str(rel).split(".")[-1] if rel else ""
                if not rel or (rel_str not in valid_relational_justifications and str(rel) not in valid_relational_justifications):
                    redundancy_penalty += 0.25
                    issues.append(f"Redundant subject '{current_subject}' in Shot {shot_id} without justified cinematic relationship.")
                    passed = False

            # Redundancy check: Consecutive identical visual jobs
            current_job = str(_get_val(shot, "visual_job", ""))
            if len(previous_jobs) >= 2 and previous_jobs[-1] == current_job and previous_jobs[-2] == current_job:
                redundancy_penalty += 0.20
                issues.append(f"Shot {shot_id} repeats VisualJob '{current_job}' three times consecutively.")
                passed = False

            # Material Integrity Check: No generic stock for historical requirements
            req_fidelity = _get_val(req, "historical_fidelity")
            if req_fidelity in [HistoricalFidelity.STRICT_ARCHIVAL, HistoricalFidelity.ERA_ACCURATE, "STRICT_ARCHIVAL", "ERA_ACCURATE"]:
                prov = _get_val(shot, "asset_provenance")
                vtype = _get_val(shot, "visual_type")
                if prov == "STOCK" and vtype == "broll_video":
                    issues.append(f"Shot {shot_id} uses generic stock B-roll for an ERA_ACCURATE requirement.")
                    passed = False

            previous_subjects.append(current_subject)
            previous_jobs.append(current_job)

        avg_information_gain = total_information_gain / max(1, len(shots))

        return SequenceVerificationResult(
            passed=passed and (redundancy_penalty < 0.5),
            information_gain_score=round(avg_information_gain, 3),
            redundancy_penalty=round(redundancy_penalty, 3),
            issues=issues
        )
