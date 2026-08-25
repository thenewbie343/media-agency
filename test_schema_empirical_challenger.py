import json
import pytest
from pydantic import ValidationError

from agents.schema import (
    NarrativeIntent,
    MiniArcPhase,
    VisualJob,
    ShotRelationship,
    LEGACY_VISUAL_JOB_MAP,
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
    VisualSequencePlan,
    VisualBible,
    ProjectMeta,
    HighlightMetadata,
    ContinuityMetadata,
    AssetMetadata,
    EditorialEvent,
    Shot,
    StrategicSilence,
    AudioMetadata,
    NarrationBlock,
    TimeContext,
    StoryBeat,
    ScriptManifest,
)
from agents.researcher import ResearcherAgent
from agents.head_writer import HeadWriterAgent
from agents.scriptwriter import ScriptwriterAgent
from agents.director import DirectorAgent


# ============================================================================
# Helpers & Fixtures
# ============================================================================

def make_sample_shot(shot_id="s001", visual_job=VisualJob.ESTABLISH_WORLD, shot_relationship=None):
    return Shot(
        shot_id=shot_id,
        duration_mode="ratio",
        duration_ratio=1.0,
        shot_role="EXPLANATION",
        asset_provenance="ARCHIVAL_FOOTAGE",
        shot_size="medium",
        visual_job=visual_job,
        shot_relationship=shot_relationship,
        visual_type="real_photo",
        fallback_type="ArchivalDocument",
        visual_description="A grainy archival document showing internal meeting memos.",
        visual_query="ARCHIVAL MEMO + TABLE + 1999 + BOARDROOM",
        ai_prompt="Cinematic documentary still of a leaked 1999 corporate memo on dark wooden table",
        cut_reason="reveal_internal_contradiction",
        continuity=ContinuityMetadata(
            group_id="grp_001",
            characters=["John Doe"],
            location="Headquarters",
            environment="Dim boardroom",
            time_period="1999",
            lighting="Moody tungsten low-key"
        )
    )

def make_sample_research_package():
    return DocumentaryResearchPackage(
        topic="The Fall of Barings Bank",
        central_question="How did a 233-year-old bank collapse from a single rogue trader in Singapore?",
        documentary_thesis="Systemic institutional blindness enabled an isolated rogue trader to wager the entire bank's reserves.",
        central_contradiction="Barings celebrated Nick Leeson as an unprecedented profit generator while he hid massive compounding losses.",
        audience_initial_belief="The collapse was caused by an unpredictable market crash.",
        what_the_audience_thinks_is_true="Nick Leeson was a mastermind market manipulator.",
        what_is_actually_more_complicated="Lack of segregation between trading and settlement allowed simple error accounts (88888) to hide losses.",
        protagonist_or_human_anchor="Nick Leeson and Peter Baring",
        antagonistic_force_or_system="The 88888 error account and complacent London management",
        stakes="Complete insolvency of Britain's oldest merchant bank and 200+ years of royal banking history erased",
        historical_context="1995 Asian financial markets, SIMEX derivatives boom, pre-electronic automated compliance checks",
        turning_points=[
            TurningPointItem(timeframe="July 1992", event="Creation of Account 88888", consequence="Unsupervised losses began accumulating off-balance-sheet."),
            TurningPointItem(timeframe="January 1995", event="Kobe Earthquake", consequence="Nikkei plummeted, destroying unhedged long positions.")
        ],
        major_reveals=[
            MajorRevealItem(phase="FIRST_DISCOVERY", revelation="Account 88888 was initially created to cover a subordinate's 20,000 pound mistake.", evidence_backing="Internal SIMEX trade error log"),
            MajorRevealItem(phase="REVELATION", revelation="London headquarters transferred over 800 million pounds without verifying collateral.", evidence_backing="Bank of England inquiry report")
        ],
        final_payoff="A single unchecked trader destroyed an empire, forcing global banking to separate trading and clearing forever.",
        evidence_items=[
            EvidenceItem(
                title="SIMEX Account 88888 Statement",
                evidence_type="ledger",
                description="The hidden error account ledger showing accumulated losses of 827 million pounds.",
                source_reference="Bank of England Report 1995",
                visual_cue="Close-up of dot-matrix printed ledger highlighted in stark white on black background."
            )
        ],
        people=[
            PersonAnchor(name="Nick Leeson", role="Rogue Trader", significance="Executed unauthorized arbitrage trades that bankrupted the firm.", visual_description="Young 28-year-old trader in colorful SIMEX trading jacket.")
        ],
        locations=["SIMEX Floor, Singapore", "8 Bishopsgate, London", "Frankfurt Airport"],
        physical_objects=["Brightly colored trading jacket", "Dot matrix terminal", "Fax machine confirmation slip"],
        numbers=[
            NumberItem(raw_value="£827,000,000", metric_label="Total Hidden Losses", visual_treatment="typographic_impact", editorial_context="Exceeded the bank's entire capitalization of £350 million."),
            NumberItem(raw_value="£1", metric_label="Sale Price of Barings to ING", visual_treatment="callout_badge", editorial_context="The symbolic acquisition price after collapse.")
        ],
        dates=["July 1992", "January 17, 1995", "February 23, 1995", "February 26, 1995"],
        archival_opportunities=["SIMEX open outcry pit trading footage", "London press conference announcements"],
        reconstruction_opportunities=["Leeson alone in Singapore trading room at night staring at green CRT monitor"],
        motion_graphic_opportunities=["Nikkei index drop vs doubling down leverage curve", "Money flow diagram London to Singapore"],
        visual_motifs=["Green phosphorescent CRT text", "Dot-matrix paper curling into wastebaskets", "Trading clock ticking"],
        ending_image_opportunity="Empty, darkened trading floor of 8 Bishopsgate with single abandoned Barings jacket on an office chair."
    )

