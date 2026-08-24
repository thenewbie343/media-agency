from enum import Enum
from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# 1. Directorial & Narrative Enums
# ============================================================================

class NarrativeIntent(str, Enum):
    """
    11 Macro-Narrative Arc Phases (R2) + Legacy Backward Compatibility.
    Arc Progression: HOOK -> CENTRAL_QUESTION -> CONTEXT -> FIRST_DISCOVERY ->
    COMPLICATION -> ESCALATION -> REVELATION -> CONSEQUENCE -> DEEPER_REVELATION ->
    FINAL_CONTRADICTION -> PAYOFF.
    """
    # 11 Macro Narrative Phases
    HOOK = "HOOK"
    CENTRAL_QUESTION = "CENTRAL_QUESTION"
    CONTEXT = "CONTEXT"
    FIRST_DISCOVERY = "FIRST_DISCOVERY"
    COMPLICATION = "COMPLICATION"
    ESCALATION = "ESCALATION"
    REVELATION = "REVELATION"
    CONSEQUENCE = "CONSEQUENCE"
    DEEPER_REVELATION = "DEEPER_REVELATION"
    FINAL_CONTRADICTION = "FINAL_CONTRADICTION"
    PAYOFF = "PAYOFF"
    
    # Backward-compatible legacy intents
    EVIDENCE = "EVIDENCE"
    MYSTERY = "MYSTERY"
    EXPLANATION = "EXPLANATION"
    CONFLICT = "CONFLICT"
    RESOLUTION = "RESOLUTION"
    LOCATION_ESTABLISH = "LOCATION_ESTABLISH"


class MiniArcPhase(str, Enum):
    """
    30-90s Mini-Arc Dramatic Tension Progression (R2).
    Every scene cluster cycles: SETUP -> BUILD -> COMPLICATION -> REVEAL -> CONSEQUENCE.
    """
    SETUP = "SETUP"
    BUILD = "BUILD"
    COMPLICATION = "COMPLICATION"
    REVEAL = "REVEAL"
    CONSEQUENCE = "CONSEQUENCE"


class VisualJob(str, Enum):
    """
    20 Editorial Visual Jobs (R4).
    Defines the precise storytelling function of every individual shot.
    """
    ESTABLISH_WORLD = "ESTABLISH_WORLD"
    INTRODUCE_CHARACTER = "INTRODUCE_CHARACTER"
    INTRODUCE_OBJECT = "INTRODUCE_OBJECT"
    FOLLOW_OBJECT = "FOLLOW_OBJECT"
    SHOW_EVIDENCE = "SHOW_EVIDENCE"
    EXAMINE_EVIDENCE = "EXAMINE_EVIDENCE"
    REVEAL_DETAIL = "REVEAL_DETAIL"
    VISUALIZE_ABSTRACT_CONCEPT = "VISUALIZE_ABSTRACT_CONCEPT"
    SHOW_SCALE = "SHOW_SCALE"
    SHOW_COMPARISON = "SHOW_COMPARISON"
    RECONSTRUCT_EVENT = "RECONSTRUCT_EVENT"
    BUILD_MYSTERY = "BUILD_MYSTERY"
    WITHHOLD_INFORMATION = "WITHHOLD_INFORMATION"
    ESCALATE = "ESCALATE"
    INTERRUPT = "INTERRUPT"
    CONTRAST = "CONTRAST"
    HUMANIZE = "HUMANIZE"
    CONSEQUENCE = "CONSEQUENCE"
    REVEAL = "REVEAL"
    PAYOFF = "PAYOFF"


class ShotRelationship(str, Enum):
    """
    12 Semantic Shot Relationships (R4).
    Governs cinematographic grammar and transitions between adjacent shots.
    """
    CONTINUATION = "CONTINUATION"
    CONTRAST = "CONTRAST"
    CAUSE_TO_EFFECT = "CAUSE_TO_EFFECT"
    QUESTION_TO_ANSWER = "QUESTION_TO_ANSWER"
    DETAIL_TO_CONTEXT = "DETAIL_TO_CONTEXT"
    CONTEXT_TO_DETAIL = "CONTEXT_TO_DETAIL"
    BEFORE_TO_AFTER = "BEFORE_TO_AFTER"
    EXPECTATION_TO_SUBVERSION = "EXPECTATION_TO_SUBVERSION"
    OBJECT_TO_PERSON = "OBJECT_TO_PERSON"
    PERSON_TO_CONSEQUENCE = "PERSON_TO_CONSEQUENCE"
    NUMBER_TO_SCALE = "NUMBER_TO_SCALE"
    EVIDENCE_TO_REVEAL = "EVIDENCE_TO_REVEAL"


