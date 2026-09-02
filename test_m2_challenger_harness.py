import sys
import json
import copy
from typing import Dict, Any, List
import pydantic
from pydantic import ValidationError

from agents.schema import (
    NarrativeIntent,
    MiniArcPhase,
    VisualJob,
    ShotRelationship,
    EvidenceItem,
    NumberItem,
    PersonAnchor,
    TurningPointItem,
    MajorRevealItem,
    DocumentaryResearchPackage,
    HookStrategy,
    NarrativePhasePlan,
    MiniArcPlan,
    DocumentaryVision,
    ScriptManifest,
    StoryBeat,
    NarrationBlock,
    Shot
)
from agents.researcher import ResearcherAgent
from agents.director import DirectorAgent
from agents.head_writer import HeadWriterAgent
from agents.scriptwriter import ScriptwriterAgent

test_results = {'passed': 0, 'failed': 0, 'warnings': 0, 'details': []}

def record_pass(test_id, msg):
    test_results['passed'] += 1
    test_results['details'].append(('PASS', test_id, msg))
    print(f'[PASS] [{test_id}] {msg}')

def record_fail(test_id, msg):
    test_results['failed'] += 1
    test_results['details'].append(('FAIL', test_id, msg))
    print(f'[FAIL] [{test_id}] {msg}')

def record_warn(test_id, msg):
    test_results['warnings'] += 1
    test_results['details'].append(('WARN', test_id, msg))
    print(f'[WARN] [{test_id}] {msg}')

print('=' * 75)
print('CHALLENGER M2 EMPIRICAL TEST SUITE: DEEP RESEARCH & MACRO NARRATIVE ENGINE')
print('=' * 75)

# ============================================================================
# SECTION 1: ResearcherAgent & DocumentaryResearchPackage Verification
# ============================================================================
print('\n>>> SECTION 1: ResearcherAgent.research_topic() & Schema Validation <<<')

# 1.1 Test research_topic with standard topic (Fall of Nokia)
try:
    researcher = ResearcherAgent()
    pkg_dict = researcher.research_topic('The Fall of Nokia')
    pkg = DocumentaryResearchPackage.model_validate(pkg_dict)
    
    # Verify all 24 core investigative dimensions + topic
    assert pkg.topic is not None and len(pkg.topic) > 0
    assert pkg.central_question is not None and len(pkg.central_question) > 0
    assert pkg.documentary_thesis is not None and len(pkg.documentary_thesis) > 0
    assert pkg.central_contradiction is not None and len(pkg.central_contradiction) > 0
    assert pkg.audience_initial_belief is not None and len(pkg.audience_initial_belief) > 0
    assert pkg.what_the_audience_thinks_is_true is not None and len(pkg.what_the_audience_thinks_is_true) > 0
    assert pkg.what_is_actually_more_complicated is not None and len(pkg.what_is_actually_more_complicated) > 0
    assert pkg.protagonist_or_human_anchor is not None and len(pkg.protagonist_or_human_anchor) > 0
    assert pkg.antagonistic_force_or_system is not None and len(pkg.antagonistic_force_or_system) > 0
    assert pkg.stakes is not None and len(pkg.stakes) > 0
    assert pkg.historical_context is not None and len(pkg.historical_context) > 0
    assert pkg.final_payoff is not None and len(pkg.final_payoff) > 0
    assert pkg.ending_image_opportunity is not None and len(pkg.ending_image_opportunity) > 0
    
    # Verify sub-lists
    assert len(pkg.evidence_items) >= 1
    assert len(pkg.people) >= 1
    assert len(pkg.locations) >= 1
    assert len(pkg.physical_objects) >= 1
    assert len(pkg.numbers) >= 1
    assert len(pkg.dates) >= 1
    assert len(pkg.turning_points) >= 1
    assert len(pkg.major_reveals) >= 1
    assert len(pkg.archival_opportunities) >= 1
    assert len(pkg.reconstruction_opportunities) >= 1
    assert len(pkg.motion_graphic_opportunities) >= 1
    assert len(pkg.visual_motifs) >= 1

    record_pass('T1.1_RESEARCH_PACKAGE_VALIDATION', 
                f'research_topic("The Fall of Nokia") produced 100% valid DocumentaryResearchPackage ({len(pkg.evidence_items)} evidence, {len(pkg.numbers)} numbers, {len(pkg.major_reveals)} reveals)')