def make_sample_vision():
    return DocumentaryVision(
        topic="The Fall of Barings Bank",
        core_premise="The anatomy of systemic institutional blindness.",
        central_question="How did a 233-year-old bank collapse from a single rogue trader in Singapore?",
        documentary_thesis="Systemic institutional blindness enabled an isolated rogue trader to wager the entire bank's reserves.",
        central_contradiction="Barings celebrated Nick Leeson as an unprecedented profit generator while he hid massive compounding losses.",
        hook_strategy=HookStrategy(
            hook_type="CONTRADICTION",
            target_duration_seconds=25.0,
            anomaly_description="In February 1995, Britain's Queen Elizabeth had her personal bank sold for exactly one pound.",
            withholding_element="The identity of Nick Leeson and the nature of derivatives trading are withheld.",
            opening_visual_cue="Extreme close-up of a crisp British one pound coin falling onto an antique polished mahagony boardroom table in slow motion."
        ),
        macro_narrative_arc=[
            NarrativePhasePlan(phase=NarrativeIntent.HOOK, target_beat_index=0, narrative_goal="Establish the £1 sale anomaly", attention_target=0.9),
            NarrativePhasePlan(phase=NarrativeIntent.CENTRAL_QUESTION, target_beat_index=1, narrative_goal="Frame the mystery of the 233-year bank", attention_target=0.8),
            NarrativePhasePlan(phase=NarrativeIntent.CONTEXT, target_beat_index=2, narrative_goal="Establish 1995 Singapore trading floor", attention_target=0.7),
            NarrativePhasePlan(phase=NarrativeIntent.FIRST_DISCOVERY, target_beat_index=3, narrative_goal="Introduce Account 88888", attention_target=0.75),
            NarrativePhasePlan(phase=NarrativeIntent.COMPLICATION, target_beat_index=4, narrative_goal="Kobe earthquake crashes Nikkei", attention_target=0.85),
            NarrativePhasePlan(phase=NarrativeIntent.ESCALATION, target_beat_index=5, narrative_goal="Doubling down and fake faxes", attention_target=0.88),
            NarrativePhasePlan(phase=NarrativeIntent.REVELATION, target_beat_index=6, narrative_goal="£827M hole discovered by auditors", attention_target=0.95),
            NarrativePhasePlan(phase=NarrativeIntent.CONSEQUENCE, target_beat_index=7, narrative_goal="Flight from Singapore and arrest in Frankfurt", attention_target=0.8),
            NarrativePhasePlan(phase=NarrativeIntent.DEEPER_REVELATION, target_beat_index=8, narrative_goal="London management signed off on all margin calls", attention_target=0.9),
            NarrativePhasePlan(phase=NarrativeIntent.FINAL_CONTRADICTION, target_beat_index=9, narrative_goal="The bank died not of greed alone, but administrative laziness", attention_target=0.85),
            NarrativePhasePlan(phase=NarrativeIntent.PAYOFF, target_beat_index=10, narrative_goal="The £1 sale and birth of modern financial compliance", attention_target=0.9)
        ],
        mini_arcs=[
            MiniArcPlan(
                beat_id="beat_001",
                time_window="0:00 - 0:45",
                setup="A 200-year-old institution of kings and queens.",
                build="Trading volumes explode in the Far East.",
                complication="A mysterious off-balance-sheet ledger appears.",
                reveal="The ledger is bleeding millions daily.",
                consequence="London sends more cash instead of auditing."
            )
        ],
        visual_motifs=["Green phosphorescent CRT text", "Dot-matrix paper", "Trading floor clock"],
        ending_image="Empty, darkened trading floor of 8 Bishopsgate with single abandoned Barings jacket."
    )

def make_sample_manifest():
    research_pkg = make_sample_research_package()
    vision = make_sample_vision()
    seq_plan = VisualSequencePlan(
        intention="Contrast royal heritage with chaotic derivatives speculation",
        visual_argument="200_year_stability vs 5_minute_derivatives_destruction",
        withholding_strategy="Hold back Leeson's face; show only manic hand movements and terminal flickers",
        memorable_image="A £1 coin spinning in silence on a 200-year-old mahogany table",
        sequence_ending_statement="The institution was already dead; only the ticker hadn't caught up.",
        information_change=0.8,
        emotional_change=0.75,
        visual_change=0.9,
        scale_change=0.6
    )
    shot1 = make_sample_shot("s001", VisualJob.ESTABLISH_WORLD, None)
    shot2 = make_sample_shot("s002", VisualJob.SHOW_EVIDENCE, ShotRelationship.CONTEXT_TO_DETAIL)
    
    narration_block = NarrationBlock(
        block_id="n001",
        voiceover="Barings Bank had financed the Napoleonic Wars. But in 1995, one man erased it all.",
        caption="Barings Bank had financed the Napoleonic Wars. But in 1995, one man erased it all.",
        duration_hint=8.5,
        mini_arc_phase=MiniArcPhase.SETUP,
        shots=[shot1, shot2]
    )
    
    beat = StoryBeat(
        beat_id="beat_001",
        time_context=TimeContext(year="1995", mode="historical", location="London & Singapore"),
        narrative_intent=NarrativeIntent.HOOK,
        mini_arc_phase=MiniArcPhase.SETUP,
        visual_sequence_plan=seq_plan,
        description="Opening hook establishing the collapse of Barings Bank",
        attention_intensity=0.9,
        chapter_color_language="cinematic_bleak",
        narration_blocks=[narration_block]
    )
    
    return ScriptManifest(
        schema_version="2.0",
        project_meta=ProjectMeta(
            topic="The Fall of Barings Bank",
            genre="documentary",
            style_profile="DOCUMENTARY_INVESTIGATIVE",
            language="hindi",
            visual_bible=VisualBible(
                era="1995",
                locations=["London", "Singapore"],
                lighting="low-key, cold, cinematic",
                color_language="teal_orange, bleak",
                film_texture="subtle grain, 35mm"
            )
        ),
        documentary_vision=vision,
        research_package=research_pkg,
        story_beats=[beat]
    )


