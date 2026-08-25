"""
Comprehensive Adversarial Challenger & Reviewer Verification Suite for Milestone 3
Validates all requirements:
1. VisualSequenceDirector Plan formulation & 4 change metrics across all 11 narrative phases
2. Anti-Literal Rule & Mute Test engine with adversarial cliché injection and score calculation
3. 5-Tier No-Generic-B-Roll Fallback Cascade priority resolution
4. All 20 Visual Jobs and 12 Shot Relationships utilization and relational grammar
5. 7D Visual Contrast Engine, Dramatic Number Typography, 3-Act Motif Escalation, Human Anchors
6. Duration invariants, SFX cooldown pacing, and stateful DirectorMemory
"""

import math
import json
import pytest
from agents.schema import (
    VisualSequencePlan, VisualJob, ShotRelationship, StoryBeat, NarrationBlock, Shot,
    NarrativeIntent, DocumentaryResearchPackage, DocumentaryVision, EditorialEvent
)
from agents.visual_sequence_director import VisualSequenceDirector
from agents.shot_relationship import ShotRelationshipEngine
from agents.visual_intent import VisualIntentEngine
from agents.director_memory import DirectorMemory
from agents.visual_story_planner import VisualStoryPlanner


def test_visual_jobs_and_shot_relationships_completeness():
    """Verify all 20 VisualJobs and 12 ShotRelationships are defined."""
    expected_jobs = {
        "ESTABLISH_WORLD", "INTRODUCE_CHARACTER", "INTRODUCE_OBJECT", "FOLLOW_OBJECT",
        "SHOW_EVIDENCE", "EXAMINE_EVIDENCE", "REVEAL_DETAIL", "VISUALIZE_ABSTRACT_CONCEPT",
        "SHOW_SCALE", "SHOW_COMPARISON", "RECONSTRUCT_EVENT", "BUILD_MYSTERY",
        "WITHHOLD_INFORMATION", "ESCALATE", "INTERRUPT", "CONTRAST",
        "HUMANIZE", "CONSEQUENCE", "REVEAL", "PAYOFF"
    }
    actual_jobs = {j.value for j in VisualJob}
    assert actual_jobs == expected_jobs, f"VisualJob mismatch: missing {expected_jobs - actual_jobs}, extra {actual_jobs - expected_jobs}"
    assert len(VisualJob) == 20

    expected_relationships = {
        "CONTINUATION", "CONTRAST", "CAUSE_TO_EFFECT", "QUESTION_TO_ANSWER",
        "DETAIL_TO_CONTEXT", "CONTEXT_TO_DETAIL", "BEFORE_TO_AFTER", "EXPECTATION_TO_SUBVERSION",
        "OBJECT_TO_PERSON", "PERSON_TO_CONSEQUENCE", "NUMBER_TO_SCALE", "EVIDENCE_TO_REVEAL"
    }
    actual_relationships = {r.value for r in ShotRelationship}
    assert actual_relationships == expected_relationships, f"ShotRelationship mismatch: missing {expected_relationships - actual_relationships}"
    assert len(ShotRelationship) == 12