# Mapping for normalizing legacy visual job names to canonical 20 VisualJob enums
LEGACY_VISUAL_JOB_MAP: Dict[str, str] = {
    "SHOW_LOCATION": "ESTABLISH_WORLD",
    "ESTABLISH_ENVIRONMENT": "ESTABLISH_WORLD",
    "SHOW_PERSON": "INTRODUCE_CHARACTER",
    "SHOW_OBJECT": "INTRODUCE_OBJECT",
    "SHOW_ACTION": "RECONSTRUCT_EVENT",
    "SHOW_EVIDENCE": "SHOW_EVIDENCE",
    "EXPLAIN_MECHANISM": "VISUALIZE_ABSTRACT_CONCEPT",
    "EXPLAIN_PROCESS": "VISUALIZE_ABSTRACT_CONCEPT",
    "COMPARE": "SHOW_COMPARISON",
    "VISUALIZE_NUMBER": "SHOW_SCALE",
    "SHOW_SCALE": "SHOW_SCALE",
    "SHOW_TIME": "ESTABLISH_WORLD",
    "CREATE_TENSION": "ESCALATE",
    "CREATE_MYSTERY": "BUILD_MYSTERY",
    "REVEAL_INFORMATION": "REVEAL",
    "TRANSITION": "INTERRUPT",
}


# ============================================================================
# 2. Deep Investigative Research Models (R1)
# ============================================================================

class EvidenceItem(BaseModel):
    title: str = Field(..., description="Name or title of the evidence artifact")
    evidence_type: str = Field(
        ..., 
        description="Physical or digital category of evidence (e.g. 'document', 'telex', 'log', 'photo', 'memo', 'court_filing', 'ledger', 'manifest', 'contract', 'financial_record')"
    )
    description: str = Field(..., description="Specific detail and contents of this evidence item")
    source_reference: Optional[str] = Field(None, description="Authentic institution, archive, or publication origin")
    visual_cue: str = Field(..., description="How this item should look when displayed on screen")


class NumberItem(BaseModel):
    raw_value: str = Field(..., description="The exact number or statistic, e.g. '$81,000,000', '11:47 AM', '49.4%'")
    metric_label: str = Field(..., description="What the number represents")
    visual_treatment: str = Field(
        default="typographic_impact", 
        description="Visual display technique for kinetic motion graphics ('odometer_counter', 'typographic_impact', 'split_comparison', 'callout_badge', 'data_stream')"
    )
    editorial_context: str = Field(..., description="Why this number is dramatic or pivotal")


class PersonAnchor(BaseModel):
    name: str = Field(..., description="Full name or alias of the person")
    role: str = Field(..., description="Role in the narrative (e.g., 'Lead Investigator', 'Rogue Trader', 'Whistleblower', 'CEO')")
    significance: str = Field(..., description="Why their actions matter to the central conflict")
    visual_description: Optional[str] = Field(None, description="Physical appearance or archival visual description")


class TurningPointItem(BaseModel):
    timeframe: str = Field(..., description="When the inflection point occurred (date, year, or phase)")
    event: str = Field(..., description="What happened")
    consequence: str = Field(..., description="How the trajectory irrevocably shifted")


class MajorRevealItem(BaseModel):
    phase: Union[NarrativeIntent, str] = Field(
        default=NarrativeIntent.REVELATION, 
        description="Narrative phase where reveal occurs (e.g., 'FIRST_DISCOVERY', 'REVELATION', 'DEEPER_REVELATION', 'FINAL_CONTRADICTION', 'PAYOFF')"
    )
    revelation: str = Field(..., description="The hidden truth revealed to the audience")
    evidence_backing: str = Field(..., description="Which evidence item or data proves this reveal")

    @field_validator("phase", mode="before")
    @classmethod
    def normalize_phase(cls, v):
        if isinstance(v, str):
            v_up = v.strip().upper()
            if v_up in NarrativeIntent.__members__:
                return NarrativeIntent[v_up]
        return v


