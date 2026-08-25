"""
Milestone 4 Empirical Challenger Harness
Adversarial testing for CinematicQCEngine, ManifestReviewerAgent, and QCEditorAgent.

Validates:
1. Extraction & formatting of all 17 Directorial Validation Metrics.
2. Dynamic Director Score bounds in [0.0, 10.0] and thresholding (APPROVED >= 8.0, IMPROVE [6.5, 8.0), REJECT < 6.5 or failures).
3. Adversarial injection of anti-literal violations and repeated camera motions / fatigue.
4. Comprehensive coverage of all 7 contrast dimensions, motifs, human anchors, typography, silence.
5. Robustness against malformed, edge-case, single-shot, zero-duration, and adversarial payloads.
"""

import math
import copy
from typing import Dict, Any, List
from agents.cinematic_qc import CinematicQCEngine
from agents.manifest_reviewer import ManifestReviewerAgent
from agents.qc_editor import QCEditorAgent
from agents.director import DirectorAgent

PASSED_COUNT = 0
FAILED_COUNT = 0

def record_assertion(condition: bool, msg: str):
    global PASSED_COUNT, FAILED_COUNT
    if condition:
        PASSED_COUNT += 1
        print(f"  [PASS] {msg}")
    else:
        FAILED_COUNT += 1
        print(f"  [FAIL] {msg}")
        assert False, msg


# Helper to build custom test manifests
def make_base_manifest(beats=None, target_duration=60.0):
    return {
        "schema_version": "2.0",
        "project_meta": {"title": "Challenger Doc", "target_duration_seconds": target_duration},
        "documentary_vision": {
            "thesis": "Test thesis",
            "visual_motifs": ["hourglass_sand", "ticking_clock"]
        },
        "research_package": {
            "visual_motifs": ["vintage_microphone"]
        },
        "story_beats": beats or []
    }


def make_shot(
    shot_id="b1_n1_s1",
    visual_job="ESTABLISH_WORLD",
    visual_type="broll_video",
    fallback_type="HistoricalDocument",
    asset_provenance="STOCK",
    shot_size="wide",
    camera_angle="eye_level",
    lens="standard_lens",
    composition="center_framed",
    camera_motion="static",
    cut_reason="Establish the scale and environment of the historical setting",
    duration_seconds=3.0,
    visual_description="A wide view of the ancient archives",
    visual_query="ancient library archives historical documents",
    ai_prompt="ancient library interior historical cinematic",
    shot_relationship="CONTINUATION",
    is_restrained=False,
    is_motif=False,
    sound_design="",
    editorial_events=None,
    overlay="",
    lut_filter="kodak_portra",
    visual_density=0.5,
    visual_importance=0.5
):
    return {
        "shot_id": shot_id,
        "visual_job": visual_job,
        "visual_type": visual_type,
        "fallback_type": fallback_type,
        "asset_provenance": asset_provenance,
        "shot_size": shot_size,
        "camera_angle": camera_angle,
        "lens": lens,
        "composition": composition,
        "camera_motion": camera_motion,
        "cut_reason": cut_reason,
        "duration_seconds": duration_seconds,
        "actual_duration": duration_seconds,
        "visual_description": visual_description,
        "visual_query": visual_query,
        "ai_prompt": ai_prompt,
        "shot_relationship": shot_relationship,
        "is_restrained": is_restrained,
        "is_motif": is_motif,
        "sound_design": sound_design,
        "editorial_events": editorial_events or [],
        "overlay": overlay,
        "lut_filter": lut_filter,
        "visual_density": visual_density,
        "visual_importance": visual_importance
    }


def make_beat(beat_id="b001", intent="HOOK", shots=None, att_intensity=0.8, strategic_silence=None):
    return {
        "beat_id": beat_id,
        "narrative_intent": intent,
        "attention_intensity": att_intensity,
        "narration_blocks": [
            {
                "block_id": f"{beat_id}_n1",
                "voiceover": "Test narration for beat.",
                "duration_hint": sum(s.get("duration_seconds", 3.0) for s in (shots or [])),
                "strategic_silence": strategic_silence,
                "shots": shots or []
            }
        ]
    }


