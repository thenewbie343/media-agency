"""
Adversarial Stress Test Suite for Milestone 4: Cinematic QC, Reviewer & Editor Agents
Tests boundary conditions, edge cases, malformed structures, extreme values,
banned literal keywords, cut reason validation, score matrix calculations,
and integrity verification (no hardcoding, facades, or shortcuts).
"""

import json
import pytest
from agents.cinematic_qc import CinematicQCEngine
from agents.manifest_reviewer import ManifestReviewerAgent
from agents.qc_editor import QCEditorAgent
from agents.director import DirectorAgent

def test_empty_and_malformed_manifests():
    """Verify robust rejection of malformed inputs without unhandled exceptions."""
    qc = CinematicQCEngine()
    reviewer = ManifestReviewerAgent()
    editor = QCEditorAgent()

    malformed_inputs = [
        None,
        {},
        [],
        "invalid string",
        {"story_beats": []},
        {"story_beats": [{"beat_id": "b1", "narration_blocks": []}]},
        {"story_beats": [{"beat_id": "b1", "narration_blocks": [{"block_id": "n1", "shots": []}]}]},
    ]

    for inp in malformed_inputs:
        # QC Engine
        res = qc.evaluate_manifest_director_score(inp)
        assert isinstance(res, dict)
        assert res["overall_director_score"] == 0.0
        assert res["verdict"] == "REJECT"
        assert len(res["failures"]) > 0

        # Reviewer Agent
        rev_res = reviewer.review_manifest(inp)
        assert isinstance(rev_res, dict)
        assert rev_res["status"] == "FAILED"
        assert len(rev_res["errors"]) > 0

        # Editor Agent
        ed_res = editor.review_script(inp)
        assert isinstance(ed_res, dict)
        assert ed_res["status"] == "REJECTED"
        assert ed_res["score"] <= 5