# ============================================================================
# Suite 1: Enum Completeness & Canonical Values (R4, R2)
# ============================================================================

def test_visual_job_enum_completeness():
    """Verify all 20 VisualJob enum members exist and match requirements."""
    expected_jobs = {
        "ESTABLISH_WORLD", "INTRODUCE_CHARACTER", "INTRODUCE_OBJECT", "FOLLOW_OBJECT",
        "SHOW_EVIDENCE", "EXAMINE_EVIDENCE", "REVEAL_DETAIL", "VISUALIZE_ABSTRACT_CONCEPT",
        "SHOW_SCALE", "SHOW_COMPARISON", "RECONSTRUCT_EVENT", "BUILD_MYSTERY",
        "WITHHOLD_INFORMATION", "ESCALATE", "INTERRUPT", "CONTRAST",
        "HUMANIZE", "CONSEQUENCE", "REVEAL", "PAYOFF"
    }
    actual_jobs = {job.value for job in VisualJob}
    assert len(VisualJob) == 20, f"Expected exactly 20 VisualJob enums, found {len(VisualJob)}"
    assert actual_jobs == expected_jobs, f"Difference: {expected_jobs.symmetric_difference(actual_jobs)}"


def test_shot_relationship_enum_completeness():
    """Verify all 12 ShotRelationship enum members exist and match requirements."""
    expected_rels = {
        "CONTINUATION", "CONTRAST", "CAUSE_TO_EFFECT", "QUESTION_TO_ANSWER",
        "DETAIL_TO_CONTEXT", "CONTEXT_TO_DETAIL", "BEFORE_TO_AFTER",
        "EXPECTATION_TO_SUBVERSION", "OBJECT_TO_PERSON", "PERSON_TO_CONSEQUENCE",
        "NUMBER_TO_SCALE", "EVIDENCE_TO_REVEAL"
    }
    actual_rels = {rel.value for rel in ShotRelationship}
    assert len(ShotRelationship) == 12, f"Expected exactly 12 ShotRelationship enums, found {len(ShotRelationship)}"
    assert actual_rels == expected_rels, f"Difference: {expected_rels.symmetric_difference(actual_rels)}"


def test_narrative_intent_macro_phases():
    """Verify all 11 Macro Narrative Arc Phases exist in NarrativeIntent."""
    expected_macro = [
        "HOOK", "CENTRAL_QUESTION", "CONTEXT", "FIRST_DISCOVERY",
        "COMPLICATION", "ESCALATION", "REVELATION", "CONSEQUENCE",
        "DEEPER_REVELATION", "FINAL_CONTRADICTION", "PAYOFF"
    ]
    for phase in expected_macro:
        assert hasattr(NarrativeIntent, phase), f"NarrativeIntent missing phase {phase}"
        assert NarrativeIntent[phase].value == phase


def test_mini_arc_phases():
    """Verify all 5 MiniArcPhase values exist."""
    expected_phases = ["SETUP", "BUILD", "COMPLICATION", "REVEAL", "CONSEQUENCE"]
    assert len(MiniArcPhase) == 5
    for phase in expected_phases:
        assert hasattr(MiniArcPhase, phase)
        assert MiniArcPhase[phase].value == phase


# ============================================================================
# Suite 2: Full JSON Round-Trip Serialization & Deserialization Across 7 Models
# ============================================================================

def test_roundtrip_documentary_research_package():
    pkg = make_sample_research_package()
    json_data = pkg.model_dump_json()
    assert isinstance(json_data, str)
    
    restored = DocumentaryResearchPackage.model_validate_json(json_data)
    assert restored == pkg
    assert len(restored.evidence_items) == 1
    assert restored.evidence_items[0].title == "SIMEX Account 88888 Statement"
    assert len(restored.numbers) == 2
    assert restored.numbers[0].raw_value == "£827,000,000"


def test_roundtrip_documentary_vision():
    vision = make_sample_vision()
    json_data = vision.model_dump_json()
    restored = DocumentaryVision.model_validate_json(json_data)
    assert restored == vision
    assert len(restored.macro_narrative_arc) == 11
    assert restored.hook_strategy.hook_type == "CONTRADICTION"
    assert restored.hook_strategy.target_duration_seconds == 25.0


def test_roundtrip_visual_sequence_plan():
    plan = VisualSequencePlan(
        intention="Visual intention",
        visual_argument="arg_a vs arg_b",
        withholding_strategy="withhold key element",
        memorable_image="striking image",
        sequence_ending_statement="final visual punch",
        information_change=0.7,
        emotional_change=0.6,
        visual_change=0.8,
        scale_change=0.5
    )
    json_data = plan.model_dump_json()
    restored = VisualSequencePlan.model_validate_json(json_data)
    assert restored == plan
    assert restored.information_change == 0.7


