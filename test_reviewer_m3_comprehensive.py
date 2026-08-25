import math
import random
import pytest
from agents.schema import (
    VisualSequencePlan, VisualJob, ShotRelationship, StoryBeat, NarrationBlock, Shot,
    DocumentaryResearchPackage, DocumentaryVision, NarrativeIntent, MiniArcPhase, ContinuityMetadata
)
from agents.visual_sequence_director import VisualSequenceDirector
from agents.shot_relationship import ShotRelationshipEngine
from agents.visual_intent import VisualIntentEngine
from agents.director_memory import DirectorMemory
from agents.visual_story_planner import VisualStoryPlanner

def make_base_shot():
    return {
        "visual_description": "Initial base shot visual description for documentary.",
        "visual_query": "investigative documentary case file",
        "ai_prompt": "Cinematic documentary shot",
        "cut_reason": "reveal_documentary_context",
        "continuity": {
            "group_id": "grp_001",
            "characters": [],
            "location": "Central Bank",
            "environment": "Dim operations floor",
            "time_period": "2016",
            "lighting": "Low-key tungsten"
        }
    }

def run_comprehensive_reviewer_tests():
    print("=== STARTING REVIEWER 2 COMPREHENSIVE VERIFICATION ===")
    
    planner = VisualStoryPlanner()
    vsd = VisualSequenceDirector()
    sre = ShotRelationshipEngine()
    vie = VisualIntentEngine()
    
    # -------------------------------------------------------------
    # 1. BOUNDARY CONDITIONS: VERY SHORT (1-2s) AND VERY LONG (>10s)
    # -------------------------------------------------------------
    print("\n--- 1. Boundary Condition Testing ---")
    boundary_durations = [0.5, 1.0, 1.2, 1.8, 2.0, 2.5, 4.5, 4.51, 5.0, 9.9, 10.0, 10.1, 15.0, 30.0, 60.0]
    
    for dur in boundary_durations:
        planner.reset_timeline()
        block = {
            "block_id": f"n_bnd_{int(dur*10)}",
            "voiceover": f"Narration block testing boundary duration of {dur} seconds.",
            "caption": f"Testing {dur}s.",
            "shots": [make_base_shot()]
        }
        shots = planner.decompose_narration_block(block, actual_duration=dur, beat_intent="FIRST_DISCOVERY")
        
        sum_dur = sum(s["duration_seconds"] for s in shots)
        assert abs(sum_dur - dur) < 1e-3, f"Sum mismatch for dur={dur}: got {sum_dur}"
        
        # Verify shot count matches math.ceil(dur / 4.5)
        min_expected_shots = math.ceil(dur / 4.5)
        assert len(shots) >= min_expected_shots, f"Expected at least {min_expected_shots} shots for dur={dur}, got {len(shots)}"
        
        for s in shots:
            assert s["duration_seconds"] <= 4.5001, f"Shot exceeded 4.5s for dur={dur}: {s['duration_seconds']}"
            assert s["duration_seconds"] > 0, f"Shot duration <= 0 for dur={dur}: {s['duration_seconds']}"
            assert s["visual_job"] in [j.value for j in VisualJob], f"Invalid VisualJob: {s['visual_job']}"
            assert s["shot_relationship"] in [r.value for r in ShotRelationship], f"Invalid ShotRelationship: {s['shot_relationship']}"
            
    print(f"Boundary conditions ({boundary_durations}) PASSED!")
    
    # -------------------------------------------------------------
    # 2. INVARIANTS: DURATION SUM == ACTUAL_DURATION, ALL SHOTS <= 4.5s
    # -------------------------------------------------------------
    print("\n--- 2. Invariant Stress Testing Across 500 Randomized Blocks ---")
    random.seed(1337)
    for i in range(500):
        rand_dur = round(random.uniform(0.3, 50.0), 3)
        rand_intent = random.choice(list(NarrativeIntent)).value
        planner.reset_timeline()
        block = {
            "block_id": f"n_rnd_{i:04d}",
            "voiceover": f"Transaction #{i} with value  Million at 11:47 AM showed typo discrepancy.",
            "caption": f"Transaction #{i}",
            "shots": [make_base_shot()]
        }
        shots = planner.decompose_narration_block(block, actual_duration=rand_dur, beat_intent=rand_intent)
        
        sum_dur = sum(s["duration_seconds"] for s in shots)
        assert abs(sum_dur - rand_dur) < 1e-3, f"Iteration {i}: sum_dur={sum_dur} != {rand_dur}"
        
        for s in shots:
            assert s["duration_seconds"] <= 4.5001, f"Iteration {i}: shot dur {s['duration_seconds']} > 4.5"
            assert s["duration_seconds"] > 0, f"Iteration {i}: shot dur {s['duration_seconds']} <= 0"
            
    print("500 Randomized Invariant Tests PASSED!")

    # -------------------------------------------------------------
    # 3. ROBUSTNESS OF FALLBACKS WHEN LLM OR EXTERNAL CALLS ARE UNAVAILABLE
    # -------------------------------------------------------------
    print("\n--- 3. LLM Offline / Exception Fallback Robustness ---")
    
    # Test plan_visual_sequence with LLM failure simulation
    class FailingVSD(VisualSequenceDirector):
        def call_llm(self, prompt, system=None):
            raise ConnectionError("Simulated LLM API offline / Timeout")
            
    failing_vsd = FailingVSD()
    for intent in NarrativeIntent:
        beat = {
            "beat_id": "b_offline",
            "narrative_intent": intent.value,
            "description": "Simulated offline narrative beat",
            "narration_blocks": [{"block_id": "n01", "voiceover": "Offline voiceover", "caption": "Offline"}]
        }
        plan = failing_vsd.plan_visual_sequence(beat)
        assert isinstance(plan, VisualSequencePlan)
        assert plan.visual_argument
        assert plan.withholding_strategy
        assert plan.memorable_image
        assert plan.sequence_ending_statement
        assert 0.0 <= plan.information_change <= 1.0
        assert 0.0 <= plan.emotional_change <= 1.0
        assert 0.0 <= plan.visual_change <= 1.0
        assert 0.0 <= plan.scale_change <= 1.0
        
    print("LLM Offline Fallback for all NarrativeIntents PASSED!")

    # -------------------------------------------------------------
    # 4. 5-TIER NO-GENERIC-B-ROLL FALLBACK CASCADE
    # -------------------------------------------------------------
    print("\n--- 4. Fallback Cascade 5-Tier Routing ---")
    
    # Level 1: Humanize / Human Anchor
    t1 = vsd.apply_fallback_cascade(VisualJob.HUMANIZE, intent_info={"has_human_anchor": True})
    assert t1["cascade_level"] == 1
    assert t1["strategy"] == "ALTERNATIVE_INTERPRETATION"
    assert t1["asset_provenance"] == "AUTHENTIC_PHOTO"
    assert t1["fallback_type"] == "PortraitCard"
    
    # Level 2: Motion Graphic / Statistic
    t2 = vsd.apply_fallback_cascade(VisualJob.SHOW_SCALE, intent_info={"has_statistic": True})
    assert t2["cascade_level"] == 2
    assert t2["strategy"] == "MOTION_GRAPHIC_DIAGRAM"
    assert t2["asset_provenance"] == "MOTION_GRAPHIC"
    assert t2["fallback_type"] == "CinematicText"
    
    # Level 3: AI Reconstruction / Covert / Mystery
    t3 = vsd.apply_fallback_cascade(VisualJob.ESCALATE, intent_info={"has_cyber": True})
    assert t3["cascade_level"] == 3
    assert t3["strategy"] == "AI_RECONSTRUCTION"
    assert t3["asset_provenance"] == "AI_RECONSTRUCTION"
    assert t3["fallback_type"] == "EvidenceBoard"
    
    # Level 4: Archival Document / Case file
    t4 = vsd.apply_fallback_cascade(VisualJob.EXAMINE_EVIDENCE, intent_info={"has_anomaly": True})
    assert t4["cascade_level"] == 4
    assert t4["strategy"] == "ARCHIVAL_DOCUMENT"
    assert t4["asset_provenance"] == "ARCHIVAL_FOOTAGE"
    assert t4["fallback_type"] == "ClassifiedFile"
    
    # Level 5: Generic B-Roll last resort
    t5 = vsd.apply_fallback_cascade(VisualJob.ESTABLISH_WORLD, intent_info={}, available_assets={})
    assert t5["cascade_level"] == 5
    assert t5["strategy"] == "GENERIC_BROLL"
    assert t5["asset_provenance"] == "STOCK"
    assert t5["fallback_type"] == "PhotoWall"
    
    print("5-Tier Fallback Cascade Routing PASSED!")

    # -------------------------------------------------------------
    # 5. SHOT RELATIONSHIP ENGINE RELATIONAL GRAMMAR
    # -------------------------------------------------------------
    print("\n--- 5. Shot Relationship Relational Grammar ---")
    
    # Number to scale transition
    prev_stat = {"visual_job": VisualJob.SHOW_SCALE.value, "visual_type": "text_stat", "shot_size": "medium", "camera_motion": "static", "visual_density": 0.8}
    curr_shot = {"visual_job": VisualJob.SHOW_COMPARISON.value, "shot_size": "medium", "camera_motion": "static", "visual_density": 0.5}
    res_num = sre.determine_and_enforce_relationship(prev_stat, curr_shot)
    assert res_num["shot_relationship"] == ShotRelationship.NUMBER_TO_SCALE.value
    assert res_num["shot_size"] == "wide"
    assert res_num["camera_motion"] == "slow_push_in"
    assert res_num["visual_density"] == 0.40
    
    # Evidence to reveal transition
    prev_ev = {"visual_job": VisualJob.EXAMINE_EVIDENCE.value, "shot_size": "close", "camera_motion": "slow_push_in", "visual_density": 0.4}
    curr_rev = {"visual_job": VisualJob.REVEAL.value, "shot_size": "wide", "camera_motion": "pan_left", "visual_density": 0.5}
    res_rev = sre.determine_and_enforce_relationship(prev_ev, curr_rev)
    assert res_rev["shot_relationship"] == ShotRelationship.EVIDENCE_TO_REVEAL.value
    assert res_rev["camera_motion"] == "static"
    assert res_rev["is_restrained"] is True
    assert res_rev["shot_size"] == "close"
    
    # Detail to Context transition
    prev_close = {"visual_job": VisualJob.REVEAL_DETAIL.value, "shot_size": "close", "camera_motion": "static", "visual_density": 0.3}
    curr_wide = {"visual_job": VisualJob.ESTABLISH_WORLD.value, "shot_size": "wide", "camera_motion": "static", "visual_density": 0.5}
    res_det_ctx = sre.determine_and_enforce_relationship(prev_close, curr_wide)
    assert res_det_ctx["shot_relationship"] == ShotRelationship.DETAIL_TO_CONTEXT.value
    assert res_det_ctx["shot_size"] == "wide"
    assert res_det_ctx["lens"] == "wide_angle_lens"
    
    # Context to Detail transition
    prev_wide = {"visual_job": VisualJob.ESTABLISH_WORLD.value, "shot_size": "wide", "camera_motion": "slow_push_in", "visual_density": 0.3}
    curr_close = {"visual_job": VisualJob.EXAMINE_EVIDENCE.value, "shot_size": "close", "camera_motion": "static", "visual_density": 0.5}
    res_ctx_det = sre.determine_and_enforce_relationship(prev_wide, curr_close)
    assert res_ctx_det["shot_relationship"] == ShotRelationship.CONTEXT_TO_DETAIL.value
    assert res_ctx_det["shot_size"] == "extreme_close"
    assert res_ctx_det["lens"] == "macro_lens"
    assert res_ctx_det["camera_motion"] == "static"
    
    print("Shot Relationship Relational Grammar PASSED!")

    # -------------------------------------------------------------
    # 6. DIRECTOR MEMORY MOTIF ESCALATION & HUMAN ANCHOR CADENCE
    # -------------------------------------------------------------
    print("\n--- 6. Director Memory Motif Escalation & Human Anchor Cadence ---")
    mem = DirectorMemory()
    mem.register_motifs(["forged telex dispatch"])
    
    # 3-act escalation
    act1_motif = mem.get_escalated_motif_prompt("forged telex dispatch", act_num=1, topic="Bangladesh Bank")
    act2_motif = mem.get_escalated_motif_prompt("forged telex dispatch", act_num=2, topic="Bangladesh Bank")
    act3_motif = mem.get_escalated_motif_prompt("forged telex dispatch", act_num=3, topic="Bangladesh Bank")
    
    assert act1_motif["treatment"] == "GROUNDING"
    assert act1_motif["visual_job"] == VisualJob.BUILD_MYSTERY.value
    assert act2_motif["treatment"] == "ESCALATION_DISTORTION"
    assert act2_motif["visual_job"] == VisualJob.ESCALATE.value
    assert act3_motif["treatment"] == "PAYOFF_AFTERMATH"
    assert act3_motif["visual_job"] == VisualJob.PAYOFF.value
    
    # Human anchor cadence check
    assert not mem.needs_human_anchor(threshold=4)
    for k in range(4):
        mem.record_shot({"visual_job": VisualJob.VISUALIZE_ABSTRACT_CONCEPT.value, "visual_query": "server racks", "duration_seconds": 3.0})
    assert mem.needs_human_anchor(threshold=4)
    
    # Reset human anchor upon recording a human shot
    mem.record_shot({"visual_job": VisualJob.HUMANIZE.value, "visual_query": "hands trembling", "duration_seconds": 3.0})
    assert not mem.needs_human_anchor(threshold=4)
    assert mem.total_human_anchors == 1
    
    print("Director Memory Motif Escalation & Human Anchor Cadence PASSED!")

    print("\n=== ALL REVIEWER 2 ADVERSARIAL VERIFICATIONS PASSED 100%! ===")

if __name__ == '__main__':
    run_comprehensive_reviewer_tests()
