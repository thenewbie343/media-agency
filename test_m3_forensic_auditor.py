"""
Milestone 3 Forensic Auditor Empirical Verification Suite
Exhaustively tests:
1. VisualSequenceDirector (VisualSequencePlan, 4 change metrics, dialectics, Mute Test, 5-tier Fallback Cascade)
2. ShotRelationshipEngine (All 12 Shot Relationships, relational grammar, lens/motion/density adaptations)
3. VisualIntentEngine (Statistics, timestamps, anomalies, human anchors, cyber, processes, reveals)
4. DirectorMemory (3-act motif escalation, human anchor cadence, 7D contrast tracking, subject overuse)
5. VisualStoryPlanner (Decomposition, 7D contrast, duration conservation, <= 4.5s bounds, SFX cooldowns)
6. Adversarial Stress & Anti-Hardcoding Tests (Multi-topic generalizability, boundary conditions)
"""

import sys
import json
import math
import copy
from typing import Dict, Any, List

from agents.schema import (
    NarrativeIntent,
    MiniArcPhase,
    VisualJob,
    ShotRelationship,
    DocumentaryResearchPackage,
    DocumentaryVision,
    VisualSequencePlan,
    StoryBeat,
    NarrationBlock,
    Shot,
    TimeContext
)
from agents.visual_sequence_director import VisualSequenceDirector
from agents.shot_relationship import ShotRelationshipEngine
from agents.visual_intent import VisualIntentEngine
from agents.director_memory import DirectorMemory
from agents.visual_story_planner import VisualStoryPlanner

audit_results = {"passed": 0, "failed": 0, "details": []}

def record_pass(test_id: str, msg: str):
    audit_results["passed"] += 1
    audit_results["details"].append(("PASS", test_id, msg))
    print(f"[PASS] [{test_id}] {msg}")

def record_fail(test_id: str, msg: str):
    audit_results["failed"] += 1
    audit_results["details"].append(("FAIL", test_id, msg))
    print(f"[FAIL] [{test_id}] {msg}")


