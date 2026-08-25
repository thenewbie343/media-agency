import sys
import json
import pydantic
from pydantic import ValidationError

from agents.schema import (
    NarrativeIntent, MiniArcPhase, VisualJob, ShotRelationship, LEGACY_VISUAL_JOB_MAP,
    EvidenceItem, NumberItem, PersonAnchor, TurningPointItem, MajorRevealItem,
    DocumentaryResearchPackage, HookStrategy, NarrativePhasePlan, MiniArcPlan,
    DocumentaryVision, VisualSequencePlan, VisualBible, ProjectMeta,
    HighlightMetadata, ContinuityMetadata, AssetMetadata, EditorialEvent,
    Shot, StrategicSilence, AudioMetadata, NarrationBlock, TimeContext,
    StoryBeat, ScriptManifest
)
from agents.base_agent import BaseAgent
from agents.researcher import ResearcherAgent
from agents.head_writer import HeadWriterAgent
from agents.scriptwriter import ScriptwriterAgent
from agents.director import DirectorAgent
from agents.qc_editor import QCEditorAgent

print("======================================================================")
print("CHALLENGER 2 EMPIRICAL TEST SUITE: M1 SCHEMA & CORE DATA MODELS")
print("======================================================================")

test_results = {"passed": 0, "failed": 0, "warnings": 0, "details": []}

def record_pass(test_id, msg):
    test_results["passed"] += 1
    test_results["details"].append(("PASS", test_id, msg))
    print(f"[PASS] [{test_id}] {msg}")

def record_fail(test_id, msg):
    test_results["failed"] += 1
    test_results["details"].append(("FAIL", test_id, msg))
    print(f"[FAIL] [{test_id}] {msg}")

def record_warn(test_id, msg):
    test_results["warnings"] += 1
    test_results["details"].append(("WARN", test_id, msg))
    print(f"[WARN] [{test_id}] {msg}")

# ----------------------------------------------------------------------------
# 1. BaseAgent Mock Fallbacks Verification
# ----------------------------------------------------------------------------
print("\n>>> SECTION 1: BaseAgent Mock Fallbacks Validation <<<")

# 1.1 ResearcherAgent Mock Fallback -> DocumentaryResearchPackage
try:
    res_agent = ResearcherAgent()
    res_mock = res_agent._get_mock_fallback("", "", True)
    pkg = DocumentaryResearchPackage.model_validate(res_mock)
    assert len(pkg.evidence_items) == 3
    assert len(pkg.major_reveals) == 5
    assert len(pkg.numbers) == 3
    assert len(pkg.people) == 2
    assert len(pkg.turning_points) == 3
    assert pkg.topic == "The Fall of Nokia"
    record_pass("T1.1_RESEARCHER_MOCK", "Researcher mock validates 24-field DocumentaryResearchPackage (3 evidence, 5 reveals, 3 numbers)")
except Exception as e:
    record_fail("T1.1_RESEARCHER_MOCK", f"Researcher mock validation failed: {e}")

# 1.2 DirectorAgent Mock Fallback -> ScriptManifest
try:
    dir_agent = DirectorAgent()
    dir_mock = dir_agent._get_mock_fallback("", "", True)
    manifest = ScriptManifest.model_validate(dir_mock)
    assert manifest.schema_version == "2.0"
    assert manifest.documentary_vision is not None
    assert manifest.research_package is not None
    assert len(manifest.story_beats) == 1
    beat = manifest.story_beats[0]
    assert beat.narrative_intent == NarrativeIntent.HOOK
    assert beat.visual_sequence_plan is not None
    assert len(beat.narration_blocks) == 2
    nb0 = beat.narration_blocks[0]
    assert nb0.mini_arc_phase == MiniArcPhase.SETUP
    assert len(nb0.shots) == 2
    s0 = nb0.shots[0]
    assert s0.visual_job == VisualJob.ESTABLISH_WORLD
    assert s0.shot_relationship == ShotRelationship.CONTINUATION
    s1 = nb0.shots[1]
    assert s1.visual_job == VisualJob.SHOW_SCALE
    assert s1.shot_relationship == ShotRelationship.NUMBER_TO_SCALE
    nb1 = beat.narration_blocks[1]
    assert nb1.mini_arc_phase == MiniArcPhase.REVEAL
    assert len(nb1.shots) == 1
    s2 = nb1.shots[0]
    assert s2.visual_job == VisualJob.EXAMINE_EVIDENCE
    assert s2.shot_relationship == ShotRelationship.EVIDENCE_TO_REVEAL
    record_pass("T1.2_DIRECTOR_MOCK", "Director mock validates complete ScriptManifest with Vision, ResearchPackage, StoryBeat, NarrationBlocks, Shots, VisualJobs, and ShotRelationships")