def test_roundtrip_shot_all_fields():
    shot = Shot(
        shot_id="shot_test_01",
        duration_mode="fixed",
        duration_seconds=3.5,
        duration_ratio=0.5,
        shot_role="REVEAL",
        asset_provenance="AUTHENTIC_PHOTO",
        shot_size="close",
        camera_angle="low_angle",
        lens="macro_lens",
        composition="rule_of_thirds",
        foreground="Hands shaking",
        background="Stock exchange ticker",
        subject_position="center",
        depth="shallow",
        source_name="Financial Times",
        source_url="https://ft.com/archive",
        source_date="1995-02-24",
        confidence=0.95,
        generation_priority=0.85,
        visual_job=VisualJob.REVEAL_DETAIL,
        shot_relationship=ShotRelationship.EVIDENCE_TO_REVEAL,
        visual_type="ai_video",
        fallback_type="EvidenceBoard",
        visual_description="Trembling hands holding the telex confirmation slip.",
        visual_query="HANDS + PAPER + TELEX + 1995 + PANIC",
        ai_prompt="Macro close up of trembling hands holding a printed telex in 1995 office",
        camera_motion="slow_push_in",
        motion_intensity=0.4,
        transition_in="hard_cut",
        text_overlay="FEBRUARY 24, 1995",
        highlight=HighlightMetadata(keyword="FEBRUARY", style="glow", importance="high"),
        sound_design="paper_rustle",
        lut_filter="noir",
        overlay="film_grain",
        cut_reason="reveal_moment_of_realization",
        visual_importance=0.9,
        visual_density=0.7,
        visual_intent="isolation_and_panic",
        is_restrained=True,
        director_score=9.2,
        continuity=ContinuityMetadata(
            group_id="grp_002",
            characters=["Nick Leeson"],
            character_id="char_leeson",
            location="Trading desk",
            environment="Darkened office room",
            time_period="1995",
            start_year=1995,
            end_year=1995,
            technology_level="1990s CRT",
            weather="rainy night",
            lighting="Single desk lamp"
        ),
        asset=AssetMetadata(source="ai", path="/tmp/gen_shot.mp4", status="success", fallback_used=False),
        editorial_events=[
            EditorialEvent(type="SFX", cue="heavy_heartbeat", timing_percent=10.0, intensity=0.8, reason="Accentuate terror"),
            EditorialEvent(type="TEXT_REVEAL", cue="FEBRUARY 24, 1995", timing_percent=50.0, intensity=0.9, reason="Date marker")
        ]
    )
    json_data = shot.model_dump_json()
    restored = Shot.model_validate_json(json_data)
    assert restored == shot
    assert restored.editorial_events[0].type == "SFX"
    assert restored.highlight.keyword == "FEBRUARY"
    assert restored.visual_job == VisualJob.REVEAL_DETAIL
    assert restored.shot_relationship == ShotRelationship.EVIDENCE_TO_REVEAL


def test_roundtrip_narration_block():
    shot = make_sample_shot("s100")
    block = NarrationBlock(
        block_id="n_test_100",
        voiceover="The trading pit was deafening, but on screen, the numbers told a silent tragedy.",
        caption="The trading pit was deafening, but on screen, the numbers told a silent tragedy.",
        audio_file="/audio/n100.mp3",
        actual_voice_duration=5.2,
        total_block_duration=6.0,
        alignment_status="PASS",
        duration_hint=5.0,
        strategic_silence=StrategicSilence(duration_seconds=0.8, position="end", ambient_level=-40, visual_behavior="hold_frame"),
        audio_metadata=AudioMetadata(music_energy=0.4, music_duck_amount=-12),
        mini_arc_phase=MiniArcPhase.BUILD,
        shots=[shot]
    )
    json_data = block.model_dump_json()
    restored = NarrationBlock.model_validate_json(json_data)
    assert restored == block
    assert restored.mini_arc_phase == MiniArcPhase.BUILD
    assert restored.strategic_silence.ambient_level == -40


def test_roundtrip_story_beat():
    shot = make_sample_shot("s200")
    block = NarrationBlock(
        block_id="n200",
        voiceover="Voiceover test",
        caption="Caption test",
        duration_hint=4.0,
        shots=[shot]
    )
    seq_plan = VisualSequencePlan(
        intention="Test sequence",
        visual_argument="A vs B",
        withholding_strategy="withhold",
        memorable_image="mem_img",
        sequence_ending_statement="ending statement",
        information_change=0.5,
        emotional_change=0.5,
        visual_change=0.5,
        scale_change=0.5
    )
    beat = StoryBeat(
        beat_id="b200",
        time_context=TimeContext(year="2008", mode="historical", location="Wall St"),
        narrative_intent=NarrativeIntent.COMPLICATION,
        mini_arc_phase=MiniArcPhase.COMPLICATION,
        visual_sequence_plan=seq_plan,
        description="Market crash acceleration",
        attention_intensity=0.85,
        chapter_color_language="cold_blue",
        narration_blocks=[block]
    )
    json_data = beat.model_dump_json()
    restored = StoryBeat.model_validate_json(json_data)
    assert restored == beat
    assert restored.narrative_intent == NarrativeIntent.COMPLICATION
    assert restored.mini_arc_phase == MiniArcPhase.COMPLICATION


def test_roundtrip_script_manifest_full():
    manifest = make_sample_manifest()
    json_data = manifest.model_dump_json()
    restored = ScriptManifest.model_validate_json(json_data)
    assert restored == manifest
    assert restored.schema_version == "2.0"
    assert len(restored.story_beats) == 1
    assert restored.story_beats[0].visual_sequence_plan is not None
    assert restored.documentary_vision is not None
    assert restored.research_package is not None


