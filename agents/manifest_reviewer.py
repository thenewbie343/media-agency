"""
Manifest Reviewer Agent
Statically analyzes the generated ScriptManifest for editorial grammar, 17 cinematic QC metrics,
directorial constraints, camera motion diversity, and anachronisms.
"""

import logging
from typing import Dict, Any, List, Optional
from .cinematic_qc import CinematicQCEngine

log = logging.getLogger("agency")


class ManifestReviewerAgent:
    """
    Manifest Reviewer Agent (R6).
    Statically analyzes the generated ScriptManifest against editorial grammar,
    all 17 Cinematic Validation Metrics, and Directorial quality standards.
    """

    def __init__(self):
        self.qc_engine = CinematicQCEngine()

    def review_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs comprehensive static linting and 17-metric cinematic QC review.
        """
        log.info("[*] ManifestReviewer analyzing editorial grammar, constraints, and 17 QC metrics...")

        errors = []
        warnings = []

        if not isinstance(manifest, dict) or "story_beats" not in manifest:
            return {
                "status": "FAILED",
                "errors": ["Invalid manifest structure, missing story_beats."],
                "warnings": [],
                "director_score": 0.0,
                "director_verdict": "REJECT",
                "director_score_matrix": {},
                "validation_metrics": self.qc_engine._empty_metrics(),
                "metrics": {
                    "total_shots": 0,
                    "ai_video_count": 0,
                    "ai_video_percentage": 0.0
                }
            }

        all_shot_ids = set()
        shot_count = 0
        ai_video_count = 0
        prev_camera_motion = None
        consecutive_camera_motion = 0
        prev_cinematography = None
        consecutive_identical_shots = 0

        for beat in manifest.get("story_beats", []):
            if not isinstance(beat, dict):
                continue
            beat_has_reset = False
            for block in beat.get("narration_blocks", []):
                if not isinstance(block, dict):
                    continue
                shots = block.get("shots", [])

                if not shots:
                    errors.append(f"Block {block.get('block_id')} has no shots.")

                prev_size = None

                for shot in shots:
                    if not isinstance(shot, dict):
                        continue
                    shot_id = shot.get("shot_id")
                    if shot_id in all_shot_ids:
                        errors.append(f"DUPLICATE_ID: {shot_id}")
                    all_shot_ids.add(shot_id)
                    shot_count += 1

                    # 1. Grammar check: Shot Size & Reset
                    size = str(shot.get("shot_size", "")).lower()
                    shot_role = str(shot.get("shot_role", "")).upper()
                    if size in ["wide", "extreme_wide", "wide_shot", "extreme_wide_shot"] or shot_role in ["ESTABLISHING", "RESET"]:
                        beat_has_reset = True

                    if prev_size and size == prev_size and size not in ["n/a", "", "none"]:
                        warnings.append(f"GRAMMAR_WARNING: Consecutive {size} shots at {shot_id}.")
                    prev_size = size

                    # 2. AI Video strictness
                    v_type = str(shot.get("visual_type", "")).lower()
                    if v_type == "ai_video":
                        ai_video_count += 1
                        priority = float(shot.get("generation_priority", 0.5))
                        if priority < 0.8:
                            warnings.append(f"AI_VIDEO_WARNING: {shot_id} uses ai_video but has low priority {priority}. Consider fallback/stock.")

                    # 3. Cinematography Constraints
                    if v_type not in ["motion_graphics", "text_stat"]:
                        for field in ["shot_size", "camera_angle", "lens", "composition"]:
                            val = shot.get(field)
                            if not val or val == "N/A" or str(val).strip() == "":
                                errors.append(f"CINEMATOGRAPHY_FAIL: {shot_id} is missing required field '{field}' for visual_type '{v_type}'.")

                    # 4. Generic cut_reason check
                    cut_reason = str(shot.get("cut_reason") or "").strip().lower()
                    generic_reasons = {
                        "", "n/a", "none", "introduce_information", "show_fact", "transition",
                        "change_scene", "next_shot", "filler", "broll", "visual_variety",
                        "show_topic", "illustration", "show_visual"
                    }
                    if cut_reason in generic_reasons or len(cut_reason) < 6:
                        errors.append(f"GENERIC_CUT_REASON: {shot_id} uses generic or missing cut_reason '{cut_reason}'. Must be specific.")

                    # 5. Camera Motion Diversity Tracking
                    cm = str(shot.get("camera_motion", "none")).strip().lower()
                    if cm not in ["none", "static"]:
                        if prev_camera_motion == cm:
                            consecutive_camera_motion += 1
                        else:
                            consecutive_camera_motion = 1

                        if consecutive_camera_motion >= 3:
                            errors.append(f"CAMERA_MOTION_FATIGUE: {shot_id} and previous shots use '{cm}' too many times consecutively.")
                    else:
                        consecutive_camera_motion = 0

                    prev_camera_motion = cm

                    # 6. Exact Match 3-Shot Cinematography Tracking
                    current_cinematography = (cm, size, shot.get("camera_angle"))
                    if current_cinematography == prev_cinematography and cm not in ["none", "static"]:
                        consecutive_identical_shots += 1
                        if consecutive_identical_shots >= 3:
                            errors.append(f"IDENTICAL_CINEMATOGRAPHY: {shot_id} and previous 2 shots have identical size, angle, and motion.")
                    else:
                        consecutive_identical_shots = 1

                    prev_cinematography = current_cinematography

                    # 7. Anachronism basic check
                    cont = shot.get("continuity", {})
                    if isinstance(cont, dict):
                        start_year = cont.get("start_year")
                        end_year = cont.get("end_year")
                        if start_year and end_year:
                            try:
                                if int(start_year) > int(end_year):
                                    errors.append(f"ANACHRONISM: {shot_id} start_year {start_year} > end_year {end_year}")
                            except (ValueError, TypeError):
                                pass

            if not beat_has_reset and beat.get("narration_blocks"):
                warnings.append(f"RESET_SHOT_WARNING: StoryBeat {beat.get('beat_id', '')} lacks a wide or establishing reset shot.")

        if shot_count == 0:
            errors.append("MANIFEST_EMPTY: No shots generated.")

        ai_percentage = (ai_video_count / max(1, shot_count)) * 100
        if ai_percentage > 40:
            warnings.append(f"OVERUSE_OF_AI: {ai_percentage:.1f}% of shots are AI video. Suggest utilizing more documents/stock.")

        # Evaluate 17 Validation Metrics & Director Score Matrix
        director_eval = self.qc_engine.evaluate_manifest_director_score(manifest)
        validation_metrics = director_eval.get("validation_metrics", {})
        director_score = float(director_eval.get("overall_director_score", 0.0))
        director_verdict = director_eval.get("verdict", "REJECT")

        # Merge QC Engine Failures into errors/warnings
        for fail in director_eval.get("failures", []):
            if fail not in errors:
                errors.append(f"CINEMATIC_QC_FAIL: {fail}")

        for rec in director_eval.get("recommendations", []):
            if rec not in warnings:
                warnings.append(f"CINEMATIC_QC_REC: {rec}")

        # Check Director Score Threshold
        if director_score < 6.5 or director_verdict == "REJECT":
            if not any("CINEMATIC_QC_FAIL" in e for e in errors):
                errors.append(f"LOW_DIRECTOR_SCORE: Manifest director score {director_score}/10.0 below minimum threshold (Verdict: {director_verdict}).")
        elif director_score < 8.0:
            warnings.append(f"SUBOPTIMAL_DIRECTOR_SCORE: Manifest director score {director_score}/10.0 is below target 8.0/10.0.")

        # Determine Final Review Status
        if errors:
            status = "FAILED"
        elif warnings:
            status = "PASS_WITH_WARNINGS"
        else:
            status = "PASS"

        result = {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "director_score": director_score,
            "director_verdict": director_verdict,
            "director_score_matrix": director_eval.get("director_score_matrix", {}),
            "validation_metrics": validation_metrics,
            "metrics": {
                "total_shots": shot_count,
                "ai_video_count": ai_video_count,
                "ai_video_percentage": ai_percentage,
                "unique_visual_concepts": validation_metrics.get("number_of_unique_visual_concepts", 0),
                "visual_contrasts": validation_metrics.get("number_of_visual_contrasts", 0),
                "human_anchors": validation_metrics.get("number_of_human_anchor_moments", 0),
                "silence_moments": validation_metrics.get("number_of_silence_moments", 0),
                "sfx_per_minute": validation_metrics.get("sfx_per_minute", 0.0),
                "percentage_illustrative_shots": validation_metrics.get("percentage_illustrative_shots", 0.0)
            }
        }

        if errors:
            log.error(f"Manifest Review FAILED. {len(errors)} errors: {errors[0]}")
        else:
            log.info(f"Manifest Review PASSED. Director Score: {result['director_score']}/10.0 ({len(warnings)} warnings).")

        return result