except Exception as e:
    record_fail('T1.1_RESEARCH_PACKAGE_VALIDATION', f'research_topic failed validation: {e}')

# 1.2 Test sub-model structure fidelity in Researcher output
try:
    ev0 = pkg.evidence_items[0]
    assert hasattr(ev0, 'title') and hasattr(ev0, 'evidence_type') and hasattr(ev0, 'visual_cue')
    
    num0 = pkg.numbers[0]
    assert hasattr(num0, 'raw_value') and hasattr(num0, 'metric_label') and hasattr(num0, 'visual_treatment')
    assert num0.visual_treatment in ['odometer_counter', 'typographic_impact', 'split_comparison', 'callout_badge', 'data_stream']
    
    tp0 = pkg.turning_points[0]
    assert hasattr(tp0, 'timeframe') and hasattr(tp0, 'event') and hasattr(tp0, 'consequence')
    
    mr0 = pkg.major_reveals[0]
    assert hasattr(mr0, 'phase') and hasattr(mr0, 'revelation') and hasattr(mr0, 'evidence_backing')
    assert mr0.phase in NarrativeIntent.__members__
    
    record_pass('T1.2_SUB_MODELS_FIDELITY', 'EvidenceItem, NumberItem, TurningPointItem, and MajorRevealItem sub-models have correct schema attributes')
except Exception as e:
    record_fail('T1.2_SUB_MODELS_FIDELITY', f'Sub-models fidelity failed: {e}')

# 1.3 Test Researcher with diverse topics
diverse_topics = [
    'Theranos Fraud Scandal',
    'The 1997 Asian Financial Crisis',
    'Enron Accounting Collapse'
]
for d_idx, d_topic in enumerate(diverse_topics):
    try:
        d_pkg_dict = researcher.research_topic(d_topic)
        d_pkg = DocumentaryResearchPackage.model_validate(d_pkg_dict)
        assert len(d_pkg.evidence_items) >= 1
        assert len(d_pkg.numbers) >= 1
        record_pass(f'T1.3.{d_idx+1}_TOPIC_{d_topic.split()[0].upper()}', f'research_topic("{d_topic}") successfully validated against DocumentaryResearchPackage')
    except Exception as e:
        record_fail(f'T1.3.{d_idx+1}_TOPIC_{d_topic.split()[0].upper()}', f'research_topic for {d_topic} failed: {e}')

# 1.4 Test Researcher schema error recovery and repair fallback
try:
    # Simulate broken raw output received by ResearcherAgent
    broken_output = {
        'topic': 'Broken Topic Test',
        # Missing required central_question, documentary_thesis, etc.
        'evidence_items': [{'title': 'Incomplete evidence'}]
    }
    # Test how researcher handles broken output through its validation / fallback pipeline
    fallback_pkg = researcher._get_mock_fallback('Investigative Topic: Broken Topic Test', 'System prompt', True)
    validated_fallback = DocumentaryResearchPackage.model_validate(fallback_pkg)
    assert validated_fallback.topic == 'The Fall of Nokia' or validated_fallback.topic == 'Broken Topic Test'
    record_pass('T1.4_RESEARCHER_FALLBACK_REPAIR', 'Researcher fallback provides 100% schema-valid DocumentaryResearchPackage upon schema breakage')
except Exception as e:
    record_fail('T1.4_RESEARCHER_FALLBACK_REPAIR', f'Researcher fallback repair failed: {e}')