except Exception as e:
    record_fail("T1.2_DIRECTOR_MOCK", f"Director mock validation failed: {e}")

# 1.3 HeadWriterAgent Mock Fallback HookStrategy
try:
    hw_agent = HeadWriterAgent()
    hw_mock = hw_agent._get_mock_fallback("", "", True)
    hook = HookStrategy.model_validate(hw_mock["hook_strategy"])
    assert hook.hook_type == "CONTRADICTION"
    assert hook.target_duration_seconds == 25.0
    record_pass("T1.3_HEADWRITER_HOOK_MOCK", "HeadWriter mock hook_strategy validates HookStrategy schema")
except Exception as e:
    record_fail("T1.3_HEADWRITER_HOOK_MOCK", f"HeadWriter hook_strategy validation failed: {e}")

# 1.4 HeadWriterAgent MacroPhases in Mock
try:
    macro_phases = hw_mock["macro_phases"]
    assert len(macro_phases) == 11
    # Check if all 11 phases are valid NarrativeIntent values
    for mp in macro_phases:
        assert mp["phase"] in NarrativeIntent.__members__, f"Invalid phase {mp['phase']}"
    record_pass("T1.4_HEADWRITER_MACRO_PHASES", f"HeadWriter mock has all 11 canonical macro phases: {[mp['phase'] for mp in macro_phases]}")
except Exception as e:
    record_fail("T1.4_HEADWRITER_MACRO_PHASES", f"HeadWriter macro_phases failed: {e}")

# 1.5 ScriptwriterAgent Mock Fallback
try:
    sw_agent = ScriptwriterAgent()
    sw_mock = sw_agent._get_mock_fallback("", "", True)
    assert len(sw_mock) == 5
    for sc in sw_mock:
        assert "scene_number" in sc
        assert "narrative_intent" in sc
        assert sc["narrative_intent"] in NarrativeIntent.__members__
        assert "voiceover" in sc
        assert "caption" in sc
    record_pass("T1.5_SCRIPTWRITER_MOCK", f"Scriptwriter mock returns 5 scenes with valid NarrativeIntent ({[sc['narrative_intent'] for sc in sw_mock]})")
except Exception as e:
    record_fail("T1.5_SCRIPTWRITER_MOCK", f"Scriptwriter mock validation failed: {e}")

# 1.6 QCEditorAgent & BaseAgent generic Mock Fallbacks
try:
    qc_mock = QCEditorAgent()._get_mock_fallback("", "", True)
    assert qc_mock["status"] == "APPROVED"
    assert qc_mock["score"] == 9
    base_mock = BaseAgent()._get_mock_fallback("", "", True)
    assert base_mock["status"] == "ok"
    record_pass("T1.6_QC_BASE_MOCK", "QCEditor and BaseAgent generic mock fallbacks validate")
except Exception as e:
    record_fail("T1.6_QC_BASE_MOCK", f"QCEditor / BaseAgent mock failed: {e}")

# ----------------------------------------------------------------------------
# 2. Macro-Narrative & Mini-Arc Phase Validation Across Models
# ----------------------------------------------------------------------------
print("\n>>> SECTION 2: 11 Macro-Narrative Arc & 5 Mini-Arc Phases Validation <<<")

macro_11_phases = [
    "HOOK", "CENTRAL_QUESTION", "CONTEXT", "FIRST_DISCOVERY",
    "COMPLICATION", "ESCALATION", "REVELATION", "CONSEQUENCE",
    "DEEPER_REVELATION", "FINAL_CONTRADICTION", "PAYOFF"
]

mini_5_phases = ["SETUP", "BUILD", "COMPLICATION", "REVEAL", "CONSEQUENCE"]