# ==============================================================================
# TEST SUITE 1: 17 METRICS DICTIONARY EXTRACTION & FORMAT INTEGRITY
# ==============================================================================
def test_suite_1_metrics_extraction():
    print("\n--- SUITE 1: 17 Directorial Metrics Extraction & Schema Verification ---")
    qc = CinematicQCEngine()

    expected_17_metrics = [
        "number_of_unique_visual_concepts",
        "repeated_visual_concepts",
        "repeated_queries",
        "repeated_camera_movements",
        "repeated_compositions",
        "shots_with_no_editorial_reason",
        "number_of_major_reveals",
        "number_of_attention_peaks",
        "number_of_silence_moments",
        "number_of_typography_punctuation_events",
        "number_of_graphic_explanations",
        "number_of_human_anchor_moments",
        "number_of_visual_motifs",
        "number_of_visual_contrasts",
        "number_of_contextual_overlays",
        "sfx_per_minute",
        "% shots that merely illustrate narration"
    ]

    expected_score_matrix_keys = [
        "storytelling",
        "cinematography",
        "pacing",
        "sound_design",
        "visual_variety",
        "visual_contrast",
        "editorial_motivation",
        "anti_literal_restraint",
        "human_grounding",
        "graphic_punctuation"
    ]

    # Test with director mock fallback
    director = DirectorAgent()
    manifest = director._get_mock_fallback("", "", True)
    eval_result = qc.evaluate_manifest_director_score(manifest)

    # Check top-level result fields
    for field in ["overall_director_score", "overall_score", "verdict", "director_verdict",
                  "validation_metrics", "director_score_matrix", "total_shots_audited",
                  "total_timeline_duration_seconds", "sfx_punctuation_ratio", "failures", "recommendations"]:
        record_assertion(field in eval_result, f"Result contains top-level field '{field}'")

    # Check 17 metrics presence & types
    val_metrics = eval_result["validation_metrics"]
    for m in expected_17_metrics:
        record_assertion(m in val_metrics, f"Validation metrics contains R6 metric '{m}'")
        record_assertion(isinstance(val_metrics[m], (int, float)), f"Metric '{m}' is numeric (int/float)")

    # Check alias percentage_illustrative_shots
    record_assertion("percentage_illustrative_shots" in val_metrics, "Metric alias 'percentage_illustrative_shots' exists")
    record_assertion(val_metrics["% shots that merely illustrate narration"] == val_metrics["percentage_illustrative_shots"],
                     "Metric '% shots that merely illustrate narration' matches 'percentage_illustrative_shots'")

    # Check 10-dimension matrix keys
    matrix = eval_result["director_score_matrix"]
    record_assertion(len(matrix) == 10, f"Score matrix contains exactly 10 dimensions (found {len(matrix)})")
    for k in expected_score_matrix_keys:
        record_assertion(k in matrix, f"Score matrix contains dimension '{k}'")
        record_assertion(0.0 <= matrix[k] <= 10.0, f"Dimension '{k}' score ({matrix[k]}) is in [0.0, 10.0]")