class DocumentaryResearchPackage(BaseModel):
    """
    Complete 24-field Deep Investigative Research Package (R1).
    Produced by ResearcherAgent to anchor all subsequent narrative and visual directing.
    """
    topic: str = Field(..., description="The central investigative subject")
    central_question: str = Field(..., description="The core investigative mystery or inquiry driving the documentary")
    documentary_thesis: str = Field(..., description="The editorial thesis or core argument of the film")
    central_contradiction: str = Field(..., description="The core paradox or contradiction at the heart of the story")
    audience_initial_belief: str = Field(..., description="What the general audience initially assumes before watching")
    what_the_audience_thinks_is_true: str = Field(..., description="The conventional narrative or public misconception")
    what_is_actually_more_complicated: str = Field(..., description="The hidden, nuanced, or systemic reality uncovered by investigation")
    protagonist_or_human_anchor: str = Field(..., description="The central human figure(s) grounding the story")
    antagonistic_force_or_system: str = Field(..., description="The opposing force, system, institution, or antagonist")
    stakes: str = Field(..., description="What was lost, risked, or transformed; universal human consequences")
    historical_context: str = Field(..., description="The era, geopolitical/economic backdrop, and preconditions")
    turning_points: List[TurningPointItem] = Field(default_factory=list, description="Key chronological inflection points")
    major_reveals: List[MajorRevealItem] = Field(default_factory=list, description="Major revelations drip-fed across the story")
    final_payoff: str = Field(..., description="The philosophical or moral resolution and lasting consequence")
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="Specific documents, telexes, logs, photos, or files")
    people: List[PersonAnchor] = Field(default_factory=list, description="Key individuals involved")
    locations: List[str] = Field(default_factory=list, description="Specific real-world locations")
    physical_objects: List[str] = Field(default_factory=list, description="Tangible artifacts and physical props")
    numbers: List[NumberItem] = Field(default_factory=list, description="Key statistics with visual experience treatments")
    dates: List[str] = Field(default_factory=list, description="Critical chronological dates")
    archival_opportunities: List[str] = Field(default_factory=list, description="Authentic historical footage and photo opportunities")
    reconstruction_opportunities: List[str] = Field(default_factory=list, description="Cinematic AI reconstruction and reenactment opportunities")
    motion_graphic_opportunities: List[str] = Field(default_factory=list, description="Data flows, maps, timelines, and network diagrams")
    visual_motifs: List[str] = Field(default_factory=list, description="Recurring visual symbols to escalate across chapters")
    ending_image_opportunity: str = Field(..., description="A final memorable lingering image for the documentary climax")


# ============================================================================
# 3. Macro Narrative & Documentary Vision Models (R2)
# ============================================================================

class HookStrategy(BaseModel):
    """
    Hook Engine Configuration (R2).
    Enforces anti-context / immediate anomaly presentation in opening 20-30s.
    """
    hook_type: Literal["QUESTION", "CONTRADICTION", "SHOCK", "MYSTERY", "VISUAL_ANOMALY"] = Field(
        default="CONTRADICTION", 
        description="The psychological hook category for the opening 20-30s"
    )
    target_duration_seconds: float = Field(
        default=25.0, 
        description="Strict 20-30 second window before revealing context"
    )
    anomaly_description: str = Field(
        ..., 
        description="The specific shock, paradox, or visual anomaly presented immediately"
    )
    withholding_element: str = Field(
        ..., 
        description="The background context/biography deliberately withheld during the hook"
    )
    opening_visual_cue: str = Field(
        ..., 
        description="The exact opening visual frame"
    )

    @field_validator("hook_type", mode="before")
    @classmethod
    def normalize_hook_type(cls, v):
        if isinstance(v, str):
            v_up = v.strip().upper()
            allowed = {"QUESTION", "CONTRADICTION", "SHOCK", "MYSTERY", "VISUAL_ANOMALY"}
            if v_up in allowed:
                return v_up
        return "CONTRADICTION"