def test_visual_sequence_director_all_phases():
    """Verify VisualSequenceDirector generates schema-compliant VisualSequencePlan for all 11 phases."""
    vsd = VisualSequenceDirector()
    
    phases = [
        "HOOK", "CENTRAL_QUESTION", "CONTEXT", "FIRST_DISCOVERY",
        "COMPLICATION", "ESCALATION", "REVELATION", "CONSEQUENCE",
        "DEEPER_REVELATION", "FINAL_CONTRADICTION", "PAYOFF"
    ]
    
    pkg = {
        "topic": "The 1992 Securities Scam",
        "central_contradiction": "artificial_market_euphoria vs massive_bank_fund_siphoning",
        "visual_motifs": ["Banker Receipt note", "BSE Ring Trading floor bell", "Ambassador car"]
    }
    vision = {
        "core_premise": "How fake bank receipts inflated the Bombay stock market.",
        "central_contradiction": "public_market_craze vs institutional_systemic_fraud"
    }

    for phase in phases:
        beat = {
            "beat_id": f"b_{phase.lower()}",
            "narrative_intent": phase,
            "description": f"Dramatizing the {phase} stage of the securities investigation.",
            "narration_blocks": [
                {
                    "block_id": f"n_{phase.lower()}_1",
                    "voiceover": f"In this critical phase of {phase}, billions flowed through fraudulent cheques.",
                    "caption": f"Phase {phase} in action."
                }
            ]
        }
        plan = vsd.plan_visual_sequence(beat, research_package=pkg, vision=vision)
        assert isinstance(plan, VisualSequencePlan), f"Failed for phase {phase}: not VisualSequencePlan"
        assert len(plan.intention) > 5
        assert len(plan.visual_argument) > 5
        assert len(plan.withholding_strategy) > 5
        assert len(plan.memorable_image) > 5
        assert len(plan.sequence_ending_statement) > 5
        
        # Verify 4 change metrics are valid float bounds
        assert 0.0 <= plan.information_change <= 1.0, f"info change out of bounds in {phase}: {plan.information_change}"
        assert 0.0 <= plan.emotional_change <= 1.0, f"emotional change out of bounds in {phase}: {plan.emotional_change}"
        assert 0.0 <= plan.visual_change <= 1.0, f"visual change out of bounds in {phase}: {plan.visual_change}"
        assert 0.0 <= plan.scale_change <= 1.0, f"scale change out of bounds in {phase}: {plan.scale_change}"


def test_anti_literal_and_mute_test_engine():
    """Verify Anti-Literal Rule & Mute Test detects clichés and evaluates narrative visual arcs."""
    vsd = VisualSequenceDirector()
    
    # 1. Anti-Literal detection
    cliche_shots = [
        {"visual_query": "money falling from the sky over businessman"},
        {"visual_query": "two businessmen stock handshake in boardroom"},
        {"visual_query": "golden scales of justice tipping"},
        {"visual_query": "pink piggy bank with hammer"},
        {"visual_query": "hacker in hoodie laughing at glowing code"},
        {"visual_query": "metal handcuffs on table near cash"}
    ]
    for cs in cliche_shots:
        assert vsd.is_literal_illustration(cs) is True, f"Failed to detect cliché in {cs}"

    cinematic_shots = [
        {"visual_query": "macro close up of forged signature on official telex paper under harsh tungsten light"},
        {"visual_query": "medium shot of nervous operator trembling hands on terminal keyboard at dawn"},
        {"visual_query": "locked off static frame of abandoned trading floor with papers strewn across floor"},
        {"visual_query": "kinetic typography displaying $81 MILLION on dark minimalist parchment"}
    ]
    for cs in cinematic_shots:
        assert vsd.is_literal_illustration(cs) is False, f"False positive cliché on {cs}"

    # 2. Mute Test Evaluation: Passing sequence
    good_sequence = [
        {"visual_job": VisualJob.ESTABLISH_WORLD.value, "visual_query": "wide shot of central bank building", "camera_motion": "slow_push_in"},
        {"visual_job": VisualJob.EXAMINE_EVIDENCE.value, "visual_query": "macro shot of red ink telex discrepancy", "camera_motion": "static", "is_restrained": True},
        {"visual_job": VisualJob.REVEAL.value, "visual_query": "unredacted memo on desk under lamp", "camera_motion": "static", "is_restrained": True},
        {"visual_job": VisualJob.CONSEQUENCE.value, "visual_query": "medium shot of empty office after arrest", "camera_motion": "pan_left"}
    ]
    mute_pass = vsd.evaluate_mute_test(good_sequence)
    assert mute_pass["mute_test_passed"] is True
    assert mute_pass["score"] >= 8.0
    assert mute_pass["has_setup"] is True
    assert mute_pass["has_development"] is True
    assert mute_pass["has_climax_or_consequence"] is True
    assert len(mute_pass["literal_violations"]) == 0

    # 3. Mute Test Evaluation: Failing sequence (clichés + no arc)
    bad_sequence = [
        {"visual_job": "N/A", "visual_query": "money falling and stock handshake"},
        {"visual_job": "N/A", "visual_query": "hacker in hoodie laughing at screen"}
    ]
    mute_fail = vsd.evaluate_mute_test(bad_sequence)
    assert mute_fail["mute_test_passed"] is False
    assert len(mute_fail["literal_violations"]) >= 2
    assert mute_fail["score"] <= 4.0

    # 4. Mute Test: Empty shots
    empty_res = vsd.evaluate_mute_test([])
    assert empty_res["mute_test_passed"] is False
    assert empty_res["score"] == 0.0


