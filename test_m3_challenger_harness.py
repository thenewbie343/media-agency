"""
Empirical Challenger Test Harness for Milestone 3 (Visual Sequence Director Layer & Visual Story Planner)
Tests VisualSequenceDirector, Mute Test, Fallback Cascade, Shot Relationships, and Directorial Integration.
"""

import sys
import json
import pytest
from typing import Dict, Any, List

from agents.schema import (
    VisualSequencePlan,
    StoryBeat,
    VisualJob,
    ShotRelationship,
    NarrativeIntent,
    DocumentaryResearchPackage,
    DocumentaryVision,
    EvidenceItem,
    NumberItem,
    PersonAnchor,
    TurningPointItem,
    MajorRevealItem,
    HookStrategy,
    NarrativePhasePlan,
    MiniArcPlan
)
from agents.visual_sequence_director import VisualSequenceDirector
from agents.shot_relationship import ShotRelationshipEngine
from agents.visual_intent import VisualIntentEngine
from agents.director_memory import DirectorMemory
from agents.visual_story_planner import VisualStoryPlanner


test_results = {"passed": 0, "failed": 0, "warnings": 0, "details": []}

def record_pass(test_id: str, msg: str):
    test_results["passed"] += 1
    test_results["details"].append(("PASS", test_id, msg))
    print(f"[PASS] [{test_id}] {msg}")

import traceback

def record_fail(test_id: str, msg: str):
    test_results["failed"] += 1
    test_results["details"].append(("FAIL", test_id, msg))
    print(f"[FAIL] [{test_id}] {msg}")
    traceback.print_exc()

def record_warn(test_id: str, msg: str):
    test_results["warnings"] += 1
    test_results["details"].append(("WARN", test_id, msg))
    print(f"[WARN] [{test_id}] {msg}")


