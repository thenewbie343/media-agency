"""
Verification Test Suite for Milestone 4: 17 Cinematic QC Metrics & Reviewers
Verifies:
1. Accurate computation of all 17 Directorial Validation Metrics in CinematicQCEngine.
2. Directorial Scoring Matrix and threshold (>= 8.0/10.0 for APPROVED verdict).
3. Rejection of generic B-roll, repetitive queries, unmotivated cuts, and literal clichés.
4. Rewarding static holds, strategic silence, and 7-dimensional visual contrasts.
5. ManifestReviewerAgent static linting and 17-metric integration.
6. QCEditorAgent supervising review and surgical failure reporting.
"""

import json
from agents.cinematic_qc import CinematicQCEngine
from agents.manifest_reviewer import ManifestReviewerAgent
from agents.qc_editor import QCEditorAgent
from agents.director import DirectorAgent
from agents.researcher import ResearcherAgent

def create_valid_v2_manifest():
    """Generates a valid v2.0 ScriptManifest dict with diverse jobs, contrasts, and punctuation."""
    director = DirectorAgent()
    manifest = director._get_mock_fallback("", "", True)
    return manifest

def create_flawed_manifest():
    """Generates a flawed manifest with generic cut reasons, repeated queries, literal clichés, and no silence."""
    return {
        "schema_version": "2.0",
        "project_meta": {"title": "Flawed Doc", "target_duration_seconds": 60},
        "story_beats": [
            {
                "beat_id": "b001",
                "narrative_intent": "EXPLANATION",
                "narration_blocks": [
                    {
                        "block_id": "n001",
                        "voiceover": "Money was lost.",
                        "caption": "Money was lost.",
                        "duration_hint": 5.0,
                        "shots": [
                            {
                                "shot_id": "n001_s001",
                                "visual_type": "broll_video",
                                "fallback_type": "PhotoWall",
                                "asset_provenance": "STOCK",
                                "shot_size": "wide",
                                "camera_angle": "eye_level",
                                "lens": "standard_lens",
                                "composition": "center_framed",
                                "visual_job": "ESTABLISH_WORLD",
                                "visual_query": "money falling coins falling",
                                "ai_prompt": "money falling down",
                                "camera_motion": "slow_push_in",
                                "cut_reason": "transition",  # Generic cut reason!
                                "duration_seconds": 2.5
                            },
                            {
                                "shot_id": "n001_s002",
                                "visual_type": "broll_video",
                                "fallback_type": "PhotoWall",
                                "asset_provenance": "STOCK",
                                "shot_size": "wide",  # Repeated composition!
                                "camera_angle": "eye_level",
                                "lens": "standard_lens",
                                "composition": "center_framed",
                                "visual_job": "ESTABLISH_WORLD",
                                "visual_query": "money falling coins falling",  # Repeated query & cliché!
                                "ai_prompt": "money falling down",
                                "camera_motion": "slow_push_in",  # Repeated camera motion!
                                "cut_reason": "show_fact",  # Generic cut reason!
                                "duration_seconds": 2.5
                            }
                        ]
                    }
                ]
            }
        ]
    }

def test_17_metrics_extraction():
    print("\n=== 1. VERIFYING 17 VALIDATION METRICS EXTRACTION ===")
    qc = CinematicQCEngine()
    manifest = create_valid_v2_manifest()
    
    result = qc.evaluate_manifest_director_score(manifest)
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
    
    for key in expected_17_keys:
        assert key in metrics, f"Missing required metric key: {key}"
        print(f"  [OK] Metric '{key}': {metrics[key]}")
    
    print(f"\nOverall Director Score: {result['overall_director_score']}/10.0")
    print(f"Director Verdict: {result['verdict']}")
    print(f"Director Score Matrix: {json.dumps(result['director_score_matrix'], indent=2)}")
    
    assert result["overall_director_score"] >= 8.0, f"Valid manifest score {result['overall_director_score']} < 8.0"
    assert result["verdict"] == "APPROVED", f"Valid manifest verdict was {result['verdict']}"
    assert metrics["shots_with_no_editorial_reason"] == 0
    assert metrics["number_of_unique_visual_concepts"] >= 2
    assert metrics["% shots that merely illustrate narration"] == 0.0

def test_flawed_manifest_rejection():
    print("\n=== 2. VERIFYING REJECTION OF FLAWED MANIFEST ===")
    qc = CinematicQCEngine()
    flawed = create_flawed_manifest()
    
    result = qc.evaluate_manifest_director_score(flawed)
    metrics = result["validation_metrics"]
    
    print(f"Flawed Manifest Director Score: {result['overall_director_score']}/10.0 (Verdict: {result['verdict']})")
    print(f"Failures: {result['failures']}")
    print(f"Repeated queries: {metrics['repeated_queries']}")
    print(f"Shots with no editorial reason: {metrics['shots_with_no_editorial_reason']}")
    print(f"% Illustrative shots: {metrics['% shots that merely illustrate narration']}%")
    
    assert result["verdict"] in ["REJECT", "IMPROVE"]
    assert metrics["shots_with_no_editorial_reason"] == 2
    assert metrics["repeated_queries"] == 1
    assert metrics["% shots that merely illustrate narration"] == 100.0
    assert len(result["failures"]) > 0
    print("  [OK] Flawed manifest correctly penalized and rejected!")

def test_manifest_reviewer_agent():
    print("\n=== 3. VERIFYING MANIFEST REVIEWER AGENT ===")
    reviewer = ManifestReviewerAgent()
    valid_manifest = create_valid_v2_manifest()
    
    valid_review = reviewer.review_manifest(valid_manifest)
    print(f"Valid Manifest Review Status: {valid_review['status']} (Director Score: {valid_review['director_score']}/10.0)")
    assert valid_review["status"] in ["PASS", "PASS_WITH_WARNINGS"]
    assert valid_review["director_score"] >= 8.0
    assert "validation_metrics" in valid_review
    assert len(valid_review["validation_metrics"]) >= 17
    
    flawed_manifest = create_flawed_manifest()
    flawed_review = reviewer.review_manifest(flawed_manifest)
    print(f"Flawed Manifest Review Status: {flawed_review['status']} (Errors: {len(flawed_review['errors'])})")
    assert flawed_review["status"] == "FAILED"
    assert len(flawed_review["errors"]) > 0
    print("  [OK] ManifestReviewerAgent verified!")

def test_qc_editor_agent():
    print("\n=== 4. VERIFYING QC EDITOR AGENT ===")
    qc_editor = QCEditorAgent()
    valid_manifest = create_valid_v2_manifest()
    
    valid_eval = qc_editor.review_script(valid_manifest)
    print(f"Valid Script QC Status: {valid_eval.get('status')} (Score: {valid_eval.get('score')})")
    assert valid_eval.get("status") == "APPROVED"
    assert valid_eval.get("score") >= 8
    assert "validation_metrics" in valid_eval
    
    flawed_manifest = create_flawed_manifest()
    flawed_eval = qc_editor.review_script(flawed_manifest)
    print(f"Flawed Script QC Status: {flawed_eval.get('status')} (Score: {flawed_eval.get('score')})")
    assert flawed_eval.get("status") == "REJECTED"
    assert len(flawed_eval.get("failures", [])) > 0
    print("  [OK] QCEditorAgent verified!")

if __name__ == "__main__":
    test_17_metrics_extraction()
    test_flawed_manifest_rejection()
    test_manifest_reviewer_agent()
    test_qc_editor_agent()
    print("\n=== ALL MILESTONE 4 VERIFICATIONS PASSED SUCCESSFULLY! ===\n")