# 2.1 NarrativeIntent enum count & members
try:
    for p in macro_11_phases:
        assert p in NarrativeIntent.__members__, f"Missing canonical macro phase: {p}"
        assert NarrativeIntent(p) == p
    # Check legacy intents
    for leg in ["EVIDENCE", "MYSTERY", "EXPLANATION", "CONFLICT", "RESOLUTION", "LOCATION_ESTABLISH"]:
        assert leg in NarrativeIntent.__members__, f"Missing legacy intent: {leg}"
    assert len(NarrativeIntent) == 17
    record_pass("T2.1_NARRATIVE_INTENT_ENUM", f"NarrativeIntent contains all 11 canonical macro phases + 6 legacy intents (Total: {len(NarrativeIntent)})")
except Exception as e:
    record_fail("T2.1_NARRATIVE_INTENT_ENUM", f"NarrativeIntent enum verification failed: {e}")

# 2.2 MiniArcPhase enum count & members
try:
    for mp in mini_5_phases:
        assert mp in MiniArcPhase.__members__, f"Missing canonical mini-arc phase: {mp}"
        assert MiniArcPhase(mp) == mp
    assert len(MiniArcPhase) == 5
    record_pass("T2.2_MINI_ARC_PHASE_ENUM", f"MiniArcPhase contains all 5 canonical dramatic phases (Total: {len(MiniArcPhase)})")
except Exception as e:
    record_fail("T2.2_MINI_ARC_PHASE_ENUM", f"MiniArcPhase enum verification failed: {e}")

# 2.3 StoryBeat narrative_intent validation across all 11 macro phases + 6 legacy + aliases + case variations
beat_base_dict = {
    "beat_id": "b_test",
    "time_context": {"year": "2007", "mode": "historical", "location": "Espoo"},
    "description": "Test Beat",
    "narration_blocks": []
}

try:
    # 11 Canonical Macro phases (Enum and str)
    for p in macro_11_phases:
        b = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": p})
        assert b.narrative_intent == NarrativeIntent[p]
        b_lower = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": p.lower()})
        assert b_lower.narrative_intent == NarrativeIntent[p]
    
    # 6 Legacy phases
    for leg in ["EVIDENCE", "MYSTERY", "EXPLANATION", "CONFLICT", "RESOLUTION", "LOCATION_ESTABLISH"]:
        b = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": leg})
        assert b.narrative_intent == NarrativeIntent[leg]
        b_lower = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": leg.lower()})
        assert b_lower.narrative_intent == NarrativeIntent[leg]
        
    # Aliases
    aliases = {
        "THE_PROBLEM": NarrativeIntent.COMPLICATION,
        "PROBLEM": NarrativeIntent.COMPLICATION,
        "SETUP": NarrativeIntent.CONTEXT,
        "DISCOVERY": NarrativeIntent.FIRST_DISCOVERY,
        "AFTERMATH": NarrativeIntent.CONSEQUENCE,
        "LOCATION": NarrativeIntent.LOCATION_ESTABLISH,
        "BACKGROUND": NarrativeIntent.CONTEXT,
        "INTRODUCTION": NarrativeIntent.HOOK,
        "CLIMAX": NarrativeIntent.REVELATION,
    }
    for alias_str, expected in aliases.items():
        b = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": alias_str})
        assert b.narrative_intent == expected, f"Alias {alias_str} did not map to {expected}"
        b_lower = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": alias_str.lower()})
        assert b_lower.narrative_intent == expected
        
    # None default
    b_none = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": None})
    assert b_none.narrative_intent == NarrativeIntent.EXPLANATION
    
    record_pass("T2.3_STORYBEAT_NARRATIVE_INTENT", "StoryBeat.narrative_intent validates all 11 macro phases, 6 legacy intents, 9 aliases, case-insensitivity, and None default")
except Exception as e:
    record_fail("T2.3_STORYBEAT_NARRATIVE_INTENT", f"StoryBeat narrative_intent validation failed: {e}")