def run_all_tests():
    print("======================================================================")
    print("CHALLENGER 1 EMPIRICAL TEST SUITE: M3 VISUAL SEQUENCE DIRECTOR LAYER")
    print("======================================================================")

    vsd = VisualSequenceDirector()

    # ============================================================================
    # SECTION 1: VisualSequenceDirector.plan_visual_sequence() & 4 Change Metrics
    # ============================================================================
    print("\n>>> SECTION 1: VisualSequenceDirector.plan_visual_sequence() & 4 Change Metrics <<<")

    # 1.1 Mock Fallback Validation
    try:
        mock_plan = vsd._get_mock_fallback("", "", True)
        plan_obj = VisualSequencePlan.model_validate(mock_plan)
        assert plan_obj.intention != ""
        assert " vs " in plan_obj.visual_argument or "vs" in plan_obj.visual_argument
        assert plan_obj.withholding_strategy != ""
        assert plan_obj.memorable_image != ""
        assert plan_obj.sequence_ending_statement != ""
        assert 0.0 <= plan_obj.information_change <= 1.0
        assert 0.0 <= plan_obj.emotional_change <= 1.0
        assert 0.0 <= plan_obj.visual_change <= 1.0
        assert 0.0 <= plan_obj.scale_change <= 1.0
        record_pass("T1.1_MOCK_FALLBACK", "VisualSequenceDirector._get_mock_fallback() generates 100% valid VisualSequencePlan")
    except Exception as e:
        record_fail("T1.1_MOCK_FALLBACK", f"Mock fallback failed validation: {e}")

    # 1.2 Deterministic Planning across all 11 Macro Narrative Intents + Legacy Intents
    all_intents = [
        "HOOK", "CENTRAL_QUESTION", "CONTEXT", "FIRST_DISCOVERY", "COMPLICATION",
        "ESCALATION", "REVELATION", "CONSEQUENCE", "DEEPER_REVELATION",
        "FINAL_CONTRADICTION", "PAYOFF", "EVIDENCE", "MYSTERY", "EXPLANATION", "CONFLICT", "RESOLUTION"
    ]
    try:
        for intent in all_intents:
            beat = {
                "beat_id": f"beat_{intent.lower()}",
                "narrative_intent": intent,
                "description": f"Testing macro sequence for {intent} phase in the documentary.",
                "narration_blocks": [
                    {"block_id": "b1", "voiceover": f"This is voiceover for {intent}.", "caption": f"{intent} caption."}
                ]
            }
            plan = vsd.plan_visual_sequence(beat)
            assert isinstance(plan, VisualSequencePlan), f"Expected VisualSequencePlan for intent {intent}"
            assert plan.intention, f"Empty intention for {intent}"
            assert plan.visual_argument, f"Empty visual_argument for {intent}"
            assert plan.withholding_strategy, f"Empty withholding_strategy for {intent}"
            assert plan.memorable_image, f"Empty memorable_image for {intent}"
            assert plan.sequence_ending_statement, f"Empty sequence_ending_statement for {intent}"
            assert 0.0 <= plan.information_change <= 1.0, f"Invalid info change {plan.information_change} for {intent}"
            assert 0.0 <= plan.emotional_change <= 1.0, f"Invalid emo change {plan.emotional_change} for {intent}"
            assert 0.0 <= plan.visual_change <= 1.0, f"Invalid vis change {plan.visual_change} for {intent}"
            assert 0.0 <= plan.scale_change <= 1.0, f"Invalid scale change {plan.scale_change} for {intent}"
        record_pass("T1.2_ALL_INTENTS_PLANS", f"Successfully generated valid VisualSequencePlan for all {len(all_intents)} narrative intents")
    except Exception as e:
        record_fail("T1.2_ALL_INTENTS_PLANS", f"Failed generating plans across intents: {e}")

    # 1.3 Integration with DocumentaryResearchPackage and DocumentaryVision objects
    try:
        research_pkg = DocumentaryResearchPackage(
            topic="The $81 Million Cyber Heist",
            central_question="How did a simple typographical error prevent a billion-dollar heist?",
            documentary_thesis="Modern financial architecture is vulnerable at the seam between automation and human oversight.",
            central_contradiction="hyper_automated_swift_network vs fragile_paper_printer_infrastructure",
            audience_initial_belief="Global banks have infallible digital security.",
            what_the_audience_thinks_is_true="SWIFT transfers are instantaneous and unhackable.",
            what_is_actually_more_complicated="A single unmonitored line printer was the sole physical verification point.",
            protagonist_or_human_anchor="Bangladesh Bank night-shift technicians",
            antagonistic_force_or_system="Lazarus Group cyber operatives",
            stakes="$951 million in sovereign reserves at imminent risk",
            historical_context="February 2016 international banking vulnerability",
            final_payoff="The realization that digital security is only as strong as physical paper logging.",
            ending_image_opportunity="Slow static pull-back from a solitary unplugged dot-matrix printer in Dhaka."
        )

        vision = DocumentaryVision(
            topic="The $81 Million Cyber Heist",
            core_premise="Forensic deconstruction of the Bangladesh Bank cyber attack",
            central_question="How did a typo save $850 million?",
            documentary_thesis="Automation without physical redundancy invites catastrophic failure.",
            central_contradiction="digital_supremacy vs mechanical_failure",
            hook_strategy=HookStrategy(
                hook_type="CONTRADICTION",
                target_duration_seconds=25.0,
                anomaly_description="A printer stops feeding paper at 11:47 PM in Dhaka.",
                withholding_element="The fact that $1 billion is currently transferring to the Philippines.",
                opening_visual_cue="Macro close up of dot matrix printer ribbon frozen mid-stroke."
            ),
            ending_image="Empty server room in Dhaka bathed in amber emergency standby light."
        )

        beat = {
            "beat_id": "b_heist_discovery",
            "narrative_intent": NarrativeIntent.FIRST_DISCOVERY,
            "description": "The technician notices the paper tray is empty and attempts a reboot.",
            "narration_blocks": [
                {"block_id": "n1", "voiceover": "On Friday morning, duty manager Zubair noticed the automatic printer was dead quiet.", "caption": "Friday morning, Dhaka."}
            ]
        }

        # Test passing models directly
        plan_from_models = vsd.plan_visual_sequence(beat, research_package=research_pkg, vision=vision)
        assert isinstance(plan_from_models, VisualSequencePlan)
        assert "hyper_automated_swift_network vs fragile_paper_printer_infrastructure" in plan_from_models.visual_argument or "vs" in plan_from_models.visual_argument
        assert plan_from_models.information_change >= 0.7

        # Test passing dicts
        plan_from_dicts = vsd.plan_visual_sequence(beat, research_package=research_pkg.model_dump(), vision=vision.model_dump())
        assert isinstance(plan_from_dicts, VisualSequencePlan)
        record_pass("T1.3_RESEARCH_VISION_INGESTION", "VisualSequenceDirector smoothly ingests both Pydantic models and plain dicts")
    except Exception as e:
        record_fail("T1.3_RESEARCH_VISION_INGESTION", f"Failed ingesting research package and vision: {e}")

    # 1.4 Edge Case Inputs for plan_visual_sequence
    try:
        # Empty beat dict
        empty_plan = vsd.plan_visual_sequence({})
        assert isinstance(empty_plan, VisualSequencePlan)
        assert 0.0 <= empty_plan.information_change <= 1.0

        # Beat with weird/unknown intent string
        custom_plan = vsd.plan_visual_sequence({"narrative_intent": "UNKNOWN_CUSTOM_PHASE", "description": "Custom test beat"})
        assert isinstance(custom_plan, VisualSequencePlan)
        assert "vs" in custom_plan.visual_argument
        record_pass("T1.4_EDGE_CASE_INPUTS", "VisualSequenceDirector handles empty dicts and unrecognized intents gracefully")
    except Exception as e:
        record_fail("T1.4_EDGE_CASE_INPUTS", f"Edge case input failure: {e}")


    # ============================================================================
    # SECTION 2: Anti-Literal Rule & Mute Test Engine (evaluate_mute_test)
    # ============================================================================
    print("\n>>> SECTION 2: Anti-Literal Rule & Mute Test Engine (evaluate_mute_test) <<<")

    # 2.1 Pass Valid Narrative-Rich Sequences
    try:
        valid_sequence = [
            {
                "shot_id": "s1",
                "visual_job": VisualJob.ESTABLISH_WORLD.value,
                "visual_query": "Dhaka central bank exterior at dusk with moody streetlights",
                "camera_motion": "slow_push_in",
                "shot_size": "wide",
                "is_restrained": False
            },
            {
                "shot_id": "s2",
                "visual_job": VisualJob.EXAMINE_EVIDENCE.value,
                "visual_query": "Forensic macro view of paper transaction logs on desk",
                "camera_motion": "static",
                "shot_size": "extreme_close",
                "is_restrained": True
            },
            {
                "shot_id": "s3",
                "visual_job": VisualJob.SHOW_SCALE.value,
                "visual_query": "Kinetic diagram showing 35 international SWIFT routing nodes",
                "camera_motion": "slow_push_in",
                "shot_size": "wide",
                "is_restrained": False
            },
            {
                "shot_id": "s4",
                "visual_job": VisualJob.REVEAL.value,
                "visual_query": "Confidential telex showing spelling mistake 'fandation' under lamp",
                "camera_motion": "static",
                "shot_size": "close",
                "is_restrained": True
            }
        ]

        mute_eval = vsd.evaluate_mute_test(valid_sequence)
        assert mute_eval["mute_test_passed"] is True, "Valid dialectical sequence must pass Mute Test"
        assert mute_eval["verdict"] == "PASSED"
        assert mute_eval["has_setup"] is True
        assert mute_eval["has_development"] is True
        assert mute_eval["has_climax_or_consequence"] is True
        assert mute_eval["distinct_visual_jobs"] >= 3
        assert mute_eval["has_restraint"] is True
        assert len(mute_eval["literal_violations"]) == 0
        assert mute_eval["score"] >= 8.0
        record_pass("T2.1_MUTE_TEST_VALID_SEQUENCE", f"Valid sequence passed Mute Test with score {mute_eval['score']}/10.0")
    except Exception as e:
        record_fail("T2.1_MUTE_TEST_VALID_SEQUENCE", f"Valid sequence failed Mute Test: {e}")

    # 2.2 Rejection of Banned Cliché Keywords
    banned_keywords = [
        "money falling", "handshake", "scales of justice", "piggy bank",
        "generic businessman", "generic code typing", "handcuffs on table",
        "coins falling", "man crying over laptop", "hacker in hoodie laughing",
        "stock handshake", "briefcase opening with money", "stock footage suit"
    ]
    try:
        for kw in banned_keywords:
            cliche_sequence = [
                {"shot_id": "s1", "visual_job": "ESTABLISH_WORLD", "visual_query": f"Authentic bank building"},
                {"shot_id": "s2", "visual_job": "SHOW_EVIDENCE", "visual_query": f"Macro view of {kw} on screen"},
                {"shot_id": "s3", "visual_job": "REVEAL", "visual_query": "Static case file"}
            ]
            eval_res = vsd.evaluate_mute_test(cliche_sequence)
            assert eval_res["mute_test_passed"] is False, f"Sequence containing banned keyword '{kw}' must FAIL Mute Test"
            assert len(eval_res["literal_violations"]) >= 1, f"Expected violation recorded for '{kw}'"
            assert vsd.is_literal_illustration(cliche_sequence[1]) is True, f"is_literal_illustration must return True for '{kw}'"

        # Also test uppercase / mixed case keyword detection
        upper_cliche = {"shot_id": "s1", "visual_job": "SHOW_EVIDENCE", "ai_prompt": "Cinematic 4K shot of MONEY FALLING into a PIGGY BANK"}
        assert vsd.is_literal_illustration(upper_cliche) is True
        record_pass("T2.2_BAN_LITERAL_CLICHES", f"All {len(banned_keywords)} banned literal cliché keywords correctly detected and rejected")
    except Exception as e:
        record_fail("T2.2_BAN_LITERAL_CLICHES", f"Banned cliché test failed: {e}")

    # 2.3 Boundary and Edge Cases in evaluate_mute_test
    try:
        # A. Empty sequence
        res_empty = vsd.evaluate_mute_test([])
        assert res_empty["mute_test_passed"] is False
        assert res_empty["score"] == 0.0
        assert res_empty["verdict"] == "FAILED"

        # B. Sequence with NO development or climax (only setup)
        setup_only = [
            {"shot_id": "s1", "visual_job": "ESTABLISH_WORLD", "visual_query": "City streets at night"},
            {"shot_id": "s2", "visual_job": "ESTABLISH_WORLD", "visual_query": "Bank building exterior"}
        ]
        res_setup_only = vsd.evaluate_mute_test(setup_only)
        assert res_setup_only["mute_test_passed"] is False, "Setup-only sequence with no development or climax must fail"

        # C. Single shot sequence
        single_shot = [{"shot_id": "s1", "visual_job": "REVEAL", "visual_query": "Smoking gun file", "camera_motion": "static", "is_restrained": True}]
        res_single = vsd.evaluate_mute_test(single_shot)
        assert res_single["distinct_visual_jobs"] == 1
        assert res_single["has_climax_or_consequence"] is True

        # D. Sequence with no restraint (all moving shots)
        moving_sequence = [
            {"shot_id": "s1", "visual_job": "ESTABLISH_WORLD", "visual_query": "Streets", "camera_motion": "pan_left"},
            {"shot_id": "s2", "visual_job": "SHOW_SCALE", "visual_query": "Network", "camera_motion": "pan_right"},
            {"shot_id": "s3", "visual_job": "REVEAL", "visual_query": "File", "camera_motion": "dolly_in"}
        ]
        res_moving = vsd.evaluate_mute_test(moving_sequence)
        assert res_moving["has_restraint"] is False
        record_pass("T2.3_MUTE_TEST_BOUNDARIES", "Boundary edge cases (empty shots, setup-only, single shot, no restraint) handled properly")
    except Exception as e:
        record_fail("T2.3_MUTE_TEST_BOUNDARIES", f"Boundary testing in evaluate_mute_test failed: {e}")


    # ============================================================================
    # SECTION 3: 5-Tier No-Generic-B-Roll Fallback Cascade (apply_fallback_cascade)
    # ============================================================================
    print("\n>>> SECTION 3: 5-Tier No-Generic-B-Roll Fallback Cascade <<<")

    # 3.1 Individual Tier Routing Verification
    try:
        # Tier 1: ALTERNATIVE_INTERPRETATION
        # Case A: VisualJob HUMANIZE or CONTRAST
        c1_job = vsd.apply_fallback_cascade(VisualJob.HUMANIZE)
        assert c1_job["cascade_level"] == 1
        assert c1_job["strategy"] == "ALTERNATIVE_INTERPRETATION"
        assert c1_job["asset_provenance"] == "AUTHENTIC_PHOTO"
        assert c1_job["fallback_type"] == "PortraitCard"
        assert c1_job["priority_score"] == 1.0

        c1_str = vsd.apply_fallback_cascade("CONTRAST")
        assert c1_str["cascade_level"] == 1

        # Case B: intent_info has_human_anchor
        c1_anchor = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_human_anchor": True})
        assert c1_anchor["cascade_level"] == 1

        # Case C: available_assets has_metaphorical_photo
        c1_meta = vsd.apply_fallback_cascade("SHOW_SCALE", available_assets={"has_metaphorical_photo": True})
        assert c1_meta["cascade_level"] == 1

        # Tier 2: MOTION_GRAPHIC_DIAGRAM
        # Case A: VisualJob SHOW_SCALE, SHOW_COMPARISON, VISUALIZE_ABSTRACT_CONCEPT
        c2_scale = vsd.apply_fallback_cascade(VisualJob.SHOW_SCALE)
        assert c2_scale["cascade_level"] == 2
        assert c2_scale["strategy"] == "MOTION_GRAPHIC_DIAGRAM"
        assert c2_scale["asset_provenance"] == "MOTION_GRAPHIC"
        assert c2_scale["priority_score"] == 0.9

        # Case B: intent_info has_statistic -> CinematicText & text_stat
        c2_stat = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_statistic": True})
        assert c2_stat["cascade_level"] == 2
        assert c2_stat["visual_type"] == "text_stat"
        assert c2_stat["fallback_type"] == "CinematicText"

        # Case C: intent_info has_process or has_timestamp
        c2_proc = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_process": True})
        assert c2_proc["cascade_level"] == 2
        assert c2_proc["fallback_type"] == "TechnicalDiagram"

        # Tier 3: AI_RECONSTRUCTION
        # Case A: VisualJob RECONSTRUCT_EVENT, BUILD_MYSTERY, ESCALATE
        c3_rec = vsd.apply_fallback_cascade(VisualJob.RECONSTRUCT_EVENT)
        assert c3_rec["cascade_level"] == 3
        assert c3_rec["strategy"] == "AI_RECONSTRUCTION"
        assert c3_rec["asset_provenance"] == "AI_RECONSTRUCTION"
        assert c3_rec["fallback_type"] == "EvidenceBoard"
        assert c3_rec["visual_type"] == "ai_image"
        assert c3_rec["priority_score"] == 0.8

        # Case B: VisualJob ESCALATE -> ai_video
        c3_esc = vsd.apply_fallback_cascade("ESCALATE")
        assert c3_esc["cascade_level"] == 3
        assert c3_esc["visual_type"] == "ai_video"

        # Case C: intent_info has_cyber
        c3_cyber = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_cyber": True})
        assert c3_cyber["cascade_level"] == 3

        # Tier 4: ARCHIVAL_DOCUMENT
        # Case A: VisualJob SHOW_EVIDENCE, EXAMINE_EVIDENCE, REVEAL_DETAIL, REVEAL, PAYOFF
        c4_ev = vsd.apply_fallback_cascade(VisualJob.SHOW_EVIDENCE)
        assert c4_ev["cascade_level"] == 4
        assert c4_ev["strategy"] == "ARCHIVAL_DOCUMENT"
        assert c4_ev["asset_provenance"] == "ARCHIVAL_FOOTAGE"
        assert c4_ev["fallback_type"] == "ArchivalDocument"
        assert c4_ev["priority_score"] == 0.7

        # Case B: intent_info has_anomaly -> ClassifiedFile
        c4_anomaly = vsd.apply_fallback_cascade(VisualJob.EXAMINE_EVIDENCE, intent_info={"has_anomaly": True})
        assert c4_anomaly["cascade_level"] == 4
        assert c4_anomaly["fallback_type"] == "ClassifiedFile"

        # Tier 5: GENERIC_BROLL (Last Resort)
        c5_broll = vsd.apply_fallback_cascade(VisualJob.ESTABLISH_WORLD)
        assert c5_broll["cascade_level"] == 5
        assert c5_broll["strategy"] == "GENERIC_BROLL"
        assert c5_broll["asset_provenance"] == "STOCK"
        assert c5_broll["fallback_type"] == "PhotoWall"
        assert c5_broll["visual_type"] == "broll_video"
        assert c5_broll["priority_score"] == 0.3

        record_pass("T3.1_INDIVIDUAL_TIERS", "All 5 individual cascade tiers route accurately with correct metadata")
    except Exception as e:
        record_fail("T3.1_INDIVIDUAL_TIERS", f"Individual tier routing failed: {e}")

    # 3.2 Precedence & Strict Priority Ordering (Higher Tiers Preempt Lower Tiers)
    try:
        # Tier 1 vs Tier 2, 3, 4, 5
        # If Tier 1 condition is met, it MUST return Level 1 even if Tier 2/3/4/5 flags are active
        conflict_1_all = vsd.apply_fallback_cascade(
            visual_job="HUMANIZE",  # Tier 1
            intent_info={
                "has_statistic": True,  # Tier 2
                "has_cyber": True,      # Tier 3
                "has_anomaly": True,    # Tier 4
            },
            available_assets={
                "can_render_diagram": True,  # Tier 2
                "has_ai_generator": True,    # Tier 3
                "has_archival_doc": True     # Tier 4
            }
        )
        assert conflict_1_all["cascade_level"] == 1, f"Expected Tier 1, got {conflict_1_all['cascade_level']}"
        assert conflict_1_all["strategy"] == "ALTERNATIVE_INTERPRETATION"

        # Tier 2 vs Tier 3, 4, 5 (Tier 1 conditions False)
        conflict_2_all = vsd.apply_fallback_cascade(
            visual_job="SHOW_SCALE",  # Tier 2
            intent_info={
                "has_human_anchor": False,
                "has_statistic": True,    # Tier 2
                "has_cyber": True,        # Tier 3
                "has_anomaly": True       # Tier 4
            },
            available_assets={
                "has_metaphorical_photo": False,
                "has_ai_generator": True,  # Tier 3
                "has_archival_doc": True   # Tier 4
            }
        )
        assert conflict_2_all["cascade_level"] == 2, f"Expected Tier 2, got {conflict_2_all['cascade_level']}"
        assert conflict_2_all["strategy"] == "MOTION_GRAPHIC_DIAGRAM"

        # Tier 3 vs Tier 4, 5 (Tier 1 and 2 False)
        conflict_3_all = vsd.apply_fallback_cascade(
            visual_job="BUILD_MYSTERY",  # Tier 3
            intent_info={
                "has_human_anchor": False,
                "has_statistic": False,
                "has_process": False,
                "has_timestamp": False,
                "has_cyber": True,         # Tier 3
                "has_anomaly": True,       # Tier 4
                "has_evidence": True       # Tier 4
            },
            available_assets={
                "has_metaphorical_photo": False,
                "can_render_diagram": False,
                "has_ai_generator": True,  # Tier 3
                "has_archival_doc": True   # Tier 4
            }
        )
        assert conflict_3_all["cascade_level"] == 3, f"Expected Tier 3, got {conflict_3_all['cascade_level']}"
        assert conflict_3_all["strategy"] == "AI_RECONSTRUCTION"

        # Tier 4 vs Tier 5 (Tier 1, 2, 3 False)
        conflict_4_all = vsd.apply_fallback_cascade(
            visual_job="SHOW_EVIDENCE",  # Tier 4
            intent_info={
                "has_human_anchor": False,
                "has_statistic": False,
                "has_process": False,
                "has_timestamp": False,
                "has_cyber": False,
                "has_anomaly": True,       # Tier 4
                "has_evidence": True       # Tier 4
            },
            available_assets={
                "has_metaphorical_photo": False,
                "can_render_diagram": False,
                "has_ai_generator": False,
                "has_archival_doc": True   # Tier 4
            }
        )
        assert conflict_4_all["cascade_level"] == 4, f"Expected Tier 4, got {conflict_4_all['cascade_level']}"
        assert conflict_4_all["strategy"] == "ARCHIVAL_DOCUMENT"

        record_pass("T3.2_STRICT_PRIORITY_PRECEDENCE", "Strict 5-tier fallback cascade priority ordering (1 > 2 > 3 > 4 > 5) rigorously verified under cross-tier conflicts")
    except Exception as e:
        record_fail("T3.2_STRICT_PRIORITY_PRECEDENCE", f"Priority precedence test failed: {e}")

    # 3.3 Coverage of all 20 VisualJobs through Fallback Cascade
    try:
        all_jobs = [j for j in VisualJob]
        tier_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for job in all_jobs:
            res = vsd.apply_fallback_cascade(job)
            lvl = res["cascade_level"]
            tier_distribution[lvl] += 1
            assert 1 <= lvl <= 5
        
        # Verify distribution
        assert tier_distribution[1] == 2   # HUMANIZE, CONTRAST
        assert tier_distribution[2] == 3   # SHOW_SCALE, SHOW_COMPARISON, VISUALIZE_ABSTRACT_CONCEPT
        assert tier_distribution[3] == 3   # RECONSTRUCT_EVENT, BUILD_MYSTERY, ESCALATE
        assert tier_distribution[4] == 5   # SHOW_EVIDENCE, EXAMINE_EVIDENCE, REVEAL_DETAIL, REVEAL, PAYOFF
        assert tier_distribution[5] == 7   # ESTABLISH_WORLD, INTRODUCE_CHARACTER, INTRODUCE_OBJECT, FOLLOW_OBJECT, WITHHOLD_INFORMATION, INTERRUPT, CONSEQUENCE
        record_pass("T3.3_ALL_20_JOBS_CASCADE_MAPPING", f"All 20 VisualJobs cleanly mapped across cascade tiers: {tier_distribution}")
    except Exception as e:
        record_fail("T3.3_ALL_20_JOBS_CASCADE_MAPPING", f"VisualJob cascade mapping failed: {e}")


    # ============================================================================
    # SECTION 4: Integration with ShotRelationship, VisualStoryPlanner & Memory
    # ============================================================================
    print("\n>>> SECTION 4: Integration with ShotRelationship, VisualStoryPlanner & Memory <<<")

    # 4.1 ShotRelationshipEngine - All 12 Relational Transitions
    try:
        sre = ShotRelationshipEngine()
        
        # 1. NUMBER_TO_SCALE
        s_prev = {"visual_job": "SHOW_SCALE", "visual_type": "text_stat", "shot_size": "medium", "camera_motion": "static"}
        s_curr = {"visual_job": "SHOW_COMPARISON", "shot_size": "medium", "camera_motion": "static"}
        res_num = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_num["shot_relationship"] == "NUMBER_TO_SCALE"
        assert res_num["shot_size"] == "wide"
        assert res_num["lens"] == "wide_angle_lens"
        assert res_num["visual_density"] == 0.40

        # 2. EVIDENCE_TO_REVEAL
        s_prev = {"visual_job": "SHOW_EVIDENCE", "shot_size": "close", "camera_motion": "slow_push_in"}
        s_curr = {"visual_job": "REVEAL", "shot_size": "wide", "camera_motion": "pan_left"}
        res_ev = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_ev["shot_relationship"] == "EVIDENCE_TO_REVEAL"
        assert res_ev["camera_motion"] == "static"
        assert res_ev["is_restrained"] is True

        # 3. OBJECT_TO_PERSON
        s_prev = {"visual_job": "INTRODUCE_OBJECT", "shot_size": "close"}
        s_curr = {"visual_job": "INTRODUCE_CHARACTER", "shot_size": "wide"}
        res_op = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_op["shot_relationship"] == "OBJECT_TO_PERSON"

        # 4. PERSON_TO_CONSEQUENCE
        s_prev = {"visual_job": "INTRODUCE_CHARACTER", "shot_size": "medium"}
        s_curr = {"visual_job": "CONSEQUENCE", "shot_size": "wide"}
        res_pc = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_pc["shot_relationship"] == "PERSON_TO_CONSEQUENCE"
        assert res_pc["visual_density"] == 0.35

        # 5. QUESTION_TO_ANSWER
        s_prev = {"visual_job": "BUILD_MYSTERY", "shot_size": "medium"}
        s_curr = {"visual_job": "EXAMINE_EVIDENCE", "shot_size": "close"}
        res_qa = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_qa["shot_relationship"] == "QUESTION_TO_ANSWER"
        assert res_qa["is_restrained"] is True

        # 6. DETAIL_TO_CONTEXT
        s_prev = {"visual_job": "REVEAL_DETAIL", "shot_size": "close"}
        s_curr = {"visual_job": "ESTABLISH_WORLD", "shot_size": "wide"}
        res_dc = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_dc["shot_relationship"] == "DETAIL_TO_CONTEXT"
        assert res_dc["lens"] == "wide_angle_lens"

        # 7. CONTEXT_TO_DETAIL
        s_prev = {"visual_job": "ESTABLISH_WORLD", "shot_size": "wide"}
        s_curr = {"visual_job": "EXAMINE_EVIDENCE", "shot_size": "close"}
        res_cd = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_cd["shot_relationship"] == "CONTEXT_TO_DETAIL"
        assert res_cd["lens"] == "macro_lens"
        assert res_cd["shot_size"] == "extreme_close"

        # 8. CONTRAST
        s_prev = {"visual_job": "ESTABLISH_WORLD", "camera_motion": "pan_left", "visual_density": 0.8}
        s_curr = {"visual_job": "CONTRAST", "camera_motion": "pan_left", "visual_density": 0.5}
        res_con = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_con["shot_relationship"] == "CONTRAST"
        assert res_con["camera_motion"] == "static"
        assert res_con["visual_density"] == 0.25

        # 9. EXPECTATION_TO_SUBVERSION
        s_prev = {"visual_job": "ESTABLISH_WORLD", "shot_size": "wide"}
        s_curr = {"visual_job": "INTERRUPT", "shot_size": "medium"}
        res_sub = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_sub["shot_relationship"] == "EXPECTATION_TO_SUBVERSION"
        assert res_sub["camera_angle"] == "dutch_angle"

        # 10. BEFORE_TO_AFTER
        s_prev = {"visual_job": "RECONSTRUCT_EVENT", "shot_size": "wide"}
        s_curr = {"visual_job": "PAYOFF", "shot_size": "wide"}
        res_ba = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_ba["shot_relationship"] == "BEFORE_TO_AFTER"

        # 11. CAUSE_TO_EFFECT
        s_prev = {"visual_job": "FOLLOW_OBJECT", "shot_size": "close"}
        s_curr = {"visual_job": "CONSEQUENCE", "shot_size": "close"}
        res_ce = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_ce["shot_relationship"] == "CAUSE_TO_EFFECT"

        # 12. CONTINUATION
        s_prev = {"visual_job": "ESTABLISH_WORLD", "shot_size": "medium", "camera_motion": "pan_right", "visual_density": 0.5}
        s_curr = {"visual_job": "ESTABLISH_WORLD", "shot_size": "medium", "camera_motion": "pan_left", "visual_density": 0.5}
        res_cont = sre.determine_and_enforce_relationship(s_prev, s_curr)
        assert res_cont["shot_relationship"] == "CONTINUATION"
        assert res_cont["camera_motion"] == "slow_push_in"  # Avoid jarring reverse pan
        assert res_cont["shot_size"] != "medium"  # Avoid identical consecutive shot sizes

        record_pass("T4.1_ALL_12_SHOT_RELATIONSHIPS", "All 12 ShotRelationships deducing and enforcing relational grammar correctly")
    except Exception as e:
        record_fail("T4.1_ALL_12_SHOT_RELATIONSHIPS", f"Shot relationship test failed: {e}")

    # 4.2 VisualStoryPlanner Decomposition with VisualSequencePlan & Invariants
    try:
        planner = VisualStoryPlanner()
        planner.reset_timeline()

        plan = vsd._generate_deterministic_plan(
            "FIRST_DISCOVERY",
            "Discrepancy discovery in the swift terminal logs",
            "Zubair found $81 million missing due to a typo in foundation",
            {"topic": "Bangladesh Bank", "central_contradiction": "security vs typo"},
            {}
        )

        test_blocks = [
            {
                "block_id": "blk_01",
                "voiceover": "At 11:47 AM, an anomalous routing request for $81 Million triggered an alert when the word foundation was misspelled as fandation, leaving operators in complete panic.",
                "caption": "11:47 AM: $81 Million anomaly flagged by fandation typo.",
                "duration": 9.5
            },
            {
                "block_id": "blk_02",
                "voiceover": "The terminal went dark. Outside the Dhaka tower, monsoon rain fell over thousands of workers who had no idea the country's treasury was being drained.",
                "caption": "Dhaka rain falling over unaware workers.",
                "duration": 6.2
            }
        ]

        for b in test_blocks:
            shots = planner.decompose_narration_block(
                b,
                actual_duration=b["duration"],
                beat_intent="FIRST_DISCOVERY",
                attention_intensity=0.85,
                sequence_plan=plan
            )
            assert len(shots) >= 2, f"Block {b['block_id']} must decompose into at least 2 shots"
            total_dur = sum(s["duration_seconds"] for s in shots)
            assert abs(total_dur - b["duration"]) < 0.05, f"Duration mismatch: {total_dur} vs {b['duration']}"
            
            # Check shot pacing constraints
            for s in shots:
                assert s["duration_seconds"] <= 4.5, f"Shot duration {s['duration_seconds']} exceeds 4.5s max"
                assert s["duration_seconds"] >= 0.8, f"Shot duration {s['duration_seconds']} too short"
                assert s["visual_job"] in [j.value for j in VisualJob]
                assert s["shot_relationship"] in [r.value for r in ShotRelationship]

            # Mute Test on each generated block sequence
            m_res = vsd.evaluate_mute_test(shots, plan)
            assert m_res["mute_test_passed"] is True, f"Decomposed block {b['block_id']} must pass Mute Test"

        record_pass("T4.2_PLANNER_DECOMPOSITION_INVARIANTS", "VisualStoryPlanner decomposition obeys all duration invariants (sum=actual, max<=4.5s) and passes Mute Test")
    except Exception as e:
        record_fail("T4.2_PLANNER_DECOMPOSITION_INVARIANTS", f"VisualStoryPlanner decomposition failed: {e}")

    # 4.3 DirectorMemory Motif Escalation
    try:
        memory = DirectorMemory()
        memory.register_motifs(["unplugged printer ribbon", "ticking control room clock"])
        
        # Test 3-act escalation
        e1 = memory.get_escalated_motif_prompt("unplugged printer ribbon", act_num=1, topic="Bangladesh Bank")
        e2 = memory.get_escalated_motif_prompt("unplugged printer ribbon", act_num=2, topic="Bangladesh Bank")
        e3 = memory.get_escalated_motif_prompt("unplugged printer ribbon", act_num=3, topic="Bangladesh Bank")

        assert e1["treatment"] == "GROUNDING" and e1["visual_job"] == "BUILD_MYSTERY"
        assert e2["treatment"] == "ESCALATION_DISTORTION" and e2["visual_job"] == "ESCALATE"
        assert e3["treatment"] == "PAYOFF_AFTERMATH" and e3["visual_job"] == "PAYOFF"
        assert "pristine condition" in e1["prompt"]
        assert "extreme tension" in e2["prompt"]
        assert "aftermath" in e3["prompt"]
        record_pass("T4.3_DIRECTOR_MEMORY_MOTIF_ESCALATION", "DirectorMemory 3-act motif escalation (Grounding -> Escalation -> Payoff) strictly verified")
    except Exception as e:
        record_fail("T4.3_DIRECTOR_MEMORY_MOTIF_ESCALATION", f"Director memory motif escalation failed: {e}")

    # ============================================================================
    # SECTION 5: Adversarial Mute Test Stress Testing
    # ============================================================================
    print("\n>>> SECTION 5: Adversarial Mute Test Stress Testing <<<")

    try:
        # 5.1 Subtle Cliché Permutations & Penalties
        for kw in vsd.banned_literal_keywords:
            dirty_seq = [
                {"shot_id": "s1", "visual_job": "ESTABLISH_WORLD", "visual_query": "Establishing cityscape", "camera_motion": "slow_push_in"},
                {"shot_id": "s2", "visual_job": "EXAMINE_EVIDENCE", "visual_query": f"Close-up of {kw} on desk", "camera_motion": "static", "is_restrained": True},
                {"shot_id": "s3", "visual_job": "REVEAL", "visual_query": "Case file", "camera_motion": "static", "is_restrained": True}
            ]
            m_eval = vsd.evaluate_mute_test(dirty_seq)
            assert m_eval["mute_test_passed"] is False, f"Mute test should fail for keyword '{kw}'"
            assert len(m_eval["literal_violations"]) >= 1

        # 5.2 Multiple Cliché Score Clamping (Never below 0.0)
        mega_cliche_seq = [
            {"shot_id": f"s{i}", "visual_job": "SHOW_EVIDENCE", "visual_query": f"Shot of {kw}"}
            for i, kw in enumerate(vsd.banned_literal_keywords)
        ]
        mega_eval = vsd.evaluate_mute_test(mega_cliche_seq)
        assert mega_eval["mute_test_passed"] is False
        assert mega_eval["score"] == 0.0, f"Score must clamp at 0.0, got {mega_eval['score']}"
        assert len(mega_eval["literal_violations"]) >= len(vsd.banned_literal_keywords)

        # 5.3 Long Sequence (10 shots) with 1 poisoned shot
        clean_9_shots = [
            {"shot_id": f"s{i}", "visual_job": VisualJob.SHOW_EVIDENCE.value, "visual_query": f"Forensic archival file {i}", "camera_motion": "static"}
            for i in range(9)
        ]
        clean_9_shots.append({"shot_id": "s10", "visual_job": VisualJob.REVEAL.value, "visual_query": "money falling from the sky"})
        poison_eval = vsd.evaluate_mute_test(clean_9_shots)
        assert poison_eval["mute_test_passed"] is False
        assert "money falling" in poison_eval["literal_violations"][0]

        record_pass("T5.1_ADVERSARIAL_MUTE_TEST", "Adversarial mute test permutations, score clamping at 0.0, and single-shot poisoning verified")
    except Exception as e:
        record_fail("T5.1_ADVERSARIAL_MUTE_TEST", f"Adversarial mute test failed: {e}")

    # ============================================================================
    # SECTION 6: Exhaustive Fallback Cascade Monotonicity & Robustness
    # ============================================================================
    print("\n>>> SECTION 6: Exhaustive Fallback Cascade Monotonicity & Robustness <<<")

    try:
        # 6.1 None / Empty / Null handling
        res_null1 = vsd.apply_fallback_cascade(None, None, None)
        assert res_null1["cascade_level"] == 5
        assert res_null1["strategy"] == "GENERIC_BROLL"

        res_null2 = vsd.apply_fallback_cascade("INVALID_JOB_STRING", {}, {})
        assert res_null2["cascade_level"] == 5

        # 6.2 Monotonic Degradation (As high-priority assets disappear, level degrades monotonically)
        # Level 1 -> Level 2 -> Level 3 -> Level 4 -> Level 5
        lvl1 = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_human_anchor": True, "has_statistic": True, "has_cyber": True, "has_anomaly": True})
        assert lvl1["cascade_level"] == 1

        lvl2 = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_human_anchor": False, "has_statistic": True, "has_cyber": True, "has_anomaly": True})
        assert lvl2["cascade_level"] == 2

        lvl3 = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_human_anchor": False, "has_statistic": False, "has_cyber": True, "has_anomaly": True})
        assert lvl3["cascade_level"] == 3

        lvl4 = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_human_anchor": False, "has_statistic": False, "has_cyber": False, "has_anomaly": True})
        assert lvl4["cascade_level"] == 4

        lvl5 = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_human_anchor": False, "has_statistic": False, "has_cyber": False, "has_anomaly": False})
        assert lvl5["cascade_level"] == 5

        record_pass("T6.1_CASCADE_MONOTONIC_DEGRADATION", "Fallback cascade exhibits strict monotonic degradation across all 5 tiers")
    except Exception as e:
        record_fail("T6.1_CASCADE_MONOTONIC_DEGRADATION", f"Monotonic degradation test failed: {e}")

    # ============================================================================
    # SECTION 7: Pacing & Duration Stress Testing in VisualStoryPlanner
    # ============================================================================
    print("\n>>> SECTION 7: Pacing & Duration Stress Testing in VisualStoryPlanner <<<")

    try:
        planner = VisualStoryPlanner()
        durations_to_test = [1.5, 3.0, 5.0, 8.4, 12.0, 18.5, 25.0]

        for dur in durations_to_test:
            planner.reset_timeline()
            blk = {
                "block_id": f"blk_dur_{dur}",
                "voiceover": "At 11:47 AM, $81 Million was transferred through 35 accounts across Manila casinos after a fatal typographical error.",
                "caption": "Transfer of $81 Million to Manila."
            }
            shots = planner.decompose_narration_block(
                blk,
                actual_duration=dur,
                beat_intent="ESCALATION",
                attention_intensity=0.9
            )
            total_dur = sum(s["duration_seconds"] for s in shots)
            assert abs(total_dur - dur) < 0.05, f"Duration mismatch for dur={dur}: got {total_dur}"
            for s in shots:
                assert s["duration_seconds"] <= 4.5, f"Shot duration {s['duration_seconds']} exceeds 4.5s for block duration {dur}"
                assert s["duration_seconds"] > 0.0, f"Shot duration {s['duration_seconds']} must be positive for block duration {dur}"

        record_pass("T7.1_PACING_AND_DURATION_STRESS", f"VisualStoryPlanner preserved exact durations across {len(durations_to_test)} varied block lengths (1.5s to 25s)")
    except Exception as e:
        record_fail("T7.1_PACING_AND_DURATION_STRESS", f"Pacing stress test failed: {e}")

    # Summary
    print("\n======================================================================")
    print(f"CHALLENGER EMPIRICAL TEST SUMMARY: PASSED={test_results['passed']}, FAILED={test_results['failed']}, WARNINGS={test_results['warnings']}")
    print("======================================================================")
    return test_results

if __name__ == "__main__":
    res = run_all_tests()
    if res["failed"] > 0:
        sys.exit(1)
    sys.exit(0)