class NarrativePhasePlan(BaseModel):
    """
    Macro-narrative plan across the 11 canonical phases (R2).
    """
    phase: Union[NarrativeIntent, str] = Field(..., description="One of the 11 Macro Narrative Arc phases")
    target_beat_index: int = Field(default=0, description="Sequential beat order (0-indexed)")
    narrative_goal: str = Field(..., description="Editorial objective of this phase")
    attention_target: float = Field(default=0.7, ge=0.0, le=1.0, description="Target attention curve (0.0 - 1.0)")
    key_evidence_or_reveal: Optional[str] = Field(None, description="Evidence or reveal tied to this phase")

    @field_validator("phase", mode="before")
    @classmethod
    def normalize_phase(cls, v):
        if isinstance(v, str):
            v_up = v.strip().upper()
            if v_up in NarrativeIntent.__members__:
                return NarrativeIntent[v_up]
        return v


class MiniArcPlan(BaseModel):
    """
    30-90s Mini-Arc Structural Plan (R2).
    Cycles through SETUP -> BUILD -> COMPLICATION -> REVEAL -> CONSEQUENCE.
    """
    beat_id: str = Field(..., description="Associated story beat ID")
    time_window: str = Field(default="0:00 - 0:45", description="30-90 second window label (e.g., '0:00 - 0:45')")
    setup: str = Field(..., description="Initial premise of the mini-arc")
    build: str = Field(..., description="Rising tension or investigation")
    complication: str = Field(..., description="Unexpected obstacle, friction, or anomaly")
    reveal: str = Field(..., description="The payoff or discovery of the mini-arc")
    consequence: str = Field(..., description="The aftermath transitioning into the next beat")


class DocumentaryVision(BaseModel):
    """
    Overarching Documentary Vision (R2).
    Formulated by DirectorAgent before outline and scene writing commences.
    """
    topic: str = Field(..., description="Documentary topic")
    core_premise: str = Field(..., description="Directorial thesis and thematic focus")
    central_question: str = Field(..., description="The central investigative inquiry")
    documentary_thesis: str = Field(..., description="Editorial argument")
    central_contradiction: str = Field(..., description="The central paradox")
    hook_strategy: HookStrategy = Field(..., description="Opening 20-30s hook execution plan")
    macro_narrative_arc: List[NarrativePhasePlan] = Field(default_factory=list, description="Full 11-phase macro arc plan")
    mini_arcs: List[MiniArcPlan] = Field(default_factory=list, description="30-90s mini-arc structural plans")
    visual_motifs: List[str] = Field(default_factory=list, description="Recurring visual motifs to track across chapters")
    ending_image: str = Field(..., description="The climactic lingering image")
    pacing_and_restraint: str = Field(
        default="Enforce deliberate static holds and strategic silence across reveals",
        description="Pacing curve and static hold / silence rules"
    )
    style_profile: str = Field(default="DOCUMENTARY_INVESTIGATIVE", description="Look Bible style profile name")


# ============================================================================
# 4. Visual Sequence Planning Models (R3)
# ============================================================================

class VisualSequencePlan(BaseModel):
    """
    Visual Sequence Plan (R3).
    Formulated by VisualSequenceDirector per beat before individual shot decomposition.
    Enforces the Anti-Literal Rule, Mute Test, and 4 Quality Change Metrics.
    """
    intention: str = Field(..., description="Editorial intention of the visual sequence")
    visual_argument: str = Field(..., description="Core visual dialectic/argument (e.g., 'industry_value_growth vs animator_wage_stagnation')")
    withholding_strategy: str = Field(..., description="Strategy for withholding information to build anticipation")
    memorable_image: str = Field(..., description="Distinctive key visual anchor shot representing the central idea")
    sequence_ending_statement: str = Field(..., description="Final visual statement transitioning into the next beat")
    information_change: float = Field(default=0.7, ge=0.0, le=1.0, description="Rate of new visual information introduced (0.0 - 1.0)")
    emotional_change: float = Field(default=0.6, ge=0.0, le=1.0, description="Shift in emotional tone/tension (0.0 - 1.0)")
    visual_change: float = Field(default=0.8, ge=0.0, le=1.0, description="Diversity of visual worlds and framing (0.0 - 1.0)")
    scale_change: float = Field(default=0.5, ge=0.0, le=1.0, description="Progression of scale: micro to macro or macro to micro (0.0 - 1.0)")