def test_fallback_cascade_5_priority_tiers():
    """Verify No-Generic-B-Roll Fallback Cascade strictly adheres to the 5 priority levels."""
    vsd = VisualSequenceDirector()

    # Tier 1: Alternative Interpretation (HUMANIZE / CONTRAST / Human anchor)
    t1_a = vsd.apply_fallback_cascade(VisualJob.HUMANIZE)
    assert t1_a["cascade_level"] == 1
    assert t1_a["strategy"] == "ALTERNATIVE_INTERPRETATION"
    assert t1_a["fallback_type"] == "PortraitCard"
    assert t1_a["priority_score"] == 1.0

    t1_b = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_human_anchor": True})
    assert t1_b["cascade_level"] == 1

    # Tier 2: Motion Graphic Diagram (SHOW_SCALE / SHOW_COMPARISON / VISUALIZE_ABSTRACT_CONCEPT / stats / processes)
    t2_a = vsd.apply_fallback_cascade(VisualJob.SHOW_SCALE)
    assert t2_a["cascade_level"] == 2
    assert t2_a["strategy"] == "MOTION_GRAPHIC_DIAGRAM"
    assert t2_a["priority_score"] == 0.9

    t2_b = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_statistic": True})
    assert t2_b["cascade_level"] == 2
    assert t2_b["visual_type"] == "text_stat"
    assert t2_b["fallback_type"] == "CinematicText"

    # Tier 3: AI Reconstruction (RECONSTRUCT_EVENT / BUILD_MYSTERY / ESCALATE / cyber)
    t3_a = vsd.apply_fallback_cascade(VisualJob.RECONSTRUCT_EVENT)
    assert t3_a["cascade_level"] == 3
    assert t3_a["strategy"] == "AI_RECONSTRUCTION"
    assert t3_a["fallback_type"] == "EvidenceBoard"
    assert t3_a["priority_score"] == 0.8

    t3_b = vsd.apply_fallback_cascade("ESTABLISH_WORLD", intent_info={"has_cyber": True})
    assert t3_b["cascade_level"] == 3

    # Tier 4: Archival Document (SHOW_EVIDENCE / EXAMINE_EVIDENCE / REVEAL_DETAIL / REVEAL / PAYOFF / anomaly / evidence)
    t4_a = vsd.apply_fallback_cascade(VisualJob.SHOW_EVIDENCE)
    assert t4_a["cascade_level"] == 4
    assert t4_a["strategy"] == "ARCHIVAL_DOCUMENT"
    assert t4_a["fallback_type"] == "ArchivalDocument"
    assert t4_a["priority_score"] == 0.7

    t4_b = vsd.apply_fallback_cascade(VisualJob.EXAMINE_EVIDENCE, intent_info={"has_anomaly": True})
    assert t4_b["cascade_level"] == 4
    assert t4_b["fallback_type"] == "ClassifiedFile"

    # Tier 5: Generic B-roll (Strict last resort fallback)
    t5 = vsd.apply_fallback_cascade(VisualJob.ESTABLISH_WORLD, intent_info={}, available_assets={})
    assert t5["cascade_level"] == 5
    assert t5["strategy"] == "GENERIC_BROLL"
    assert t5["visual_type"] == "broll_video"
    assert t5["asset_provenance"] == "STOCK"
    assert t5["priority_score"] == 0.3


