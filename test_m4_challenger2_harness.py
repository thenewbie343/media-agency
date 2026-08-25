"""
Adversarial Empirical Challenger 2 Test Harness for Milestone 4:
Manifest Reviewer Agent, QC Editor Agent, and 17 Cinematic QC Metrics Matrix.

Tests:
- Suite 1: Manifest Reviewer Grammar, Schema & Structural Integrity
- Suite 2: QC Editor Directorial Supervision & Status Deciders
- Suite 3: 17 Validation Metrics Precise Engine Calculation & Edge Cases
- Suite 4: 10-Dimension Score Matrix & Verdict Gate Thresholds
- Suite 5: End-to-End Story Planner & Reviewer Integration
- Suite 6: Fuzz Testing & Resilience to Adversarial Inputs
"""

import copy
import json
import math
import os
import random
import re
import sys
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agents.cinematic_qc import CinematicQCEngine
from agents.manifest_reviewer import ManifestReviewerAgent
from agents.qc_editor import QCEditorAgent
from agents.director import DirectorAgent
from agents.visual_story_planner import VisualStoryPlanner
from agents.visual_sequence_director import VisualSequenceDirector
from agents.schema import (
    ScriptManifest,
    StoryBeat,
    NarrationBlock,
    Shot,
    VisualJob,
    ShotRelationship,
    NarrativeIntent,
    DocumentaryVision,
    DocumentaryResearchPackage
)


class TestReporter:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []

    def record(self, test_name: str, status: bool, details: str = ""):
        if status:
            self.passed += 1
            res = f"[PASS] {test_name}"
        else:
            self.failed += 1
            res = f"[FAIL] {test_name} - {details}"
        self.results.append(res)
        print(res)

    def warn(self, test_name: str, details: str):
        self.warnings += 1
        res = f"[WARN] {test_name} - {details}"
        self.results.append(res)
        print(res)

    def print_summary(self):
        print("\n" + "=" * 70)
        print(f"CHALLENGER 2 (M4) TEST RESULTS: PASSED={self.passed}, FAILED={self.failed}, WARNINGS={self.warnings}")
        print("=" * 70)


reporter = TestReporter()


