import json
from agents.schema import (
    VisualSequencePlan, VisualJob, ShotRelationship, StoryBeat, NarrationBlock, Shot,
    DocumentaryResearchPackage, DocumentaryVision
)
from agents.visual_sequence_director import VisualSequenceDirector
from agents.shot_relationship import ShotRelationshipEngine
from agents.visual_intent import VisualIntentEngine
from agents.director_memory import DirectorMemory
from agents.visual_story_planner import VisualStoryPlanner

def verify_m3():
    print("=== 1. VERIFYING SCHEMAS & ENUMS ===")
    assert len(VisualJob) == 20, f"Expected 20 VisualJobs, got {len(VisualJob)}"
    assert len(ShotRelationship) == 12, f"Expected 12 ShotRelationships, got {len(ShotRelationship)}"
    print("20 VisualJobs:", [j.value for j in VisualJob])
    print("12 ShotRelationships:", [r.value for r in ShotRelationship])

    print("\n=== 2. VERIFYING VISUAL SEQUENCE DIRECTOR ===")
    vsd = VisualSequenceDirector()
    beat = {
        "beat_id": "b001",
        "narrative_intent": "HOOK",
        "description": "The shocking cyber breach at Bangladesh Bank where $81 million vanished.",
        "narration_blocks": [
            {"block_id": "n001", "voiceover": "February 4, 2016. At 11:47 PM, printer logs stopped in Dhaka.", "caption": "Dhaka printer logs stopped."}
        ]
    }
    plan = vsd.plan_visual_sequence(beat)
    assert isinstance(plan, VisualSequencePlan), "Plan must be a VisualSequencePlan instance"
    assert plan.visual_argument, "Visual argument must be non-empty"
    assert plan.withholding_strategy, "Withholding strategy must be non-empty"
    assert plan.memorable_image, "Memorable image must be non-empty"
    assert 0.0 <= plan.information_change <= 1.0
    assert 0.0 <= plan.emotional_change <= 1.0
    assert 0.0 <= plan.visual_change <= 1.0
    assert 0.0 <= plan.scale_change <= 1.0
    print("Generated Plan:\n", plan.model_dump_json(indent=2))

    # Test Fallback Cascade (5 Tiers)
    cascade_1 = vsd.apply_fallback_cascade("HUMANIZE")
    assert cascade_1["cascade_level"] == 1
    assert cascade_1["strategy"] == "ALTERNATIVE_INTERPRETATION"

    cascade_2 = vsd.apply_fallback_cascade("SHOW_SCALE", intent_info={"has_statistic": True})
    assert cascade_2["cascade_level"] == 2
    assert cascade_2["strategy"] == "MOTION_GRAPHIC_DIAGRAM"

    cascade_3 = vsd.apply_fallback_cascade("ESCALATE", intent_info={"has_cyber": True})
    assert cascade_3["cascade_level"] == 3
    assert cascade_3["strategy"] == "AI_RECONSTRUCTION"

    cascade_4 = vsd.apply_fallback_cascade("SHOW_EVIDENCE", intent_info={"has_anomaly": True})
    assert cascade_4["cascade_level"] == 4
    assert cascade_4["strategy"] == "ARCHIVAL_DOCUMENT"

    cascade_5 = vsd.apply_fallback_cascade("ESTABLISH_WORLD", available_assets={"has_ai_generator": False})
    assert cascade_5["cascade_level"] == 5
    assert cascade_5["strategy"] == "GENERIC_BROLL"
    print("Fallback Cascade 5 Tiers Verified Successfully!")

    print("\n=== 3. VERIFYING VISUAL INTENT & DRAMATIC NUMBERS ===")
    intent_engine = VisualIntentEngine()
    res_intent = intent_engine.analyze_block_intent(
        "Hackers stole $81 Million after a typo fandation was detected at 11:47 AM, leaving workers trembling.",
        "Hackers stole $81 Million."
    )
    assert res_intent["has_statistic"] is True
    assert res_intent["statistic_text"] == "$81 MILLION"
    assert res_intent["has_anomaly"] is True
    assert res_intent["has_human_anchor"] is True
    assert res_intent["has_cyber"] is True
    print("Intent Engine Output:\n", json.dumps(res_intent, indent=2))

    print("\n=== 4. VERIFYING SHOT RELATIONSHIP ENGINE ===")
    sre = ShotRelationshipEngine()
    shot1 = {"visual_job": "SHOW_SCALE", "visual_type": "text_stat", "shot_size": "medium", "camera_motion": "static", "visual_density": 0.8}
    shot2 = {"visual_job": "SHOW_COMPARISON", "shot_size": "medium", "camera_motion": "static", "visual_density": 0.5}
    shot2_rel = sre.determine_and_enforce_relationship(shot1, shot2)
    assert shot2_rel["shot_relationship"] == "NUMBER_TO_SCALE"
    assert shot2_rel["shot_size"] == "wide"

    shot_ev = {"visual_job": "EXAMINE_EVIDENCE", "shot_size": "close", "camera_motion": "slow_push_in", "visual_density": 0.4}
    shot_rev = {"visual_job": "REVEAL", "shot_size": "wide", "camera_motion": "pan_left", "visual_density": 0.5}
    shot_rev_rel = sre.determine_and_enforce_relationship(shot_ev, shot_rev)
    assert shot_rev_rel["shot_relationship"] == "EVIDENCE_TO_REVEAL"
    assert shot_rev_rel["camera_motion"] == "static"
    assert shot_rev_rel["is_restrained"] is True
    print("Shot Relationship Engine Relational Grammar Verified Successfully!")

    print("\n=== 5. VERIFYING VISUAL STORY PLANNER DECOMPOSITION ===")
    planner = VisualStoryPlanner()
    planner.reset_timeline()
    block = {
        "block_id": "n001",
        "voiceover": "Hackers attempted to route $81 Million across 35 accounts before a single spelling mistake fandation flagged the transaction, exposing nervous operators.",
        "caption": "$81 Million routed before fandation typo.",
        "shots": [{"visual_query": "Bangladesh bank heist document"}]
    }
    shots = planner.decompose_narration_block(
        block,
        actual_duration=8.4,
        beat_intent="FIRST_DISCOVERY",
        attention_intensity=0.9,
        time_mode="modern",
        sequence_plan=plan
    )
    assert len(shots) >= 2
    total_dur = sum(s["duration_seconds"] for s in shots)
    assert abs(total_dur - 8.4) < 0.01
    for s in shots:
        assert s["duration_seconds"] <= 4.5
        assert s["visual_job"] in [j.value for j in VisualJob]
        assert s["shot_relationship"] in [r.value for r in ShotRelationship]

    print(f"Decomposed {len(shots)} shots across 8.4s block:")
    for s in shots:
        print(f"  - Shot {s['shot_id']}: Job={s['visual_job']}, Rel={s['shot_relationship']}, Size={s['shot_size']}, Motion={s['camera_motion']}, Dur={s['duration_seconds']}s, Density={s['visual_density']}, SFX={s['sound_design']}")

    # Test Mute Test on generated shots
    mute_result = vsd.evaluate_mute_test(shots, plan)
    print("\nMute Test Result:\n", json.dumps(mute_result, indent=2))
    assert mute_result["mute_test_passed"] is True, "Mute test must pass on planner output"

    print("\n=== 6. VERIFYING DIRECTOR MEMORY MOTIF ESCALATION ===")
    memory = DirectorMemory()
    memory.register_motifs(["ticking control room clock"])
    p1 = memory.get_escalated_motif_prompt("ticking control room clock", act_num=1, topic="Bangladesh Bank")
    p2 = memory.get_escalated_motif_prompt("ticking control room clock", act_num=2, topic="Bangladesh Bank")
    p3 = memory.get_escalated_motif_prompt("ticking control room clock", act_num=3, topic="Bangladesh Bank")
    assert p1["treatment"] == "GROUNDING" and p1["visual_job"] == "BUILD_MYSTERY"
    assert p2["treatment"] == "ESCALATION_DISTORTION" and p2["visual_job"] == "ESCALATE"
    assert p3["treatment"] == "PAYOFF_AFTERMATH" and p3["visual_job"] == "PAYOFF"
    print("Director Memory 3-Act Motif Escalation Verified Successfully!")

    print("\nALL MILESTONE 3 VERIFICATIONS PASSED!")

if __name__ == "__main__":
    verify_m3()