# 2.4 StoryBeat mini_arc_phase validation across all 5 phases + case variations + None
try:
    for mp in mini_5_phases:
        b = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": "HOOK", "mini_arc_phase": mp})
        assert b.mini_arc_phase == MiniArcPhase[mp]
        b_lower = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": "HOOK", "mini_arc_phase": mp.lower()})
        assert b_lower.mini_arc_phase == MiniArcPhase[mp]
    b_none = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": "HOOK", "mini_arc_phase": None})
    assert b_none.mini_arc_phase is None
    b_empty = StoryBeat.model_validate({**beat_base_dict, "narrative_intent": "HOOK", "mini_arc_phase": ""})
    assert b_empty.mini_arc_phase is None
    record_pass("T2.4_STORYBEAT_MINI_ARC_PHASE", "StoryBeat.mini_arc_phase validates all 5 mini-arc phases, case-insensitivity, and None/empty string")
except Exception as e:
    record_fail("T2.4_STORYBEAT_MINI_ARC_PHASE", f"StoryBeat mini_arc_phase validation failed: {e}")

# 2.5 NarrationBlock mini_arc_phase validation across all 5 phases + case variations + None
nblock_base_dict = {
    "block_id": "nb_test",
    "voiceover": "नोकिया एक दिग्गज कंपनी थी।",
    "caption": "Nokia was a giant company.",
    "duration_hint": 4.0,
    "shots": []
}

try:
    for mp in mini_5_phases:
        nb = NarrationBlock.model_validate({**nblock_base_dict, "mini_arc_phase": mp})
        assert nb.mini_arc_phase == MiniArcPhase[mp]
        nb_lower = NarrationBlock.model_validate({**nblock_base_dict, "mini_arc_phase": mp.lower()})
        assert nb_lower.mini_arc_phase == MiniArcPhase[mp]
    nb_none = NarrationBlock.model_validate({**nblock_base_dict, "mini_arc_phase": None})
    assert nb_none.mini_arc_phase is None
    nb_empty = NarrationBlock.model_validate({**nblock_base_dict, "mini_arc_phase": ""})
    assert nb_empty.mini_arc_phase is None
    record_pass("T2.5_NARRATIONBLOCK_MINI_ARC_PHASE", "NarrationBlock.mini_arc_phase validates all 5 mini-arc phases, case-insensitivity, and None/empty string")
except Exception as e:
    record_fail("T2.5_NARRATIONBLOCK_MINI_ARC_PHASE", f"NarrationBlock mini_arc_phase validation failed: {e}")

# 2.6 NarrativePhasePlan model validation across all 11 phases + case variations
try:
    for idx, p in enumerate(macro_11_phases):
        npp = NarrativePhasePlan.model_validate({
            "phase": p,
            "target_beat_index": idx,
            "narrative_goal": f"Goal for {p}",
            "attention_target": 0.8
        })
        assert npp.phase == NarrativeIntent[p]
        npp_lower = NarrativePhasePlan.model_validate({
            "phase": p.lower(),
            "target_beat_index": idx,
            "narrative_goal": f"Goal for {p}",
            "attention_target": 0.8
        })
        assert npp_lower.phase == NarrativeIntent[p]
    record_pass("T2.6_NARRATIVE_PHASE_PLAN", "NarrativePhasePlan validates all 11 canonical macro phases with case normalization")
except Exception as e:
    record_fail("T2.6_NARRATIVE_PHASE_PLAN", f"NarrativePhasePlan validation failed: {e}")

# 2.7 MiniArcPlan model validation
try:
    maplan = MiniArcPlan.model_validate({
        "beat_id": "b001",
        "time_window": "0:00 - 0:45",
        "setup": "Initial status quo",
        "build": "Rising tension",
        "complication": "Fatal flaw discovered",
        "reveal": "Shelved prototype revealed",
        "consequence": "Market collapse initiates"
    })
    assert maplan.beat_id == "b001"
    assert maplan.reveal == "Shelved prototype revealed"
    record_pass("T2.7_MINI_ARC_PLAN", "MiniArcPlan validates full 5-stage mini-arc dramatic structure")
except Exception as e:
    record_fail("T2.7_MINI_ARC_PLAN", f"MiniArcPlan validation failed: {e}")