# ============================================================================
# 5. Core Video, Metadata & Shot Models (R4, R5, R7)
# ============================================================================

class VisualBible(BaseModel):
    era: str = Field(..., description="The primary time period (e.g., '1965', 'Late 19th Century')")
    locations: List[str] = Field(..., description="Key geographic locations featured in the story")
    lighting: str = Field(..., description="Lighting style (e.g., 'low-key, cold, cinematic')")
    color_language: str = Field(..., description="Color grading (e.g., 'teal_orange, bleak', 'warm archival')")
    film_texture: str = Field(..., description="Texture (e.g., 'subtle grain, 35mm', 'clean digital')")

class ProjectMeta(BaseModel):
    topic: str = Field(..., description="The main topic of the documentary")
    genre: str = Field(default="documentary", description="Genre style")
    style_profile: Optional[str] = Field(default="DOCUMENTARY_INVESTIGATIVE", description="Look Bible and directorial style profile")
    language: str = Field(default="hindi", description="Language of the voiceover")
    visual_bible: VisualBible = Field(..., description="Global visual style guidelines")

class HighlightMetadata(BaseModel):
    keyword: str = Field(..., description="The exact word(s) to highlight in the text_overlay")
    style: Literal["marker", "underline", "glow", "box"] = Field(default="marker")
    importance: Literal["low", "medium", "high"] = Field(default="medium")

class ContinuityMetadata(BaseModel):
    group_id: str = Field(..., description="ID linking shots that occur in the same continuous scene")
    characters: List[str] = Field(default_factory=list, description="Characters present in the shot")
    character_id: Optional[str] = Field(None, description="Unique ID for recurring character tracking")
    location: str = Field(..., description="Specific location for this shot")
    environment: str = Field(..., description="Specific environment details (e.g., 'dimly lit bunker')")
    time_period: str = Field(..., description="Time period for the shot")
    start_year: Optional[int] = Field(None, description="Start year of the era (e.g., 2008)")
    end_year: Optional[int] = Field(None, description="End year of the era (e.g., 2012)")
    technology_level: Optional[str] = Field(None, description="Allowed tech level (e.g., 'no smartphones', '1990s tech')")
    weather: Optional[str] = Field(None, description="Weather conditions if applicable")
    lighting: str = Field(..., description="Specific lighting for this shot")

class AssetMetadata(BaseModel):
    source: Optional[str] = Field(None, description="Source of the asset (ai, pexels, archival, fallback)")
    path: Optional[str] = Field(None, description="Path to the generated or downloaded asset")
    status: Optional[str] = Field("pending", description="Status of asset generation (pending, success, failed)")
    fallback_used: bool = Field(False, description="Whether a fallback had to be used")
    fallback_type: Optional[str] = Field(None, description="The type of fallback used if any")

class EditorialEvent(BaseModel):
    type: Literal["SFX", "MUSIC_CHANGE", "MUSIC_DUCK", "GRAPHIC", "TEXT_REVEAL", "HIGHLIGHT", "COLOR_SHIFT", "OVERLAY", "CUT", "HARD_CUT", "DISSOLVE", "SILENCE", "IMPACT", "ZOOM_EMPHASIS", "MAP_REVEAL", "DOCUMENT_REVEAL", "NUMBER_REVEAL", "ARCHIVE_INSERT", "REACTION_INSERT"] = Field(..., description="Type of editorial event")
    cue: str = Field(..., description="Specific preset, asset name, or text to display")
    timing_percent: Optional[float] = Field(None, description="Percentage (0 to 100) through the shot when this event occurs")
    intensity: Optional[float] = Field(None, description="Intensity of the event (0.0 to 1.0)")
    duration: Optional[float] = Field(None, description="Duration in seconds if applicable")
    reason: Optional[str] = Field(None, description="Editorial reason for this event (important for QC)")