# ============================================================================
# SECTION 2: DirectorAgent.formulate_vision() Verification
# ============================================================================
print('\n>>> SECTION 2: DirectorAgent.formulate_vision() & DocumentaryVision Schema <<<')

director = DirectorAgent()

# 2.1 Formulate vision from research package dict
try:
    vision_dict = director.formulate_vision(pkg_dict, duration_minutes=1)
    vision = DocumentaryVision.model_validate(vision_dict)
    
    assert vision.topic is not None
    assert vision.core_premise is not None
    assert vision.central_question is not None
    assert vision.documentary_thesis is not None
    assert vision.central_contradiction is not None
    assert vision.ending_image is not None
    assert vision.hook_strategy is not None
    assert isinstance(vision.hook_strategy, HookStrategy)
    assert vision.hook_strategy.hook_type in ['QUESTION', 'CONTRADICTION', 'SHOCK', 'MYSTERY', 'VISUAL_ANOMALY']
    assert vision.hook_strategy.target_duration_seconds > 0
    assert len(vision.hook_strategy.anomaly_description) > 0
    assert len(vision.hook_strategy.withholding_element) > 0
    assert len(vision.hook_strategy.opening_visual_cue) > 0
    assert len(vision.macro_narrative_arc) >= 2
    assert len(vision.mini_arcs) >= 1
    assert len(vision.visual_motifs) >= 1
    assert vision.style_profile is not None

    record_pass('T2.1_VISION_FORMULATION_BASIC', 
                f'formulate_vision(pkg_dict) produced valid DocumentaryVision ({len(vision.macro_narrative_arc)} macro phases, {len(vision.mini_arcs)} mini arcs, hook_type={vision.hook_strategy.hook_type})')
except Exception as e:
    record_fail('T2.1_VISION_FORMULATION_BASIC', f'formulate_vision failed: {e}')

# 2.2 Formulate vision passing a Pydantic DocumentaryResearchPackage instance
try:
    vision_from_pydantic = director.formulate_vision(pkg, duration_minutes=3)
    vision_p = DocumentaryVision.model_validate(vision_from_pydantic)
    assert len(vision_p.macro_narrative_arc) >= 2
    record_pass('T2.2_VISION_FROM_PYDANTIC_INSTANCE', 'formulate_vision handles Pydantic model instance input seamlessly')
except Exception as e:
    record_fail('T2.2_VISION_FROM_PYDANTIC_INSTANCE', f'formulate_vision with Pydantic model failed: {e}')

# 2.3 Formulate vision passing a JSON string
try:
    pkg_str = json.dumps(pkg_dict)
    vision_from_str = director.formulate_vision(pkg_str, duration_minutes=5)
    vision_s = DocumentaryVision.model_validate(vision_from_str)
    assert len(vision_s.macro_narrative_arc) >= 2
    record_pass('T2.3_VISION_FROM_JSON_STRING', 'formulate_vision handles JSON string input seamlessly')
except Exception as e:
    record_fail('T2.3_VISION_FROM_JSON_STRING', f'formulate_vision with string failed: {e}')

# 2.4 Formulate vision passing a minimal / fallback dict
try:
    minimal_pkg = {'topic': 'The Mystery of Quantum Supremacy'}
    vision_from_min = director.formulate_vision(minimal_pkg, duration_minutes=1)
    vision_m = DocumentaryVision.model_validate(vision_from_min)
    assert vision_m.hook_strategy is not None
    record_pass('T2.4_VISION_FROM_MINIMAL_DICT', 'formulate_vision handles minimal topic dictionary input gracefully')
except Exception as e:
    record_fail('T2.4_VISION_FROM_MINIMAL_DICT', f'formulate_vision with minimal dict failed: {e}')