# 2.8 MajorRevealItem phase validation across macro phases
try:
    for p in ["FIRST_DISCOVERY", "REVELATION", "DEEPER_REVELATION", "FINAL_CONTRADICTION", "PAYOFF"]:
        mri = MajorRevealItem.model_validate({
            "phase": p,
            "revelation": f"Hidden truth in {p}",
            "evidence_backing": "Archival document"
        })
        assert mri.phase == NarrativeIntent[p]
        mri_lower = MajorRevealItem.model_validate({
            "phase": p.lower(),
            "revelation": f"Hidden truth in {p}",
            "evidence_backing": "Archival document"
        })
        assert mri_lower.phase == NarrativeIntent[p]
    record_pass("T2.8_MAJOR_REVEAL_ITEM", "MajorRevealItem normalizes and validates macro-narrative phases")
except Exception as e:
    record_fail("T2.8_MAJOR_REVEAL_ITEM", f"MajorRevealItem phase validation failed: {e}")

# ----------------------------------------------------------------------------
# 3. 20 Visual Jobs & 12 Shot Relationships Validation
# ----------------------------------------------------------------------------
print("\n>>> SECTION 3: 20 Visual Jobs & 12 Shot Relationships Validation <<<")

visual_20_jobs = [
    "ESTABLISH_WORLD", "INTRODUCE_CHARACTER", "INTRODUCE_OBJECT", "FOLLOW_OBJECT",
    "SHOW_EVIDENCE", "EXAMINE_EVIDENCE", "REVEAL_DETAIL", "VISUALIZE_ABSTRACT_CONCEPT",
    "SHOW_SCALE", "SHOW_COMPARISON", "RECONSTRUCT_EVENT", "BUILD_MYSTERY",
    "WITHHOLD_INFORMATION", "ESCALATE", "INTERRUPT", "CONTRAST",
    "HUMANIZE", "CONSEQUENCE", "REVEAL", "PAYOFF"
]

shot_12_relationships = [
    "CONTINUATION", "CONTRAST", "CAUSE_TO_EFFECT", "QUESTION_TO_ANSWER",
    "DETAIL_TO_CONTEXT", "CONTEXT_TO_DETAIL", "BEFORE_TO_AFTER",
    "EXPECTATION_TO_SUBVERSION", "OBJECT_TO_PERSON", "PERSON_TO_CONSEQUENCE",
    "NUMBER_TO_SCALE", "EVIDENCE_TO_REVEAL"
]

# 3.1 VisualJob enum verification
try:
    assert len(VisualJob) == 20
    for vj in visual_20_jobs:
        assert vj in VisualJob.__members__, f"Missing VisualJob: {vj}"
        assert VisualJob(vj) == vj
    record_pass("T3.1_VISUAL_JOB_ENUM", f"VisualJob contains all 20 canonical editorial jobs (Total: {len(VisualJob)})")
except Exception as e:
    record_fail("T3.1_VISUAL_JOB_ENUM", f"VisualJob enum verification failed: {e}")

# 3.2 ShotRelationship enum verification
try:
    assert len(ShotRelationship) == 12
    for sr in shot_12_relationships:
        assert sr in ShotRelationship.__members__, f"Missing ShotRelationship: {sr}"
        assert ShotRelationship(sr) == sr
    record_pass("T3.2_SHOT_RELATIONSHIP_ENUM", f"ShotRelationship contains all 12 canonical relationships (Total: {len(ShotRelationship)})")
except Exception as e:
    record_fail("T3.2_SHOT_RELATIONSHIP_ENUM", f"ShotRelationship enum verification failed: {e}")

# 3.3 Shot model with all 20 visual jobs and 12 shot relationships
shot_base_dict = {
    "shot_id": "s_test",
    "visual_type": "ai_image",
    "fallback_type": "ClassifiedFile",
    "visual_description": "A dramatic visual shot",
    "visual_query": "nokia headquarters 2000s",
    "ai_prompt": "Cinematic shot of nokia headquarters",
    "cut_reason": "establish_scene",
    "continuity": {
        "group_id": "g1",
        "location": "Espoo",
        "environment": "office",
        "time_period": "2000s",
        "lighting": "dramatic"
    }
}