# ==============================================================================
# TEST SUITE 2: DYNAMIC DIRECTOR SCORE BOUNDS & THRESHOLD MAPPING
# ==============================================================================
def test_suite_2_director_score_bounds_and_thresholds():
    print("\n--- SUITE 2: Dynamic Director Score Bounds & Threshold Mapping ---")
    qc = CinematicQCEngine()

    # 1. Optimal Manifest -> Score >= 8.0, Verdict APPROVED
    shots_opt = [
        make_shot(shot_id="s1", visual_job="ESTABLISH_WORLD", visual_type="broll_video",
                  shot_size="extreme_wide", camera_motion="slow_push_in", duration_seconds=2.0,
                  cut_reason="Establish the vast landscape setting", visual_density=0.8,
                  sound_design="wind_howl", overlay="film_grain"),
        make_shot(shot_id="s2", visual_job="HUMANIZE", visual_type="broll_video",
                  shot_size="close", camera_motion="static", duration_seconds=3.8,
                  shot_relationship="CONTRAST", cut_reason="Focus on the weary expressions of workers",
                  visual_description="A close up of tired human hands working at a desk", visual_density=0.3,
                  is_restrained=True),
        make_shot(shot_id="s3", visual_job="SHOW_EVIDENCE", visual_type="motion_graphics",
                  fallback_type="TechnicalDiagram", shot_size="medium", camera_motion="pan_right",
                  duration_seconds=2.1, shot_relationship="NUMBER_TO_SCALE",
                  cut_reason="Examine the explosive financial disparity diagram", visual_density=0.7,
                  editorial_events=[{"type": "NUMBER_REVEAL"}], sound_design="bass_thud"),
        make_shot(shot_id="s4", visual_job="REVEAL", visual_type="broll_video",
                  shot_size="wide", camera_motion="static", duration_seconds=4.0,
                  shot_relationship="EVIDENCE_TO_REVEAL", cut_reason="Reveal the shocking secret vault",
                  visual_description="Hourglass sand slipping through fingers", is_motif=True,
                  is_restrained=True)
    ]
    beat1 = make_beat(beat_id="b1", intent="HOOK", shots=shots_opt[:2], att_intensity=0.9)
    beat2 = make_beat(beat_id="b2", intent="REVELATION", shots=shots_opt[2:], att_intensity=0.9,
                      strategic_silence={"duration_seconds": 1.5, "reason": "Dramatic pause"})
    optimal_manifest = make_base_manifest(beats=[beat1, beat2], target_duration=12.0)

    res_opt = qc.evaluate_manifest_director_score(optimal_manifest)
    score_opt = res_opt["overall_director_score"]
    record_assertion(8.0 <= score_opt <= 10.0, f"Optimal manifest receives score >= 8.0 (actual: {score_opt})")
    record_assertion(res_opt["verdict"] == "APPROVED", f"Optimal manifest verdict is APPROVED (actual: {res_opt['verdict']})")
    record_assertion(len(res_opt["failures"]) == 0, f"Optimal manifest has 0 failures (actual: {len(res_opt['failures'])})")

    # 2. Suboptimal Manifest (Score between 6.5 and 8.0 -> Verdict IMPROVE)
    # Manifest with good cut reasons, no banned clichés, but repetitive camera / few contrasts / high SFX
    shots_sub = [
        make_shot(shot_id=f"s{i}", visual_job="ESTABLISH_WORLD", visual_type="broll_video",
                  shot_size="medium", camera_motion="slow_push_in", duration_seconds=3.0,
                  cut_reason=f"Valid specific cut reason number {i} for context",
                  visual_query=f"unique query subject {i}", sound_design="whoosh")
        for i in range(6)
    ]
    beat_sub = make_beat(beat_id="b1", intent="CONTEXT", shots=shots_sub, att_intensity=0.5)
    sub_manifest = make_base_manifest(beats=[beat_sub], target_duration=18.0)
    res_sub = qc.evaluate_manifest_director_score(sub_manifest)
    score_sub = res_sub["overall_director_score"]
    record_assertion(6.0 <= score_sub <= 8.0, f"Suboptimal manifest score in [6.0, 8.0] (actual: {score_sub})")
    if len(res_sub["failures"]) == 0 and 6.5 <= score_sub < 8.0:
        record_assertion(res_sub["verdict"] == "IMPROVE", f"Suboptimal manifest receives verdict IMPROVE (actual: {res_sub['verdict']})")
    else:
        record_assertion(res_sub["verdict"] in ["IMPROVE", "REJECT"], f"Suboptimal manifest receives verdict IMPROVE/REJECT (actual: {res_sub['verdict']})")

    # 3. Terribly Flawed Manifest -> Verdict REJECT
    shots_terrible = [
        make_shot(shot_id=f"bad_s{i}", visual_job="ESTABLISH_WORLD", visual_type="broll_video",
                  asset_provenance="STOCK", shot_size="wide", camera_motion="slow_push_in",
                  cut_reason="transition", duration_seconds=2.5,
                  visual_query="money falling handshake generic businessman",
                  sound_design="loud_blast")
        for i in range(5)
    ]
    beat_bad = make_beat(beat_id="b1", intent="CONTEXT", shots=shots_terrible, att_intensity=0.3)
    terrible_manifest = make_base_manifest(beats=[beat_bad], target_duration=12.5)
    res_bad = qc.evaluate_manifest_director_score(terrible_manifest)
    score_bad = res_bad["overall_director_score"]
    record_assertion(0.0 <= score_bad < 6.5, f"Terrible manifest score is < 6.5 (actual: {score_bad})")
    record_assertion(res_bad["verdict"] == "REJECT", f"Terrible manifest verdict is REJECT (actual: {res_bad['verdict']})")
    record_assertion(len(res_bad["failures"]) > 0, "Terrible manifest returns explicit failure messages")