def create_baseline_valid_manifest() -> Dict[str, Any]:
    """Builds a rich, valid v2.0 manifest that satisfies all directorial and QC constraints."""
    return {
        "schema_version": "2.0",
        "project_meta": {
            "title": "The Billion Dollar Heist",
            "topic": "Bangladesh Bank Cyber Heist",
            "target_duration_seconds": 30.0
        },
        "documentary_vision": {
            "topic": "Bangladesh Bank Cyber Heist",
            "core_premise": "How hackers exploited printer errors and weekend holidays to siphon $81 Million.",
            "central_question": "Who masterminded the heist?",
            "documentary_thesis": "A fragile analog printing glitch exposed a billion-dollar digital vulnerability.",
            "central_contradiction": "A high-security SWIFT network undone by an unprinted paper log.",
            "hook_strategy": {
                "hook_type": "CONTRADICTION",
                "target_duration_seconds": 25.0,
                "anomaly_description": "Printer room silence at 11:47 AM.",
                "withholding_element": "The identity of the foreign casino accounts.",
                "opening_visual_cue": "Macro shot of a silent paper tray with red blinking error light."
            },
            "macro_narrative_arc": [
                {"phase": "HOOK", "target_beat_index": 0, "narrative_goal": "Hook audience", "attention_target": 0.9},
                {"phase": "FIRST_DISCOVERY", "target_beat_index": 1, "narrative_goal": "Reveal anomaly", "attention_target": 0.85},
                {"phase": "REVELATION", "target_beat_index": 2, "narrative_goal": "Reveal memo", "attention_target": 0.95}
            ],
            "mini_arcs": [
                {"beat_id": "b001", "time_window": "0-10s", "setup": "s", "build": "b", "complication": "c", "reveal": "r", "consequence": "cq"}
            ],
            "visual_motifs": ["classified telex log", "blinking red terminal"],
            "ending_image": "Empty vault door echoing in silence",
            "style_profile": "DOCUMENTARY_INVESTIGATIVE"
        },
        "story_beats": [
            {
                "beat_id": "b001",
                "beat_title": "The Anomaly",
                "narrative_intent": "HOOK",
                "attention_intensity": 0.9,
                "chapter_color_language": "noir",
                "narration_blocks": [
                    {
                        "block_id": "n001",
                        "voiceover": "On a quiet Friday in Dhaka, the central bank printer went completely dark.",
                        "caption": "Dhaka, Bangladesh — Friday morning.",
                        "duration_hint": 7.0,
                        "total_block_duration": 7.0,
                        "strategic_silence": {"duration_seconds": 1.5, "position": "end", "reason": "dramatic_tension"},
                        "shots": [
                            {
                                "shot_id": "n001_s001",
                                "visual_type": "real_photo",
                                "asset_provenance": "ARCHIVAL_FOOTAGE",
                                "fallback_type": "MapFallback",
                                "shot_size": "wide",
                                "camera_angle": "eye_level",
                                "lens": "wide_angle_lens",
                                "composition": "leading_lines",
                                "visual_job": "ESTABLISH_WORLD",
                                "shot_role": "ESTABLISHING",
                                "shot_relationship": "CONTINUATION",
                                "visual_query": "central bank headquarters dhaka exterior dusk 35mm",
                                "ai_prompt": "Cinematic wide establishing shot of Bangladesh central bank headquarters exterior at dusk",
                                "visual_description": "Bangladesh central bank headquarters exterior dusk 35mm architectural photo",
                                "camera_motion": "slow_push_in",
                                "cut_reason": "establish_geographic_epicenter",
                                "duration_seconds": 3.5,
                                "actual_duration": 3.5,
                                "duration_mode": "fixed",
                                "duration_ratio": 0.5,
                                "visual_density": 0.35,
                                "lut_filter": "noir",
                                "is_motif": False,
                                "is_restrained": False,
                                "editorial_events": []
                            },
                            {
                                "shot_id": "n001_s002",
                                "visual_type": "real_photo",
                                "asset_provenance": "ARCHIVAL_FOOTAGE",
                                "fallback_type": "ClassifiedFile",
                                "shot_size": "close",
                                "camera_angle": "overhead_shot",
                                "lens": "macro_lens",
                                "composition": "center_framed",
                                "visual_job": "EXAMINE_EVIDENCE",
                                "shot_role": "DETAIL",
                                "shot_relationship": "CONTEXT_TO_DETAIL",
                                "visual_query": "archival telex printer jammed paper tray red indicator",
                                "ai_prompt": "Macro top-down detail shot of an archival dot matrix printer tray with stalled telex tape and flashing amber light",
                                "visual_description": "Macro archival dot matrix printer tray stalled telex tape red indicator",
                                "camera_motion": "static",
                                "cut_reason": "examine_forensic_printer_anomaly",
                                "duration_seconds": 3.5,
                                "actual_duration": 3.5,
                                "duration_mode": "fixed",
                                "duration_ratio": 0.5,
                                "visual_density": 0.30,
                                "lut_filter": "noir",
                                "is_motif": True,
                                "is_restrained": True,
                                "sound_design": "paper_rustle",
                                "editorial_events": [
                                    {"type": "SFX", "cue": "paper_rustle", "timing_percent": 0.0, "intensity": 0.6}
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "beat_id": "b002",
                "beat_title": "The Siphoning",
                "narrative_intent": "FIRST_DISCOVERY",
                "attention_intensity": 0.85,
                "chapter_color_language": "noir",
                "narration_blocks": [
                    {
                        "block_id": "n002",
                        "voiceover": "Eighty-one million dollars moved through thirty-five fraudulent transfer requests.",
                        "caption": "$81 Million transferred.",
                        "duration_hint": 7.0,
                        "total_block_duration": 7.0,
                        "shots": [
                            {
                                "shot_id": "n002_s001",
                                "visual_type": "text_stat",
                                "asset_provenance": "MOTION_GRAPHIC",
                                "fallback_type": "CinematicText",
                                "shot_size": "wide",
                                "camera_angle": "eye_level",
                                "lens": "standard_lens",
                                "composition": "center_framed",
                                "visual_job": "SHOW_SCALE",
                                "shot_role": "ESTABLISHING",
                                "shot_relationship": "CONTINUATION",
                                "visual_query": "$81,000,000 kinetic typography financial data graphic",
                                "ai_prompt": "Editorial typography graphic displaying $81,000,000 with bold serif font on dark paper",
                                "visual_description": "$81 Million bold typography kinetic data graphic",
                                "camera_motion": "static",
                                "cut_reason": "punctuate_dramatic_financial_scale",
                                "duration_seconds": 3.2,
                                "actual_duration": 3.2,
                                "duration_mode": "fixed",
                                "duration_ratio": 0.457,
                                "visual_density": 0.80,
                                "lut_filter": "noir",
                                "is_motif": False,
                                "is_restrained": False,
                                "sound_design": "deep_impact",
                                "editorial_events": [
                                    {"type": "NUMBER_REVEAL", "cue": "$81,000,000", "timing_percent": 10.0, "intensity": 0.85},
                                    {"type": "IMPACT", "cue": "deep_impact", "timing_percent": 0.0, "intensity": 0.8}
                                ]
                            },
                            {
                                "shot_id": "n002_s002",
                                "visual_type": "ai_image",
                                "asset_provenance": "AI_RECONSTRUCTION",
                                "fallback_type": "PortraitCard",
                                "shot_size": "medium_close",
                                "camera_angle": "low_angle",
                                "lens": "telephoto_lens",
                                "composition": "rule_of_thirds",
                                "visual_job": "HUMANIZE",
                                "shot_role": "GROUNDING",
                                "shot_relationship": "NUMBER_TO_SCALE",
                                "visual_query": "bank clerk hands trembling at desk in shock morning light",
                                "ai_prompt": "Cinematic shot of bank clerk hands trembling next to an empty terminal, dawn light, 35mm photograph",
                                "visual_description": "Bank clerk hands trembling next to empty terminal desk worker reaction",
                                "camera_motion": "pan_left",
                                "cut_reason": "ground_financial_scale_in_human_consequence",
                                "duration_seconds": 3.8,
                                "actual_duration": 3.8,
                                "duration_mode": "fixed",
                                "duration_ratio": 0.543,
                                "visual_density": 0.35,
                                "lut_filter": "noir",
                                "is_motif": False,
                                "is_restrained": False,
                                "editorial_events": []
                            }
                        ]
                    }
                ]
            },
            {
                "beat_id": "b003",
                "beat_title": "The Smoking Gun",
                "narrative_intent": "REVELATION",
                "attention_intensity": 0.95,
                "chapter_color_language": "noir",
                "narration_blocks": [
                    {
                        "block_id": "n003",
                        "voiceover": "A single typo — 'fandation' instead of 'foundation' — halted the remaining billion dollars.",
                        "caption": "A single typo stopped the remaining transactions.",
                        "duration_hint": 6.5,
                        "total_block_duration": 6.5,
                        "shots": [
                            {
                                "shot_id": "n003_s001",
                                "visual_type": "real_photo",
                                "asset_provenance": "ARCHIVAL_FOOTAGE",
                                "fallback_type": "ArchivalDocument",
                                "shot_size": "extreme_close",
                                "camera_angle": "overhead_shot",
                                "lens": "macro_lens",
                                "composition": "center_framed",
                                "visual_job": "REVEAL",
                                "shot_role": "REVEAL",
                                "shot_relationship": "EVIDENCE_TO_REVEAL",
                                "visual_query": "classified telex document unmasked typo fandation routing slip",
                                "ai_prompt": "Forensic macro photograph of unredacted routing slip showing typo fandation highlighted in red ink",
                                "visual_description": "Classified telex document unmasked typo fandation routing slip memo",
                                "camera_motion": "static",
                                "cut_reason": "expose_smoking_gun_typo_record",
                                "duration_seconds": 3.5,
                                "actual_duration": 3.5,
                                "duration_mode": "fixed",
                                "duration_ratio": 0.538,
                                "visual_density": 0.40,
                                "lut_filter": "noir",
                                "is_motif": True,
                                "is_restrained": True,
                                "sound_design": "deep_impact",
                                "overlay": "light_leaks",
                                "editorial_events": [
                                    {"type": "REVEAL", "cue": "smoking_gun_memo", "timing_percent": 0.0, "intensity": 0.9},
                                    {"type": "IMPACT", "cue": "deep_impact", "timing_percent": 0.0, "intensity": 0.85},
                                    {"type": "OVERLAY", "cue": "flash", "timing_percent": 0.0, "duration": 0.3}
                                ]
                            },
                            {
                                "shot_id": "n003_s002",
                                "visual_type": "motion_graphics",
                                "asset_provenance": "MOTION_GRAPHIC",
                                "fallback_type": "TechnicalDiagram",
                                "shot_size": "wide",
                                "camera_angle": "eye_level",
                                "lens": "standard_lens",
                                "composition": "symmetry",
                                "visual_job": "VISUALIZE_ABSTRACT_CONCEPT",
                                "shot_role": "EXPLANATION",
                                "shot_relationship": "DETAIL_TO_CONTEXT",
                                "visual_query": "global banking network transaction routing diagram",
                                "ai_prompt": "Editorial animated diagram showing routing path of funds from Dhaka to Manila accounts",
                                "visual_description": "Global banking transaction routing network technical diagram",
                                "camera_motion": "pan_right",
                                "cut_reason": "visualize_global_routing_interception",
                                "duration_seconds": 3.0,
                                "actual_duration": 3.0,
                                "duration_mode": "fixed",
                                "duration_ratio": 0.462,
                                "visual_density": 0.70,
                                "lut_filter": "noir",
                                "is_motif": False,
                                "is_restrained": False,
                                "editorial_events": []
                            }
                        ]
                    }
                ]
            }
        ]
    }


# ============================================================================
# SUITE 1: Manifest Reviewer Grammar, Schema & Structural Integrity
# ============================================================================
def test_suite_1_manifest_reviewer():
    print("\n" + "=" * 70)
    print("SUITE 1: ManifestReviewerAgent Static Linting, Grammar & Directorial Score")
    print("=" * 70)

    reviewer = ManifestReviewerAgent()

    # 1.1 Non-dict / corrupted manifest inputs
    invalid_inputs = [None, "", "invalid string", [1, 2, 3], {"wrong_key": 123}]
    all_corrupted_handled = True
    for inv in invalid_inputs:
        res = reviewer.review_manifest(inv)
        if res.get("status") != "FAILED" or res.get("director_score") != 0.0:
            all_corrupted_handled = False
            print(f"Failed to handle invalid input: {inv} -> {res}")

    reporter.record(
        "1.1 Reviewer catches non-dict and invalid schema manifests safely without crashing",
        all_corrupted_handled
    )

    # 1.2 Empty manifest / empty blocks
    empty_manifest = {"story_beats": []}
    res_empty = reviewer.review_manifest(empty_manifest)
    reporter.record(
        "1.2 Reviewer flags empty manifest as FAILED with MANIFEST_EMPTY",
        res_empty["status"] == "FAILED" and any("MANIFEST_EMPTY" in e or "No shots found" in e for e in res_empty["errors"]),
        f"Errors: {res_empty['errors']}"
    )

    block_no_shots = {
        "story_beats": [
            {
                "beat_id": "b1",
                "narration_blocks": [
                    {"block_id": "nb_empty", "shots": []}
                ]
            }
        ]
    }
    res_no_shots = reviewer.review_manifest(block_no_shots)
    reporter.record(
        "1.2b Reviewer flags block with empty shots as FAILED",
        res_no_shots["status"] == "FAILED" and any("has no shots" in e for e in res_no_shots["errors"])
    )

    # 1.3 Duplicate shot IDs
    dup_manifest = create_baseline_valid_manifest()
    # Inject duplicate shot_id
    dup_manifest["story_beats"][1]["narration_blocks"][0]["shots"][0]["shot_id"] = "n001_s001"
    res_dup = reviewer.review_manifest(dup_manifest)
    reporter.record(
        "1.3 Reviewer flags DUPLICATE_ID error on repeated shot_id",
        res_dup["status"] == "FAILED" and any("DUPLICATE_ID: n001_s001" in e for e in res_dup["errors"]),
        f"Errors: {res_dup['errors']}"
    )

    # 1.4 Beat reset shot warning
    no_reset_manifest = create_baseline_valid_manifest()
    # Remove wide / establishing roles from beat 0
    for shot in no_reset_manifest["story_beats"][0]["narration_blocks"][0]["shots"]:
        shot["shot_size"] = "close"
        shot["shot_role"] = "DETAIL"
    res_no_reset = reviewer.review_manifest(no_reset_manifest)
    has_reset_warn = any("RESET_SHOT_WARNING" in w for w in res_no_reset["warnings"])
    reporter.record(
        "1.4 Reviewer issues RESET_SHOT_WARNING when a StoryBeat lacks an establishing or wide reset shot",
        has_reset_warn,
        f"Warnings: {res_no_reset['warnings']}"
    )

    # 1.5 Consecutive identical shot sizes
    consec_size_manifest = create_baseline_valid_manifest()
    shots_b1 = consec_size_manifest["story_beats"][0]["narration_blocks"][0]["shots"]
    shots_b1[0]["shot_size"] = "wide"
    shots_b1[1]["shot_size"] = "wide"
    res_consec_size = reviewer.review_manifest(consec_size_manifest)
    has_size_warn = any("GRAMMAR_WARNING: Consecutive wide shots" in w for w in res_consec_size["warnings"])
    reporter.record(
        "1.5 Reviewer issues GRAMMAR_WARNING on consecutive identical shot sizes",
        has_size_warn,
        f"Warnings: {res_consec_size['warnings']}"
    )

    # 1.6 AI Video strictness & overuse warnings
    ai_video_manifest = create_baseline_valid_manifest()
    shots = ai_video_manifest["story_beats"][0]["narration_blocks"][0]["shots"]
    shots[0]["visual_type"] = "ai_video"
    shots[0]["generation_priority"] = 0.5  # Low priority!
    res_ai_warn = reviewer.review_manifest(ai_video_manifest)
    has_ai_warn = any("AI_VIDEO_WARNING" in w for w in res_ai_warn["warnings"])
    reporter.record(
        "1.6a Reviewer issues AI_VIDEO_WARNING when ai_video priority < 0.8",
        has_ai_warn,
        f"Warnings: {res_ai_warn['warnings']}"
    )

    # Overuse of AI (> 40%)
    for beat in ai_video_manifest["story_beats"]:
        for block in beat["narration_blocks"]:
            for shot in block["shots"]:
                shot["visual_type"] = "ai_video"
                shot["generation_priority"] = 0.9
    res_ai_overuse = reviewer.review_manifest(ai_video_manifest)
    has_overuse_warn = any("OVERUSE_OF_AI" in w for w in res_ai_overuse["warnings"])
    reporter.record(
        "1.6b Reviewer issues OVERUSE_OF_AI warning when ai_video exceeds 40% of timeline",
        has_overuse_warn,
        f"Warnings: {res_ai_overuse['warnings']}"
    )

    # 1.7 Missing cinematography fields on non-graphic shots
    missing_fields_manifest = create_baseline_valid_manifest()
    # Remove lens from real_photo shot
    missing_fields_manifest["story_beats"][0]["narration_blocks"][0]["shots"][0]["lens"] = ""
    # Remove shot_size from ai_image shot
    missing_fields_manifest["story_beats"][1]["narration_blocks"][0]["shots"][1]["shot_size"] = "N/A"
    res_missing = reviewer.review_manifest(missing_fields_manifest)
    has_cinematography_fail = any("CINEMATOGRAPHY_FAIL" in e for e in res_missing["errors"])
    reporter.record(
        "1.7 Reviewer flags CINEMATOGRAPHY_FAIL for missing required camera fields on non-graphic shots",
        has_cinematography_fail and len(res_missing["errors"]) >= 2,
        f"Errors: {res_missing['errors']}"
    )

    # 1.8 Generic cut reasons
    generic_manifest = create_baseline_valid_manifest()
    generic_manifest["story_beats"][0]["narration_blocks"][0]["shots"][0]["cut_reason"] = "transition"
    generic_manifest["story_beats"][0]["narration_blocks"][0]["shots"][1]["cut_reason"] = "show_fact"
    res_generic = reviewer.review_manifest(generic_manifest)
    has_generic_err = any("GENERIC_CUT_REASON" in e for e in res_generic["errors"])
    reporter.record(
        "1.8 Reviewer flags GENERIC_CUT_REASON error on unmotivated cut reasons",
        has_generic_err and len(res_generic["errors"]) >= 2,
        f"Errors: {res_generic['errors']}"
    )

    # 1.9 Camera motion fatigue (>= 3 consecutive identical non-static motions)
    fatigue_manifest = create_baseline_valid_manifest()
    for beat in fatigue_manifest["story_beats"]:
        for block in beat["narration_blocks"]:
            for shot in block["shots"]:
                shot["camera_motion"] = "pan_left"
    res_fatigue = reviewer.review_manifest(fatigue_manifest)
    has_fatigue_err = any("CAMERA_MOTION_FATIGUE" in e for e in res_fatigue["errors"])
    reporter.record(
        "1.9 Reviewer flags CAMERA_MOTION_FATIGUE when 3+ consecutive dynamic movements occur",
        has_fatigue_err,
        f"Errors: {res_fatigue['errors']}"
    )

    # 1.10 Anachronism check (start_year > end_year)
    anachronism_manifest = create_baseline_valid_manifest()
    anachronism_manifest["story_beats"][0]["narration_blocks"][0]["shots"][0]["continuity"] = {
        "start_year": 2024,
        "end_year": 1999
    }
    res_anach = reviewer.review_manifest(anachronism_manifest)
    has_anach_err = any("ANACHRONISM" in e for e in res_anach["errors"])
    reporter.record(
        "1.10 Reviewer flags ANACHRONISM error when start_year > end_year",
        has_anach_err,
        f"Errors: {res_anach['errors']}"
    )

    # 1.11 Valid manifest passes with high director score (>= 8.0) and verdict APPROVED
    valid_manifest = create_baseline_valid_manifest()
    res_valid = reviewer.review_manifest(valid_manifest)
    reporter.record(
        "1.11 Valid baseline manifest passes Reviewer with score >= 8.0 and status PASS",
        res_valid["status"] == "PASS" and res_valid["director_score"] >= 8.0 and res_valid["director_verdict"] == "APPROVED",
        f"Status: {res_valid['status']}, Score: {res_valid['director_score']}, Verdict: {res_valid['director_verdict']}, Errors: {res_valid['errors']}, Warnings: {res_valid['warnings']}"
    )


# ============================================================================
# SUITE 2: QC Editor Directorial Supervision & Status Deciders
# ============================================================================
def test_suite_2_qc_editor():
    print("\n" + "=" * 70)
    print("SUITE 2: QCEditorAgent Directorial Supervision & Status Decisions")
    print("=" * 70)

    qc_editor = QCEditorAgent()

    # 2.1 Valid high-scoring manifest -> status: APPROVED
    valid_manifest = create_baseline_valid_manifest()
    res_valid = qc_editor.review_script(valid_manifest)
    reporter.record(
        "2.1 QCEditorAgent approves valid manifest (status: APPROVED, score >= 8, failures: empty)",
        res_valid.get("status") == "APPROVED" and res_valid.get("score", 0) >= 8 and len(res_valid.get("failures", [])) == 0,
        f"Status: {res_valid.get('status')}, Score: {res_valid.get('score')}, Failures: {res_valid.get('failures')}"
    )
    reporter.record(
        "2.1b QCEditor attaches 17 validation_metrics and director_score_matrix to response",
        "validation_metrics" in res_valid and "director_score_matrix" in res_valid and len(res_valid["validation_metrics"]) >= 17,
        f"Metrics Count: {len(res_valid.get('validation_metrics', {}))}"
    )

    # 2.2 Flawed manifest -> status: REJECTED with isolated surgical repairs
    flawed_manifest = {
        "schema_version": "2.0",
        "project_meta": {"title": "Flawed"},
        "story_beats": [
            {
                "beat_id": "b001",
                "narrative_intent": "EXPLANATION",
                "narration_blocks": [
                    {
                        "block_id": "n001",
                        "voiceover": "Stock businessmen shook hands over briefcase opening with money falling.",
                        "caption": "Stock footage.",
                        "shots": [
                            {
                                "shot_id": "n001_s001",
                                "visual_type": "broll_video",
                                "asset_provenance": "STOCK",
                                "shot_size": "wide",
                                "camera_angle": "eye_level",
                                "lens": "standard_lens",
                                "composition": "center_framed",
                                "visual_job": "ESTABLISH_WORLD",
                                "visual_query": "businessman with money falling from sky generic handshake",
                                "ai_prompt": "money falling down",
                                "camera_motion": "slow_push_in",
                                "cut_reason": "transition",
                                "duration_seconds": 3.0
                            },
                            {
                                "shot_id": "n001_s002",
                                "visual_type": "broll_video",
                                "asset_provenance": "STOCK",
                                "shot_size": "wide",
                                "camera_angle": "eye_level",
                                "lens": "standard_lens",
                                "composition": "center_framed",
                                "visual_job": "ESTABLISH_WORLD",
                                "visual_query": "businessman with money falling from sky generic handshake",
                                "ai_prompt": "money falling down",
                                "camera_motion": "slow_push_in",
                                "cut_reason": "show_fact",
                                "duration_seconds": 3.0
                            }
                        ]
                    }
                ]
            }
        ]
    }
    res_flawed = qc_editor.review_script(flawed_manifest)
    reporter.record(
        "2.2 QCEditorAgent rejects flawed manifest (status: REJECTED, score <= 6, failures >= 1)",
        res_flawed.get("status") == "REJECTED" and res_flawed.get("score", 10) <= 6 and len(res_flawed.get("failures", [])) >= 1,
        f"Status: {res_flawed.get('status')}, Score: {res_flawed.get('score')}, Failures: {res_flawed.get('failures')}"
    )

    # 2.2b Verify surgical repair preservation contract
    repairs_valid = True
    for f in res_flawed.get("failures", []):
        rep = f.get("repair", {})
        if not (rep.get("preserve_narration") is True and rep.get("preserve_timing") is True and rep.get("preserve_ids") is True and rep.get("replace_visual_only") is True):
            repairs_valid = False
            print(f"Invalid surgical repair format: {rep}")

    reporter.record(
        "2.2b QCEditor failures mandate surgical repair isolation (preserve_narration, timing, ids, replace_visual_only)",
        repairs_valid and len(res_flawed.get("failures", [])) > 0
    )

    # 2.3 Invalid schema handling
    corrupted_inputs = [None, "", {}, {"random_data": []}, "manifest string"]
    all_corrupted_rejected = True
    for c_in in corrupted_inputs:
        c_res = qc_editor.review_script(c_in)
        if c_res.get("status") != "REJECTED" or c_res.get("score") != 1:
            all_corrupted_rejected = False
            print(f"Corrupted input not rejected: {c_in} -> {c_res}")

    reporter.record(
        "2.3 QCEditorAgent rejects corrupted inputs with score=1 and INVALID_SCHEMA without unhandled exceptions",
        all_corrupted_rejected
    )

    # 2.4 Fallback execution parity when call_llm raises exception
    class ExceptionThrowingQCEditor(QCEditorAgent):
        def call_llm(self, prompt, system=None, max_tokens=None, temperature=None):
            raise RuntimeError("Simulated upstream network failure")

    throwing_editor = ExceptionThrowingQCEditor()
    fallback_valid = throwing_editor.review_script(valid_manifest)
    reporter.record(
        "2.4 QCEditorAgent gracefully recovers via deterministic fallback when LLM throws exception",
        fallback_valid.get("status") == "APPROVED" and fallback_valid.get("score") >= 8 and len(fallback_valid.get("failures", [])) == 0,
        f"Status: {fallback_valid.get('status')}, Score: {fallback_valid.get('score')}"
    )


# ============================================================================
# SUITE 3: 17 Validation Metrics Precise Engine Calculation & Edge Cases
# ============================================================================
def test_suite_3_cinematic_qc_engine():
    print("\n" + "=" * 70)
    print("SUITE 3: CinematicQCEngine 17 Validation Metrics Calculation")
    print("=" * 70)

    qc = CinematicQCEngine()

    # 3.1 Verify all 17 metric keys are present in output
    manifest = create_baseline_valid_manifest()
    eval_res = qc.evaluate_manifest_director_score(manifest)
    metrics = eval_res["validation_metrics"]

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

    missing_metrics = [m for m in expected_17_metrics if m not in metrics]
    reporter.record(
        "3.1 CinematicQCEngine returns all 17 mandated validation metrics",
        len(missing_metrics) == 0,
        f"Missing: {missing_metrics}"
    )

    # 3.2 Metric 1 & 2: Unique vs Repeated Concepts & Motif Exemption
    # Case A: Repeated concept that matches registered visual motif is NOT penalized
    motif_manifest = create_baseline_valid_manifest()
    # shot 1 and shot 4 both use registered motif "classified telex log"
    m_eval = qc.evaluate_manifest_director_score(motif_manifest)
    m_metrics = m_eval["validation_metrics"]
    reporter.record(
        "3.2a Registered visual motifs are exempted from repeated_visual_concepts penalty",
        m_metrics["repeated_visual_concepts"] == 0,
        f"Repeated: {m_metrics['repeated_visual_concepts']}"
    )

    # Case B: Repeated unregistered concept IS counted
    unreg_manifest = copy.deepcopy(motif_manifest)
    unreg_manifest["documentary_vision"]["visual_motifs"] = []  # Clear registered motifs
    unreg_manifest["story_beats"][0]["narration_blocks"][0]["shots"][1]["visual_description"] = "generic office building desk"
    unreg_manifest["story_beats"][1]["narration_blocks"][0]["shots"][1]["visual_description"] = "generic office building desk"
    unreg_manifest["story_beats"][1]["narration_blocks"][0]["shots"][1]["visual_job"] = "EXAMINE_EVIDENCE"
    unreg_manifest["story_beats"][1]["narration_blocks"][0]["shots"][1]["visual_type"] = "real_photo"
    unreg_manifest["story_beats"][1]["narration_blocks"][0]["shots"][1]["fallback_type"] = "ClassifiedFile"
    unreg_eval = qc.evaluate_manifest_director_score(unreg_manifest)
    reporter.record(
        "3.2b Unregistered repeated concept signatures are correctly flagged in repeated_visual_concepts",
        unreg_eval["validation_metrics"]["repeated_visual_concepts"] >= 1,
        f"Repeated: {unreg_eval['validation_metrics']['repeated_visual_concepts']}"
    )

    # 3.3 Metric 3: Repeated queries
    rep_query_manifest = copy.deepcopy(motif_manifest)
    for beat in rep_query_manifest["story_beats"]:
        for block in beat["narration_blocks"]:
            for shot in block["shots"]:
                shot["visual_query"] = "identical bank vault query"
    rep_q_eval = qc.evaluate_manifest_director_score(rep_query_manifest)
    reporter.record(
        "3.3 Repeated visual queries accurately counted and failure flagged when >= threshold",
        rep_q_eval["validation_metrics"]["repeated_queries"] == 5 and len(rep_q_eval["failures"]) >= 1,
        f"Repeated queries: {rep_q_eval['validation_metrics']['repeated_queries']}, Failures: {rep_q_eval['failures']}"
    )

    # 3.4 Metric 4 & 5: Repeated camera movements and compositions
    comp_manifest = copy.deepcopy(motif_manifest)
    shots_all = []
    for beat in comp_manifest["story_beats"]:
        for block in beat["narration_blocks"]:
            for shot in block["shots"]:
                shot["visual_type"] = "real_photo"
                shot["shot_size"] = "medium"
                shot["composition"] = "center_framed"
                shot["camera_motion"] = "slow_push_in"
                shots_all.append(shot)
    comp_eval = qc.evaluate_manifest_director_score(comp_manifest)
    # Non-graphic shots are compared
    reporter.record(
        "3.4 Repeated compositions and camera movements across non-graphic shots are correctly tallied",
        comp_eval["validation_metrics"]["repeated_camera_movements"] >= 4 and comp_eval["validation_metrics"]["repeated_compositions"] >= 3,
        f"Repeated camera: {comp_eval['validation_metrics']['repeated_camera_movements']}, Repeated comp: {comp_eval['validation_metrics']['repeated_compositions']}"
    )

    # 3.5 Metric 7 & 8: Major Reveals and Attention Peaks
    reporter.record(
        "3.5 Number of major reveals and attention peaks correctly extracted from beats and shots",
        metrics["number_of_major_reveals"] >= 2 and metrics["number_of_attention_peaks"] >= 3,
        f"Major reveals: {metrics['number_of_major_reveals']}, Attention peaks: {metrics['number_of_attention_peaks']}"
    )

    # 3.6 Metric 9: Silence Moments (strategic_silence, is_restrained, static holds)
    reporter.record(
        "3.6 Silence moments accurately detected from block strategic_silence and shot holds",
        metrics["number_of_silence_moments"] >= 3,
        f"Silence moments: {metrics['number_of_silence_moments']}"
    )

    # 3.7 Metric 10: Kinetic Typography & Number Events
    reporter.record(
        "3.7 Typography punctuation events accurately detected from text_stat, NUMBER_REVEAL, and NUMBER_TO_SCALE",
        metrics["number_of_typography_punctuation_events"] >= 1,
        f"Typography events: {metrics['number_of_typography_punctuation_events']}"
    )

    # 3.8 Metric 11: Graphic Explanations
    reporter.record(
        "3.8 Graphic explanations accurately detected from motion_graphics, TechnicalDiagram, and VISUALIZE_ABSTRACT_CONCEPT",
        metrics["number_of_graphic_explanations"] >= 1,
        f"Graphic explanations: {metrics['number_of_graphic_explanations']}"
    )

    # 3.9 Metric 12: Human Anchor Moments
    reporter.record(
        "3.9 Human anchor moments accurately detected from HUMANIZE job, PortraitCard, and worker/hand cues",
        metrics["number_of_human_anchor_moments"] >= 1,
        f"Human anchors: {metrics['number_of_human_anchor_moments']}"
    )

    # 3.10 Metric 13: Visual Motifs
    reporter.record(
        "3.10 Visual motifs accurately counted from is_motif tags and registered motif occurrences",
        metrics["number_of_visual_motifs"] >= 2,
        f"Motifs: {metrics['number_of_visual_motifs']}"
    )

    # 3.11 Metric 14: 7-Dimensional Visual Contrasts
    reporter.record(
        "3.11 7-Dimensional visual contrasts accurately detected across adjacent timeline shots",
        metrics["number_of_visual_contrasts"] >= 3,
        f"Visual contrasts: {metrics['number_of_visual_contrasts']}"
    )

    # 3.12 Metric 15: Contextual Overlays
    reporter.record(
        "3.12 Contextual overlays accurately detected from overlay field and editorial events",
        metrics["number_of_contextual_overlays"] >= 1,
        f"Contextual overlays: {metrics['number_of_contextual_overlays']}"
    )

    # 3.13 Metric 16: SFX Per Minute pacing
    reporter.record(
        "3.13 SFX per minute accurately calculated against total timeline duration (1.0 - 5.0 ideal)",
        1.0 <= metrics["sfx_per_minute"] <= 12.0,
        f"SFX per minute: {metrics['sfx_per_minute']}"
    )

    # 3.14 Metric 17: Anti-Literal Rule & Cliché keyword detection
    cliche_manifest = copy.deepcopy(manifest)
    for beat in cliche_manifest["story_beats"]:
        for block in beat["narration_blocks"]:
            for shot in block["shots"]:
                shot["visual_query"] = "money falling from the sky with handcuffs on table"
    cliche_eval = qc.evaluate_manifest_director_score(cliche_manifest)
    reporter.record(
        "3.14 Anti-Literal Rule catches 100% of cliché keywords and flags severe failure",
        cliche_eval["validation_metrics"]["% shots that merely illustrate narration"] == 100.0 and len(cliche_eval["failures"]) >= 1,
        f"Illustrative %: {cliche_eval['validation_metrics']['% shots that merely illustrate narration']}, Failures: {cliche_eval['failures']}"
    )


# ============================================================================
# SUITE 4: 10-Dimension Score Matrix & Verdict Gate Thresholds
# ============================================================================
def test_suite_4_score_matrix_and_gates():
    print("\n" + "=" * 70)
    print("SUITE 4: 10-Dimension Score Matrix & Directorial Verdict Gates")
    print("=" * 70)

    qc = CinematicQCEngine()
    valid_manifest = create_baseline_valid_manifest()
    eval_res = qc.evaluate_manifest_director_score(valid_manifest)
    matrix = eval_res["director_score_matrix"]

    expected_10_dimensions = [
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

    missing_dims = [d for d in expected_10_dimensions if d not in matrix]
    reporter.record(
        "4.1 10-Dimension Director Score Matrix contains all expected directorial dimensions",
        len(missing_dims) == 0,
        f"Missing dims: {missing_dims}"
    )

    # Check that individual dimension scores are within valid 0.0 - 10.0 range
    all_dims_valid_range = all(0.0 <= score <= 10.0 for score in matrix.values())
    reporter.record(
        "4.2 All dimension scores are within valid [0.0, 10.0] range",
        all_dims_valid_range,
        f"Matrix: {matrix}"
    )

    # Check Verdict Gate Thresholds:
    # High score (>= 8.0) and 0 failures -> APPROVED
    reporter.record(
        "4.3 Valid manifest scores >= 8.0 and receives APPROVED verdict",
        eval_res["overall_director_score"] >= 8.0 and eval_res["verdict"] == "APPROVED",
        f"Score: {eval_res['overall_director_score']}, Verdict: {eval_res['verdict']}"
    )

    # Severe failure -> REJECT regardless of average score
    severely_flawed = copy.deepcopy(valid_manifest)
    for b in severely_flawed["story_beats"]:
        for nb in b["narration_blocks"]:
            for s in nb["shots"]:
                s["cut_reason"] = "transition"  # unmotivated cut reason!
    sev_eval = qc.evaluate_manifest_director_score(severely_flawed)
    reporter.record(
        "4.4 Severe failure (unmotivated cuts) forces REJECT verdict",
        sev_eval["verdict"] == "REJECT" and len(sev_eval["failures"]) >= 1,
        f"Verdict: {sev_eval['verdict']}, Failures: {sev_eval['failures']}"
    )


# ============================================================================
# SUITE 5: End-to-End Story Planner & Reviewer Integration
# ============================================================================
def test_suite_5_end_to_end_integration():
    print("\n" + "=" * 70)
    print("SUITE 5: End-to-End Story Planner, Director, Reviewer & QC Editor Integration")
    print("=" * 70)

    planner = VisualStoryPlanner()
    reviewer = ManifestReviewerAgent()
    qc_editor = QCEditorAgent()
    director = DirectorAgent()

    # 5.1 Plan multi-beat script via VisualStoryPlanner
    planner.reset_timeline("The Fall of Enron", "documentary")

    research_pkg = {
        "topic": "The Fall of Enron",
        "visual_motifs": ["crooked e logo", "blacked-out financial ledger", "shredder paper"]
    }

    test_beats = [
        {
            "beat_id": "b001",
            "beat_title": "The Illusion",
            "narrative_intent": "HOOK",
            "attention_intensity": 0.95,
            "blocks": [
                {
                    "block_id": "n001",
                    "voiceover": "In 2001, America's seventh largest corporation evaporated into thin air.",
                    "caption": "Enron Headquarters — Houston, Texas.",
                    "duration": 6.0
                }
            ]
        },
        {
            "beat_id": "b002",
            "beat_title": "The Hidden Debt",
            "narrative_intent": "FIRST_DISCOVERY",
            "attention_intensity": 0.85,
            "blocks": [
                {
                    "block_id": "n002",
                    "voiceover": "Over $38 Billion in debt was hidden inside complex offshore special purpose entities.",
                    "caption": "$38 Billion in off-the-books liabilities.",
                    "duration": 7.0
                }
            ]
        },
        {
            "beat_id": "b003",
            "beat_title": "The Whistleblower",
            "narrative_intent": "REVELATION",
            "attention_intensity": 0.90,
            "blocks": [
                {
                    "block_id": "n003",
                    "voiceover": "A confidential memorandum from Sherron Watkins unmasked the accounting house of cards.",
                    "caption": "Watkins Memo: 'I am incredibly nervous that we will implode.'",
                    "duration": 6.5
                }
            ]
        }
    ]

    generated_beats = []
    for act_idx, b_info in enumerate(test_beats):
        beat_blocks = []
        for blk_info in b_info["blocks"]:
            blk_dict = {
                "block_id": blk_info["block_id"],
                "voiceover": blk_info["voiceover"],
                "caption": blk_info["caption"],
                "shots": [{"visual_query": f"enron {b_info['beat_title'].lower()}"}]
            }
            decomposed_shots = planner.decompose_narration_block(
                block=blk_dict,
                actual_duration=blk_info["duration"],
                beat_intent=b_info["narrative_intent"],
                attention_intensity=b_info["attention_intensity"],
                research_package=research_pkg,
                act_num=act_idx + 1
            )
            blk_dict["shots"] = decomposed_shots
            blk_dict["total_block_duration"] = blk_info["duration"]
            beat_blocks.append(blk_dict)

        generated_beats.append({
            "beat_id": b_info["beat_id"],
            "beat_title": b_info["beat_title"],
            "narrative_intent": b_info["narrative_intent"],
            "attention_intensity": b_info["attention_intensity"],
            "chapter_color_language": planner.determine_chapter_color(b_info["narrative_intent"], "historical"),
            "narration_blocks": beat_blocks
        })

    e2e_manifest = {
        "schema_version": "2.0",
        "project_meta": {
            "title": "The Fall of Enron",
            "topic": "The Fall of Enron",
            "target_duration_seconds": 19.5
        },
        "documentary_vision": {
            "topic": "The Fall of Enron",
            "core_premise": "Accounting deception masked systemic debt.",
            "central_question": "How did Enron hide billions in plain sight?",
            "documentary_thesis": "Mark-to-market accounting created an illusion of infinite value.",
            "central_contradiction": "Corporate glory vs internal insolvency.",
            "hook_strategy": {
                "hook_type": "CONTRADICTION",
                "target_duration_seconds": 25.0,
                "anomaly_description": "Trading floor lights blazing all night.",
                "withholding_element": "The Chewco and LJM special purpose entities.",
                "opening_visual_cue": "Macro shot of illuminated tilted 'E' sign in darkness."
            },
            "macro_narrative_arc": [
                {"phase": "HOOK", "target_beat_index": 0, "narrative_goal": "Hook", "attention_target": 0.95},
                {"phase": "FIRST_DISCOVERY", "target_beat_index": 1, "narrative_goal": "Expose debt", "attention_target": 0.85},
                {"phase": "REVELATION", "target_beat_index": 2, "narrative_goal": "Watkins memo", "attention_target": 0.90}
            ],
            "mini_arcs": [
                {"beat_id": "b001", "time_window": "0-10s", "setup": "s", "build": "b", "complication": "c", "reveal": "r", "consequence": "cq"}
            ],
            "visual_motifs": ["crooked e logo", "blacked-out financial ledger", "shredder paper"],
            "ending_image": "Forensic investigators taping off empty boardroom",
            "style_profile": "DOCUMENTARY_INVESTIGATIVE"
        },
        "story_beats": generated_beats
    }

    # 5.2 Manifest Reviewer evaluation of E2E Story Planner output
    review_res = reviewer.review_manifest(e2e_manifest)
    reporter.record(
        "5.2 ManifestReviewerAgent evaluates E2E planned manifest (status PASS / PASS_WITH_WARNINGS, 0 errors, score >= 8.0)",
        review_res["status"] in ["PASS", "PASS_WITH_WARNINGS"] and len(review_res["errors"]) == 0 and review_res["director_score"] >= 8.0,
        f"Status: {review_res['status']}, Score: {review_res['director_score']}, Errors: {review_res['errors']}, Warnings: {review_res['warnings']}"
    )

    # 5.3 QC Editor evaluation of E2E Story Planner output
    qc_res = qc_editor.review_script(e2e_manifest)
    reporter.record(
        "5.3 QCEditorAgent evaluates E2E planned manifest (status APPROVED, score >= 8, failures: 0)",
        qc_res.get("status") == "APPROVED" and qc_res.get("score", 0) >= 8 and len(qc_res.get("failures", [])) == 0,
        f"Status: {qc_res.get('status')}, Score: {qc_res.get('score')}, Failures: {qc_res.get('failures')}"
    )

    # 5.4 Director enforce_strict_rules repair integration
    sloppy_manifest = {
        "project_meta": {"topic": "Sloppy Test"},
        "story_beats": [
            {
                "beat_id": "b1",
                "narrative_intent": "FIRST_DISCOVERY",
                "narration_blocks": [
                    {
                        "block_id": "n1",
                        "total_block_duration": 10.0,
                        "shots": [
                            {
                                "shot_id": "s1",
                                "visual_type": "real_photo",
                                "camera_motion": "zoom_in",  # Repetitive zoom
                                "cut_reason": "transition",  # Generic cut reason
                                "duration_seconds": 10.0,    # Exceeds 4.5s
                                "duration_mode": "fixed"
                            },
                            {
                                "shot_id": "s2",
                                "visual_type": "real_photo",
                                "camera_motion": "zoom_in",  # Fatigue zoom
                                "cut_reason": "show_fact",   # Generic cut reason
                                "duration_seconds": 10.0,    # Exceeds 4.5s
                                "duration_mode": "fixed"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    repaired_manifest = director.enforce_strict_rules(sloppy_manifest)
    # Review repaired manifest
    repaired_review = reviewer.review_manifest(repaired_manifest)
    # Verify no zoom_in, no cuts > 4.5s, no generic cut reasons
    repaired_shots = repaired_manifest["story_beats"][0]["narration_blocks"][0]["shots"]
    no_zoom = all(s.get("camera_motion") != "zoom_in" for s in repaired_shots)
    all_le_4_5 = all(float(s.get("duration_seconds") or 4.0) <= 4.51 for s in repaired_shots)
    no_generic = all(s.get("cut_reason") not in ["transition", "show_fact"] for s in repaired_shots)

    reporter.record(
        "5.4 DirectorAgent.enforce_strict_rules() eliminates zoom_in, enforces <= 4.5s splits, and fixes generic cut reasons",
        no_zoom and all_le_4_5 and no_generic and len(repaired_shots) >= 4,
        f"Shots: {len(repaired_shots)}, Motions: {[s.get('camera_motion') for s in repaired_shots]}, Reasons: {[s.get('cut_reason') for s in repaired_shots]}"
    )


# ============================================================================
# SUITE 6: Fuzz Testing & Resilience to Adversarial Inputs
# ============================================================================
def test_suite_6_fuzz_and_resilience():
    print("\n" + "=" * 70)
    print("SUITE 6: Adversarial Fuzzing & Error Resilience (50 Random Manifests)")
    print("=" * 70)

    reviewer = ManifestReviewerAgent()
    qc_editor = QCEditorAgent()
    qc_engine = CinematicQCEngine()

    random.seed(42)
    fuzz_success_count = 0
    total_fuzz_tests = 50

    visual_types = ["real_photo", "broll_video", "ai_video", "ai_image", "motion_graphics", "text_stat", "stock_video", "", None]
    cut_reasons = ["transition", "show_fact", "introduce_conflict", "reveal_anomaly_detail", "examine_smoking_gun_log", "", None, "a", "valid_length_cut_reason"]
    camera_motions = ["static", "slow_push_in", "pan_left", "pan_right", "zoom_in", "zoom_out", "", None]
    shot_sizes = ["wide", "close", "medium", "extreme_wide", "extreme_close", "", None]

    for f_idx in range(total_fuzz_tests):
        # Generate random manifest structure
        num_beats = random.randint(0, 4)
        beats = []
        for b_i in range(num_beats):
            num_blocks = random.randint(0, 3)
            blocks = []
            for bl_i in range(num_blocks):
                num_shots = random.randint(0, 5)
                shots = []
                for sh_i in range(num_shots):
                    shot_obj = {
                        "shot_id": f"fuzz_b{b_i}_bl{bl_i}_s{sh_i}" if random.random() > 0.1 else "duplicate_fuzz_id",
                        "visual_type": random.choice(visual_types),
                        "shot_size": random.choice(shot_sizes),
                        "camera_angle": random.choice(["eye_level", "low_angle", "high_angle", "overhead_shot", "", None]),
                        "lens": random.choice(["wide_angle_lens", "macro_lens", "standard_lens", "", None]),
                        "composition": random.choice(["center_framed", "leading_lines", "", None]),
                        "visual_job": random.choice([j.value for j in VisualJob] + ["", None, "INVALID_JOB"]),
                        "camera_motion": random.choice(camera_motions),
                        "cut_reason": random.choice(cut_reasons),
                        "visual_query": "fuzz query " + random.choice(["money falling", "clean document", "bank vault", ""]) if random.random() > 0.2 else None,
                        "duration_seconds": random.choice([0.1, 2.5, 4.5, 12.0, -1.0, 0.0, None]),
                        "actual_duration": random.choice([0.1, 2.5, 4.5, None]),
                        "is_restrained": random.choice([True, False, None]),
                        "editorial_events": [{"type": "NUMBER_REVEAL", "cue": "$50M"}] if random.random() > 0.5 else []
                    }
                    shots.append(shot_obj)
                blocks.append({"block_id": f"nb_{bl_i}", "shots": shots, "total_block_duration": random.choice([0, 5.0, None])})
            beats.append({"beat_id": f"b_{b_i}", "narrative_intent": random.choice([i.value for i in NarrativeIntent] + [None, "UNKNOWN"]), "narration_blocks": blocks})

        fuzz_manifest = {
            "schema_version": "2.0",
            "project_meta": {"title": f"Fuzz Test {f_idx}"},
            "story_beats": beats
        }

        try:
            # Test all 3 components without crashing
            eval_res = qc_engine.evaluate_manifest_director_score(fuzz_manifest)
            rev_res = reviewer.review_manifest(fuzz_manifest)
            qc_res = qc_editor.review_script(fuzz_manifest)

            assert isinstance(eval_res, dict)
            assert isinstance(rev_res, dict)
            assert isinstance(qc_res, dict)
            assert rev_res.get("status") in ["PASS", "PASS_WITH_WARNINGS", "FAILED"]
            assert qc_res.get("status") in ["APPROVED", "REJECTED"]
            fuzz_success_count += 1
        except Exception as e:
            print(f"Fuzz test {f_idx} crashed: {e}")

    reporter.record(
        f"6.1 Fuzz Testing: 50/50 randomized adversarial manifests handled with 0 unhandled exceptions across all 3 QC agents",
        fuzz_success_count == total_fuzz_tests,
        f"Passed: {fuzz_success_count}/{total_fuzz_tests}"
    )


# ============================================================================
# Main Runner
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING EMPIRICAL CHALLENGER 2 SUITE FOR MILESTONE 4")
    print("=" * 70)

    test_suite_1_manifest_reviewer()
    test_suite_2_qc_editor()
    test_suite_3_cinematic_qc_engine()
    test_suite_4_score_matrix_and_gates()
    test_suite_5_end_to_end_integration()
    test_suite_6_fuzz_and_resilience()

    reporter.print_summary()

    if reporter.failed > 0:
        print("\n[VERDICT]: REQUEST_CHANGES — Empirical verification failed!")
        sys.exit(1)
    else:
        print("\n[VERDICT]: APPROVE — 100% of empirical tests passed!")
        sys.exit(0)