try:
    for vj in visual_20_jobs:
        s = Shot.model_validate({**shot_base_dict, "visual_job": vj})
        assert s.visual_job == VisualJob[vj]
        s_lower = Shot.model_validate({**shot_base_dict, "visual_job": vj.lower()})
        assert s_lower.visual_job == VisualJob[vj]
    
    for sr in shot_12_relationships:
        s = Shot.model_validate({**shot_base_dict, "shot_relationship": sr})
        assert s.shot_relationship == ShotRelationship[sr]
        s_lower = Shot.model_validate({**shot_base_dict, "shot_relationship": sr.lower()})
        assert s_lower.shot_relationship == ShotRelationship[sr]
        
    s_none_sr = Shot.model_validate({**shot_base_dict, "shot_relationship": None})
    assert s_none_sr.shot_relationship is None
    
    s_none_vj = Shot.model_validate({**shot_base_dict, "visual_job": None})
    assert s_none_vj.visual_job == VisualJob.ESTABLISH_WORLD

    record_pass("T3.3_SHOT_JOBS_AND_RELATIONSHIPS", "Shot model validates all 20 VisualJobs and 12 ShotRelationships with case-normalization and defaults")
except Exception as e:
    record_fail("T3.3_SHOT_JOBS_AND_RELATIONSHIPS", f"Shot VisualJob / ShotRelationship validation failed: {e}")

# 3.4 Legacy VisualJob normalization mapping
try:
    for legacy_str, canonical_target in LEGACY_VISUAL_JOB_MAP.items():
        s = Shot.model_validate({**shot_base_dict, "visual_job": legacy_str})
        assert s.visual_job == VisualJob[canonical_target], f"Legacy {legacy_str} did not normalize to {canonical_target}"
        s_lower = Shot.model_validate({**shot_base_dict, "visual_job": legacy_str.lower()})
        assert s_lower.visual_job == VisualJob[canonical_target]
    record_pass("T3.4_LEGACY_VISUAL_JOB_MAP", f"All {len(LEGACY_VISUAL_JOB_MAP)} legacy visual job strings successfully normalize to canonical VisualJob enums")
except Exception as e:
    record_fail("T3.4_LEGACY_VISUAL_JOB_MAP", f"Legacy visual job map failed: {e}")

# ----------------------------------------------------------------------------
# 4. Edge Cases, Missing Optionals & Boundary Values
# ----------------------------------------------------------------------------
print("\n>>> SECTION 4: Edge Cases, Missing Optionals & Boundary Values <<<")

# 4.1 VisualSequencePlan Boundary Values (ge=0.0, le=1.0)
vsp_base = {
    "intention": "Directorial intention",
    "visual_argument": "arg_a vs arg_b",
    "withholding_strategy": "withhold details",
    "memorable_image": "key anchor frame",
    "sequence_ending_statement": "lingering conclusion"
}

try:
    # Exact boundary 0.0 and 1.0
    vsp_min = VisualSequencePlan.model_validate({**vsp_base, "information_change": 0.0, "emotional_change": 0.0, "visual_change": 0.0, "scale_change": 0.0})
    assert vsp_min.information_change == 0.0
    vsp_max = VisualSequencePlan.model_validate({**vsp_base, "information_change": 1.0, "emotional_change": 1.0, "visual_change": 1.0, "scale_change": 1.0})
    assert vsp_max.scale_change == 1.0
    record_pass("T4.1A_VSP_BOUNDARIES_VALID", "VisualSequencePlan accepts exact 0.0 and 1.0 boundaries for all 4 quality change metrics")
except Exception as e:
    record_fail("T4.1A_VSP_BOUNDARIES_VALID", f"VSP valid boundary test failed: {e}")

try:
    # Out of bounds < 0.0
    try:
        VisualSequencePlan.model_validate({**vsp_base, "information_change": -0.1})
        record_fail("T4.1B_VSP_BOUNDARIES_NEGATIVE", "VisualSequencePlan failed to reject information_change < 0.0")
    except ValidationError:
        record_pass("T4.1B_VSP_BOUNDARIES_NEGATIVE", "VisualSequencePlan correctly raised ValidationError for information_change < 0.0")
        
    # Out of bounds > 1.0
    try:
        VisualSequencePlan.model_validate({**vsp_base, "visual_change": 1.05})
        record_fail("T4.1C_VSP_BOUNDARIES_OVERFLOW", "VisualSequencePlan failed to reject visual_change > 1.0")
    except ValidationError:
        record_pass("T4.1C_VSP_BOUNDARIES_OVERFLOW", "VisualSequencePlan correctly raised ValidationError for visual_change > 1.0")