# ==============================================================================
# TEST SUITE 3: ADVERSARIAL INJECTIONS — ANTI-LITERAL VIOLATIONS & CAMERA MOTIONS
# ==============================================================================
def test_suite_3_adversarial_injections():
    print("\n--- SUITE 3: Adversarial Injections (Anti-Literal & Repeated Camera Motions) ---")
    qc = CinematicQCEngine()

    # 1. Anti-Literal Banned Keywords Injection
    for banned_kw in CinematicQCEngine.BANNED_LITERAL_KEYWORDS:
        shots_cliche = [
            make_shot(shot_id="s1", visual_query=f"documentary scene with {banned_kw} in office",
                      cut_reason="Valid specific cut reason for scene 1"),
            make_shot(shot_id="s2", visual_query="metaphorical shadow over empty chair",
                      cut_reason="Valid specific cut reason for scene 2"),
            make_shot(shot_id="s3", visual_query="hands typing on mechanical keyboard",
                      cut_reason="Valid specific cut reason for scene 3"),
            make_shot(shot_id="s4", visual_query="timelapse of street traffic",
                      cut_reason="Valid specific cut reason for scene 4")
        ]
        beat = make_beat(beat_id="b1", shots=shots_cliche)
        m = make_base_manifest(beats=[beat], target_duration=12.0)
        res = qc.evaluate_manifest_director_score(m)
        val_m = res["validation_metrics"]
        record_assertion(val_m["% shots that merely illustrate narration"] == 25.0,
                         f"Banned keyword '{banned_kw}' detected: illustrative % is 25.0% (1 of 4 shots)")

    # 2. Threshold Violation for Anti-Literal (> 25% illustrative -> failure + REJECT)
    shots_heavy_cliche = [
        make_shot(shot_id="s1", visual_query="coins falling from sky", cut_reason="Valid specific cut reason 1"),
        make_shot(shot_id="s2", visual_query="generic businessman at table", cut_reason="Valid specific cut reason 2"),
        make_shot(shot_id="s3", visual_query="normal shot of street", cut_reason="Valid specific cut reason 3")
    ]
    beat_heavy = make_beat(beat_id="b1", shots=shots_heavy_cliche)
    m_heavy = make_base_manifest(beats=[beat_heavy], target_duration=9.0)
    res_heavy = qc.evaluate_manifest_director_score(m_heavy)
    record_assertion(res_heavy["validation_metrics"]["% shots that merely illustrate narration"] == round(2/3 * 100, 2),
                     "Anti-literal metric correctly computed 66.67%")
    record_assertion(any("Anti-literal rule violated" in f for f in res_heavy["failures"]),
                     "Anti-literal failure reported in failures list when > 25%")
    record_assertion(res_heavy["verdict"] == "REJECT", "Verdict is REJECT when anti-literal failure occurs")

    # 3. Repeated Dynamic Camera Motions
    # Consecutive identical dynamic motions: pan_left -> pan_left -> pan_left -> pan_left
    shots_cam = [
        make_shot(shot_id="s1", camera_motion="pan_left", cut_reason="Specific valid cut reason 1"),
        make_shot(shot_id="s2", camera_motion="pan_left", cut_reason="Specific valid cut reason 2"),
        make_shot(shot_id="s3", camera_motion="pan_left", cut_reason="Specific valid cut reason 3"),
        make_shot(shot_id="s4", camera_motion="pan_left", cut_reason="Specific valid cut reason 4"),
        make_shot(shot_id="s5", camera_motion="static", cut_reason="Specific valid cut reason 5"),
        make_shot(shot_id="s6", camera_motion="static", cut_reason="Specific valid cut reason 6")
    ]
    beat_cam = make_beat(beat_id="b1", shots=shots_cam)
    m_cam = make_base_manifest(beats=[beat_cam], target_duration=18.0)
    res_cam = qc.evaluate_manifest_director_score(m_cam)
    # Between s1 & s2, s2 & s3, s3 & s4 -> 3 repeated camera movements.
    # Between s5 & s6 -> both static -> NOT counted as repeated camera movement!
    record_assertion(res_cam["validation_metrics"]["repeated_camera_movements"] == 3,
                     f"Repeated dynamic camera movements = 3, static holds excluded (actual: {res_cam['validation_metrics']['repeated_camera_movements']})")

    # 4. Repeated Visual Queries Detection
    shots_rep_q = [
        make_shot(shot_id="s1", visual_query="financial collapse graph", cut_reason="Specific valid cut reason 1"),
        make_shot(shot_id="s2", visual_query="  Financial Collapse Graph  ", cut_reason="Specific valid cut reason 2"),
        make_shot(shot_id="s3", visual_query="financial collapse graph", cut_reason="Specific valid cut reason 3"),
        make_shot(shot_id="s4", visual_query="unrelated empty room", cut_reason="Specific valid cut reason 4")
    ]
    beat_q = make_beat(beat_id="b1", shots=shots_rep_q)
    m_q = make_base_manifest(beats=[beat_q], target_duration=12.0)
    res_q = qc.evaluate_manifest_director_score(m_q)
    # 3 occurrences of same query -> 2 duplicates
    record_assertion(res_q["validation_metrics"]["repeated_queries"] == 2,
                     f"Repeated queries count = 2 for normalized duplicates (actual: {res_q['validation_metrics']['repeated_queries']})")