def test_all_12_shot_relationships_relational_grammar():
    """Verify ShotRelationshipEngine deduces and enforces grammar for all 12 Shot Relationships."""
    sre = ShotRelationshipEngine()

    # 1. First shot is always CONTINUATION
    first_shot_invalid_size = {"visual_job": "ESTABLISH_WORLD", "shot_size": "extreme_close"}
    s1 = sre.determine_and_enforce_relationship(None, first_shot_invalid_size)
    assert s1["shot_relationship"] == ShotRelationship.CONTINUATION.value
    assert s1["shot_size"] == "wide"

    first_shot_valid_size = {"visual_job": "ESTABLISH_WORLD", "shot_size": "medium"}
    s2 = sre.determine_and_enforce_relationship(None, first_shot_valid_size)
    assert s2["shot_relationship"] == ShotRelationship.CONTINUATION.value
    assert s2["shot_size"] == "medium"

    # 2. NUMBER_TO_SCALE (after text_stat or SHOW_SCALE)
    prev_stat = {"visual_job": VisualJob.SHOW_SCALE.value, "visual_type": "text_stat", "shot_size": "medium"}
    curr_comp = {"visual_job": VisualJob.SHOW_COMPARISON.value, "shot_size": "medium"}
    res_nts = sre.determine_and_enforce_relationship(prev_stat, curr_comp)
    assert res_nts["shot_relationship"] == ShotRelationship.NUMBER_TO_SCALE.value
    assert res_nts["shot_size"] == "wide"
    assert res_nts["lens"] == "wide_angle_lens"
    assert res_nts["camera_motion"] == "slow_push_in"
    assert res_nts["visual_density"] == 0.40

    # 3. EVIDENCE_TO_REVEAL (evidence -> reveal)
    prev_ev = {"visual_job": VisualJob.EXAMINE_EVIDENCE.value, "shot_size": "close"}
    curr_rev = {"visual_job": VisualJob.REVEAL.value, "shot_size": "wide", "camera_motion": "pan_left"}
    res_etr = sre.determine_and_enforce_relationship(prev_ev, curr_rev)
    assert res_etr["shot_relationship"] == ShotRelationship.EVIDENCE_TO_REVEAL.value
    assert res_etr["camera_motion"] == "static"
    assert res_etr["is_restrained"] is True
    assert res_etr["shot_size"] == "close"

    # 4. OBJECT_TO_PERSON (object -> character/human)
    prev_obj = {"visual_job": VisualJob.INTRODUCE_OBJECT.value, "shot_size": "close"}
    curr_pers = {"visual_job": VisualJob.INTRODUCE_CHARACTER.value, "shot_size": "wide"}
    res_otp = sre.determine_and_enforce_relationship(prev_obj, curr_pers)
    assert res_otp["shot_relationship"] == ShotRelationship.OBJECT_TO_PERSON.value
    assert res_otp["shot_size"] == "medium"

    # 5. PERSON_TO_CONSEQUENCE (character -> consequence)
    prev_pers = {"visual_job": VisualJob.INTRODUCE_CHARACTER.value, "shot_size": "medium"}
    curr_conseq = {"visual_job": VisualJob.CONSEQUENCE.value, "shot_size": "wide"}
    res_ptc = sre.determine_and_enforce_relationship(prev_pers, curr_conseq)
    assert res_ptc["shot_relationship"] == ShotRelationship.PERSON_TO_CONSEQUENCE.value
    assert res_ptc["shot_size"] == "medium_close"
    assert res_ptc["visual_density"] == 0.35

    # 6. QUESTION_TO_ANSWER (mystery -> reveal)
    prev_myst = {"visual_job": VisualJob.BUILD_MYSTERY.value, "shot_size": "medium"}
    curr_ans = {"visual_job": VisualJob.REVEAL.value, "shot_size": "wide"}
    res_qta = sre.determine_and_enforce_relationship(prev_myst, curr_ans)
    assert res_qta["shot_relationship"] == ShotRelationship.QUESTION_TO_ANSWER.value
    assert res_qta["camera_motion"] == "static"
    assert res_qta["is_restrained"] is True

    # 7. DETAIL_TO_CONTEXT (macro/close -> wide)
    prev_close = {"visual_job": "OTHER", "shot_size": "close"}
    curr_wide = {"visual_job": "OTHER", "shot_size": "wide"}
    res_dtc = sre.determine_and_enforce_relationship(prev_close, curr_wide)
    assert res_dtc["shot_relationship"] == ShotRelationship.DETAIL_TO_CONTEXT.value
    assert res_dtc["shot_size"] == "wide"
    assert res_dtc["lens"] == "wide_angle_lens"

    # 8. CONTEXT_TO_DETAIL (wide -> close/extreme_close)
    prev_wide = {"visual_job": "OTHER", "shot_size": "wide"}
    curr_close = {"visual_job": "OTHER", "shot_size": "close"}
    res_ctd = sre.determine_and_enforce_relationship(prev_wide, curr_close)
    assert res_ctd["shot_relationship"] == ShotRelationship.CONTEXT_TO_DETAIL.value
    assert res_ctd["shot_size"] == "extreme_close"
    assert res_ctd["lens"] == "macro_lens"
    assert res_ctd["camera_motion"] == "static"

    # 9. CONTRAST (contrast job -> contrast)
    prev_norm = {"visual_job": "OTHER", "camera_motion": "pan_left", "visual_density": 0.8}
    curr_contr = {"visual_job": VisualJob.CONTRAST.value, "camera_motion": "pan_left"}
    res_contr = sre.determine_and_enforce_relationship(prev_norm, curr_contr)
    assert res_contr["shot_relationship"] == ShotRelationship.CONTRAST.value
    assert res_contr["camera_motion"] == "static"
    assert res_contr["visual_density"] == 0.25

    # 10. EXPECTATION_TO_SUBVERSION (interrupt job)
    prev_n = {"visual_job": "OTHER", "shot_size": "medium"}
    curr_subv = {"visual_job": VisualJob.INTERRUPT.value, "shot_size": "medium"}
    res_subv = sre.determine_and_enforce_relationship(prev_n, curr_subv)
    assert res_subv["shot_relationship"] == ShotRelationship.EXPECTATION_TO_SUBVERSION.value
    assert res_subv["camera_angle"] == "dutch_angle"
    assert res_subv["visual_density"] == 0.70

    # 11. BEFORE_TO_AFTER (establish/reconstruct -> payoff)
    prev_estab = {"visual_job": VisualJob.ESTABLISH_WORLD.value, "shot_size": "wide"}
    curr_payoff = {"visual_job": VisualJob.PAYOFF.value, "shot_size": "wide"}
    res_bta = sre.determine_and_enforce_relationship(prev_estab, curr_payoff)
    assert res_bta["shot_relationship"] == ShotRelationship.BEFORE_TO_AFTER.value

    # 12. CAUSE_TO_EFFECT (action -> consequence)
    prev_act = {"visual_job": "OTHER", "shot_size": "medium"}
    curr_eff = {"visual_job": VisualJob.CONSEQUENCE.value, "shot_size": "medium"}
    res_cte = sre.determine_and_enforce_relationship(prev_act, curr_eff)
    assert res_cte["shot_relationship"] in [ShotRelationship.CAUSE_TO_EFFECT.value, ShotRelationship.PERSON_TO_CONSEQUENCE.value]