except Exception as e:
    record_fail("T4.1_VSP_BOUNDARIES", f"VSP boundary testing failed: {e}")

# 4.2 NarrativePhasePlan Boundary Values (attention_target ge=0.0, le=1.0)
try:
    npp_0 = NarrativePhasePlan.model_validate({"phase": "HOOK", "narrative_goal": "goal", "attention_target": 0.0})
    npp_1 = NarrativePhasePlan.model_validate({"phase": "HOOK", "narrative_goal": "goal", "attention_target": 1.0})
    assert npp_0.attention_target == 0.0 and npp_1.attention_target == 1.0
    
    try:
        NarrativePhasePlan.model_validate({"phase": "HOOK", "narrative_goal": "goal", "attention_target": -0.01})
        record_fail("T4.2A_NPP_ATTENTION_NEGATIVE", "NarrativePhasePlan failed to reject attention_target < 0.0")
    except ValidationError:
        record_pass("T4.2A_NPP_ATTENTION_NEGATIVE", "NarrativePhasePlan correctly raised ValidationError for attention_target < 0.0")
        
    try:
        NarrativePhasePlan.model_validate({"phase": "HOOK", "narrative_goal": "goal", "attention_target": 1.01})
        record_fail("T4.2B_NPP_ATTENTION_OVERFLOW", "NarrativePhasePlan failed to reject attention_target > 1.0")
    except ValidationError:
        record_pass("T4.2B_NPP_ATTENTION_OVERFLOW", "NarrativePhasePlan correctly raised ValidationError for attention_target > 1.0")
except Exception as e:
    record_fail("T4.2_NPP_BOUNDARIES", f"NarrativePhasePlan boundary test failed: {e}")

# 4.3 HookStrategy normalizer and edge cases
try:
    for ht in ["QUESTION", "CONTRADICTION", "SHOCK", "MYSTERY", "VISUAL_ANOMALY"]:
        hs = HookStrategy.model_validate({
            "hook_type": ht.lower(),
            "anomaly_description": "anomaly",
            "withholding_element": "withhold",
            "opening_visual_cue": "cue"
        })
        assert hs.hook_type == ht
    # Unknown hook type falls back to CONTRADICTION
    hs_invalid = HookStrategy.model_validate({
        "hook_type": "INVALID_HOOK_NAME",
        "anomaly_description": "anomaly",
        "withholding_element": "withhold",
        "opening_visual_cue": "cue"
    })
    assert hs_invalid.hook_type == "CONTRADICTION"
    record_pass("T4.3_HOOK_STRATEGY_NORMALIZER", "HookStrategy normalizes all 5 hook types and recovers invalid strings to CONTRADICTION")
except Exception as e:
    record_fail("T4.3_HOOK_STRATEGY_NORMALIZER", f"HookStrategy normalizer failed: {e}")