# ============================================================================
# Suite 3: All 20 VisualJob Values on Shot
# ============================================================================

@pytest.mark.parametrize("job", list(VisualJob))
def test_all_20_visual_jobs_assignment_and_serialization(job):
    """Verify that every one of the 20 VisualJob values can be assigned and round-tripped."""
    shot = make_sample_shot(f"shot_{job.value}", visual_job=job)
    assert shot.visual_job == job
    
    # JSON roundtrip
    dumped = shot.model_dump_json()
    reloaded = Shot.model_validate_json(dumped)
    assert reloaded.visual_job == job
    
    # Dict roundtrip
    as_dict = shot.model_dump()
    assert as_dict["visual_job"] == job.value
    from_dict = Shot.model_validate(as_dict)
    assert from_dict.visual_job == job


# ============================================================================
# Suite 4: All 12 ShotRelationship Values on Shot
# ============================================================================

@pytest.mark.parametrize("rel", list(ShotRelationship))
def test_all_12_shot_relationships_assignment_and_serialization(rel):
    """Verify that every one of the 12 ShotRelationship values can be assigned and round-tripped."""
    shot = make_sample_shot(f"shot_{rel.value}", shot_relationship=rel)
    assert shot.shot_relationship == rel
    
    # JSON roundtrip
    dumped = shot.model_dump_json()
    reloaded = Shot.model_validate_json(dumped)
    assert reloaded.shot_relationship == rel
    
    # Dict roundtrip
    as_dict = shot.model_dump()
    assert as_dict["shot_relationship"] == rel.value
    from_dict = Shot.model_validate(as_dict)
    assert from_dict.shot_relationship == rel


def test_shot_relationship_none_and_empty():
    """Verify Shot handles None and empty string for shot_relationship."""
    shot_none = make_sample_shot("shot_none", shot_relationship=None)
    assert shot_none.shot_relationship is None
    
    shot_empty = make_sample_shot("shot_empty", shot_relationship="")
    assert shot_empty.shot_relationship is None


# ============================================================================
# Suite 5: Normalization, Pre-Validators & Legacy Mapping
# ============================================================================

@pytest.mark.parametrize("legacy_key,expected_canonical", list(LEGACY_VISUAL_JOB_MAP.items()))
def test_legacy_visual_job_mapping(legacy_key, expected_canonical):
    """Verify that legacy visual job strings are mapped to canonical 20 VisualJobs."""
    # Test uppercase
    shot_up = make_sample_shot("s_leg_up", visual_job=legacy_key)
    assert shot_up.visual_job == VisualJob[expected_canonical]
    
    # Test lowercase with whitespace
    shot_low = make_sample_shot("s_leg_low", visual_job=f"  {legacy_key.lower()}  ")
    assert shot_low.visual_job == VisualJob[expected_canonical]


def test_shot_visual_job_none_fallback():
    """Verify None visual_job falls back to ESTABLISH_WORLD."""
    shot = make_sample_shot("s_none", visual_job=None)
    assert shot.visual_job == VisualJob.ESTABLISH_WORLD


@pytest.mark.parametrize("alias,expected_intent", [
    ("THE_PROBLEM", NarrativeIntent.COMPLICATION),
    ("problem", NarrativeIntent.COMPLICATION),
    ("SETUP", NarrativeIntent.CONTEXT),
    ("setup", NarrativeIntent.CONTEXT),
    ("DISCOVERY", NarrativeIntent.FIRST_DISCOVERY),
    ("AFTERMATH", NarrativeIntent.CONSEQUENCE),
    ("LOCATION", NarrativeIntent.LOCATION_ESTABLISH),
    ("BACKGROUND", NarrativeIntent.CONTEXT),
    ("INTRODUCTION", NarrativeIntent.HOOK),
    ("CLIMAX", NarrativeIntent.REVELATION),
])
def test_story_beat_narrative_intent_aliases(alias, expected_intent):
    """Verify StoryBeat narrative_intent aliases normalize to canonical intents."""
    beat = StoryBeat(
        beat_id="b_alias",
        time_context=TimeContext(year="2000", mode="historical", location="London"),
        narrative_intent=alias,
        description="Alias test",
        narration_blocks=[]
    )
    assert beat.narrative_intent == expected_intent


def test_story_beat_narrative_intent_none_fallback():
    """Verify None narrative_intent falls back to EXPLANATION."""
    beat = StoryBeat(
        beat_id="b_none",
        time_context=TimeContext(year="2000", mode="historical", location="London"),
        narrative_intent=None,
        description="None fallback test",
        narration_blocks=[]
    )
    assert beat.narrative_intent == NarrativeIntent.EXPLANATION


@pytest.mark.parametrize("phase_str,expected_enum", [
    ("setup", MiniArcPhase.SETUP),
    (" BUILD ", MiniArcPhase.BUILD),
    ("complication", MiniArcPhase.COMPLICATION),
    ("REVEAL", MiniArcPhase.REVEAL),
    ("Consequence", MiniArcPhase.CONSEQUENCE),
])
def test_mini_arc_phase_normalization(phase_str, expected_enum):
    """Verify case and whitespace normalization for MiniArcPhase in NarrationBlock and StoryBeat."""
    shot = make_sample_shot("s_mini")
    block = NarrationBlock(
        block_id="n_mini",
        voiceover="V", caption="C", duration_hint=1.0,
        mini_arc_phase=phase_str,
        shots=[shot]
    )
    assert block.mini_arc_phase == expected_enum
    
    beat = StoryBeat(
        beat_id="b_mini",
        time_context=TimeContext(year="2000", mode="historical", location="London"),
        narrative_intent=NarrativeIntent.CONTEXT,
        mini_arc_phase=phase_str,
        description="Mini arc test",
        narration_blocks=[]
    )
    assert beat.mini_arc_phase == expected_enum


