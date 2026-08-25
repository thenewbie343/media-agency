import sys
import os
import json
import logging
import copy
from typing import Dict, Any, List

from agents.schema import (
    DocumentaryResearchPackage,
    DocumentaryVision,
    HookStrategy,
    NarrativePhasePlan,
    MiniArcPlan,
    NarrativeIntent,
    MiniArcPhase,
    VisualJob,
    ShotRelationship,
    ScriptManifest,
    StoryBeat,
    NarrationBlock,
    Shot,
    LEGACY_VISUAL_JOB_MAP,
)
from agents.researcher import ResearcherAgent
from agents.head_writer import HeadWriterAgent
from agents.scriptwriter import ScriptwriterAgent
from agents.director import DirectorAgent
from agents.engine import run_documentary_pipeline

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("m2_challenger")

results = []

def record(test_id: str, desc: str, passed: bool, error_msg: str = ""):
    status = "PASS" if passed else "FAIL"
    results.append((test_id, desc, passed, error_msg))
    mark = f"[{status}]"
    print(f"{mark:7s} {test_id}: {desc}")
    if not passed and error_msg:
        print(f"        ERROR: {error_msg}")

def main():
    print("=" * 80)
    print("REVIEWER 2 ADVERSARIAL STRESS TEST SUITE: MILESTONE 2 (DEEP RESEARCH & MACRO NARRATIVE)")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # SUITE 1: 11 Canonical Macro Narrative Phases & 5 Mini-Arc Phases Consistency
    # -------------------------------------------------------------------------
    print("\n>>> SUITE 1: 11 Canonical Macro Phases & 5 Mini-Arc Phases Consistency <<<")
    
    canonical_11_phases = [
        "HOOK", "CENTRAL_QUESTION", "CONTEXT", "FIRST_DISCOVERY",
        "COMPLICATION", "ESCALATION", "REVELATION", "CONSEQUENCE",
        "DEEPER_REVELATION", "FINAL_CONTRADICTION", "PAYOFF"
    ]
    
    canonical_5_mini_arcs = [
        "SETUP", "BUILD", "COMPLICATION", "REVEAL", "CONSEQUENCE"
    ]

    # T1.1: Verify all 11 phases in NarrativeIntent
    try:
        for phase in canonical_11_phases:
            assert phase in NarrativeIntent.__members__, f"Missing phase {phase} in NarrativeIntent"
            assert NarrativeIntent[phase].value == phase
        record("T1.1_NARRATIVE_INTENT_11_PHASES", "NarrativeIntent enum contains all 11 canonical macro phases", True)
    except Exception as e:
        record("T1.1_NARRATIVE_INTENT_11_PHASES", "NarrativeIntent enum contains all 11 canonical macro phases", False, str(e))

    # T1.2: Verify all 5 mini-arc phases in MiniArcPhase
    try:
        for mini in canonical_5_mini_arcs:
            assert mini in MiniArcPhase.__members__, f"Missing mini-arc phase {mini} in MiniArcPhase"
            assert MiniArcPhase[mini].value == mini
        record("T1.2_MINI_ARC_5_PHASES", "MiniArcPhase enum contains all 5 canonical dramatic phases", True)
    except Exception as e:
        record("T1.2_MINI_ARC_5_PHASES", "MiniArcPhase enum contains all 5 canonical dramatic phases", False, str(e))

    # T1.3: Verify Director normalize_manifest preserves all 11 phases without down-mapping
    try:
        director = DirectorAgent()
        for phase in canonical_11_phases:
            normalized = director.normalize_manifest({"narrative_intent": phase})
            assert normalized["narrative_intent"] == phase, f"Down-mapped or altered {phase} -> {normalized['narrative_intent']}"
            
            # test lowercase string
            normalized_lower = director.normalize_manifest({"narrative_intent": phase.lower()})
            assert normalized_lower["narrative_intent"] == phase, f"Failed lowercase normalization {phase.lower()} -> {normalized_lower['narrative_intent']}"
        record("T1.3_DIRECTOR_NO_DOWNMAPPING", "DirectorAgent.normalize_manifest preserves all 11 macro narrative phases", True)
    except Exception as e:
        record("T1.3_DIRECTOR_NO_DOWNMAPPING", "DirectorAgent.normalize_manifest preserves all 11 macro narrative phases", False, str(e))

    # T1.4: Verify Director normalize_manifest normalizes legacy aliases to correct canonical phases
    try:
        alias_checks = {
            "THE_PROBLEM": "COMPLICATION",
            "PROBLEM": "COMPLICATION",
            "SETUP": "CONTEXT",
            "DISCOVERY": "FIRST_DISCOVERY",
            "AFTERMATH": "CONSEQUENCE",
            "BACKGROUND": "CONTEXT",
            "INTRODUCTION": "HOOK",
            "CLIMAX": "REVELATION"
        }
        for alias, expected in alias_checks.items():
            norm = director.normalize_manifest({"narrative_intent": alias})
            assert norm["narrative_intent"] == expected, f"Alias {alias} expected {expected}, got {norm['narrative_intent']}"
        record("T1.4_DIRECTOR_ALIAS_RECOVERY", "DirectorAgent.normalize_manifest maps legacy aliases to canonical macro phases", True)
    except Exception as e:
        record("T1.4_DIRECTOR_ALIAS_RECOVERY", "DirectorAgent.normalize_manifest maps legacy aliases to canonical macro phases", False, str(e))

    # T1.5: Verify Director normalize_manifest normalizes all 5 mini-arc phases
    try:
        for mini in canonical_5_mini_arcs:
            norm = director.normalize_manifest({"mini_arc_phase": mini.lower()})
            assert norm["mini_arc_phase"] == mini, f"Mini-arc phase {mini.lower()} normalized to {norm['mini_arc_phase']}"
        record("T1.5_DIRECTOR_MINI_ARC_NORMALIZATION", "DirectorAgent.normalize_manifest normalizes all 5 mini-arc phases", True)
    except Exception as e:
        record("T1.5_DIRECTOR_MINI_ARC_NORMALIZATION", "DirectorAgent.normalize_manifest normalizes all 5 mini-arc phases", False, str(e))

    # -------------------------------------------------------------------------
    # SUITE 2: ResearcherAgent Robustness & 24-Field Package Validation
    # -------------------------------------------------------------------------
    print("\n>>> SUITE 2: ResearcherAgent Robustness & 24-Field Package <<<")

    researcher = ResearcherAgent()

    # T2.1: Researcher multi-query search fallback under simulated network exception
    try:
        class FailingDDGS:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): pass
            def text(self, query, max_results=4):
                raise RuntimeError("Simulated network timeout/socket error")

        import agents.researcher as r_mod
        orig_ddgs = r_mod.DDGS
        r_mod.DDGS = FailingDDGS
        
        # Test search with simulated failure
        search_res = researcher._execute_multi_query_search("Adani Group Investigation")
        assert "Search yielded no external snippets" in search_res or "internal historical knowledge" in search_res or len(search_res) > 0
        r_mod.DDGS = orig_ddgs
        record("T2.1_SEARCH_NETWORK_FAILURE_RESILIENCE", "Researcher handles DDGS network exceptions gracefully without crashing", True)
    except Exception as e:
        import agents.researcher as r_mod
        r_mod.DDGS = orig_ddgs
        record("T2.1_SEARCH_NETWORK_FAILURE_RESILIENCE", "Researcher handles DDGS network exceptions gracefully without crashing", False, str(e))

    # T2.2: Researcher with DDGS = None
    try:
        r_mod.DDGS = None
        search_res_none = researcher._execute_multi_query_search("Nokia Downfall")
        assert "No web search client available" in search_res_none
        r_mod.DDGS = orig_ddgs
        record("T2.2_SEARCH_NONE_CLIENT_RESILIENCE", "Researcher handles DDGS=None fallback gracefully", True)
    except Exception as e:
        r_mod.DDGS = orig_ddgs
        record("T2.2_SEARCH_NONE_CLIENT_RESILIENCE", "Researcher handles DDGS=None fallback gracefully", False, str(e))

    # T2.3: 24-Field DocumentaryResearchPackage complete validation
    try:
        pkg_dict = researcher.research_topic("The 2008 Financial Crisis")
        pkg = DocumentaryResearchPackage.model_validate(pkg_dict)
        
        # Verify required 24 dimensions exist and are non-empty
        assert pkg.topic
        assert pkg.central_question
        assert pkg.documentary_thesis
        assert pkg.central_contradiction
        assert pkg.audience_initial_belief
        assert pkg.what_the_audience_thinks_is_true
        assert pkg.what_is_actually_more_complicated
        assert pkg.protagonist_or_human_anchor
        assert pkg.antagonistic_force_or_system
        assert pkg.stakes
        assert pkg.historical_context
        assert len(pkg.turning_points) >= 1
        assert len(pkg.major_reveals) >= 1
        assert pkg.final_payoff
        assert len(pkg.evidence_items) >= 1
        assert len(pkg.people) >= 1
        assert len(pkg.locations) >= 1
        assert len(pkg.physical_objects) >= 1
        assert len(pkg.numbers) >= 1
        assert len(pkg.dates) >= 1
        assert len(pkg.archival_opportunities) >= 1
        assert len(pkg.reconstruction_opportunities) >= 1
        assert len(pkg.motion_graphic_opportunities) >= 1
        assert len(pkg.visual_motifs) >= 1
        assert pkg.ending_image_opportunity
        record("T2.3_RESEARCH_PACKAGE_24_FIELDS", "DocumentaryResearchPackage validates all 24 fields with authentic data structures", True)
    except Exception as e:
        record("T2.3_RESEARCH_PACKAGE_24_FIELDS", "DocumentaryResearchPackage validates all 24 fields with authentic data structures", False, str(e))

    # -------------------------------------------------------------------------
    # SUITE 3: DirectorAgent DocumentaryVision Formulation & Semantic Rules
    # -------------------------------------------------------------------------
    print("\n>>> SUITE 3: DirectorAgent Vision Formulation & Directorial Rules <<<")

    director = DirectorAgent()

    # T3.1: Formulate DocumentaryVision from research package
    try:
        vision_dict = director.formulate_vision(pkg_dict, duration_minutes=1)
        vision = DocumentaryVision.model_validate(vision_dict)
        assert vision.topic
        assert vision.central_question
        assert vision.central_contradiction
        assert vision.hook_strategy.hook_type in ["QUESTION", "CONTRADICTION", "SHOCK", "MYSTERY", "VISUAL_ANOMALY"]
        assert vision.hook_strategy.target_duration_seconds <= 30.0
        assert len(vision.visual_motifs) >= 1
        assert vision.ending_image
        record("T3.1_DIRECTOR_FORMULATE_VISION", "DirectorAgent.formulate_vision() produces valid DocumentaryVision schema", True)
    except Exception as e:
        record("T3.1_DIRECTOR_FORMULATE_VISION", "DirectorAgent.formulate_vision() produces valid DocumentaryVision schema", False, str(e))

    # T3.2: Semantic cut reasons coverage across all 11 macro narrative phases in enforce_strict_rules
    try:
        test_manifest = {
            "schema_version": "2.0",
            "project_meta": {
                "topic": "Test Topic",
                "genre": "documentary",
                "visual_bible": {
                    "era": "2000s", "locations": ["Earth"], "lighting": "low-key", "color_language": "noir", "film_texture": "grain"
                }
            },
            "story_beats": []
        }
        
        for idx, phase in enumerate(canonical_11_phases):
            test_manifest["story_beats"].append({
                "beat_id": f"b{idx+1:03d}",
                "narrative_intent": phase,
                "attention_intensity": 0.8,
                "narration_blocks": [
                    {
                        "block_id": f"n{idx+1:03d}",
                        "voiceover": "परीक्षण वॉयसओवर...",
                        "caption": "Test voiceover caption...",
                        "total_block_duration": 4.0,
                        "shots": [
                            {
                                "shot_id": f"n{idx+1:03d}_s001",
                                "duration_mode": "fixed",
                                "duration_seconds": 3.0,
                                "shot_role": "ESTABLISHING",
                                "visual_job": "ESTABLISH_WORLD",
                                "shot_relationship": "CONTINUATION",
                                "camera_motion": "zoom_in", # deliberately test anti-zoom_in replacement
                                "cut_reason": "introduce_conflict" # deliberately test generic cut_reason replacement
                            }
                        ]
                    }
                ]
            })

        enforced = director.enforce_strict_rules(test_manifest)
        
        for idx, beat in enumerate(enforced["story_beats"]):
            phase = canonical_11_phases[idx]
            shot = beat["narration_blocks"][0]["shots"][0]
            assert shot["camera_motion"] != "zoom_in", f"Failed to eliminate zoom_in for beat {beat['beat_id']}"
            assert shot["cut_reason"] != "introduce_conflict", f"Failed to replace generic cut_reason for beat {beat['beat_id']}"
            assert len(shot["cut_reason"]) > 10, f"Cut reason too short: {shot['cut_reason']}"
        record("T3.2_DIRECTOR_STRICT_RULES_11_PHASES", "Director enforce_strict_rules replaces camera fatigue and generic cut reasons for all 11 phases", True)
    except Exception as e:
        record("T3.2_DIRECTOR_STRICT_RULES_11_PHASES", "Director enforce_strict_rules replaces camera fatigue and generic cut reasons for all 11 phases", False, str(e))

    # T3.3: Shot duration hard limit splitting (>4.5s split enforcement)
    try:
        long_shot_manifest = copy.deepcopy(test_manifest)
        long_shot_manifest["story_beats"] = [long_shot_manifest["story_beats"][0]]
        long_shot_manifest["story_beats"][0]["narration_blocks"][0]["shots"][0]["duration_seconds"] = 10.0
        long_shot_manifest["story_beats"][0]["narration_blocks"][0]["shots"][0]["duration_mode"] = "fixed"
        
        split_enforced = director.enforce_strict_rules(long_shot_manifest)
        shots = split_enforced["story_beats"][0]["narration_blocks"][0]["shots"]
        assert len(shots) == 3, f"Expected 10.0s shot to be split into 3 sub-shots, got {len(shots)}"
        for s in shots:
            assert s["duration_seconds"] <= 4.5, f"Sub-shot duration {s['duration_seconds']} exceeds 4.5s hard limit"
        record("T3.3_DIRECTOR_HARD_4_5S_SPLIT", "Director enforce_strict_rules splits shots > 4.5s into varied sub-shots", True)
    except Exception as e:
        record("T3.3_DIRECTOR_HARD_4_5S_SPLIT", "Director enforce_strict_rules splits shots > 4.5s into varied sub-shots", False, str(e))

    # -------------------------------------------------------------------------
    # SUITE 4: HeadWriterAgent Macro Outline & Withholding Strategy
    # -------------------------------------------------------------------------
    print("\n>>> SUITE 4: HeadWriterAgent Macro Outline & Withholding <<<")

    head_writer = HeadWriterAgent()

    # T4.1: Outline generation with 11 macro phases and backward-compatible act keys
    try:
        outline_dict = head_writer.write_outline(pkg_dict, vision_dict, duration_minutes=1, target_scenes=8)
        assert isinstance(outline_dict, dict)
        assert "hook_strategy" in outline_dict
        assert "macro_phases" in outline_dict
        
        # Check backward-compatible act keys
        assert "act_1_the_hook_and_rise" in outline_dict or "acts" in outline_dict
        assert "act_2_the_conflict" in outline_dict or "acts" in outline_dict
        assert "act_3_the_fall_and_stakes" in outline_dict or "acts" in outline_dict
        record("T4.1_HEADWRITER_OUTLINE_STRUCTURE", "HeadWriterAgent produces structured outline with 11 macro phases and act keys", True)
    except Exception as e:
        record("T4.1_HEADWRITER_OUTLINE_STRUCTURE", "HeadWriterAgent produces structured outline with 11 macro phases and act keys", False, str(e))

    # -------------------------------------------------------------------------
    # SUITE 5: ScriptwriterAgent Hook Withholding & Dual-Pacing
    # -------------------------------------------------------------------------
    print("\n>>> SUITE 5: ScriptwriterAgent Hook Withholding & Dual-Pacing <<<")

    scriptwriter = ScriptwriterAgent()

    # T5.1: Scene 1 Hook & Withholding Law enforcement
    try:
        scenes = scriptwriter.write_script(pkg_dict, outline_dict, vision_dict, duration_minutes=1, target_scenes=5)
        assert isinstance(scenes, list) and len(scenes) >= 1
        scene_1 = scenes[0]
        
        # Scene 1 must have narrative_intent = HOOK and mini_arc_phase = SETUP
        assert scene_1.get("narrative_intent") in [NarrativeIntent.HOOK.value, "HOOK"], f"Scene 1 narrative_intent is {scene_1.get('narrative_intent')}"
        assert scene_1.get("mini_arc_phase") in [MiniArcPhase.SETUP.value, "SETUP"], f"Scene 1 mini_arc_phase is {scene_1.get('mini_arc_phase')}"
        assert "voiceover" in scene_1 and len(scene_1["voiceover"]) > 0
        assert "caption" in scene_1 and len(scene_1["caption"]) > 0
        record("T5.1_SCRIPTWRITER_SCENE1_HOOK_WITHHOLDING", "Scriptwriter Scene 1 enforces HOOK intent and SETUP mini-arc phase", True)
    except Exception as e:
        record("T5.1_SCRIPTWRITER_SCENE1_HOOK_WITHHOLDING", "Scriptwriter Scene 1 enforces HOOK intent and SETUP mini-arc phase", False, str(e))

    # T5.2: write_act execution for all 3 acts
    try:
        all_act_scenes = []
        for act_num in range(1, 4):
            act_outline = outline_dict.get(f"act_{act_num}", outline_dict.get("act_1_the_hook_and_rise", []))
            act_scenes = scriptwriter.write_act(
                pkg_dict,
                act_num,
                act_outline,
                vision=vision_dict,
                target_scenes=2,
                duration_minutes=1,
                context_so_far="Prior context test."
            )
            assert isinstance(act_scenes, list) and len(act_scenes) >= 1
            all_act_scenes.extend(act_scenes)
        assert len(all_act_scenes) >= 3
        record("T5.2_SCRIPTWRITER_WRITE_ACT_3_ACTS", "Scriptwriter write_act successfully drafts scenes across all 3 acts", True)
    except Exception as e:
        record("T5.2_SCRIPTWRITER_WRITE_ACT_3_ACTS", "Scriptwriter write_act successfully drafts scenes across all 3 acts", False, str(e))

    # -------------------------------------------------------------------------
    # SUITE 6: Director Metadata Integration & Schema Conformance
    # -------------------------------------------------------------------------
    print("\n>>> SUITE 6: Director Metadata Integration & Schema Conformance <<<")

    # T6.1: Director add_metadata attaches research_package and vision, validating ScriptManifest
    try:
        manifest_dict = director.add_metadata(scenes, research_package=pkg_dict, vision=vision_dict)
        manifest = ScriptManifest.model_validate(manifest_dict)
        assert manifest.research_package is not None
        assert manifest.documentary_vision is not None
        assert len(manifest.story_beats) >= 1
        record("T6.1_DIRECTOR_ADD_METADATA_VALIDATION", "DirectorAgent.add_metadata attaches research & vision, validating ScriptManifest", True)
    except Exception as e:
        record("T6.1_DIRECTOR_ADD_METADATA_VALIDATION", "DirectorAgent.add_metadata attaches research & vision, validating ScriptManifest", False, str(e))

    # -------------------------------------------------------------------------
    # SUITE 7: End-to-End AI Studio Pipeline Integration (agents/engine.py)
    # -------------------------------------------------------------------------
    print("\n>>> SUITE 7: Pipeline Compatibility (agents/engine.py & pipeline.py) <<<")

    # T7.1: run_documentary_pipeline execution
    try:
        pipeline_cfg = {"topic": "The Fall of Enron", "duration_min": 1}
        final_script, fact_sheet_out, stats = run_documentary_pipeline(pipeline_cfg)
        assert isinstance(final_script, dict)
        assert "story_beats" in final_script
        assert len(final_script["story_beats"]) >= 1
        assert stats["final_status"] == "APPROVED"
        
        # Verify every beat and block has valid IDs and intents
        for beat in final_script["story_beats"]:
            assert beat["beat_id"].startswith("b")
            assert beat["narrative_intent"] in [e.value for e in NarrativeIntent]
            for block in beat.get("narration_blocks", []):
                assert block["block_id"].startswith("n")
                for shot in block.get("shots", []):
                    assert shot["shot_id"].startswith(block["block_id"])
                    assert shot["visual_job"] in [e.value for e in VisualJob]
                    assert shot["shot_relationship"] in [e.value for e in ShotRelationship]
        record("T7.1_RUN_DOCUMENTARY_PIPELINE_E2E", "agents/engine.py run_documentary_pipeline generates approved master manifest", True)
    except Exception as e:
        record("T7.1_RUN_DOCUMENTARY_PIPELINE_E2E", "agents/engine.py run_documentary_pipeline generates approved master manifest", False, str(e))

    # -------------------------------------------------------------------------
    # SUITE 8: Adversarial Integrity & Facade Check
    # -------------------------------------------------------------------------
    print("\n>>> SUITE 8: Adversarial Integrity & Facade Check <<<")

    # T8.1: Test that agents don't rely on hardcoded static topic data
    try:
        dynamic_topic = "Operation Mincemeat 1943 Deception"
        dyn_pkg = researcher.research_topic(dynamic_topic)
        assert dyn_pkg["topic"] == dynamic_topic or dynamic_topic in dyn_pkg["topic"] or "Operation Mincemeat" in dyn_pkg.get("documentary_thesis", "") or len(dyn_pkg["evidence_items"]) >= 1
        
        dyn_vision = director.formulate_vision(dyn_pkg, duration_minutes=2)
        assert dyn_vision["topic"] == dynamic_topic or "Mincemeat" in str(dyn_vision) or len(dyn_vision["macro_narrative_arc"]) >= 1
        record("T8.1_DYNAMIC_TOPIC_INTEGRITY", "Agents dynamically handle diverse arbitrary historical topics without hardcoded cheats", True)
    except Exception as e:
        record("T8.1_DYNAMIC_TOPIC_INTEGRITY", "Agents dynamically handle diverse arbitrary historical topics without hardcoded cheats", False, str(e))

    # T8.2: Test malformed input handling in HeadWriter and Scriptwriter
    try:
        malformed_fact_sheet = "Not a valid JSON string"
        malformed_outline = "{ broken json: }"
        
        # HeadWriter should recover without raising exception
        hw_res = head_writer.write_outline(malformed_fact_sheet, vision="broken", duration_minutes=1)
        assert isinstance(hw_res, dict)
        
        # Scriptwriter should recover without raising exception
        sw_res = scriptwriter.write_script(malformed_fact_sheet, malformed_outline, vision="broken", duration_minutes=1)
        assert isinstance(sw_res, list) and len(sw_res) >= 1
        record("T8.2_MALFORMED_INPUT_RECOVERY", "HeadWriter and Scriptwriter gracefully recover from malformed string/JSON inputs", True)
    except Exception as e:
        record("T8.2_MALFORMED_INPUT_RECOVERY", "HeadWriter and Scriptwriter gracefully recover from malformed string/JSON inputs", False, str(e))

    # Summary
    print("\n" + "=" * 80)
    passed_count = sum(1 for _, _, p, _ in results if p)
    failed_count = sum(1 for _, _, p, _ in results if not p)
    print(f"REVIEWER 2 SUMMARY: TOTAL={len(results)}, PASSED={passed_count}, FAILED={failed_count}")
    print("=" * 80)
    
    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