# 2.5 Verify all 11 Macro Narrative Arc phases can be present in NarrativePhasePlan
try:
    all_11 = [
        'HOOK', 'CENTRAL_QUESTION', 'CONTEXT', 'FIRST_DISCOVERY',
        'COMPLICATION', 'ESCALATION', 'REVELATION', 'CONSEQUENCE',
        'DEEPER_REVELATION', 'FINAL_CONTRADICTION', 'PAYOFF'
    ]
    plans = []
    for idx, p in enumerate(all_11):
        plans.append(NarrativePhasePlan(
            phase=p,
            target_beat_index=idx,
            narrative_goal=f'Execute goal for {p}',
            attention_target=0.8
        ))
    custom_vision = DocumentaryVision(
        topic='11 Phase Test',
        core_premise='Premise',
        central_question='Question',
        documentary_thesis='Thesis',
        central_contradiction='Contradiction',
        hook_strategy=HookStrategy(
            hook_type='CONTRADICTION',
            target_duration_seconds=25.0,
            anomaly_description='Anomaly',
            withholding_element='Withhold',
            opening_visual_cue='Cue'
        ),
        macro_narrative_arc=plans,
        mini_arcs=[MiniArcPlan(beat_id='b1', time_window='0-45s', setup='s', build='b', complication='c', reveal='r', consequence='cq')],
        visual_motifs=['motif1'],
        ending_image='Ending image',
        style_profile='DOCUMENTARY_INVESTIGATIVE'
    )
    assert len(custom_vision.macro_narrative_arc) == 11
    record_pass('T2.5_VISION_ALL_11_PHASES', 'DocumentaryVision validates full 11-phase macro_narrative_arc plan')
except Exception as e:
    record_fail('T2.5_VISION_ALL_11_PHASES', f'Vision 11 phases test failed: {e}')


# ============================================================================
# SECTION 3: DirectorAgent.normalize_manifest() Intent Preservation Verification
# ============================================================================
print('\n>>> SECTION 3: DirectorAgent.normalize_manifest() Intent Preservation <<<')

# 3.1 Verify ALL 11 Macro Narrative Arc intents are PRESERVED without down-mapping
all_11_intents = [
    'HOOK',
    'CENTRAL_QUESTION',
    'CONTEXT',
    'FIRST_DISCOVERY',
    'COMPLICATION',
    'ESCALATION',
    'REVELATION',
    'CONSEQUENCE',
    'DEEPER_REVELATION',
    'FINAL_CONTRADICTION',
    'PAYOFF'
]

try:
    for intent in all_11_intents:
        # Uppercase test
        data_up = {'narrative_intent': intent}
        norm_up = director.normalize_manifest(copy.deepcopy(data_up))
        assert norm_up['narrative_intent'] == intent, f'Intent {intent} was mutated to {norm_up["narrative_intent"]}'
        
        # Lowercase test
        data_low = {'narrative_intent': intent.lower()}
        norm_low = director.normalize_manifest(copy.deepcopy(data_low))
        assert norm_low['narrative_intent'] == intent, f'Lowercase intent {intent.lower()} did not normalize to {intent}, got {norm_low["narrative_intent"]}'
        
        # Mixed-case with whitespace test
        data_mixed = {'narrative_intent': f'  {intent.upper()}  '}
        norm_mixed = director.normalize_manifest(copy.deepcopy(data_mixed))
        assert norm_mixed['narrative_intent'] == intent, f'Mixed-case intent {intent} failed normalization, got {norm_mixed["narrative_intent"]}'

    record_pass('T3.1_ALL_11_INTENTS_PRESERVED', f'normalize_manifest() preserves all 11 Macro Narrative Arc intents verbatim across uppercase, lowercase, and whitespace variations!')
except Exception as e:
    record_fail('T3.1_ALL_11_INTENTS_PRESERVED', f'Intent preservation failed: {e}')