@pytest.mark.parametrize("hook_input,expected_hook", [
    ("question", "QUESTION"),
    ("contradiction", "CONTRADICTION"),
    ("SHOCK", "SHOCK"),
    ("mystery", "MYSTERY"),
    ("visual_anomaly", "VISUAL_ANOMALY"),
    ("unknown_hook_category", "CONTRADICTION"),  # Fallback
])
def test_hook_strategy_normalization(hook_input, expected_hook):
    """Verify HookStrategy hook_type normalization and invalid fallback."""
    hook = HookStrategy(
        hook_type=hook_input,
        anomaly_description="Anomaly",
        withholding_element="Withheld",
        opening_visual_cue="Visual cue"
    )
    assert hook.hook_type == expected_hook


def test_major_reveal_and_narrative_phase_plan_normalization():
    """Verify phase normalization in MajorRevealItem and NarrativePhasePlan."""
    reveal = MajorRevealItem(
        phase="  first_discovery  ",
        revelation="Hidden secret",
        evidence_backing="Doc A"
    )
    assert reveal.phase == NarrativeIntent.FIRST_DISCOVERY

    phase_plan = NarrativePhasePlan(
        phase="  deeper_revelation  ",
        narrative_goal="Deeper reveal",
        attention_target=0.8
    )
    assert phase_plan.phase == NarrativeIntent.DEEPER_REVELATION


# ============================================================================
# Suite 6: Boundary, Constraints & Negative Validation
# ============================================================================

def test_visual_sequence_plan_metric_bounds():
    """Verify VisualSequencePlan change metrics enforce [0.0, 1.0] bounds."""
    # Valid boundaries
    plan_valid = VisualSequencePlan(
        intention="Intention",
        visual_argument="Arg",
        withholding_strategy="Withhold",
        memorable_image="Image",
        sequence_ending_statement="Ending",
        information_change=0.0,
        emotional_change=1.0,
        visual_change=0.5,
        scale_change=0.0
    )
    assert plan_valid.information_change == 0.0
    assert plan_valid.emotional_change == 1.0

    # Invalid: information_change > 1.0
    with pytest.raises(ValidationError):
        VisualSequencePlan(
            intention="Intention",
            visual_argument="Arg",
            withholding_strategy="Withhold",
            memorable_image="Image",
            sequence_ending_statement="Ending",
            information_change=1.5
        )

    # Invalid: visual_change < 0.0
    with pytest.raises(ValidationError):
        VisualSequencePlan(
            intention="Intention",
            visual_argument="Arg",
            withholding_strategy="Withhold",
            memorable_image="Image",
            sequence_ending_statement="Ending",
            visual_change=-0.1
        )


def test_narrative_phase_plan_attention_bounds():
    """Verify NarrativePhasePlan attention_target enforces [0.0, 1.0] bounds."""
    with pytest.raises(ValidationError):
        NarrativePhasePlan(
            phase=NarrativeIntent.HOOK,
            narrative_goal="Goal",
            attention_target=1.2
        )
    with pytest.raises(ValidationError):
        NarrativePhasePlan(
            phase=NarrativeIntent.HOOK,
            narrative_goal="Goal",
            attention_target=-0.5
        )


def test_missing_required_fields_raise_validation_error():
    """Verify missing required fields raise Pydantic ValidationError."""
    # DocumentaryResearchPackage missing central_question
    with pytest.raises(ValidationError):
        DocumentaryResearchPackage(
            topic="Test",
            documentary_thesis="Thesis",
            # missing central_question and others
        )

    # Shot missing cut_reason
    with pytest.raises(ValidationError):
        Shot(
            shot_id="s1",
            visual_type="real_photo",
            fallback_type="ArchivalDocument",
            visual_description="Desc",
            visual_query="Query",
            ai_prompt="Prompt",
            continuity=ContinuityMetadata(
                group_id="g1", location="L", environment="E", time_period="T", lighting="L"
            )
            # missing cut_reason
        )


# ============================================================================
# Suite 7: BaseAgent Mock Fallbacks Schema Conformance
# ============================================================================

def test_researcher_mock_fallback_schema_conformance():
    """Verify ResearcherAgent fallback produces valid DocumentaryResearchPackage."""
    agent = ResearcherAgent()
    fallback = agent._get_mock_fallback("The Fall of Nokia", "", True)
    assert isinstance(fallback, dict)
    
    pkg = DocumentaryResearchPackage.model_validate(fallback)
    assert pkg.topic == "The Fall of Nokia"
    assert len(pkg.evidence_items) >= 1
    assert len(pkg.numbers) >= 1
    assert len(pkg.turning_points) >= 1
    assert len(pkg.major_reveals) >= 1
    assert pkg.ending_image_opportunity is not None