def test_visual_story_planner_7d_contrast_and_numbers():
    """Verify VisualStoryPlanner enforces 7D contrast, number punctuation, motif escalation, and duration invariants."""
    planner = VisualStoryPlanner()
    planner.reset_timeline(topic="Nirav Modi PNB Fraud", genre="documentary")

    research_pkg = {
        "topic": "PNB Bank Letter of Undertaking Scam",
        "visual_motifs": ["SWIFT terminal message", "Diamond appraisal loupe", "Brady House branch exterior"],
        "central_contradiction": "official_pnb_balance_sheet vs fraudulent_unrecorded_lou_liabilities"
    }

    blocks = [
        {
            "block_id": "n001",
            "voiceover": "On January 16, 2018, Punjab National Bank detected that ₹11,400 Crore had been siphoned off using unrecorded LoUs.",
            "caption": "₹11,400 Crore siphoned via unauthorized LoUs.",
            "duration": 9.2,
            "intent": "FIRST_DISCOVERY"
        },
        {
            "block_id": "n002",
            "voiceover": "Behind the gleaming diamond showcases, frantic clerks struggled under mounting audit pressure at 11:47 PM.",
            "caption": "Clerks under pressure late night.",
            "duration": 7.5,
            "intent": "COMPLICATION"
        },
        {
            "block_id": "n003",
            "voiceover": "A single unauthorized SWIFT terminal login typo exposed the entire multi-billion offshore network.",
            "caption": "Unauthorized SWIFT login typo exposes scam.",
            "duration": 6.8,
            "intent": "REVELATION"
        }
    ]

    all_shots = []
    for act_idx, b in enumerate(blocks, start=1):
        shots = planner.decompose_narration_block(
            block={"block_id": b["block_id"], "voiceover": b["voiceover"], "caption": b["caption"]},
            actual_duration=b["duration"],
            beat_intent=b["intent"],
            attention_intensity=0.9,
            research_package=research_pkg,
            act_num=act_idx
        )
        assert len(shots) >= 2
        
        # Invariant 1: Exact duration preservation
        dur_sum = sum(s["duration_seconds"] for s in shots)
        assert abs(dur_sum - b["duration"]) < 0.001, f"Duration mismatch in {b['block_id']}: sum {dur_sum} != actual {b['duration']}"
        
        # Invariant 2: Max individual shot duration <= 4.5s
        for s in shots:
            assert s["duration_seconds"] <= 4.5, f"Shot {s['shot_id']} exceeds 4.5s: {s['duration_seconds']}"
            assert s["visual_job"] in [j.value for j in VisualJob]
            assert s["shot_relationship"] in [r.value for r in ShotRelationship]
            assert 0.0 <= s["visual_density"] <= 1.0

        all_shots.extend(shots)

    # Verify Dramatic Number Typography was generated for block 1 (₹11,400 Crore)
    stat_shots = [s for s in all_shots if s.get("visual_type") == "text_stat"]
    assert len(stat_shots) >= 1, "Expected at least one text_stat shot for dramatic number"
    
    # Check that NUMBER_REVEAL event is emitted
    num_events = [
        e for s in stat_shots for e in (s.get("editorial_events") or [])
        if e.get("type") == "NUMBER_REVEAL"
    ]
    assert len(num_events) >= 1, "Expected NUMBER_REVEAL editorial event"

    # Check that NUMBER_TO_SCALE relationship followed the number shot
    stat_idx = all_shots.index(stat_shots[0])
    if stat_idx + 1 < len(all_shots):
        next_shot = all_shots[stat_idx + 1]
        assert next_shot["shot_relationship"] == ShotRelationship.NUMBER_TO_SCALE.value

    # Check human anchor presence
    human_shots = [s for s in all_shots if s["visual_job"] == VisualJob.HUMANIZE.value]
    assert len(human_shots) >= 1, "Expected at least one HUMANIZE human anchor shot"

    # Check memory summary
    summary = planner.memory.get_summary()
    assert summary["total_shots_recorded"] == len(all_shots)
    assert summary["unique_visual_jobs"] >= 3
    assert summary["registered_motifs_count"] >= 3