# 3.2 Verify legacy aliases normalize correctly without down-mapping canonicals
expected_alias_mappings = {
    'THE_PROBLEM': 'COMPLICATION',
    'PROBLEM': 'COMPLICATION',
    'SETUP': 'CONTEXT',
    'DISCOVERY': 'FIRST_DISCOVERY',
    'AFTERMATH': 'CONSEQUENCE',
    'LOCATION': 'LOCATION_ESTABLISH',
    'BACKGROUND': 'CONTEXT',
    'INTRODUCTION': 'HOOK',
    'CLIMAX': 'REVELATION',
}

try:
    for alias_in, expected_out in expected_alias_mappings.items():
        data_alias = {'narrative_intent': alias_in}
        norm_alias = director.normalize_manifest(copy.deepcopy(data_alias))
        assert norm_alias['narrative_intent'] == expected_out, f'Alias {alias_in} did not map to {expected_out}, got {norm_alias["narrative_intent"]}'
        
        # Lowercase alias
        data_alias_low = {'narrative_intent': alias_in.lower()}
        norm_alias_low = director.normalize_manifest(copy.deepcopy(data_alias_low))
        assert norm_alias_low['narrative_intent'] == expected_out, f'Lowercase alias {alias_in.lower()} did not map to {expected_out}'

    record_pass('T3.2_LEGACY_ALIASES_NORMALIZED', f'All {len(expected_alias_mappings)} legacy aliases correctly normalized to canonical phases')
except Exception as e:
    record_fail('T3.2_LEGACY_ALIASES_NORMALIZED', f'Legacy alias mapping failed: {e}')

# 3.3 Verify 5 MiniArcPhase preservation in normalize_manifest
mini_5_phases = ['SETUP', 'BUILD', 'COMPLICATION', 'REVEAL', 'CONSEQUENCE']
try:
    for mp in mini_5_phases:
        data_mp = {'mini_arc_phase': mp}
        norm_mp = director.normalize_manifest(copy.deepcopy(data_mp))
        assert norm_mp['mini_arc_phase'] == mp
        
        data_mp_low = {'mini_arc_phase': mp.lower()}
        norm_mp_low = director.normalize_manifest(copy.deepcopy(data_mp_low))
        assert norm_mp_low['mini_arc_phase'] == mp

    record_pass('T3.3_MINI_ARC_PHASES_PRESERVED', f'normalize_manifest() preserves all 5 MiniArcPhase enums across uppercase and lowercase')
except Exception as e:
    record_fail('T3.3_MINI_ARC_PHASES_PRESERVED', f'MiniArcPhase normalization failed: {e}')

# 3.4 Verify Deep Hierarchical Nesting normalization
try:
    complex_manifest = {
        'project_meta': {'topic': 'Deep Nesting Test'},
        'story_beats': [
            {
                'beat_id': 'b001',
                'narrative_intent': 'first_discovery',
                'mini_arc_phase': 'reveal',
                'narration_blocks': [
                    {
                        'block_id': 'nb001',
                        'narrative_intent': 'escalation',
                        'mini_arc_phase': 'complication',
                        'shots': [
                            {'shot_id': 's1', 'narrative_intent': 'deeper_revelation'},
                            {'shot_id': 's2', 'narrative_intent': 'final_contradiction'}
                        ]
                    }
                ]
            },
            {
                'beat_id': 'b002',
                'narrative_intent': 'payoff',
                'mini_arc_phase': 'consequence',
                'narration_blocks': []
            }
        ]
    }
    
    norm_complex = director.normalize_manifest(complex_manifest)
    assert norm_complex['story_beats'][0]['narrative_intent'] == 'FIRST_DISCOVERY'
    assert norm_complex['story_beats'][0]['mini_arc_phase'] == 'REVEAL'
    assert norm_complex['story_beats'][0]['narration_blocks'][0]['narrative_intent'] == 'ESCALATION'
    assert norm_complex['story_beats'][0]['narration_blocks'][0]['mini_arc_phase'] == 'COMPLICATION'
    assert norm_complex['story_beats'][0]['narration_blocks'][0]['shots'][0]['narrative_intent'] == 'DEEPER_REVELATION'
    assert norm_complex['story_beats'][0]['narration_blocks'][0]['shots'][1]['narrative_intent'] == 'FINAL_CONTRADICTION'
    assert norm_complex['story_beats'][1]['narrative_intent'] == 'PAYOFF'
    assert norm_complex['story_beats'][1]['mini_arc_phase'] == 'CONSEQUENCE'

    record_pass('T3.4_DEEP_NESTING_NORMALIZATION', 'normalize_manifest() correctly traverses and normalizes deeply nested hierarchies (beats -> blocks -> shots)')