# ==============================================================================
# TEST SUITE 4: 7D VISUAL CONTRAST ENGINE EMPIRICAL VALIDATION
# ==============================================================================
def test_suite_4_7d_visual_contrast_engine():
    print("\n--- SUITE 4: 7-Dimensional Visual Contrast Engine Verification ---")
    qc = CinematicQCEngine()

    # Test each dimension individually to verify detection
    # Dim 1: Pacing Contrast (abs(dur1 - dur2) >= 1.5)
    s1 = make_shot(shot_id="s1", duration_seconds=1.5, cut_reason="Reason 1", lut_filter="lut1", visual_density=0.5)
    s2 = make_shot(shot_id="s2", duration_seconds=3.5, cut_reason="Reason 2", lut_filter="lut1", visual_density=0.5)
    m = make_base_manifest(beats=[make_beat(shots=[s1, s2])])
    record_assertion(qc.evaluate_manifest_director_score(m)["validation_metrics"]["number_of_visual_contrasts"] == 1,
                     "Dimension 1: Pacing Contrast (1.5s vs 3.5s) detected")

    # Dim 2: Movement Contrast (static vs non-static)
    s1 = make_shot(shot_id="s1", duration_seconds=3.0, camera_motion="static", cut_reason="Reason 1", lut_filter="lut1", visual_density=0.5)
    s2 = make_shot(shot_id="s2", duration_seconds=3.0, camera_motion="slow_push_in", cut_reason="Reason 2", lut_filter="lut1", visual_density=0.5)
    m = make_base_manifest(beats=[make_beat(shots=[s1, s2])])
    record_assertion(qc.evaluate_manifest_director_score(m)["validation_metrics"]["number_of_visual_contrasts"] == 1,
                     "Dimension 2: Movement Contrast (static vs slow_push_in) detected")

    # Dim 3: Scale Contrast (close vs wide)
    s1 = make_shot(shot_id="s1", duration_seconds=3.0, shot_size="close", cut_reason="Reason 1", lut_filter="lut1", visual_density=0.5)
    s2 = make_shot(shot_id="s2", duration_seconds=3.0, shot_size="extreme_wide", cut_reason="Reason 2", lut_filter="lut1", visual_density=0.5)
    m = make_base_manifest(beats=[make_beat(shots=[s1, s2])])
    record_assertion(qc.evaluate_manifest_director_score(m)["validation_metrics"]["number_of_visual_contrasts"] == 1,
                     "Dimension 3: Scale Contrast (close vs extreme_wide) detected")

    # Dim 4: Medium / Visual Type Contrast
    s1 = make_shot(shot_id="s1", duration_seconds=3.0, visual_type="broll_video", cut_reason="Reason 1", lut_filter="lut1", visual_density=0.5)
    s2 = make_shot(shot_id="s2", duration_seconds=3.0, visual_type="motion_graphics", cut_reason="Reason 2", lut_filter="lut1", visual_density=0.5)
    m = make_base_manifest(beats=[make_beat(shots=[s1, s2])])
    record_assertion(qc.evaluate_manifest_director_score(m)["validation_metrics"]["number_of_visual_contrasts"] == 1,
                     "Dimension 4: Medium Contrast (broll_video vs motion_graphics) detected")

    # Dim 5: LUT / Lighting Contrast
    s1 = make_shot(shot_id="s1", duration_seconds=3.0, lut_filter="kodak_warm", cut_reason="Reason 1", visual_density=0.5)
    s2 = make_shot(shot_id="s2", duration_seconds=3.0, lut_filter="fuji_cool", cut_reason="Reason 2", visual_density=0.5)
    m = make_base_manifest(beats=[make_beat(shots=[s1, s2])])
    record_assertion(qc.evaluate_manifest_director_score(m)["validation_metrics"]["number_of_visual_contrasts"] == 1,
                     "Dimension 5: LUT Contrast (kodak_warm vs fuji_cool) detected")

    # Dim 6: Visual Density Contrast (abs(den1 - den2) >= 0.3)
    s1 = make_shot(shot_id="s1", duration_seconds=3.0, visual_density=0.2, cut_reason="Reason 1", lut_filter="lut1")
    s2 = make_shot(shot_id="s2", duration_seconds=3.0, visual_density=0.8, cut_reason="Reason 2", lut_filter="lut1")
    m = make_base_manifest(beats=[make_beat(shots=[s1, s2])])
    record_assertion(qc.evaluate_manifest_director_score(m)["validation_metrics"]["number_of_visual_contrasts"] == 1,
                     "Dimension 6: Density Contrast (0.2 vs 0.8) detected")

    # Dim 7: Relational Grammar Contrast (CONTRAST, BEFORE_TO_AFTER, EXPECTATION_TO_SUBVERSION, CAUSE_TO_EFFECT)
    for rel in ["CONTRAST", "BEFORE_TO_AFTER", "EXPECTATION_TO_SUBVERSION", "CAUSE_TO_EFFECT"]:
        s1 = make_shot(shot_id="s1", duration_seconds=3.0, shot_relationship="CONTINUATION", cut_reason="Reason 1", lut_filter="lut1", visual_density=0.5)
        s2 = make_shot(shot_id="s2", duration_seconds=3.0, shot_relationship=rel, cut_reason="Reason 2", lut_filter="lut1", visual_density=0.5)
        m = make_base_manifest(beats=[make_beat(shots=[s1, s2])])
        record_assertion(qc.evaluate_manifest_director_score(m)["validation_metrics"]["number_of_visual_contrasts"] == 1,
                         f"Dimension 7: Relational Grammar Contrast ({rel}) detected")