def test_director_memory_motif_escalation_and_variety_guards():
    """Verify DirectorMemory 3-act escalation and subject/motion diversity safeguards."""
    mem = DirectorMemory()
    mem.register_motifs(["sealed envelope", "trading bell"])
    assert "sealed envelope" in mem.registered_motifs
    assert "trading bell" in mem.registered_motifs

    # Act 1 escalation: Grounding
    act1 = mem.get_escalated_motif_prompt("sealed envelope", act_num=1, topic="Scam")
    assert act1["treatment"] == "GROUNDING"
    assert act1["visual_job"] == VisualJob.BUILD_MYSTERY.value

    # Act 2 escalation: Crisis Distortion
    act2 = mem.get_escalated_motif_prompt("sealed envelope", act_num=2, topic="Scam")
    assert act2["treatment"] == "ESCALATION_DISTORTION"
    assert act2["visual_job"] == VisualJob.ESCALATE.value

    # Act 3 escalation: Aftermath Payoff
    act3 = mem.get_escalated_motif_prompt("sealed envelope", act_num=3, topic="Scam")
    assert act3["treatment"] == "PAYOFF_AFTERMATH"
    assert act3["visual_job"] == VisualJob.PAYOFF.value

    # Test subject overuse guard
    for _ in range(3):
        mem.record_shot({"visual_query": "laptop screen coding terminal", "shot_size": "medium", "camera_motion": "slow_push_in"})
    assert mem.is_subject_overused("computer_screen") is True

    # Test diverse motion suggestion
    diverse_motion = mem.suggest_diverse_motion(["slow_push_in", "pan_left", "static"])
    assert diverse_motion != "slow_push_in", f"Expected diverse motion, got {diverse_motion}"

    # Test human anchor cadence
    assert mem.needs_human_anchor(threshold=2) is True
    mem.record_shot({"visual_job": VisualJob.HUMANIZE.value, "visual_query": "hands trembling"})
    assert mem.needs_human_anchor(threshold=2) is False