# 4.4 Missing Optional Fields Stress-Testing
try:
    # DocumentaryResearchPackage with empty optional list fields
    drp_minimal = DocumentaryResearchPackage.model_validate({
        "topic": "Minimal Topic",
        "central_question": "What is minimal?",
        "documentary_thesis": "Thesis",
        "central_contradiction": "Contradiction",
        "audience_initial_belief": "Belief",
        "what_the_audience_thinks_is_true": "Truth",
        "what_is_actually_more_complicated": "Complication",
        "protagonist_or_human_anchor": "Protagonist",
        "antagonistic_force_or_system": "Antagonist",
        "stakes": "Stakes",
        "historical_context": "Context",
        "final_payoff": "Payoff",
        "ending_image_opportunity": "Image"
    })
    assert drp_minimal.evidence_items == []
    assert drp_minimal.numbers == []
    assert drp_minimal.people == []
    assert drp_minimal.turning_points == []
    assert drp_minimal.major_reveals == []
    record_pass("T4.4A_DRP_EMPTY_LISTS", "DocumentaryResearchPackage instantiates with empty default list factories for all 13 list fields")

    # Shot with all optional fields omitted
    shot_min = Shot.model_validate({
        "shot_id": "s_min",
        "visual_type": "real_photo",
        "fallback_type": "Newspaper",
        "visual_description": "Minimal shot",
        "visual_query": "nokia",
        "ai_prompt": "nokia prompt",
        "cut_reason": "cut",
        "continuity": {
            "group_id": "g1",
            "location": "loc",
            "environment": "env",
            "time_period": "era",
            "lighting": "light"
        }
    })
    assert shot_min.shot_relationship is None
    assert shot_min.visual_job == VisualJob.ESTABLISH_WORLD
    assert shot_min.text_overlay is None
    assert shot_min.highlight is None
    assert shot_min.sound_design is None
    assert shot_min.lut_filter is None
    assert shot_min.editorial_events is None
    record_pass("T4.4B_SHOT_OPTIONALS", "Shot instantiates cleanly with all optional fields omitted (defaults applied)")

    # ScriptManifest with optional vision and research_package omitted
    manifest_min = ScriptManifest.model_validate({
        "project_meta": {
            "topic": "Min topic",
            "visual_bible": {
                "era": "2000s",
                "locations": ["Espoo"],
                "lighting": "dim",
                "color_language": "cool",
                "film_texture": "grain"
            }
        },
        "story_beats": []
    })
    assert manifest_min.documentary_vision is None
    assert manifest_min.research_package is None
    assert manifest_min.schema_version == "2.0"
    record_pass("T4.4C_MANIFEST_OPTIONALS", "ScriptManifest instantiates cleanly when documentary_vision and research_package are omitted")
except Exception as e:
    record_fail("T4.4_MISSING_OPTIONALS", f"Missing optionals stress test failed: {e}")

# ----------------------------------------------------------------------------
# 5. JSON Roundtrip & Deep Nesting Verification
# ----------------------------------------------------------------------------
print("\n>>> SECTION 5: JSON Roundtrip & Deep Nesting Verification <<<")

try:
    dir_agent = DirectorAgent()
    dir_mock = dir_agent._get_mock_fallback("", "", True)
    manifest = ScriptManifest.model_validate(dir_mock)
    json_str = manifest.model_dump_json(indent=2)
    manifest_reloaded = ScriptManifest.model_validate_json(json_str)
    assert manifest == manifest_reloaded
    record_pass("T5.1_MANIFEST_JSON_ROUNDTRIP", "Full ScriptManifest model_dump_json -> model_validate_json roundtrip is 100% losslessly identical")

    event_types = [
        "SFX", "MUSIC_CHANGE", "MUSIC_DUCK", "GRAPHIC", "TEXT_REVEAL", "HIGHLIGHT",
        "COLOR_SHIFT", "OVERLAY", "CUT", "HARD_CUT", "DISSOLVE", "SILENCE", "IMPACT",
        "ZOOM_EMPHASIS", "MAP_REVEAL", "DOCUMENT_REVEAL", "NUMBER_REVEAL",
        "ARCHIVE_INSERT", "REACTION_INSERT"
    ]
    shot_dict = manifest.story_beats[0].narration_blocks[0].shots[0].model_dump()
    events = [{"type": et, "cue": f"cue_{et}", "timing_percent": 50.0, "intensity": 0.8, "duration": 1.0, "reason": f"reason_{et}"} for et in event_types]
    shot_dict["editorial_events"] = events
    shot_with_events = Shot.model_validate(shot_dict)
    assert len(shot_with_events.editorial_events) == 19
    record_pass("T5.2_ALL_19_EDITORIAL_EVENTS", f"All {len(event_types)} EditorialEvent types validate inside Shot model")
except Exception as e:
    record_fail("T5.1_JSON_ROUNDTRIP", f"JSON roundtrip failed: {e}")

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
print("\n======================================================================")
print(f"TEST SUMMARY: PASSED={test_results['passed']}, FAILED={test_results['failed']}, WARNINGS={test_results['warnings']}")
print("======================================================================")

if test_results["failed"] > 0:
    sys.exit(1)
sys.exit(0)