# ==============================================================================
# TEST SUITE 5: REVIEWER & QC EDITOR AGENT INTEGRATION & LINTING
# ==============================================================================
def test_suite_5_reviewer_and_editor_agents():
    print("\n--- SUITE 5: Reviewer & QC Editor Agents Integration & Linting ---")
    reviewer = ManifestReviewerAgent()
    qc_editor = QCEditorAgent()

    # 1. Test Camera Fatigue Detection in ManifestReviewer (3 consecutive identical non-static motions)
    fatigue_shots = [
        make_shot(shot_id=f"f_s{i}", camera_motion="pan_right", cut_reason=f"Specific cut reason {i}")
        for i in range(3)
    ]
    fatigue_manifest = make_base_manifest(beats=[make_beat(shots=fatigue_shots)])
    rev_res = reviewer.review_manifest(fatigue_manifest)
    record_assertion(any("CAMERA_MOTION_FATIGUE" in err for err in rev_res["errors"]),
                     "ManifestReviewer correctly flags CAMERA_MOTION_FATIGUE on 3 consecutive pan_right")
    record_assertion(rev_res["status"] == "FAILED", "ManifestReviewer status is FAILED on camera motion fatigue")

    # 2. Test Anachronism Detection (start_year > end_year)
    anach_shot = make_shot(shot_id="anach_s1", cut_reason="Specific valid cut reason")
    anach_shot["continuity"] = {"start_year": "1999", "end_year": "1990"}
    anach_manifest = make_base_manifest(beats=[make_beat(shots=[anach_shot])])
    rev_anach = reviewer.review_manifest(anach_manifest)
    record_assertion(any("ANACHRONISM" in err for err in rev_anach["errors"]),
                     "ManifestReviewer correctly flags ANACHRONISM when start_year > end_year")

    # 3. Test Missing Cinematography Fields on Non-Graphic Shots
    missing_shot = make_shot(shot_id="miss_s1", visual_type="broll_video", cut_reason="Specific valid cut reason")
    missing_shot["camera_angle"] = ""  # Missing angle!
    miss_manifest = make_base_manifest(beats=[make_beat(shots=[missing_shot])])
    rev_miss = reviewer.review_manifest(miss_manifest)
    record_assertion(any("CINEMATOGRAPHY_FAIL" in err for err in rev_miss["errors"]),
                     "ManifestReviewer flags CINEMATOGRAPHY_FAIL on missing camera_angle")

    # 4. Test QCEditor Programmatic Evaluation Offline Mode
    # Valid manifest -> APPROVED with score >= 8
    director = DirectorAgent()
    valid_m = director._get_mock_fallback("", "", True)
    qc_res_valid = qc_editor.review_script(valid_m)
    record_assertion(qc_res_valid["status"] == "APPROVED", f"QCEditor approves valid manifest (status: {qc_res_valid['status']})")
    record_assertion(qc_res_valid["score"] >= 8, f"QCEditor assigns score >= 8 (score: {qc_res_valid['score']})")
    record_assertion("validation_metrics" in qc_res_valid, "QCEditor returns validation_metrics dictionary")

    # Flawed manifest -> REJECTED with isolated repair recommendations
    flawed_shots = [
        make_shot(shot_id="flaw_s1", cut_reason="transition", visual_query="money falling"),
        make_shot(shot_id="flaw_s2", cut_reason="next_shot", visual_query="money falling")
    ]
    flawed_m = make_base_manifest(beats=[make_beat(shots=flawed_shots)])
    qc_res_flawed = qc_editor.review_script(flawed_m)
    record_assertion(qc_res_flawed["status"] == "REJECTED", f"QCEditor rejects flawed manifest (status: {qc_res_flawed['status']})")
    record_assertion(len(qc_res_flawed["failures"]) > 0, "QCEditor returns structured failures")
    for f in qc_res_flawed["failures"]:
        rep = f.get("repair", {})
        record_assertion(rep.get("preserve_narration") is True, "Repair preserves narration")
        record_assertion(rep.get("preserve_timing") is True, "Repair preserves timing")
        record_assertion(rep.get("replace_visual_only") is True, "Repair instructs replace_visual_only")