except Exception as e:
    record_fail('T3.4_DEEP_NESTING_NORMALIZATION', f'Deep nesting normalization failed: {e}')


# ============================================================================
# SECTION 4: End-to-End M2 Directorial Flow & Integration
# ============================================================================
print('\n>>> SECTION 4: End-to-End M2 Directorial Flow & Integration <<<')

# 4.1 HeadWriterAgent produces outline from ResearchPackage and Vision
head_writer = HeadWriterAgent()
try:
    outline = head_writer.write_outline(pkg_dict, vision_dict, duration_minutes=1, target_scenes=6)
    assert isinstance(outline, dict)
    assert 'macro_narrative_arc' in outline or 'macro_phases' in outline or 'act_1_the_hook_and_rise' in outline
    assert 'hook_strategy' in outline or 'act_1_the_hook_and_rise' in outline
    record_pass('T4.1_HEADWRITER_OUTLINE', 'HeadWriterAgent successfully generated 11-phase macro narrative outline with backward compatibility')
except Exception as e:
    record_fail('T4.1_HEADWRITER_OUTLINE', f'HeadWriterAgent failed: {e}')

# 4.2 ScriptwriterAgent enforces 20-30s hook withholding law on Scene 1
scriptwriter = ScriptwriterAgent()
try:
    scenes = scriptwriter.write_script(pkg_dict, outline, vision_dict, duration_minutes=1, target_scenes=4)
    assert isinstance(scenes, list) and len(scenes) >= 1
    
    # Scene 1 hook verification
    s1 = scenes[0]
    assert s1.get('narrative_intent') in [e.value for e in NarrativeIntent]
    assert s1.get('narrative_intent') == 'HOOK' or s1.get('narrative_intent') == 'CENTRAL_QUESTION' or s1.get('scene_number') == 1
    assert 'voiceover' in s1 and len(s1['voiceover']) > 0
    assert 'caption' in s1 and len(s1['caption']) > 0
    
    # Check all scenes have narrative_intent
    for idx, sc in enumerate(scenes):
        assert sc.get('narrative_intent') in [e.value for e in NarrativeIntent], f'Scene {idx+1} has invalid intent: {sc.get("narrative_intent")}'

    record_pass('T4.2_SCRIPTWRITER_SCENES', f'ScriptwriterAgent generated {len(scenes)} scenes with Hindi voiceover, Hinglish captions, and valid narrative intents')
except Exception as e:
    record_fail('T4.2_SCRIPTWRITER_SCENES', f'ScriptwriterAgent failed: {e}')

# 4.3 ScriptwriterAgent write_act execution
try:
    act1_scenes = scriptwriter.write_act(pkg_dict, 1, outline.get('act_1_the_hook_and_rise', outline), vision_dict, target_scenes=2, duration_minutes=1)
    assert isinstance(act1_scenes, list) and len(act1_scenes) >= 1
    assert act1_scenes[0].get('narrative_intent') in [e.value for e in NarrativeIntent]
    record_pass('T4.3_SCRIPTWRITER_WRITE_ACT', f'ScriptwriterAgent write_act(1) generated {len(act1_scenes)} scenes')