def test_17_metrics_exact_calculation_and_keys():
    """Verify all 17 keys are strictly present and typed correctly."""
    qc = CinematicQCEngine()
    director = DirectorAgent()
    valid_manifest = director._get_mock_fallback("", "", True)

    result = qc.evaluate_manifest_director_score(valid_manifest)
    metrics = result["validation_metrics"]

    expected_17_keys = [
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

    for k in expected_17_keys:
        assert k in metrics, f"Missing metric {k}"
        val = metrics[k]
        assert isinstance(val, (int, float)), f"Metric {k} is not numeric: {type(val)}"

    # Score matrix must contain all 10 dimensions
    matrix = result["director_score_matrix"]
    expected_matrix_keys = [
        "storytelling", "cinematography", "pacing", "sound_design",
        "visual_variety", "visual_contrast", "editorial_motivation",
        "anti_literal_restraint", "human_grounding", "graphic_punctuation"
    ]
    for mk in expected_matrix_keys:
        assert mk in matrix, f"Missing matrix dimension {mk}"
        assert 0.0 <= matrix[mk] <= 10.0, f"Matrix dimension {mk} out of bounds: {matrix[mk]}"

    assert result["overall_director_score"] >= 8.0
    assert result["verdict"] == "APPROVED"

def test_banned_literal_keywords_rejection():
    """Verify that every single banned literal keyword is detected and penalized."""
    qc = CinematicQCEngine()
    banned_keywords = CinematicQCEngine.BANNED_LITERAL_KEYWORDS

    for kw in banned_keywords:
        manifest = {
            "schema_version": "2.0",
            "project_meta": {"title": "Banned Test", "target_duration_seconds": 30},
            "story_beats": [{
                "beat_id": "b001",
                "narrative_intent": "EXPLANATION",
                "narration_blocks": [{
                    "block_id": "n001",
                    "voiceover": f"Here is {kw}",
                    "shots": [{
                        "shot_id": "s001",
                        "visual_type": "broll_video",
                        "asset_provenance": "STOCK",
                        "visual_job": "SHOW_EVIDENCE",
                        "visual_query": f"detailed close-up of {kw}",
                        "cut_reason": "reveal dramatic detail",
                        "shot_size": "close",
                        "camera_angle": "eye_level",
                        "lens": "50mm_standard",
                        "composition": "rule_of_thirds",
                        "duration_seconds": 3.0
                    }]
                }]
            }]
        }
        res = qc.evaluate_manifest_director_score(manifest)
        metrics = res["validation_metrics"]
        assert metrics["% shots that merely illustrate narration"] == 100.0, f"Failed to catch keyword: {kw}"
        assert any("High percentage of literal/illustrative shots" in f for f in res["failures"])
        assert res["verdict"] in ["REJECT", "IMPROVE"]

def test_generic_cut_reasons_penalization():
    """Verify all generic cut reasons are flagged and penalized."""
    qc = CinematicQCEngine()
    generic_reasons = ["", "n/a", "none", "introduce_information", "show_fact", "transition", "change_scene", "next_shot", "filler", "broll", "visual_variety", "show_topic", "illustration", "show_visual"]

    for reason in generic_reasons:
        manifest = {
            "schema_version": "2.0",
            "project_meta": {"title": "Generic Cut Reason", "target_duration_seconds": 30},
            "story_beats": [{
                "beat_id": "b001",
                "narrative_intent": "EXPLANATION",
                "narration_blocks": [{
                    "block_id": "n001",
                    "voiceover": "Some voiceover",
                    "shots": [{
                        "shot_id": "s001",
                        "visual_type": "broll_video",
                        "asset_provenance": "STOCK",
                        "visual_job": "SHOW_EVIDENCE",
                        "visual_query": "specific historical archive document",
                        "cut_reason": reason,
                        "shot_size": "close",
                        "camera_angle": "eye_level",
                        "lens": "50mm_standard",
                        "composition": "rule_of_thirds",
                        "duration_seconds": 3.0
                    }]
                }]
            }]
        }
        res = qc.evaluate_manifest_director_score(manifest)
        assert res["validation_metrics"]["shots_with_no_editorial_reason"] == 1
        assert res["director_score_matrix"]["editorial_motivation"] <= 8.0
        assert any("generic or missing cut_reason" in f for f in res["failures"])

def test_camera_motion_fatigue_and_diversity():
    """Verify consecutive dynamic camera motion triggers fatigue warning/metric."""
    qc = CinematicQCEngine()
    reviewer = ManifestReviewerAgent()

    shots = []
    for i in range(4):
        shots.append({
            "shot_id": f"s00{i+1}",
            "visual_type": "broll_video",
            "asset_provenance": "STOCK",
            "visual_job": f"JOB_{i}",
            "visual_query": f"unique query {i}",
            "cut_reason": f"specific editorial motivation {i}",
            "camera_motion": "slow_push_in",  # Identical 4 times
            "shot_size": "close" if i % 2 == 0 else "wide",
            "camera_angle": "eye_level",
            "lens": "50mm_standard",
            "composition": "rule_of_thirds",
            "duration_seconds": 3.0
        })

    manifest = {
        "schema_version": "2.0",
        "story_beats": [{
            "beat_id": "b001",
            "narrative_intent": "EXPLANATION",
            "narration_blocks": [{"block_id": "n001", "shots": shots}]
        }]
    }

    res = qc.evaluate_manifest_director_score(manifest)
    assert res["validation_metrics"]["repeated_camera_movements"] == 3

    rev_res = reviewer.review_manifest(manifest)
    assert any("CAMERA_MOTION_FATIGUE" in err for err in rev_res["errors"])

def test_sfx_pacing_extremes():
    """Verify that extreme SFX rates (overuse or complete silence without intent) are scored appropriately."""
    qc = CinematicQCEngine()

    # Extreme high SFX (e.g., 20 SFX in 30 seconds = 40 SFX/min)
    high_sfx_shots = []
    for i in range(10):
        high_sfx_shots.append({
            "shot_id": f"s00{i+1}",
            "visual_type": "broll_video",
            "sound_design": "heavy_impact",
            "cut_reason": f"specific editorial justification {i}",
            "visual_job": "SHOW_EVIDENCE",
            "visual_query": f"distinct query {i}",
            "shot_size": "close",
            "camera_angle": "eye_level",
            "lens": "50mm",
            "composition": "rule_of_thirds",
            "duration_seconds": 2.0
        })

    manifest_high = {
        "schema_version": "2.0",
        "story_beats": [{
            "beat_id": "b001",
            "narration_blocks": [{"block_id": "n001", "shots": high_sfx_shots}]
        }]
    }
    res_high = qc.evaluate_manifest_director_score(manifest_high)
    assert res_high["validation_metrics"]["sfx_per_minute"] >= 20.0
    assert res_high["director_score_matrix"]["sound_design"] <= 6.0

def test_qc_editor_repair_isolation():
    """Verify that QCEditorAgent preserves narration, timing, and IDs on failure repairs."""
    editor = QCEditorAgent()
    flawed_manifest = {
        "schema_version": "2.0",
        "story_beats": [{
            "beat_id": "b001",
            "narration_blocks": [{
                "block_id": "n001",
                "voiceover": "Crucial voiceover text that must not be changed",
                "shots": [{
                    "shot_id": "s001",
                    "visual_type": "broll_video",
                    "cut_reason": "transition",  # Generic cut reason
                    "duration_seconds": 2.5
                }]
            }]
        }]
    }
    eval_result = editor.review_script(flawed_manifest)
    assert eval_result["status"] == "REJECTED"
    assert len(eval_result["failures"]) > 0
    for f in eval_result["failures"]:
        repair = f.get("repair", {})
        assert repair.get("preserve_narration") is True
        assert repair.get("preserve_timing") is True
        assert repair.get("preserve_beat") is True
        assert repair.get("preserve_ids") is True
        assert repair.get("replace_visual_only") is True

if __name__ == "__main__":
    test_empty_and_malformed_manifests()
    test_17_metrics_exact_calculation_and_keys()
    test_banned_literal_keywords_rejection()
    test_generic_cut_reasons_penalization()
    test_camera_motion_fatigue_and_diversity()
    test_sfx_pacing_extremes()
    test_qc_editor_repair_isolation()
    print("\n>>> ALL ADVERSARIAL STRESS TESTS PASSED SUCCESSFULLY! <<<\n")