def test_director_mock_fallback_schema_conformance():
    """Verify DirectorAgent fallback produces valid ScriptManifest with v2.0 fields."""
    agent = DirectorAgent()
    fallback = agent._get_mock_fallback("mock script", "", True)
    assert isinstance(fallback, dict)
    
    manifest = ScriptManifest.model_validate(fallback)
    assert manifest.schema_version == "2.0"
    assert manifest.documentary_vision is not None
    assert manifest.research_package is not None
    assert len(manifest.story_beats) >= 1
    
    # Check story beat structure
    beat = manifest.story_beats[0]
    assert beat.visual_sequence_plan is not None
    assert beat.visual_sequence_plan.information_change >= 0.0
    assert len(beat.narration_blocks) >= 1
    
    # Check shot structure
    shot = beat.narration_blocks[0].shots[0]
    assert shot.visual_job in VisualJob
    assert shot.shot_relationship is not None or shot.shot_relationship is None


# ============================================================================
# Suite 8: Combinatorial 240 Matrix (20 VisualJobs x 12 ShotRelationships)
# ============================================================================

def test_combinatorial_visual_job_x_shot_relationship_matrix():
    """Test all 240 combinations of VisualJob and ShotRelationship on Shot instances."""
    shots = []
    idx = 0
    for job in VisualJob:
        for rel in ShotRelationship:
            shot = make_sample_shot(f"combo_s_{idx}", visual_job=job, shot_relationship=rel)
            assert shot.visual_job == job
            assert shot.shot_relationship == rel
            shots.append(shot)
            idx += 1
    assert len(shots) == 240
    
    # Build NarrationBlock containing all 240 shots
    block = NarrationBlock(
        block_id="n_combo",
        voiceover="Combinatorial stress test voiceover",
        caption="Combinatorial stress test caption",
        duration_hint=240.0,
        shots=shots
    )
    # Validate roundtrip
    dumped = block.model_dump_json()
    restored = NarrationBlock.model_validate_json(dumped)
    assert len(restored.shots) == 240
    for i, orig_shot in enumerate(shots):
        assert restored.shots[i].visual_job == orig_shot.visual_job
        assert restored.shots[i].shot_relationship == orig_shot.shot_relationship


# ============================================================================
# Suite 9: Combinatorial 55 Matrix (11 Macro Phases x 5 Mini-Arc Phases)
# ============================================================================

def test_combinatorial_macro_phases_x_mini_arc_phases():
    """Test all 55 combinations of 11 Macro phases and 5 MiniArc phases on StoryBeat."""
    macro_phases = [
        NarrativeIntent.HOOK, NarrativeIntent.CENTRAL_QUESTION, NarrativeIntent.CONTEXT,
        NarrativeIntent.FIRST_DISCOVERY, NarrativeIntent.COMPLICATION, NarrativeIntent.ESCALATION,
        NarrativeIntent.REVELATION, NarrativeIntent.CONSEQUENCE, NarrativeIntent.DEEPER_REVELATION,
        NarrativeIntent.FINAL_CONTRADICTION, NarrativeIntent.PAYOFF
    ]
    mini_phases = list(MiniArcPhase)
    
    beats = []
    idx = 0
    for macro in macro_phases:
        for mini in mini_phases:
            shot = make_sample_shot(f"shot_m_{idx}")
            block = NarrationBlock(
                block_id=f"n_m_{idx}",
                voiceover="Voiceover test",
                caption="Caption test",
                duration_hint=5.0,
                mini_arc_phase=mini,
                shots=[shot]
            )
            beat = StoryBeat(
                beat_id=f"beat_m_{idx}",
                time_context=TimeContext(year="2020", mode="present_day", location="Global"),
                narrative_intent=macro,
                mini_arc_phase=mini,
                description=f"Phase combo {macro.value} + {mini.value}",
                narration_blocks=[block]
            )
            assert beat.narrative_intent == macro
            assert beat.mini_arc_phase == mini
            assert block.mini_arc_phase == mini
            beats.append(beat)
            idx += 1
    assert len(beats) == 55


# ============================================================================
# Suite 10: Unicode, Multilingual (Hindi) & Special Characters
# ============================================================================