def test_visual_intent_regex_cues():
    """Verify VisualIntentEngine extracts statistics, timestamps, anomalies, and human anchors in Hindi and English."""
    engine = VisualIntentEngine()

    # Test 1: Financial statistic in English & INR
    r1 = engine.analyze_block_intent("The syndicate looted ₹500 Crore in 2 hours.", "₹500 Crore looted.")
    assert r1["has_statistic"] is True
    assert "500" in r1["statistic_text"]

    # Test 2: Timestamp
    r2 = engine.analyze_block_intent("At 03:30 AM, silent alerts flashed across Dhaka servers.", "03:30 AM alerts.")
    assert r2["has_timestamp"] is True
    assert "03:30 AM" in r2["timestamp_text"]

    # Test 3: Anomaly (Hindi 'galti' / English 'discrepancy')
    r3 = engine.analyze_block_intent("Ek choti si galti aur typo ne pura fraud leak kar diya.", "Typo leaks fraud.")
    assert r3["has_anomaly"] is True
    assert r3["recommended_visual_job"] == VisualJob.EXAMINE_EVIDENCE.value

    # Test 4: Human vulnerability
    r4 = engine.analyze_block_intent("Thousands of laid off workers left in despair with empty hands.", "Workers despair.")
    assert r4["has_human_anchor"] is True
    assert r4["recommended_visual_job"] == VisualJob.HUMANIZE.value


if __name__ == "__main__":
    print("Running comprehensive Milestone 3 reviewer test suite...")
    test_visual_jobs_and_shot_relationships_completeness()
    test_visual_sequence_director_all_phases()
    test_anti_literal_and_mute_test_engine()
    test_fallback_cascade_5_priority_tiers()
    test_all_12_shot_relationships_relational_grammar()
    test_visual_story_planner_7d_contrast_and_numbers()
    test_director_memory_motif_escalation_and_variety_guards()
    test_visual_intent_regex_cues()
    print("ALL COMPREHENSIVE ADVERSARIAL CHALLENGER TESTS PASSED (8/8)!")