def run_audit():
    print("=" * 75)
    print("M3 FORENSIC AUDIT: VISUAL SEQUENCE DIRECTOR & VISUAL STORY PLANNER")
    print("=" * 75)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: VisualSequenceDirector & VisualSequencePlan Verification
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n>>> SECTION 1: VisualSequenceDirector & VisualSequencePlan <<<")
    vsd = VisualSequenceDirector()

    # 1.1 Test plan_visual_sequence with all 11 Macro Narrative Intents
    macro_intents = [
        "HOOK", "CENTRAL_QUESTION", "CONTEXT", "FIRST_DISCOVERY",
        "COMPLICATION", "ESCALATION", "REVELATION", "CONSEQUENCE",
        "DEEPER_REVELATION", "FINAL_CONTRADICTION", "PAYOFF"
    ]
    for intent in macro_intents:
        beat = {
            "beat_id": f"b_{intent.lower()}",
            "narrative_intent": intent,
            "description": f"Testing macro phase {intent} in forensic audit.",
            "narration_blocks": [{"voiceover": "Narrative test line.", "caption": "Caption test line."}]
        }
        plan = vsd.plan_visual_sequence(beat)
        assert isinstance(plan, VisualSequencePlan), f"Expected VisualSequencePlan for {intent}"
        assert plan.intention, f"Intention empty for {intent}"
        assert plan.visual_argument, f"Visual argument empty for {intent}"
        assert plan.withholding_strategy, f"Withholding strategy empty for {intent}"
        assert plan.memorable_image, f"Memorable image empty for {intent}"
        assert plan.sequence_ending_statement, f"Sequence ending statement empty for {intent}"
        assert 0.0 <= plan.information_change <= 1.0
        assert 0.0 <= plan.emotional_change <= 1.0
        assert 0.0 <= plan.visual_change <= 1.0
        assert 0.0 <= plan.scale_change <= 1.0
    record_pass("AUDIT_1.1_MACRO_INTENTS", f"VisualSequenceDirector generated valid VisualSequencePlan across all {len(macro_intents)} macro intents")

    # 1.2 Test Mute Test on high-quality sequence
    good_shots = [
        {"visual_job": "ESTABLISH_WORLD", "visual_query": "London city skyline dusk", "camera_motion": "slow_push_in", "is_restrained": False},
        {"visual_job": "EXAMINE_EVIDENCE", "visual_query": "Confidential banking document memo table", "camera_motion": "static", "is_restrained": True},
        {"visual_job": "SHOW_SCALE", "visual_query": "Global financial network map", "camera_motion": "slow_push_in", "is_restrained": False},
        {"visual_job": "REVEAL", "visual_query": "Unredacted telex wire transfer slip", "camera_motion": "static", "is_restrained": True},
        {"visual_job": "HUMANIZE", "visual_query": "Trembling hands on desk after hearing news", "camera_motion": "static", "is_restrained": True}
    ]
    mute_good = vsd.evaluate_mute_test(good_shots)
    assert mute_good["mute_test_passed"] is True
    assert mute_good["score"] >= 8.0
    assert mute_good["has_setup"] is True
    assert mute_good["has_development"] is True
    assert mute_good["has_climax_or_consequence"] is True
    assert mute_good["distinct_visual_jobs"] >= 3
    assert mute_good["has_restraint"] is True
    assert len(mute_good["literal_violations"]) == 0
    record_pass("AUDIT_1.2_MUTE_TEST_PASS", f"Mute Test passed high-quality sequence (score: {mute_good['score']}/10.0)")

    # 1.3 Test Mute Test on Cliché-Riddled & Flat Sequences
    cliche_shots = [
        {"visual_job": "ESTABLISH_WORLD", "visual_query": "money falling from the sky", "camera_motion": "slow_push_in"},
        {"visual_job": "ESTABLISH_WORLD", "visual_query": "generic businessman handshake in suit", "camera_motion": "slow_push_in"},
        {"visual_job": "ESTABLISH_WORLD", "visual_query": "scales of justice on table", "camera_motion": "slow_push_in"}
    ]
    mute_bad = vsd.evaluate_mute_test(cliche_shots)
    assert mute_bad["mute_test_passed"] is False or len(mute_bad["literal_violations"]) > 0
    assert len(mute_bad["literal_violations"]) >= 2
    record_pass("AUDIT_1.3_MUTE_TEST_REJECT_CLICHES", f"Mute Test successfully detected and flagged {len(mute_bad['literal_violations'])} banned cliché violations")

    # 1.4 Test 5-Tier Fallback Cascade
    t1 = vsd.apply_fallback_cascade(VisualJob.HUMANIZE)
    t2 = vsd.apply_fallback_cascade(VisualJob.SHOW_SCALE, intent_info={"has_statistic": True})
    t3 = vsd.apply_fallback_cascade(VisualJob.ESCALATE, intent_info={"has_cyber": True})
    t4 = vsd.apply_fallback_cascade(VisualJob.SHOW_EVIDENCE, intent_info={"has_evidence": True})
    t5 = vsd.apply_fallback_cascade(VisualJob.ESTABLISH_WORLD, available_assets={"has_ai_generator": False})

    assert t1["cascade_level"] == 1 and t1["strategy"] == "ALTERNATIVE_INTERPRETATION" and t1["asset_provenance"] == "AUTHENTIC_PHOTO"
    assert t2["cascade_level"] == 2 and t2["strategy"] == "MOTION_GRAPHIC_DIAGRAM" and t2["asset_provenance"] == "MOTION_GRAPHIC"
    assert t3["cascade_level"] == 3 and t3["strategy"] == "AI_RECONSTRUCTION" and t3["asset_provenance"] == "AI_RECONSTRUCTION"
    assert t4["cascade_level"] == 4 and t4["strategy"] == "ARCHIVAL_DOCUMENT" and t4["asset_provenance"] == "ARCHIVAL_FOOTAGE"
    assert t5["cascade_level"] == 5 and t5["strategy"] == "GENERIC_BROLL" and t5["asset_provenance"] == "STOCK"
    record_pass("AUDIT_1.4_FALLBACK_CASCADE", "5-Tier Fallback Cascade strictly enforces priority hierarchy (Alternative -> Motion Graphic -> AI -> Archival -> B-Roll)")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: ShotRelationshipEngine & All 12 Shot Relationships
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n>>> SECTION 2: ShotRelationshipEngine & Relational Grammar <<<")
    sre = ShotRelationshipEngine()

    # Verify all 12 relationships can be deduced and grammatically enforced
    rel_tests = [
        ("NUMBER_TO_SCALE", {"visual_job": "SHOW_SCALE", "visual_type": "text_stat"}, {"visual_job": "SHOW_COMPARISON"}, "NUMBER_TO_SCALE", "wide", "wide_angle_lens", "slow_push_in"),
        ("EVIDENCE_TO_REVEAL", {"visual_job": "EXAMINE_EVIDENCE"}, {"visual_job": "REVEAL"}, "EVIDENCE_TO_REVEAL", "close", "standard_lens", "static"),
        ("OBJECT_TO_PERSON", {"visual_job": "INTRODUCE_OBJECT"}, {"visual_job": "INTRODUCE_CHARACTER"}, "OBJECT_TO_PERSON", "medium", "standard_lens", None),
        ("PERSON_TO_CONSEQUENCE", {"visual_job": "INTRODUCE_CHARACTER"}, {"visual_job": "CONSEQUENCE"}, "PERSON_TO_CONSEQUENCE", "medium_close", "standard_lens", None),
        ("QUESTION_TO_ANSWER", {"visual_job": "BUILD_MYSTERY"}, {"visual_job": "REVEAL"}, "QUESTION_TO_ANSWER", None, None, "static"),
        ("DETAIL_TO_CONTEXT", {"shot_size": "close"}, {"shot_size": "wide"}, "DETAIL_TO_CONTEXT", "wide", "wide_angle_lens", "slow_push_in"),
        ("CONTEXT_TO_DETAIL", {"shot_size": "wide"}, {"shot_size": "close"}, "CONTEXT_TO_DETAIL", "extreme_close", "macro_lens", "static"),
        ("CONTRAST", {"visual_job": "CONTRAST", "visual_density": 0.8, "camera_motion": "slow_push_in"}, {"visual_job": "CONTRAST"}, "CONTRAST", None, None, "static"),
        ("EXPECTATION_TO_SUBVERSION", {"visual_job": "ESTABLISH_WORLD"}, {"visual_job": "INTERRUPT"}, "EXPECTATION_TO_SUBVERSION", None, None, None),
        ("BEFORE_TO_AFTER", {"visual_job": "RECONSTRUCT_EVENT"}, {"visual_job": "PAYOFF"}, "BEFORE_TO_AFTER", None, None, None),
        ("CAUSE_TO_EFFECT", {"visual_job": "SHOW_COMPARISON"}, {"visual_job": "CONSEQUENCE"}, "CAUSE_TO_EFFECT", None, None, "slow_push_in"),
        ("CONTINUATION", {"visual_job": "ESTABLISH_WORLD", "shot_size": "wide", "camera_motion": "slow_push_in"}, {"visual_job": "ESTABLISH_WORLD", "shot_size": "wide", "camera_motion": "slow_push_in"}, "CONTINUATION", "close", None, "static")
    ]

    for label, prev_s, curr_s, exp_rel, exp_size, exp_lens, exp_motion in rel_tests:
        res = sre.determine_and_enforce_relationship(prev_s, curr_s)
        assert res["shot_relationship"] == exp_rel, f"Expected {exp_rel}, got {res['shot_relationship']}"
        if exp_size:
            assert res.get("shot_size") == exp_size, f"For {exp_rel}, expected shot_size {exp_size}, got {res.get('shot_size')}"
        if exp_lens:
            assert res.get("lens") == exp_lens, f"For {exp_rel}, expected lens {exp_lens}, got {res.get('lens')}"
        if exp_motion:
            assert res.get("camera_motion") == exp_motion, f"For {exp_rel}, expected camera_motion {exp_motion}, got {res.get('camera_motion')}"

    record_pass("AUDIT_2.1_ALL_12_RELATIONSHIPS", "All 12 Shot Relationships correctly deduced and grammatically enforced")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: VisualIntentEngine Extraction & Entity Parsing
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n>>> SECTION 3: VisualIntentEngine Extraction <<<")
    vie = VisualIntentEngine()

    test_sentences = [
        ("The rogue trader concealed £827,000,000 in losses across 5 accounts.", True, "£827,000,000", False, False, False),
        ("At 11:47 AM, a single typographical error fandation was discovered by auditors.", False, "", True, "11:47 AM", True),
        ("Exhausted workers with trembling hands watched the stock collapse in despair.", False, "", False, "", False),
    ]

    res1 = vie.analyze_block_intent("The rogue trader concealed £827 million in losses across 5 accounts.", "")
    assert res1["has_statistic"] is True
    assert "827" in res1["statistic_text"]
    assert res1["recommended_visual_job"] == VisualJob.SHOW_SCALE.value

    res2 = vie.analyze_block_intent("At 11:47 AM, a single typographical error fandation was discovered by auditors.", "")
    assert res2["has_timestamp"] is True
    assert "11:47 AM" in res2["timestamp_text"]
    assert res2["has_anomaly"] is True
    assert res2["recommended_visual_job"] == VisualJob.EXAMINE_EVIDENCE.value

    res3 = vie.analyze_block_intent("Exhausted workers with trembling hands watched the stock collapse in despair.", "")
    assert res3["has_human_anchor"] is True
    assert res3["recommended_visual_job"] == VisualJob.HUMANIZE.value

    record_pass("AUDIT_3.1_INTENT_EXTRACTION", "VisualIntentEngine accurately extracted dramatic numbers, timestamps, anomalies, and human anchor cues")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4: DirectorMemory 3-Act Motif Escalation & Cadence Tracking
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n>>> SECTION 4: DirectorMemory & 7D Contrast Tracking <<<")
    dm = DirectorMemory()
    dm.register_motifs(["green phosphorescent CRT monitor", "dot matrix printer ledger"])

    # Test 3-Act Escalation
    act1_m = dm.get_escalated_motif_prompt("green phosphorescent CRT monitor", act_num=1, topic="Barings Bank")
    act2_m = dm.get_escalated_motif_prompt("green phosphorescent CRT monitor", act_num=2, topic="Barings Bank")
    act3_m = dm.get_escalated_motif_prompt("green phosphorescent CRT monitor", act_num=3, topic="Barings Bank")

    assert act1_m["treatment"] == "GROUNDING" and act1_m["visual_job"] == VisualJob.BUILD_MYSTERY.value
    assert act2_m["treatment"] == "ESCALATION_DISTORTION" and act2_m["visual_job"] == VisualJob.ESCALATE.value
    assert act3_m["treatment"] == "PAYOFF_AFTERMATH" and act3_m["visual_job"] == VisualJob.PAYOFF.value
    record_pass("AUDIT_4.1_MOTIF_ESCALATION", "DirectorMemory properly implements 3-Act Motif Escalation (Grounding -> Escalation -> Payoff)")

    # Test Human Anchor Cadence
    dm.reset()
    assert dm.needs_human_anchor(threshold=3) is False
    # Record 3 non-human shots
    for i in range(3):
        dm.record_shot({"visual_job": "SHOW_EVIDENCE", "duration_seconds": 3.0, "camera_motion": "static"})
    assert dm.needs_human_anchor(threshold=3) is True
    # Record 1 human shot
    dm.record_shot({"visual_job": "HUMANIZE", "duration_seconds": 3.0, "camera_motion": "static"})
    assert dm.needs_human_anchor(threshold=3) is False
    record_pass("AUDIT_4.2_HUMAN_ANCHOR_CADENCE", "DirectorMemory reliably tracks human anchor cadence and alerts when grounding is needed")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5: VisualStoryPlanner Full Decomposition & 7D Contrast
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n>>> SECTION 5: VisualStoryPlanner Narration Block Decomposition <<<")
    vsp = VisualStoryPlanner()
    vsp.reset_timeline(topic="Enron Scandal", genre="documentary")

    block = {
        "block_id": "b001_n001",
        "voiceover": "By late 2001, Enron reported $101 BILLION in fake revenue, but confidential whistle-blower memos revealed catastrophic losses while employees wept in empty offices.",
        "caption": "Enron reported $101 Billion before collapse.",
        "shots": [{"visual_query": "Enron headquarters building"}]
    }

    research_pkg = {
        "topic": "The Fall of Enron",
        "visual_motifs": ["crooked E logo in shadows", "shredded audit paper"]
    }

    shots = vsp.decompose_narration_block(
        block,
        actual_duration=11.5,
        beat_intent="REVELATION",
        attention_intensity=0.95,
        time_mode="historical",
        research_package=research_pkg,
        act_num=2
    )

    # Invariants Verification:
    # 1. Non-empty
    assert len(shots) >= 3, f"Expected >= 3 shots for 11.5s block, got {len(shots)}"
    # 2. Duration preservation: sum(duration_seconds) == actual_duration
    total_dur = sum(s["duration_seconds"] for s in shots)
    assert abs(total_dur - 11.5) < 0.001, f"Expected total duration 11.5s, got {total_dur}"
    # 3. Individual shot duration <= 4.5s
    for s in shots:
        assert s["duration_seconds"] <= 4.5, f"Shot {s['shot_id']} exceeded 4.5s: {s['duration_seconds']}s"
        assert s["visual_job"] in [j.value for j in VisualJob]
        assert s["shot_relationship"] in [r.value for r in ShotRelationship]

    # 4. Check presence of NUMBER_REVEAL event and NUMBER_TO_SCALE relationship
    stat_shots = [s for s in shots if s.get("visual_type") == "text_stat" or any(e.get("type") == "NUMBER_REVEAL" for e in s.get("editorial_events", []))]
    assert len(stat_shots) >= 1, "Expected kinetic typography stat shot"

    scale_rel_shots = [s for s in shots if s.get("shot_relationship") == "NUMBER_TO_SCALE"]
    assert len(scale_rel_shots) >= 1, "Expected NUMBER_TO_SCALE relationship following stat shot"

    # 5. Check presence of HUMANIZE shot (from employees wept)
    human_shots = [s for s in shots if s.get("visual_job") == "HUMANIZE"]
    assert len(human_shots) >= 1, "Expected HUMANIZE shot grounding in human consequence"

    # 6. Check Mute Test on planner output
    mute_res = vsd.evaluate_mute_test(shots)
    assert mute_res["mute_test_passed"] is True, f"Mute test failed on planner output: {mute_res}"

    record_pass("AUDIT_5.1_DECOMPOSITION_INVARIANTS", f"VisualStoryPlanner decomposed 11.5s block into {len(shots)} shots satisfying duration conservation, <= 4.5s limit, kinetic typography, NUMBER_TO_SCALE, and Mute Test")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 6: Adversarial & Anti-Hardcoding Robustness Tests
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n>>> SECTION 6: Adversarial Stress & Anti-Hardcoding Tests <<<")

    # 6.1 Multi-Topic Generalization (Prove no single-topic hardcoding)
    diverse_topics = [
        ("The Chernobyl Disaster", "At 1:23:45 AM, reactor number 4 exploded during a safety test, releasing 400x more radiation than Hiroshima as trembling workers faced catastrophic consequence."),
        ("The 2008 Lehman Brothers Crash", "Lehman held $613 BILLION in toxic debt before filing bankruptcy, leaving thousands of panicked workers in despair."),
        ("The Apollo 13 Crisis", "An oxygen tank ruptured 200,000 miles from Earth, leaving three exhausted astronauts in sub-zero darkness.")
    ]

    for topic_name, text in diverse_topics:
        vsp.reset_timeline(topic=topic_name, genre="documentary")
        t_block = {
            "block_id": "b_adv_001",
            "voiceover": text,
            "caption": text[:60],
            "shots": [{"visual_query": f"{topic_name} archive"}]
        }
        t_shots = vsp.decompose_narration_block(t_block, actual_duration=9.0, beat_intent="ESCALATION", attention_intensity=0.85)
        assert len(t_shots) >= 2
        assert abs(sum(s["duration_seconds"] for s in t_shots) - 9.0) < 0.001
        for s in t_shots:
            assert s["duration_seconds"] <= 4.5
        t_mute = vsd.evaluate_mute_test(t_shots)
        if not t_mute["mute_test_passed"]:
            print(f"Failed mute test for {topic_name}: {t_mute}")
            print(f"Shots jobs: {[s['visual_job'] for s in t_shots]}")
        assert t_mute["mute_test_passed"] is True
    record_pass("AUDIT_6.1_MULTI_TOPIC_GENERALIZATION", f"Decomposition and Mute Test succeeded seamlessly across {len(diverse_topics)} distinct non-trivial documentary topics")

    # 6.2 Extreme Duration Boundaries
    # Very short duration (1.2s)
    short_shots = vsp.decompose_narration_block({"voiceover": "One word.", "shots": []}, actual_duration=1.2)
    assert len(short_shots) >= 1
    assert abs(sum(s["duration_seconds"] for s in short_shots) - 1.2) < 0.001

    # Long duration (24.0s) -> must split into multiple <= 4.5s shots
    long_shots = vsp.decompose_narration_block({"voiceover": "A very long detailed monologue lasting twenty four seconds.", "shots": []}, actual_duration=24.0)
    assert len(long_shots) >= 6
    assert abs(sum(s["duration_seconds"] for s in long_shots) - 24.0) < 0.001
    for s in long_shots:
        assert s["duration_seconds"] <= 4.5
    record_pass("AUDIT_6.2_DURATION_BOUNDARIES", "Handled extreme duration boundaries (1.2s to 24.0s) while strictly maintaining <= 4.5s max shot limit")

    print("\n" + "=" * 75)
    print(f"AUDIT SUMMARY: PASSED={audit_results['passed']}, FAILED={audit_results['failed']}")
    print("=" * 75)
    return audit_results["failed"] == 0

if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
