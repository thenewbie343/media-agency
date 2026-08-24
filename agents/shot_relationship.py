"""
Shot Relationship Engine & Cinematic Relational Grammar
Defines and enforces all 12 semantic Shot Relationships across shot transitions:
1. CONTINUATION
2. CONTRAST
3. CAUSE_TO_EFFECT
4. QUESTION_TO_ANSWER
5. DETAIL_TO_CONTEXT
6. CONTEXT_TO_DETAIL
7. BEFORE_TO_AFTER
8. EXPECTATION_TO_SUBVERSION
9. OBJECT_TO_PERSON
10. PERSON_TO_CONSEQUENCE
11. NUMBER_TO_SCALE
12. EVIDENCE_TO_REVEAL

Governs cinematographic continuity, scale progression, camera vector harmony,
density alternation, and cinematic restraint across the documentary timeline.
"""

from typing import Dict, Any, List, Optional, Union
from .schema import ShotRelationship, VisualJob


class ShotRelationshipEngine:
    def __init__(self):
        self.sizes = ["extreme_wide", "wide", "medium", "medium_close", "close", "extreme_close"]
        self.motions = ["slow_push_in", "pan_left", "pan_right", "dolly_in", "dolly_out", "static"]

    def determine_and_enforce_relationship(
        self,
        prev_shot: Optional[Dict[str, Any]],
        current_shot: Dict[str, Any],
        next_intent: Optional[str] = None,
        sequence_plan: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Determines the appropriate ShotRelationship between prev_shot and current_shot
        and adjusts current_shot's cinematographic attributes to satisfy relational grammar.
        """
        if not prev_shot:
            current_shot["shot_relationship"] = ShotRelationship.CONTINUATION.value
            if current_shot.get("shot_size") not in ["establishing_shot", "wide", "extreme_wide", "medium"]:
                current_shot["shot_size"] = "wide"
            return current_shot

        prev_job = str(prev_shot.get("visual_job", ""))
        curr_job = str(current_shot.get("visual_job", ""))
        prev_size = str(prev_shot.get("shot_size", "medium"))
        curr_size = str(current_shot.get("shot_size", "medium"))
        prev_motion = str(prev_shot.get("camera_motion", "static"))
        prev_density = float(prev_shot.get("visual_density", 0.5))
        prev_type = str(prev_shot.get("visual_type", ""))
        curr_type = str(current_shot.get("visual_type", ""))

        # ─── 1. DEDUCE SEMANTIC RELATIONSHIP ───
        rel = current_shot.get("shot_relationship")
        
        if not rel or rel == ShotRelationship.CONTINUATION.value:
            # Rule A: NUMBER_TO_SCALE (Previous shot was a statistic or number callout)
            if (
                prev_job in [VisualJob.SHOW_SCALE.value, VisualJob.VISUALIZE_ABSTRACT_CONCEPT.value, "VISUALIZE_DATA", "SHOW_SCALE"]
                or prev_type == "text_stat"
                or (prev_shot.get("editorial_events") and any(e.get("type") == "NUMBER_REVEAL" for e in prev_shot.get("editorial_events", [])))
            ):
                rel = ShotRelationship.NUMBER_TO_SCALE

            # Rule B: EVIDENCE_TO_REVEAL (Archival document/log preceding smoking gun reveal)
            elif (
                prev_job in [VisualJob.SHOW_EVIDENCE.value, VisualJob.EXAMINE_EVIDENCE.value, "HIGHLIGHT_ANOMALY", "SHOW_EVIDENCE"]
                and curr_job in [VisualJob.REVEAL.value, VisualJob.REVEAL_DETAIL.value, VisualJob.PAYOFF.value, "REVEAL"]
            ):
                rel = ShotRelationship.EVIDENCE_TO_REVEAL

            # Rule C: OBJECT_TO_PERSON (Physical artifact -> human individual)
            elif (
                prev_job in [VisualJob.INTRODUCE_OBJECT.value, VisualJob.SHOW_EVIDENCE.value, "SHOW_OBJECT"]
                and curr_job in [VisualJob.INTRODUCE_CHARACTER.value, VisualJob.HUMANIZE.value, "SHOW_PERSON"]
            ):
                rel = ShotRelationship.OBJECT_TO_PERSON

            # Rule D: PERSON_TO_CONSEQUENCE (Decision-maker -> human fallout/victim consequence)
            elif (
                prev_job in [VisualJob.INTRODUCE_CHARACTER.value, VisualJob.ESCALATE.value, "SHOW_PERSON", "CREATE_TENSION"]
                and curr_job in [VisualJob.CONSEQUENCE.value, VisualJob.HUMANIZE.value, "CONSEQUENCE"]
            ):
                rel = ShotRelationship.PERSON_TO_CONSEQUENCE

            # Rule E: QUESTION_TO_ANSWER (Mystery/anomaly setup -> decisive clarification)
            elif (
                prev_job in [VisualJob.BUILD_MYSTERY.value, VisualJob.WITHHOLD_INFORMATION.value, "CREATE_MYSTERY"]
                and curr_job in [VisualJob.REVEAL.value, VisualJob.EXAMINE_EVIDENCE.value, VisualJob.REVEAL_DETAIL.value, "REVEAL"]
            ):
                rel = ShotRelationship.QUESTION_TO_ANSWER

            # Rule F: DETAIL_TO_CONTEXT (Macro/close shot widening to full environment)
            elif prev_size in ["close", "extreme_close"] and curr_size in ["wide", "extreme_wide", "establishing_shot"]:
                rel = ShotRelationship.DETAIL_TO_CONTEXT

            # Rule G: CONTEXT_TO_DETAIL (Wide establishing environment punching in to macro clue)
            elif prev_size in ["wide", "extreme_wide", "establishing_shot"] and curr_size in ["close", "extreme_close"]:
                rel = ShotRelationship.CONTEXT_TO_DETAIL

            # Rule H: CONTRAST (Dialectical thematic or visual conflict)
            elif curr_job == VisualJob.CONTRAST.value or prev_job == VisualJob.CONTRAST.value:
                rel = ShotRelationship.CONTRAST

            # Rule I: EXPECTATION_TO_SUBVERSION (Interruption or shock contradiction)
            elif curr_job in [VisualJob.INTERRUPT.value, VisualJob.WITHHOLD_INFORMATION.value]:
                rel = ShotRelationship.EXPECTATION_TO_SUBVERSION

            # Rule J: BEFORE_TO_AFTER (Historical baseline transitioning to transformation)
            elif (
                prev_job in [VisualJob.ESTABLISH_WORLD.value, VisualJob.RECONSTRUCT_EVENT.value]
                and curr_job in [VisualJob.CONSEQUENCE.value, VisualJob.PAYOFF.value]
            ):
                rel = ShotRelationship.BEFORE_TO_AFTER

            # Rule K: CAUSE_TO_EFFECT (Direct action leading to consequence)
            elif curr_job in [VisualJob.CONSEQUENCE.value, VisualJob.PAYOFF.value]:
                rel = ShotRelationship.CAUSE_TO_EFFECT

            else:
                rel = ShotRelationship.CONTINUATION

        # Normalize to enum value string
        rel_str = rel.value if isinstance(rel, ShotRelationship) else str(rel)
        current_shot["shot_relationship"] = rel_str

        # ─── 2. ENFORCE CINEMATOGRAPHIC RELATIONAL GRAMMAR ───

        if rel_str == ShotRelationship.DETAIL_TO_CONTEXT.value:
            current_shot["shot_size"] = "wide"
            current_shot["lens"] = "wide_angle_lens"
            current_shot["camera_motion"] = "slow_push_in"

        elif rel_str == ShotRelationship.CONTEXT_TO_DETAIL.value:
            current_shot["shot_size"] = "extreme_close"
            current_shot["lens"] = "macro_lens"
            current_shot["camera_motion"] = "static"

        elif rel_str == ShotRelationship.NUMBER_TO_SCALE.value:
            current_shot["shot_size"] = "wide"
            current_shot["lens"] = "wide_angle_lens"
            current_shot["camera_motion"] = "slow_push_in"
            current_shot["visual_density"] = 0.40  # Clear visual scale breathing room

        elif rel_str == ShotRelationship.EVIDENCE_TO_REVEAL.value:
            current_shot["camera_motion"] = "static"
            current_shot["is_restrained"] = True
            current_shot["shot_size"] = "close"
            current_shot["lens"] = "standard_lens"

        elif rel_str == ShotRelationship.QUESTION_TO_ANSWER.value:
            current_shot["camera_motion"] = "static"
            current_shot["is_restrained"] = True
            current_shot["visual_density"] = 0.45

        elif rel_str == ShotRelationship.PERSON_TO_CONSEQUENCE.value:
            current_shot["shot_size"] = "medium_close"
            current_shot["lens"] = "standard_lens"
            current_shot["visual_density"] = 0.35

        elif rel_str == ShotRelationship.OBJECT_TO_PERSON.value:
            current_shot["shot_size"] = "medium"
            current_shot["lens"] = "standard_lens"

        elif rel_str == ShotRelationship.EXPECTATION_TO_SUBVERSION.value:
            current_shot["camera_angle"] = "dutch_angle"
            current_shot["motion_intensity"] = 0.5
            current_shot["visual_density"] = 0.70

        elif rel_str == ShotRelationship.CAUSE_TO_EFFECT.value:
            current_shot["camera_motion"] = "slow_push_in"
            current_shot["visual_density"] = 0.40

        elif rel_str == ShotRelationship.CONTRAST.value:
            # Flip motion vector and visual density
            current_shot["camera_motion"] = "static" if prev_motion != "static" else "slow_push_in"
            current_shot["visual_density"] = 0.25 if prev_density >= 0.6 else 0.75

        elif rel_str == ShotRelationship.CONTINUATION.value:
            # Scale Progression: Prevent identical consecutive shot sizes
            curr_size_val = current_shot.get("shot_size", "medium")
            if curr_size_val == prev_size:
                if prev_size in ["medium", "medium_close"]:
                    current_shot["shot_size"] = "close" if curr_job in [VisualJob.HUMANIZE.value, VisualJob.EXAMINE_EVIDENCE.value] else "wide"
                elif prev_size in ["wide", "extreme_wide", "establishing_shot"]:
                    current_shot["shot_size"] = "close"
                else:
                    current_shot["shot_size"] = "medium"

            # Camera Vector Harmony: Prevent jarring opposing pans
            curr_motion_val = current_shot.get("camera_motion", "static")
            if prev_motion == "pan_right" and curr_motion_val == "pan_left":
                current_shot["camera_motion"] = "slow_push_in"
            elif prev_motion == "pan_left" and curr_motion_val == "pan_right":
                current_shot["camera_motion"] = "static"
            elif prev_motion == curr_motion_val and curr_motion_val != "static":
                current_shot["camera_motion"] = "static" if prev_motion == "slow_push_in" else "slow_push_in"

            # Density Alternation
            if prev_density >= 0.75:
                current_shot["visual_density"] = 0.25  # Breathing room
            elif prev_density <= 0.30 and curr_job in [VisualJob.VISUALIZE_ABSTRACT_CONCEPT.value, VisualJob.SHOW_SCALE.value]:
                current_shot["visual_density"] = 0.80

        return current_shot

    def enforce_triad_grammar(
        self,
        prev_shot: Optional[Dict[str, Any]],
        current_shot: Dict[str, Any],
        next_intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Backwards-compatible interface for triad grammar enforcement.
        Delegates to determine_and_enforce_relationship.
        """
        return self.determine_and_enforce_relationship(prev_shot, current_shot, next_intent=next_intent)
