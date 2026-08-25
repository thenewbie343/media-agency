"""
V3 Fixture Data: Deterministic Research Package, Claims, Evidence Assets, and Authored Editorial Scenes
Topic: The 1983 Soviet Nuclear False Alarm Incident (Stanislav Petrov)
"""

from agents.schema import (
    Claim, EvidenceAsset, EditorialScene, Shot, NarrationBlock, 
    StoryBeat, ProjectMeta, VisualBible, ScriptManifest, TimeContext,
    StrategicSilence, HighlightMetadata, ContinuityMetadata, VisualJob, ShotRelationship
)

def get_v3_petrov_fixture():
    # 1. Structured Fact & Claim Graph
    claim_1 = Claim(
        claim_id="claim_001",
        text="At 00:15 MSK on September 26, 1983, the Soviet Oko early warning system reported five inbound US Minuteman ICBMs.",
        claim_type="historical_fact",
        importance=0.98,
        confidence=1.0,
        evidence_required=True,
        evidence_ids=["ev_001"],
        visual_strategy="EVIDENCE_TO_RECONSTRUCTION"
    )

    claim_2 = Claim(
        claim_id="claim_002",
        text="Soviet military doctrine mandated immediate nuclear retaliation upon satellite launch confirmation.",
        claim_type="official_verdict",
        importance=0.95,
        confidence=1.0,
        evidence_required=True,
        evidence_ids=["ev_002"],
        visual_strategy="EVIDENCE_HOLD"
    )

    claim_3 = Claim(
        claim_id="claim_003",
        text="Duty officer Stanislav Petrov recognized that a genuine US first strike would involve hundreds of missiles, suspecting a technical sensor glitch.",
        claim_type="eyewitness_account",
        importance=0.92,
        confidence=0.98,
        evidence_required=True,
        evidence_ids=["ev_003"],
        visual_strategy="HUMAN_ANCHOR_TO_EVIDENCE"
    )

    claim_4 = Claim(
        claim_id="claim_004",
        text="Post-incident investigation confirmed the alert was triggered by rare sunlight reflections off high-altitude clouds aligned with Molniya satellites.",
        claim_type="technical_detail",
        importance=0.90,
        confidence=1.0,
        evidence_required=True,
        evidence_ids=["ev_004"],
        visual_strategy="GRAPHIC_TO_EVIDENCE"
    )

    # 2. Distinct Evidence Assets (Preserving provenance and rights)
    ev_001 = EvidenceAsset(
        id="ev_001",
        claim_id="claim_001",
        source_name="Soviet Air Defense Command (Declassified)",
        source_type="declassified_file",
        publisher="Ministry of Defense Archives, Podolsk",
        title="Oko Early Warning Incident Report #83-0926",
        publication_date="1983-09-26",
        relevant_excerpt="СИСТЕМА 'ОКО': ОБНАРУЖЕНО 5 СТАРТОВ МБР 'МИНУТМЕН'. ВЫСОКИЙ УРОВЕНЬ ДОСТОВЕРНОСТИ.",
        confidence=0.99,
        capture_type="document_scan",
        rights_status="public_domain",
        visual_treatment="document_inspection",
        fallback_used=False,
        status="success"
    )

    ev_002 = EvidenceAsset(
        id="ev_002",
        claim_id="claim_002",
        source_name="Strategic Rocket Forces Directive #414",
        source_type="official_log",
        publisher="General Staff of the Soviet Armed Forces",
        title="Standard Operating Procedure for Retaliatory Launch-on-Warning",
        publication_date="1981-04-15",
        relevant_excerpt="Upon combat confirmation from early-warning systems, counter-strike authorization is mandatory within 12 minutes.",
        confidence=0.97,
        capture_type="quote",
        rights_status="fair_use_documentary",
        visual_treatment="quote_highlight",
        fallback_used=False,
        status="success"
    )

    ev_003 = EvidenceAsset(
        id="ev_003",
        claim_id="claim_003",
        source_name="Special Commission of Inquiry Report",
        source_type="technical_manual",
        publisher="State Scientific Research Institute #45",
        title="Technical Analysis of Oko False Alert Telemetry",
        publication_date="1983-11-12",
        relevant_excerpt="Probability of 5 simultaneous US solo missiles during high alert: Statistically Null. Ground radar cross-checks showed zero confirmation.",
        confidence=1.0,
        capture_type="article",
        rights_status="public_domain",
        visual_treatment="article_clipping",
        fallback_used=False,
        status="success"
    )

    # 3. Authored 10-Shot Visual Sequence (60.0 Seconds total)
    shots = [
        # Shot 1: Hook (0-5s) - Black / Silence / Timecode
        Shot(
            shot_id="s001_hook_black",
            linked_claim_id="claim_001",
            duration_mode="fixed",
            duration_seconds=5.0,
            shot_role="HOLD",
            asset_provenance="EDITORIAL_TYPOGRAPHY",
            visual_type="BLACK_HOLD",
            fallback_type="EvidenceCard",
            visual_job=VisualJob.BUILD_MYSTERY,
            visual_description="Cinematic black screen with digital military timecode ticking in silence.",
            visual_query="cold war military timecode black screen",
            ai_prompt="Pure black screen with ticking timecode",
            camera_motion="static",
            motion_intensity=0.0,
            transition_in="hard_cut",
            cut_reason="establish_tension_in_silence",
            continuity=ContinuityMetadata(group_id="bunker", location="Serpukhov-15", environment="darkness", time_period="1983", lighting="none"),
            text_overlay="00:15:00 MSK // SEPTEMBER 26, 1983",
            sound_design="wind_howl"
        ),

        # Shot 2: Reconstruction (5-13s) - Soviet Control Room
        Shot(
            shot_id="s002_reconstruction_bunker",
            linked_claim_id="claim_001",
            duration_mode="fixed",
            duration_seconds=8.0,
            shot_role="ESTABLISHING",
            asset_provenance="AI_RECONSTRUCTION",
            visual_type="RECONSTRUCTION",
            fallback_type="EvidenceCard",
            visual_job=VisualJob.ESTABLISH_WORLD,
            visual_description="Cinematic slow push in on 1983 Soviet nuclear command center, amber CRT screens casting low-key light across Soviet equipment.",
            visual_query="1983 Soviet nuclear bunker command center amber screens cinematic low key lighting",
            ai_prompt="1983 Soviet nuclear command center Serpukhov-15, amber CRT phosphor computer monitors, analog dials, cold war military atmosphere, 35mm film grain, cinematic anamorphic lighting",
            camera_motion="slow_push_in",
            motion_intensity=0.25,
            transition_in="fade",
            cut_reason="establish_historical_setting",
            lut_filter="vintage_film",
            overlay="film_grain",
            continuity=ContinuityMetadata(group_id="bunker", location="Serpukhov-15", environment="bunker", time_period="1983", lighting="amber low-key")
        ),

        # Shot 3: Evidence Document (13-18s) - Declassified Alert Log
        Shot(
            shot_id="s003_evidence_oko_log",
            linked_claim_id="claim_001",
            duration_mode="fixed",
            duration_seconds=5.0,
            shot_role="EVIDENCE",
            asset_provenance="HISTORICAL_DOCUMENT",
            visual_type="EVIDENCE_DOCUMENT",
            fallback_type="EvidenceCard",
            visual_job=VisualJob.SHOW_EVIDENCE,
            visual_description="Declassified Soviet Defense log showing 5 missile alerts with red military stamps.",
            visual_query="Declassified Soviet missile alert document 1983",
            ai_prompt="Declassified Soviet document",
            camera_motion="slow_push_in",
            motion_intensity=0.15,
            transition_in="hard_cut",
            cut_reason="ground_narrative_in_primary_evidence",
            continuity=ContinuityMetadata(group_id="archive", location="Podolsk Archives", environment="paper", time_period="1983", lighting="flat archival"),
            asset=ev_001,
            text_overlay="5 INBOUND MISSILES DETECTED // HIGH CONFIDENCE",
            source_name="Soviet Air Defense Command"
        ),

        # Shot 4: Graphic Explanation (18-23s) - Orbital Satellite Trajectory
        Shot(
            shot_id="s004_graphic_orbit",
            linked_claim_id="claim_004",
            duration_mode="fixed",
            duration_seconds=5.0,
            shot_role="EXPLANATION",
            asset_provenance="MOTION_GRAPHIC",
            visual_type="MOTION_GRAPHIC",
            fallback_type="TechnicalDiagram",
            visual_job=VisualJob.VISUALIZE_ABSTRACT_CONCEPT,
            visual_description="Orbital telemetry diagram illustrating Molniya satellite orbit and high-altitude sunlight reflection.",
            visual_query="Orbital trajectory satellite telemetry technical diagram",
            ai_prompt="Orbital trajectory satellite diagram technical blueprint",
            camera_motion="pan_right",
            motion_intensity=0.3,
            transition_in="fade",
            cut_reason="explain_underlying_technical_anomaly",
            continuity=ContinuityMetadata(group_id="technical", location="orbit", environment="telemetry", time_period="1983", lighting="vector"),
            text_overlay="MOLNIYA SATELLITE SENSOR CONFLICT",
            lut_filter="noir"
        ),

        # Shot 5: Human Anchor (23-28s) - Petrov Operator Reaction
        Shot(
            shot_id="s005_human_anchor_petrov",
            linked_claim_id="claim_003",
            duration_mode="fixed",
            duration_seconds=5.0,
            shot_role="REACTION",
            asset_provenance="AI_RECONSTRUCTION",
            visual_type="RECONSTRUCTION",
            fallback_type="PortraitCard",
            visual_job=VisualJob.HUMANIZE,
            visual_description="Close-up of Stanislav Petrov in Soviet uniform, intense focus and perspiration under flickering alarm lights.",
            visual_query="1983 Soviet officer Stanislav Petrov face close up tense intense focus cinematic",
            ai_prompt="Close-up portrait of 1983 Soviet duty officer Stanislav Petrov, sweating under cold amber lighting, wearing Soviet military uniform, intense human focus, cinematic documentary photography",
            camera_motion="slow_push_in",
            motion_intensity=0.3,
            transition_in="hard_cut",
            cut_reason="anchor_stakes_in_human_decision",
            lut_filter="vintage_film",
            overlay="film_grain",
            continuity=ContinuityMetadata(group_id="bunker", location="Serpukhov-15", environment="bunker", time_period="1983", lighting="amber low-key")
        ),

        # Shot 6: Evidence Detail Highlight (28-34s) - Inquiry Excerpt
        Shot(
            shot_id="s006_evidence_inquiry_excerpt",
            linked_claim_id="claim_003",
            duration_mode="fixed",
            duration_seconds=6.0,
            shot_role="DETAIL",
            asset_provenance="HISTORICAL_DOCUMENT",
            visual_type="EVIDENCE_ARTICLE",
            fallback_type="EvidenceCard",
            visual_job=VisualJob.EXAMINE_EVIDENCE,
            visual_description="Official inquiry report highlighting statistical impossibility of 5 solo missile strike.",
            visual_query="Soviet military inquiry document highlight",
            ai_prompt="Soviet military inquiry document",
            camera_motion="static",
            motion_intensity=0.0,
            transition_in="hard_cut",
            cut_reason="reveal_analytical_contradiction",
            continuity=ContinuityMetadata(group_id="archive", location="Podolsk Archives", environment="paper", time_period="1983", lighting="archival"),
            asset=ev_003,
            text_overlay="STATISTICALLY NULL: 5 MISSILE FIRST STRIKE",
            source_name="Special Commission of Inquiry Report"
        ),

        # Shot 7: Consequence Map (34-40s) - 5 Projected Trajectories
        Shot(
            shot_id="s007_consequence_map",
            linked_claim_id="claim_002",
            duration_mode="fixed",
            duration_seconds=6.0,
            shot_role="CONSEQUENCE",
            asset_provenance="MOTION_GRAPHIC",
            visual_type="MOTION_GRAPHIC",
            fallback_type="MapFallback",
            visual_job=VisualJob.SHOW_SCALE,
            visual_description="Global polar projection map animating 5 nuclear strike trajectories across the Arctic toward USSR targets.",
            visual_query="Polar projection military map missile trajectories nuclear strike",
            ai_prompt="Cold war tactical map ICBM trajectories polar projection",
            camera_motion="slow_push_in",
            motion_intensity=0.35,
            transition_in="fade",
            cut_reason="visualize_global_existential_scale",
            continuity=ContinuityMetadata(group_id="technical", location="global", environment="tactical map", time_period="1983", lighting="vector"),
            text_overlay="STRATEGIC WARNING: 12 MINUTES TO IMPACT",
            lut_filter="high_contrast"
        ),

        # Shot 8: Strategic Silence (40-43s) - Black Hold
        Shot(
            shot_id="s008_silence_decision_hold",
            linked_claim_id="claim_002",
            duration_mode="fixed",
            duration_seconds=3.0,
            shot_role="HOLD",
            asset_provenance="EDITORIAL_TYPOGRAPHY",
            visual_type="BLACK_HOLD",
            fallback_type="EvidenceCard",
            visual_job=VisualJob.WITHHOLD_INFORMATION,
            visual_description="Pure black hold. Total silence. The agonizing moment before Petrov called the general staff.",
            visual_query="black silence hold",
            ai_prompt="black screen",
            camera_motion="static",
            motion_intensity=0.0,
            transition_in="hard_cut",
            cut_reason="force_audience_to_feel_the_weight_of_silence",
            continuity=ContinuityMetadata(group_id="bunker", location="Serpukhov-15", environment="darkness", time_period="1983", lighting="none"),
            text_overlay="THE DECISION"
        ),

        # Shot 9: Major Typography Reveal (43-50s) - Sunlight Anomaly
        Shot(
            shot_id="s009_typography_reveal",
            linked_claim_id="claim_004",
            duration_mode="fixed",
            duration_seconds=7.0,
            shot_role="REVEAL",
            asset_provenance="EDITORIAL_TYPOGRAPHY",
            visual_type="TYPOGRAPHY_REVEAL",
            fallback_type="EvidenceCard",
            visual_job=VisualJob.REVEAL,
            visual_description="Authoritative editorial typography punctuation revealing the true cause.",
            visual_query="editorial typography reveal",
            ai_prompt="typography reveal",
            camera_motion="static",
            motion_intensity=0.0,
            transition_in="hard_cut",
            cut_reason="deliver_definitive_documentary_revelation",
            continuity=ContinuityMetadata(group_id="typography", location="title", environment="editorial", time_period="1983", lighting="graphic"),
            text_overlay="SEPTEMBER 26, 1983 — A FALSE ALARM CAUSED BY SUNLIGHT"
        ),

        # Shot 10: Consequence & Human Payoff (50-60s) - Petrov in Morning Fog
        Shot(
            shot_id="s010_consequence_payoff",
            linked_claim_id="claim_004",
            duration_mode="fixed",
            duration_seconds=10.0,
            shot_role="TRANSITION",
            asset_provenance="AI_RECONSTRUCTION",
            visual_type="RECONSTRUCTION",
            fallback_type="EvidenceCard",
            visual_job=VisualJob.PAYOFF,
            visual_description="Stanislav Petrov stepping out of the concrete bunker into the quiet morning fog, the world saved by a single man's doubt.",
            visual_query="1983 Soviet officer walking outside concrete bunker morning mist fog sunrise cinematic",
            ai_prompt="1983 Soviet officer in heavy military greatcoat walking away from brutalist concrete bunker into morning fog, soft golden sunrise breaking through mist, evocative cinematic ending, 35mm film grain",
            camera_motion="slow_push_in",
            motion_intensity=0.2,
            transition_in="fade",
            cut_reason="resolve_narrative_with_lasting_human_legacy",
            lut_filter="warm_cinema",
            overlay="film_grain",
            continuity=ContinuityMetadata(group_id="bunker", location="Serpukhov-15 exterior", environment="morning fog", time_period="1983", lighting="golden sunrise")
        )
    ]

    # 4. Construct Blocks & StoryBeat
    block_1 = NarrationBlock(
        block_id="n001",
        voiceover="At fifteen minutes past midnight on September twenty-sixth, nineteen eighty-three, the Soviet nuclear early warning system detected five incoming intercontinental ballistic missiles.",
        caption="September 26, 1983: Soviet early warning systems detect 5 incoming US missiles.",
        duration_hint=18.0,
        actual_voice_duration=18.0,
        total_block_duration=18.0,
        shots=shots[0:3]
    )

    block_2 = NarrationBlock(
        block_id="n002",
        voiceover="Under strict Soviet doctrine, retaliation was mandatory. But duty officer Stanislav Petrov recognized an anomaly: a true first strike would unleash hundreds of missiles, not five.",
        caption="Protocol demanded immediate retaliation. But Petrov suspected a technical failure.",
        duration_hint=22.0,
        actual_voice_duration=22.0,
        total_block_duration=22.0,
        shots=shots[3:7]
    )

    block_3 = NarrationBlock(
        block_id="n003",
        voiceover="He broke protocol and logged a false alarm. What the satellites had seen was not a nuclear launch, but the reflection of autumn sunlight off high-altitude clouds.",
        caption="He logged a false alarm. The satellites had been blinded by sunlight reflecting off clouds.",
        duration_hint=20.0,
        actual_voice_duration=20.0,
        total_block_duration=20.0,
        shots=shots[7:10],
        strategic_silence=StrategicSilence(duration_seconds=3.0, position="start")
    )

    beat = StoryBeat(
        beat_id="beat_001_petrov_false_alarm",
        time_context=TimeContext(year="1983", mode="historical", location="Serpukhov-15"),
        narrative_intent="REVELATION",
        description="Stanislav Petrov defies protocol and averts nuclear war during a satellite sensor failure.",
        chapter_color_language="vintage_film",
        narration_blocks=[block_1, block_2, block_3]
    )

    meta = ProjectMeta(
        topic="The Computer Error That Almost Started World War 3",
        language="english",
        visual_bible=VisualBible(
            era="1983",
            locations=["Serpukhov-15 Command Center", "Podolsk Defense Archives", "Satellite Orbit"],
            lighting="amber low-key, cold fluorescent, dramatic morning fog",
            color_language="vintage_film",
            film_texture="35mm grain"
        )
    )

    manifest = ScriptManifest(
        schema_version="3.0",
        project_meta=meta,
        story_beats=[beat]
    )

    return manifest, [claim_1, claim_2, claim_3, claim_4], [ev_001, ev_002, ev_003]