def test_unicode_hindi_and_special_character_resilience():
    """Verify that models handle Hindi Devanagari script, currency symbols, and quotes cleanly."""
    hindi_voiceover = "1995 में, एक 28 वर्षीय ट्रेडर निक लीसन ने 233 साल पुराने बेरिंग्स बैंक को दिवालिया कर दिया।"
    hindi_caption = "1995 में, एक 28 वर्षीय ट्रेडर निक लीसन ने 233 साल पुराने बेरिंग्स बैंक को दिवालिया कर दिया।"
    
    pkg = DocumentaryResearchPackage(
        topic="बेरिंग्स बैंक का पतन (Fall of Barings Bank)",
        central_question="कैसे 233 साल पुराना शाही बैंक £827M के नुकसान से ढह गया?",
        documentary_thesis="संस्थागत अंधापन और 88888 गुप्त खाता।",
        central_contradiction="भारी मुनाफे का दिखावा बनाम छिपा हुआ घाटा।",
        audience_initial_belief="अप्रत्याशित बाजार दुर्घटना।",
        what_the_audience_thinks_is_true="निक लीसन एक जीनियस था।",
        what_is_actually_more_complicated="निगरानी और ऑडिटिंग का पूर्ण अभाव।",
        protagonist_or_human_anchor="निक लीसन (Nick Leeson)",
        antagonistic_force_or_system="खाता संख्या 88888 (Account 88888)",
        stakes="ब्रिटेन के सबसे पुराने बैंक का £1 में बिकना",
        historical_context="1995 सिंगापुर और लंदन",
        final_payoff="वैश्विक वित्तीय नियमों का स्थायी परिवर्तन।",
        ending_image_opportunity="खाली ट्रेडिंग डेस्क और त्याग दी गई जैकेट।"
    )
    
    shot = Shot(
        shot_id="shot_hindi_01",
        visual_job=VisualJob.VISUALIZE_ABSTRACT_CONCEPT,
        shot_relationship=ShotRelationship.NUMBER_TO_SCALE,
        visual_type="text_stat",
        fallback_type="CinematicText",
        visual_description="स्क्रीन पर £827,000,000 लाल अक्षरों में चमकता है।",
        visual_query="HINDI TEXT + NUMBERS + 827M + GLOW",
        ai_prompt="Kinetic typographic display of £827,000,000 with glowing embers",
        cut_reason="दबाव और घाटे का नाटकीय प्रकटीकरण",
        text_overlay="कुल घाटा: £827M (~₹4,500 करोड़)",
        continuity=ContinuityMetadata(
            group_id="grp_hi",
            location="सिंगापुर",
            environment="ट्रेडिंग रूम",
            time_period="1995",
            lighting="नियॉन चमक"
        )
    )
    
    block = NarrationBlock(
        block_id="n_hi_01",
        voiceover=hindi_voiceover,
        caption=hindi_caption,
        duration_hint=7.5,
        shots=[shot]
    )
    
    beat = StoryBeat(
        beat_id="b_hi_01",
        time_context=TimeContext(year="1995", mode="historical", location="सिंगापुर"),
        narrative_intent=NarrativeIntent.REVELATION,
        description="घाटे का खुलासा",
        narration_blocks=[block]
    )
    
    manifest = ScriptManifest(
        schema_version="2.0",
        project_meta=ProjectMeta(
            topic="बेरिंग्स बैंक का पतन",
            language="hindi",
            visual_bible=VisualBible(
                era="1995",
                locations=["लंदन", "सिंगापुर"],
                lighting="सिनेमैटिक",
                color_language="कोल्ड टील",
                film_texture="35एमएम ग्रेन"
            )
        ),
        research_package=pkg,
        story_beats=[beat]
    )
    
    # JSON roundtrip
    dumped = manifest.model_dump_json()
    restored = ScriptManifest.model_validate_json(dumped)
    assert restored.story_beats[0].narration_blocks[0].voiceover == hindi_voiceover
    assert restored.research_package.topic == "बेरिंग्स बैंक का पतन (Fall of Barings Bank)"
    assert restored.story_beats[0].narration_blocks[0].shots[0].text_overlay == "कुल घाटा: £827M (~₹4,500 करोड़)"


# ============================================================================
# Suite 11: Deep Scale & Hierarchy Stress (Massive Manifest)
# ============================================================================

def test_deep_scale_and_hierarchy_stress():
    """Verify performance and memory stability on a 50-beat, 150-block, 450-shot documentary."""
    beats = []
    shot_count = 0
    for b_idx in range(50):
        blocks = []
        for n_idx in range(3):
            shots = []
            for s_idx in range(3):
                shot = make_sample_shot(
                    f"s_{b_idx}_{n_idx}_{s_idx}",
                    visual_job=list(VisualJob)[(shot_count) % 20],
                    shot_relationship=list(ShotRelationship)[(shot_count) % 12]
                )
                shots.append(shot)
                shot_count += 1
            block = NarrationBlock(
                block_id=f"n_{b_idx}_{n_idx}",
                voiceover=f"Narration line for beat {b_idx} block {n_idx}",
                caption=f"Caption line for beat {b_idx} block {n_idx}",
                duration_hint=6.0,
                mini_arc_phase=list(MiniArcPhase)[n_idx % 5],
                shots=shots
            )
            blocks.append(block)
        beat = StoryBeat(
            beat_id=f"b_{b_idx}",
            time_context=TimeContext(year=str(1990 + b_idx % 30), mode="historical", location=f"Location {b_idx}"),
            narrative_intent=list(NarrativeIntent)[b_idx % 11],
            mini_arc_phase=list(MiniArcPhase)[b_idx % 5],
            visual_sequence_plan=VisualSequencePlan(
                intention=f"Intention {b_idx}",
                visual_argument=f"Arg {b_idx} vs Counter {b_idx}",
                withholding_strategy=f"Withhold {b_idx}",
                memorable_image=f"Image {b_idx}",
                sequence_ending_statement=f"Ending {b_idx}",
                information_change=0.7,
                emotional_change=0.6,
                visual_change=0.8,
                scale_change=0.5
            ),
            description=f"Deep beat {b_idx}",
            narration_blocks=blocks
        )
        beats.append(beat)
        
    assert shot_count == 450
    manifest = ScriptManifest(
        schema_version="2.0",
        project_meta=ProjectMeta(
            topic="Massive Documentary Stress Test",
            genre="documentary",
            style_profile="DOCUMENTARY_INVESTIGATIVE",
            language="hindi",
            visual_bible=VisualBible(
                era="1990-2020",
                locations=["Global"],
                lighting="cinematic",
                color_language="teal_orange",
                film_texture="subtle grain"
            )
        ),
        research_package=make_sample_research_package(),
        documentary_vision=make_sample_vision(),
        story_beats=beats
    )
    
    # Serialize and measure
    json_bytes = manifest.model_dump_json()
    assert len(json_bytes) > 100_000, "Manifest JSON size should exceed 100KB"
    
    # Deserialize
    restored = ScriptManifest.model_validate_json(json_bytes)
    assert len(restored.story_beats) == 50
    total_restored_shots = sum(len(n.shots) for b in restored.story_beats for n in b.narration_blocks)
    assert total_restored_shots == 450