class Shot(BaseModel):
    """
    The individual cinematic shot unit.
    Embeds 20 Visual Jobs, 12 Shot Relationships, and 7-Dimensional Contrast parameters.
    """
    shot_id: str = Field(..., description="Unique ID for this shot (e.g., 'n001_s001')")
    duration_mode: Literal["ratio", "fixed"] = Field(default="ratio", description="Whether duration is calculated via ratio of parent block or a fixed seconds count")
    duration_ratio: float = Field(default=1.0, description="If ratio mode, proportion of the parent narration block this shot occupies (0.0 to 1.0)")
    duration_seconds: Optional[float] = Field(None, description="If fixed mode, exact duration in seconds")
    
    shot_role: Literal["ESTABLISHING", "ACTION", "REACTION", "DETAIL", "INSERT", "EVIDENCE", "EXPLANATION", "TRANSITION", "REVEAL", "HOLD"] = Field(
        default="EXPLANATION", description="The grammatical role of this shot"
    )
    asset_provenance: Literal[
        "AUTHENTIC_PHOTO", "ARCHIVAL_FOOTAGE", "DOCUMENT", "STOCK", 
        "AI_RECONSTRUCTION", "AI_ILLUSTRATION", "MOTION_GRAPHIC", "SEMANTIC_FALLBACK"
    ] = Field(default="STOCK", description="The required provenance of the visual")
    
    shot_size: Literal["extreme_wide", "wide", "medium", "medium_close", "close", "extreme_close", "N/A"] = Field(
        default="N/A", description="Camera shot size. Do NOT use N/A unless it's a motion graphic."
    )
    camera_angle: Optional[str] = Field(None, description="Camera angle (e.g., eye_level, low_angle, overhead_shot, high_angle, dutch_angle)")
    lens: Optional[str] = Field(None, description="Lens type (e.g., wide_angle_lens, telephoto_lens, standard_lens, macro_lens)")
    composition: Optional[str] = Field(None, description="Composition rule (e.g., rule_of_thirds, center_framed, golden_ratio, leading_lines)")
    foreground: Optional[str] = Field(None, description="What is in the foreground")
    background: Optional[str] = Field(None, description="What is in the background")
    subject_position: Optional[str] = Field(None, description="Position of the main subject")
    depth: Optional[str] = Field(None, description="Depth of field (e.g., shallow, deep)")
    
    source_name: Optional[str] = Field(None, description="Source of evidence (e.g., 'The New York Times', 'Court Document')")
    source_url: Optional[str] = Field(None, description="URL or reference for evidence")
    source_date: Optional[str] = Field(None, description="Date of the evidence")
    confidence: Optional[float] = Field(None, description="Confidence in authenticity of evidence (0.0 to 1.0)")
    generation_priority: float = Field(default=0.5, description="Priority for expensive AI generation (0.0 to 1.0). AI video requires >= 0.8.")
    
    visual_job: Union[VisualJob, str] = Field(
        default=VisualJob.ESTABLISH_WORLD, 
        description="One of 20 Editorial Visual Jobs"
    )
    shot_relationship: Optional[Union[ShotRelationship, str]] = Field(
        default=None, 
        description="One of 12 Shot Relationships to previous shot"
    )
    
    visual_type: Literal["motion_graphics", "ai_video", "real_photo", "ai_image", "broll_video", "text_stat"] = Field(
        ..., description="Type of visual to generate"
    )
    fallback_type: Literal[
        "ClassifiedFile", "Newspaper", "ArchivalDocument", "EvidenceBoard", 
        "MapFallback", "PhotoWall", "Timeline", "CinematicText", 
        "PortraitCard", "TechnicalDiagram", "AnimatedDiagram"
    ] = Field(..., description="React fallback component if generation fails or is specifically requested")
    
    visual_description: str = Field(..., description="What happens visually in the shot")
    visual_query: str = Field(..., description="Structured search query for stock footage. Format: [SUBJECT] + [ACTION] + [LOCATION] + [ERA].")
    ai_prompt: str = Field(..., description="Exact prompt for image/video generation.")
    camera_motion: str = Field(default="slow_push_in", description="Camera movement (e.g., slow_push_in, pan_right, pan_left, dolly_in, static)")
    motion_intensity: float = Field(default=0.3, description="Speed/intensity of the camera motion (0.1 to 1.0)")
    transition_in: Literal["hard_cut", "fade", "dissolve"] = Field(default="hard_cut", description="Transition into this shot")
    
    text_overlay: Optional[str] = Field(None, description="Text to display on screen (e.g., location names, dates, quotes). Null if none.")
    highlight: Optional[HighlightMetadata] = Field(None, description="Highlight instructions for the text_overlay")
    sound_design: Optional[str] = Field(None, description="SFX cue (e.g., 'subtle_whoosh', 'paper_rustle', 'deep_impact', 'wind_howl')")
    lut_filter: Optional[str] = Field(None, description="CSS color grade filter (e.g., 'sepia', 'vintage_film', 'noir', 'high_contrast')")
    overlay: Optional[str] = Field(None, description="Visual overlay effect (e.g., 'film_grain', 'vhs_glitch', 'dust_scratches', 'light_leaks')")
    
    cut_reason: str = Field(..., description="Why are we cutting to this shot? Must be highly specific (e.g. 'reveal_financial_consequence', 'bridge_luxury_to_collapse').")
    visual_importance: float = Field(default=0.5, description="Scale of visual emphasis (0.0 to 1.0). High means intense motion/sound.")
    visual_density: float = Field(default=0.5, description="Visual complexity score from 0.0 minimal breathing room to 1.0 maximum density")
    visual_intent: Optional[str] = Field(default=None, description="The abstract visual storytelling intent")
    is_restrained: bool = Field(default=False, description="Whether this shot enforces cinematic restraint (no motion/no sfx)")
    director_score: Optional[float] = Field(default=None, description="Director quality score from 0.0 to 10.0")
    
    continuity: ContinuityMetadata = Field(..., description="Continuity constraints for consistent generation")
    asset: AssetMetadata = Field(default_factory=AssetMetadata, description="Asset tracking metadata (populated during pipeline execution)")
    editorial_events: Optional[List[EditorialEvent]] = Field(None, description="Editorial events (SFX, Graphics, Color shifts) tied to narrative punctuation")

    @field_validator("visual_job", mode="before")
    @classmethod
    def normalize_visual_job(cls, v):
        if v is None:
            return VisualJob.ESTABLISH_WORLD
        if isinstance(v, VisualJob):
            return v
        if isinstance(v, str):
            v_clean = v.strip().upper()
            if v_clean in VisualJob.__members__:
                return VisualJob[v_clean]
            if v_clean in LEGACY_VISUAL_JOB_MAP:
                return VisualJob[LEGACY_VISUAL_JOB_MAP[v_clean]]
        return v

    @field_validator("shot_relationship", mode="before")
    @classmethod
    def normalize_shot_relationship(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, ShotRelationship):
            return v
        if isinstance(v, str):
            v_clean = v.strip().upper()
            if v_clean in ShotRelationship.__members__:
                return ShotRelationship[v_clean]
        return v