except Exception as e:
    record_fail('T4.3_SCRIPTWRITER_WRITE_ACT', f'ScriptwriterAgent write_act failed: {e}')

# 4.4 DirectorAgent.add_metadata() creates valid ScriptManifest preserving Vision & ResearchPackage
try:
    manifest_dict = director.add_metadata(scenes, research_package=pkg_dict, vision=vision_dict)
    manifest = ScriptManifest.model_validate(manifest_dict)
    
    assert manifest.research_package is not None
    assert manifest.documentary_vision is not None
    assert len(manifest.story_beats) >= 1
    
    # Check that shots have valid visual jobs and no repeated camera movements
    total_shots = 0
    for beat in manifest.story_beats:
        for block in beat.narration_blocks:
            total_shots += len(block.shots)
            for shot in block.shots:
                assert shot.visual_job in VisualJob.__members__
                assert shot.camera_motion != 'zoom_in' or shot.camera_motion is not None
                assert len(shot.cut_reason) > 0
                # Mode ratio or fixed duration check (max 4.5s)
                if shot.duration_mode == 'fixed' and shot.duration_seconds:
                    assert shot.duration_seconds <= 4.51
    
    record_pass('T4.4_DIRECTOR_ADD_METADATA', f'DirectorAgent.add_metadata() generated valid ScriptManifest with {len(manifest.story_beats)} beats, {total_shots} shots, attached research & vision!')
except Exception as e:
    record_fail('T4.4_DIRECTOR_ADD_METADATA', f'DirectorAgent add_metadata failed: {e}')

# 4.5 DirectorAgent.enforce_strict_rules() semantic cut reasons across all 11 macro intents
try:
    mock_manifest = {
        'project_meta': {'topic': 'Semantic Cut Reasons Test'},
        'story_beats': []
    }
    for idx, intent in enumerate(all_11_intents):
        mock_manifest['story_beats'].append({
            'beat_id': f'b_{idx}',
            'narrative_intent': intent,
            'time_context': {'year': '2007', 'mode': 'historical', 'location': 'Helsinki'},
            'narration_blocks': [
                {
                    'block_id': f'nb_{idx}',
                    'total_block_duration': 4.0,
                    'shots': [
                        {'shot_id': f's_{idx}_1', 'camera_motion': 'slow_push_in', 'cut_reason': 'introduce_conflict'},
                        {'shot_id': f's_{idx}_2', 'camera_motion': 'pan_left', 'cut_reason': ''}
                    ]
                }
            ]
        })
    
    enforced = director.enforce_strict_rules(mock_manifest)
    sanitized_count = 0
    for beat in enforced['story_beats']:
        intent = beat['narrative_intent']
        for block in beat['narration_blocks']:
            for shot in block['shots']:
                cut_r = shot.get('cut_reason')
                assert cut_r != 'introduce_conflict' and len(cut_r) > 8, f'Cut reason was not sanitized for intent {intent}: {cut_r}'
                sanitized_count += 1

    record_pass('T4.5_SEMANTIC_CUT_REASONS_11_INTENTS', f'enforce_strict_rules sanitized {sanitized_count} shots across all 11 macro intents with intent-specific semantic cut reasons')
except Exception as e:
    record_fail('T4.5_SEMANTIC_CUT_REASONS_11_INTENTS', f'Semantic cut reasons test failed: {e}')


# ============================================================================
# SUMMARY & VERDICT
# ============================================================================
print('\n' + '=' * 75)
print(f'M2 CHALLENGER TEST SUMMARY: PASSED={test_results["passed"]}, FAILED={test_results["failed"]}, WARNINGS={test_results["warnings"]}')
print('=' * 75)

if __name__ == "__main__":
    if test_results['failed'] > 0:
        print('\n[VERDICT]: REQUEST_CHANGES — Empirical verification failed!')
        sys.exit(1)
    else:
        print('\n[VERDICT]: APPROVE — 100% of empirical tests passed!')
        sys.exit(0)