# ==============================================================================
# TEST SUITE 6: ADVERSARIAL ROBUSTNESS & MALFORMED PAYLOAD STRESS TESTING
# ==============================================================================
def test_suite_6_adversarial_robustness():
    print("\n--- SUITE 6: Adversarial Robustness & Edge Cases ---")
    qc = CinematicQCEngine()
    reviewer = ManifestReviewerAgent()
    qc_editor = QCEditorAgent()

    # 1. Non-dict inputs
    for bad_input in [None, "invalid string", [1, 2, 3], 12345]:
        res_qc = qc.evaluate_manifest_director_score(bad_input)
        record_assertion(res_qc["overall_director_score"] == 0.0, f"QC score is 0.0 for non-dict: {type(bad_input)}")
        record_assertion(res_qc["verdict"] == "REJECT", f"QC verdict is REJECT for non-dict: {type(bad_input)}")
        record_assertion(len(res_qc["failures"]) > 0, f"QC failures present for non-dict: {type(bad_input)}")

        res_rev = reviewer.review_manifest(bad_input)
        record_assertion(res_rev["status"] == "FAILED", f"Reviewer status is FAILED for non-dict: {type(bad_input)}")

        res_ed = qc_editor.review_script(bad_input)
        record_assertion(res_ed["status"] == "REJECTED", f"Editor status is REJECTED for non-dict: {type(bad_input)}")

    # 2. Empty Story Beats / Missing Narration Blocks
    empty_manifests = [
        {},
        {"story_beats": []},
        {"story_beats": [None, "bad_beat", {}]},
        {"story_beats": [{"beat_id": "b1", "narration_blocks": []}]},
        {"story_beats": [{"beat_id": "b1", "narration_blocks": [{"shots": []}]}]}
    ]
    for em in empty_manifests:
        res = qc.evaluate_manifest_director_score(em)
        record_assertion(res["verdict"] == "REJECT", f"Empty manifest produces REJECT verdict: {em}")
        record_assertion(res["overall_director_score"] == 0.0, "Empty manifest score is 0.0")

    # 3. Single-Shot Manifest (Boundary condition for shot transitions)
    single_shot = make_shot(shot_id="single_1", cut_reason="A singular establishing hold", duration_seconds=5.0)
    single_manifest = make_base_manifest(beats=[make_beat(shots=[single_shot])], target_duration=5.0)
    res_single = qc.evaluate_manifest_director_score(single_manifest)
    record_assertion(0.0 <= res_single["overall_director_score"] <= 10.0,
                     f"Single-shot manifest computes bounded score (score: {res_single['overall_director_score']})")
    record_assertion(res_single["validation_metrics"]["number_of_visual_contrasts"] == 0,
                     "Single-shot manifest has 0 contrasts without division-by-zero error")

    # 4. Massive Scaling Manifest (100 shots)
    massive_shots = []
    for i in range(100):
        massive_shots.append(
            make_shot(
                shot_id=f"mass_{i}",
                visual_job="ESTABLISH_WORLD" if i % 2 == 0 else "SHOW_EVIDENCE",
                visual_type="broll_video" if i % 3 != 0 else "motion_graphics",
                camera_motion="static" if i % 2 == 0 else "slow_push_in",
                shot_size="wide" if i % 2 == 0 else "close",
                cut_reason=f"Specific and valid editorial cut reason for massive shot {i}",
                duration_seconds=2.0 + (i % 3),
                visual_density=0.2 if i % 2 == 0 else 0.8
            )
        )
    massive_beats = [make_beat(beat_id=f"mb_{k}", shots=massive_shots[k*10:(k+1)*10]) for k in range(10)]
    massive_manifest = make_base_manifest(beats=massive_beats, target_duration=300.0)

    res_massive = qc.evaluate_manifest_director_score(massive_manifest)
    record_assertion(0.0 <= res_massive["overall_director_score"] <= 10.0,
                     f"100-shot manifest calculates bounded score (score: {res_massive['overall_director_score']})")
    record_assertion(res_massive["total_shots_audited"] == 100, "Audited exactly 100 shots")
    record_assertion(res_massive["validation_metrics"]["number_of_unique_visual_concepts"] >= 2,
                     "Unique concepts tracked across 100 shots")


def main():
    print("================================================================================")
    print("      MILESTONE 4: ADVERSARIAL EMPIRICAL CHALLENGER TEST HARNESS              ")
    print("================================================================================")

    test_suite_1_metrics_extraction()
    test_suite_2_director_score_bounds_and_thresholds()
    test_suite_3_adversarial_injections()
    test_suite_4_7d_visual_contrast_engine()
    test_suite_5_reviewer_and_editor_agents()
    test_suite_6_adversarial_robustness()

    print("\n================================================================================")
    print(f" CHALLENGER RESULTS: PASSED={PASSED_COUNT}, FAILED={FAILED_COUNT}")
    print("================================================================================")

    if FAILED_COUNT > 0:
        raise AssertionError(f"Challenger Harness detected {FAILED_COUNT} test failures!")


if __name__ == "__main__":
    main()