class StrategicSilence(BaseModel):
    duration_seconds: float = Field(default=0.0, description="Seconds of silence to add")
    position: Literal["start", "end"] = Field(default="end", description="Where the silence occurs relative to the voiceover")
    ambient_level: int = Field(default=-35, description="Ambient noise dB level during silence")
    visual_behavior: str = Field(default="continue", description="What visually happens during silence (e.g., 'hold_frame', 'slow_pan', 'fade_to_black')")


class AudioMetadata(BaseModel):
    music_energy: float = Field(default=0.5, description="Energy of the background music (0.0 to 1.0)")
    music_duck_amount: int = Field(default=0, description="Amount to duck music by in dB")


class NarrationBlock(BaseModel):
    """
    Narration Block representing continuous TTS voiceover and its decomposed shots.
    """
    block_id: str = Field(..., description="Unique ID for this narration block (e.g., 'n001')")
    voiceover: str = Field(..., description="The actual text to be spoken by TTS")
    caption: str = Field(..., description="The caption/translation for on-screen subtitles")
    
    # Execution metadata (populated later by pipeline)
    audio_file: Optional[str] = Field(None, description="Path to the generated TTS file")
    actual_voice_duration: Optional[float] = Field(None, description="Measured duration of the TTS file in seconds")
    total_block_duration: Optional[float] = Field(None, description="Calculated total duration including silence")
    alignment_status: Optional[Literal["PASS", "PARTIAL", "FAILED"]] = Field(None, description="Status of word-level forced alignment")
    
    duration_hint: float = Field(..., description="Estimated duration in seconds (planning only, do NOT rely on for final timing)")
    
    strategic_silence: StrategicSilence = Field(default_factory=StrategicSilence, description="Silence padding at timeline level")
    audio_metadata: AudioMetadata = Field(default_factory=AudioMetadata, description="Music and ducking levels")
    mini_arc_phase: Optional[Union[MiniArcPhase, str]] = Field(default=None, description="Phase within the 30-90s mini-arc")
    
    shots: List[Shot] = Field(..., description="Visual shots that occur during this narration block")

    @field_validator("mini_arc_phase", mode="before")
    @classmethod
    def normalize_mini_arc_phase(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, MiniArcPhase):
            return v
        if isinstance(v, str):
            v_clean = v.strip().upper()
            if v_clean in MiniArcPhase.__members__:
                return MiniArcPhase[v_clean]
        return v


class TimeContext(BaseModel):
    year: str = Field(..., description="The year or era of this beat (e.g., '2016', '1990s', 'Present Day')")
    mode: Literal["historical", "present_day", "future_projection"] = Field(..., description="The temporal mode")
    location: str = Field(..., description="The primary location for this beat")
    transition_reason: Optional[str] = Field(None, description="Mandatory if transitioning time periods. Why did we jump in time?")


class StoryBeat(BaseModel):
    """
    Story Beat container for macro-narrative phases and sequence planning.
    """
    beat_id: str = Field(..., description="Unique ID for this story beat (e.g., 'b001')")
    time_context: TimeContext = Field(..., description="The global time and location context for this beat")
    narrative_intent: Union[NarrativeIntent, str] = Field(..., description="The 11-phase macro narrative intent or legacy intent")
    mini_arc_phase: Optional[Union[MiniArcPhase, str]] = Field(default=None, description="Phase within the 30-90s mini-arc")
    visual_sequence_plan: Optional[VisualSequencePlan] = Field(default=None, description="Visual Sequence Plan formulated for this beat")
    description: str = Field(..., description="Description of the story beat")
    attention_intensity: float = Field(default=0.5, description="Expected audience attention curve intensity (0.0 to 1.0). Hook=0.8, Revelation=1.0")
    chapter_color_language: Optional[str] = Field(None, description="Consistent LUT/Color treatment for this entire chapter (e.g., 'archival', 'cinematic', 'high_contrast')")
    narration_blocks: List[NarrationBlock] = Field(..., description="Narration blocks within this story beat")

    @field_validator("narrative_intent", mode="before")
    @classmethod
    def normalize_narrative_intent(cls, v):
        if v is None:
            return NarrativeIntent.EXPLANATION
        if isinstance(v, NarrativeIntent):
            return v
        if isinstance(v, str):
            v_clean = v.strip().upper()
            if v_clean in NarrativeIntent.__members__:
                return NarrativeIntent[v_clean]
            alias_map = {
                "THE_PROBLEM": "COMPLICATION",
                "PROBLEM": "COMPLICATION",
                "SETUP": "CONTEXT",
                "DISCOVERY": "FIRST_DISCOVERY",
                "AFTERMATH": "CONSEQUENCE",
                "LOCATION": "LOCATION_ESTABLISH",
                "BACKGROUND": "CONTEXT",
                "INTRODUCTION": "HOOK",
                "CLIMAX": "REVELATION",
            }
            if v_clean in alias_map:
                return NarrativeIntent[alias_map[v_clean]]
        return v

    @field_validator("mini_arc_phase", mode="before")
    @classmethod
    def normalize_mini_arc_phase(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, MiniArcPhase):
            return v
        if isinstance(v, str):
            v_clean = v.strip().upper()
            if v_clean in MiniArcPhase.__members__:
                return MiniArcPhase[v_clean]
        return v


class ScriptManifest(BaseModel):
    """
    Master Script Manifest (Schema Version 2.0).
    Holds the complete documentary metadata, research package, vision, and sequence beats.
    """
    schema_version: str = Field(default="2.0", description="Version of the script schema")
    project_meta: ProjectMeta = Field(..., description="Project metadata")
    documentary_vision: Optional[DocumentaryVision] = Field(default=None, description="Overarching documentary vision and hook strategy")
    research_package: Optional[DocumentaryResearchPackage] = Field(default=None, description="Deep investigative research package")
    story_beats: List[StoryBeat] = Field(..., description="The story beats containing narration and shots")
