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
# 4. Visual Sequence Planning Models (R3 & Phase 2)
# ============================================================================

class AssetClass(str, Enum):
    EVIDENCE = "EVIDENCE"
    ARCHIVAL = "ARCHIVAL"
    REAL_WORLD = "REAL_WORLD"
    RECONSTRUCTION = "RECONSTRUCTION"
    GENERATED_IMAGE = "GENERATED_IMAGE"
    GENERATED_VIDEO = "GENERATED_VIDEO"
    MOTION_GRAPHIC = "MOTION_GRAPHIC"
    MAP = "MAP"
    DOCUMENT = "DOCUMENT"
    PHOTOGRAPH = "PHOTOGRAPH"
    TYPOGRAPHY = "TYPOGRAPHY"
    BLACK_SCREEN = "BLACK_SCREEN"

class EvidenceTreatment(str, Enum):
    FULL_PAGE = "FULL_PAGE"
    HEADLINE_FOCUS = "HEADLINE_FOCUS"
    DETAIL_CROP = "DETAIL_CROP"
    HIGHLIGHT_LINE = "HIGHLIGHT_LINE"
    QUOTE_FOCUS = "QUOTE_FOCUS"
    TIMESTAMP_FOCUS = "TIMESTAMP_FOCUS"
    SOURCE_COMPARISON = "SOURCE_COMPARISON"
    PHOTO_ANNOTATION = "PHOTO_ANNOTATION"
    SIGNATURE_FOCUS = "SIGNATURE_FOCUS"
    DATE_FOCUS = "DATE_FOCUS"
    DOCUMENT_STACK = "DOCUMENT_STACK"

class CameraLanguage(str, Enum):
    SLOW_PUSH = "SLOW_PUSH"
    PULL_BACK = "PULL_BACK"
    LATERAL_MOVE = "LATERAL_MOVE"
    LOCKED_OFF = "LOCKED_OFF"
    HANDHELD = "HANDHELD"
    STATIC_CLOSE = "STATIC_CLOSE"
    ORBIT = "ORBIT"

class GraphicType(str, Enum):
    MAP = "MAP"
    TIMELINE = "TIMELINE"
    COMPARISON = "COMPARISON"
    FLOW = "FLOW"
    NETWORK = "NETWORK"
    CAUSAL_GRAPH = "CAUSAL_GRAPH"
    DATA_TYPOGRAPHY = "DATA_TYPOGRAPHY"

class ReconstructionPlan(BaseModel):
    environment: str = Field(..., description="The setting environment")
    time_period: str = Field(..., description="The time period")
    location: str = Field(..., description="The location")
    characters: List[str] = Field(..., description="Characters present")
    objects: List[str] = Field(..., description="Key objects in the scene")
    action: str = Field(..., description="The specific action happening")
    camera: str = Field(..., description="Camera placement/movement")
    lighting: str = Field(..., description="Lighting description")
    continuity: str = Field(..., description="Continuity rules")

class GraphicDecision(BaseModel):
    graphic_type: GraphicType = Field(..., description="Type of graphic")
    information_goal: str = Field(..., description="What the graphic visualizes")

class VisualInformationTarget(BaseModel):
    knowledge_before: str = Field(..., description="What the audience knows before")
    knowledge_after: str = Field(..., description="What the audience learns here")
    visualizable_concept: str = Field(..., description="The core visual concept")

class NarrativeMicroBeat(BaseModel):
    text: str = Field(..., description="The voiceover text slice")
    micro_intent: str = Field(..., description="What this slice accomplishes")

class SequenceVerificationResult(BaseModel):
    passed: bool = Field(default=False)
    information_gain_score: float = Field(default=0.0)
    redundancy_penalty: float = Field(default=0.0)
    issues: List[str] = Field(default_factory=list)

class VisualSequencePlan(BaseModel):
    """
    Visual Sequence Plan (R3).
    Formulated by VisualSequenceDirector per beat before individual shot decomposition.
    """
    intention: str = Field(..., description="Editorial intention of the visual sequence")
    visual_argument: str = Field(..., description="Core visual dialectic/argument")
    withholding_strategy: str = Field(..., description="Strategy for withholding information")
    memorable_image: str = Field(..., description="Distinctive key visual anchor shot")
    sequence_ending_statement: str = Field(..., description="Final visual statement")
    information_change: float = Field(default=0.7, ge=0.0, le=1.0)
    emotional_change: float = Field(default=0.6, ge=0.0, le=1.0)
    visual_change: float = Field(default=0.8, ge=0.0, le=1.0)
    scale_change: float = Field(default=0.5, ge=0.0, le=1.0)
    micro_beats: List[NarrativeMicroBeat] = Field(default_factory=list)



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

# ============================================================================
# YouTube Discovery + Authorized Media Layer
# ============================================================================

class YouTubeAssetState(str, Enum):
    """Three-state classification for every YouTube discovery."""
    REFERENCE = "YOUTUBE_REFERENCE"      # Discovery/research only. MUST NOT enter final render.
    AUTHORIZED = "YOUTUBE_AUTHORIZED"    # Explicitly licensed. May enter final pipeline.
    UNUSABLE = "YOUTUBE_UNUSABLE"         # Metadata kept for research, media acquisition blocked.

class YouTubeDiscovery(BaseModel):
    """A YouTube video discovered during claim-driven research."""
    youtube_video_id: str = Field(..., description="YouTube video ID (e.g. 'dQw4w9WgXcQ')")
    channel_id: str = Field(..., description="YouTube channel ID")
    channel_name: str = Field(..., description="YouTube channel display name")
    title: str = Field(..., description="Video title")
    url: str = Field(..., description="Full YouTube URL")
    description: Optional[str] = Field(None, description="Video description snippet")
    publication_date: Optional[str] = Field(None, description="Video publication date (ISO 8601)")
    duration_seconds: Optional[float] = Field(None, description="Video duration in seconds")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    discovery_timestamp: str = Field(..., description="ISO 8601 timestamp when we discovered this video")
    linked_claim_id: Optional[str] = Field(None, description="ID of the claim this discovery supports")
    source_role: YouTubeAssetState = Field(default=YouTubeAssetState.REFERENCE, description="Asset state after rights resolution")
    rights_status: Literal[
        "unknown", "public_domain", "creative_commons", 
        "standard_youtube_license", "project_owned", "explicit_permission"
    ] = Field(default="unknown", description="Resolved rights status")
    authorization_reference: Optional[str] = Field(None, description="License doc, email, or ownership proof path")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Search relevance score")
    candidate_timestamps: Optional[List[str]] = Field(None, description="e.g. ['00:14:32-00:14:38']")
    visual_description: Optional[str] = Field(None, description="What the video visually contains")
    alternative_archive_query: Optional[str] = Field(None, description="Query to find rights-cleared version of this material")

class TrustedChannel(BaseModel):
    """A pre-approved YouTube channel for discovery or authorized media."""
    channel_id: str = Field(..., description="YouTube channel ID")
    channel_name: str = Field(..., description="Channel display name")
    institution: str = Field(..., description="e.g. 'NASA', 'National Archives'")
    trust_level: Literal["discovery_only", "authorized_media", "project_owned"] = Field(
        ..., description="Level of trust for this channel"
    )
    permitted_media_policy: Literal[
        "no_reuse", "creative_commons", "public_domain", 
        "fair_use_clips", "full_authorization"
    ] = Field(..., description="What media use is permitted")
    notes: Optional[str] = Field(None, description="Additional context about this channel's rights")

# ============================================================================
# Visual Requirement & Semantic Verification Layer
# ============================================================================

class HistoricalFidelity(str, Enum):
    """Degrees of historical fidelity required for a shot."""
    STRICT_ARCHIVAL = "STRICT_ARCHIVAL"                         # Authentic historical artifact / photo from the exact era
    ERA_ACCURATE = "ERA_ACCURATE"                               # Accurate depiction of the era, no modern anachronisms
    MODERN_RECONSTRUCTION_ALLOWED = "MODERN_RECONSTRUCTION_ALLOWED"  # AI reconstruction allowed, but must strictly preserve era appearance
    ABSTRACT = "ABSTRACT"                                       # Conceptual / symbolic / non-literal
    OPTIONAL = "OPTIONAL"                                       # Standard modern or timeless b-roll allowed

class VisualRequirement(BaseModel):
    """Normalized visual specification for a shot."""
    shot_id: str = Field(..., description="Unique ID of the shot this requirement governs")
    claim_id: Optional[str] = Field(None, description="Linked claim ID if applicable")
    visual_job: str = Field(..., description="Editorial visual job")
    subject_entity: Optional[str] = Field(None, description="Core entity/person required (e.g., 'Napoleon Bonaparte')")
    event: Optional[str] = Field(None, description="Specific historical/narrative event (e.g., 'Imperial Coronation')")
    location: Optional[str] = Field(None, description="Specific location required (e.g., 'Paris, France')")
    time_period: Optional[str] = Field(None, description="Era or period (e.g., '1804', '19th century')")
    date_range: Optional[str] = Field(None, description="Date or date range (e.g., '1804')")
    start_year: Optional[int] = Field(None, description="Start year of the era")
    end_year: Optional[int] = Field(None, description="End year of the era")
    required_objects: List[str] = Field(default_factory=list, description="Objects that MUST be present")
    forbidden_objects: List[str] = Field(default_factory=list, description="Objects strictly forbidden (anachronisms, mismatches)")
    visual_type: str = Field(..., description="Target visual type")
    evidence_required: bool = Field(default=False, description="Whether authentic archival evidence is required")
    provenance_required: Optional[str] = Field(None, description="Required provenance (e.g., 'AUTHENTIC_ARCHIVE')")
    historical_required: bool = Field(default=False, description="Whether historical accuracy is mandatory")
    historical_fidelity: HistoricalFidelity = Field(default=HistoricalFidelity.OPTIONAL, description="Degree of historical fidelity")
    visual_purpose: Optional[str] = Field(None, description="Editorial purpose of the visual")
    allowed_sources: List[str] = Field(default_factory=list, description="Allowed provider sources")
    unresolved_visual_requirement: bool = Field(default=False, description="Flagged true if no candidate met the requirement")

class VerificationResult(BaseModel):
    """Detailed score card from pixel and semantic verification."""
    candidate_id: str = Field(..., description="Candidate identifier")
    candidate_url_or_path: str = Field(..., description="URL or local path to candidate media")
    entity_match: float = Field(default=0.0, ge=0.0, le=1.0, description="Match score for subject entity (0..1)")
    event_match: float = Field(default=0.0, ge=0.0, le=1.0, description="Match score for event (0..1)")
    date_match: float = Field(default=0.0, ge=0.0, le=1.0, description="Match score for date/era (0..1)")
    location_match: float = Field(default=0.0, ge=0.0, le=1.0, description="Match score for location (0..1)")
    object_match: float = Field(default=0.0, ge=0.0, le=1.0, description="Match score for required objects (0..1)")
    visual_role_match: float = Field(default=0.0, ge=0.0, le=1.0, description="Match score for visual job/role (0..1)")
    evidence_match: float = Field(default=0.0, ge=0.0, le=1.0, description="Authentic evidence provenance match (0..1)")
    anachronism_risk: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk of anachronisms (0..1, high = reject)")
    unrelated_subject_risk: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk of unrelated subject/painting (0..1, high = reject)")
    overall_match: float = Field(default=0.0, ge=0.0, le=1.0, description="Deterministic overall match score (0..1)")
    passed: bool = Field(default=False, description="Whether the candidate passed all threshold gates")
    rejection_reasons: List[str] = Field(default_factory=list, description="Specific reasons for rejection if failed")

class Claim(BaseModel):
    claim_id: str = Field(..., description="Unique ID for this claim (e.g. 'claim_001')")
    text: str = Field(..., description="The factual assertion being made")
    claim_type: Literal[
        "historical_fact", "technical_detail", "statistical_claim", 
        "eyewitness_account", "official_verdict", "contradiction"
    ] = Field(default="historical_fact", description="Category of the claim")
    importance: float = Field(default=0.8, ge=0.0, le=1.0, description="Editorial importance weight (0.0 to 1.0)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Verification confidence (0.0 to 1.0)")
    evidence_required: bool = Field(default=True, description="Whether visual evidence must be shown for this claim")
    evidence_ids: List[str] = Field(default_factory=list, description="IDs of linked EvidenceAsset items")
    visual_strategy: Literal[
        "EVIDENCE_TO_RECONSTRUCTION", "RECONSTRUCTION_TO_EVIDENCE",
        "GRAPHIC_TO_EVIDENCE", "EVIDENCE_HOLD", "HUMAN_ANCHOR_TO_EVIDENCE",
        "EVIDENCE_TO_CONSEQUENCE"
    ] = Field(default="EVIDENCE_TO_RECONSTRUCTION", description="The editorial visual strategy for this claim")

class AssetMetadata(BaseModel):
    source: Optional[str] = Field(None, description="Source of the asset (ai, pexels, archival, youtube_authorized, fallback)")
    path: Optional[str] = Field(None, description="Path to the generated or downloaded asset")
    status: Optional[str] = Field("pending", description="Status of asset generation (pending, success, failed)")
    fallback_used: bool = Field(False, description="Whether a fallback had to be used")
    fallback_type: Optional[str] = Field(None, description="The type of fallback used if any")

class EvidenceAsset(AssetMetadata):
    id: Optional[str] = Field(None, description="Unique Evidence ID (e.g. 'ev_001')")
    claim_id: Optional[str] = Field(None, description="ID of the claim this evidence supports")
    source_name: str = Field(..., description="Archive, agency, or collection name (e.g. 'Soviet Air Defense Command')")
    source_type: Literal[
        "primary_source", "declassified_file", "news_archive", 
        "technical_manual", "official_log", "court_record"
    ] = Field(default="declassified_file", description="Type of archival source")
    publisher: Optional[str] = Field(None, description="Publisher or issuing body")
    title: Optional[str] = Field(None, description="Title of the document or record")
    url: Optional[str] = Field(None, description="URL or archival reference link")
    publication_date: Optional[str] = Field(None, description="Original publication or incident date")
    relevant_excerpt: Optional[str] = Field(None, description="Key excerpt or quote extracted from the evidence")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in authenticity (0.0 to 1.0)")
    capture_type: Literal[
        "document_scan", "article", "photograph", "screenshot", "quote", "diagram"
    ] = Field(default="document_scan", description="Format of the evidence capture")
    rights_status: Literal[
        "public_domain", "fair_use_documentary", "creative_commons", "restricted"
    ] = Field(default="public_domain", description="Legal / rights provenance")
    asset_path: Optional[str] = Field(None, description="Path to the evidence image/scan asset")
    visual_treatment: Literal[
        "document_inspection", "classified_reveal", "quote_highlight", 
        "article_clipping", "photo_pan"
    ] = Field(default="document_inspection", description="Remotion visual treatment style")
    # YouTube provenance (when evidence originates from YouTube discovery)
    youtube_video_id: Optional[str] = Field(None, description="YouTube video ID if sourced via YouTube")
    youtube_channel_id: Optional[str] = Field(None, description="YouTube channel ID")
    youtube_channel_name: Optional[str] = Field(None, description="YouTube channel name")
    youtube_asset_state: Optional[str] = Field(None, description="YOUTUBE_REFERENCE, YOUTUBE_AUTHORIZED, or YOUTUBE_UNUSABLE")

class EditorialEvent(BaseModel):
    type: Literal["SFX", "MUSIC_CHANGE", "MUSIC_DUCK", "GRAPHIC", "TEXT_REVEAL", "HIGHLIGHT", "COLOR_SHIFT", "OVERLAY", "CUT", "HARD_CUT", "DISSOLVE", "SILENCE", "IMPACT", "ZOOM_EMPHASIS", "MAP_REVEAL", "DOCUMENT_REVEAL", "NUMBER_REVEAL", "ARCHIVE_INSERT", "REACTION_INSERT"] = Field(..., description="Type of editorial event")
    cue: str = Field(..., description="Specific preset, asset name, or text to display")
    timing_percent: Optional[float] = Field(None, description="Percentage (0 to 100) through the shot when this event occurs")
    intensity: Optional[float] = Field(None, description="Intensity of the event (0.0 to 1.0)")
    duration: Optional[float] = Field(None, description="Duration in seconds if applicable")
    reason: Optional[str] = Field(None, description="Editorial reason for this event (important for QC)")

class CinematicSceneBlueprint(BaseModel):
    visual_style: Optional[str] = Field(None, description="Global visual style for this scene (e.g., '1970s archive', 'high-contrast tech')")
    camera_language: Optional[CameraLanguage] = Field(None, description="Dominant camera movement/language for the scene")
    lighting_language: Optional[str] = Field(None, description="Lighting style (e.g., 'high-contrast', 'motivated practical')")
    depth_strategy: Optional[str] = Field(None, description="Depth strategy (e.g., 'shallow focus', 'layered parallax')")
    transition_language: Optional[str] = Field(None, description="How the scene enters/exits (e.g., 'HARD_CUT', 'MATCH_CUT')")
    evidence_style: Optional[EvidenceTreatment] = Field(None, description="How evidence is treated visually in this scene")
    texture_language: Optional[str] = Field(None, description="Texture feeling (e.g., 'film grain', 'clean digital')")
    typography_style: Optional[str] = Field(None, description="Typography style (e.g., 'bold serif', 'minimalist sans')")
    graphics_style: Optional[str] = Field(None, description="Graphics style")
    sound_style: Optional[str] = Field(None, description="Sound design language (e.g., 'room tone heavy', 'subtle drones')")

class EditorialScene(BaseModel):
    """
    An editorial scene represents a conceptual segment of the documentary, structured around a specific claim.
    Now acts as the core orchestrator for Phase 2 visual planning.
    """
    scene_id: str = Field(..., description="Unique ID for this scene")
    cinematic_blueprint: Optional[CinematicSceneBlueprint] = Field(default_factory=CinematicSceneBlueprint, description="Cinematic rules for the entire scene")
    claim: Optional[Claim] = Field(None, description="The central claim being asserted and visually supported")
    strategic_silence_seconds: float = Field(default=0.0, description="Amount of room tone/silence to hold before or after TTS")
    
    scene_intent: str = Field(default="", description="Editorial intent of the scene")
    narrative_function: str = Field(default="", description="Narrative function (e.g. SETUP, REVEAL, ESCALATION)")
    viewer_emotion: str = Field(default="", description="The intended viewer emotion")
    viewer_question: str = Field(default="", description="The question placed in the viewer's mind")
    knowledge_before: str = Field(default="", description="What the audience knows before the scene")
    knowledge_after: str = Field(default="", description="What the audience learns after the scene")
    visual_argument: str = Field(default="", description="The core visual dialectic or argument")
    scene_world: str = Field(default="", description="The setting or conceptual world of the scene")
    human_anchor: str = Field(default="", description="The human subject anchoring the information")
    
    evidence_material: Optional[EvidenceTreatment] = Field(None, description="If evidence is used, how it's treated")
    reconstruction_material: Optional[ReconstructionPlan] = Field(None, description="If reconstruction, the exact plan")
    graphic_material: Optional[GraphicDecision] = Field(None, description="If graphic, the visualization decision")
    
    recurring_motif: Optional[str] = Field(None, description="Any recurring visual motif used")
    
    opening_visual: str = Field(default="", description="Opening shot description")
    development: str = Field(default="", description="Development shots description")
    reveal: str = Field(default="", description="The reveal visual description")
    consequence: str = Field(default="", description="The consequence visual description")
    closing_visual: str = Field(default="", description="Closing shot description")
    
class Shot(BaseModel):
    """
    The individual cinematic shot unit.
    Embeds 20 Visual Jobs, 12 Shot Relationships, and 7-Dimensional Contrast parameters.
    """
    shot_id: str = Field(..., description="Unique ID for this shot (e.g., 'n001_s001')")
    linked_claim_id: Optional[str] = Field(None, description="ID of the claim this shot supports")
    duration_mode: Literal["ratio", "fixed"] = Field(default="ratio", description="Whether duration is calculated via ratio of parent block or a fixed seconds count")
    duration_ratio: float = Field(default=1.0, description="If ratio mode, proportion of the parent narration block this shot occupies (0.0 to 1.0)")
    duration_seconds: Optional[float] = Field(None, description="If fixed mode, exact duration in seconds")
    
    shot_role: Literal["ESTABLISHING", "ACTION", "REACTION", "DETAIL", "INSERT", "EVIDENCE", "EXPLANATION", "TRANSITION", "REVEAL", "HOLD", "CONSEQUENCE"] = Field(
        default="EXPLANATION", description="The grammatical role of this shot"
    )
    asset_provenance: Literal[
        "AUTHENTIC_ARCHIVE", "HISTORICAL_DOCUMENT", "AUTHENTIC_PHOTO", 
        "AI_RECONSTRUCTION", "AI_ILLUSTRATION", "MOTION_GRAPHIC", "STOCK", 
        "EDITORIAL_TYPOGRAPHY", "SEMANTIC_FALLBACK", "DOCUMENT", "ARCHIVAL_FOOTAGE",
        "YOUTUBE_AUTHORIZED"
    ] = Field(default="STOCK", description="The required provenance of the visual")
    
    shot_size: Literal["extreme_wide", "wide", "medium", "medium_close", "close", "extreme_close", "N/A"] = Field(
        default="N/A", description="Camera shot size. Do NOT use N/A unless it's a motion graphic."
    )
    camera_angle: Optional[str] = Field(None, description="Camera angle (e.g., eye_level, low_angle, overhead_shot, high_angle, dutch_angle)")
    camera_movement: Optional[CameraLanguage] = Field(None, description="Specific camera movement for this shot (e.g., SLOW_PUSH, LATERAL_MOVE, LOCKED_OFF)")
    lens: Optional[str] = Field(None, description="Lens type (e.g., wide_angle_lens, telephoto_lens, standard_lens, macro_lens)")
    composition: Optional[str] = Field(None, description="Composition rule (e.g., negative space, leading lines, foreground obstruction)")
    evidence_treatment: Optional[EvidenceTreatment] = Field(None, description="If this is an evidence shot, how it is treated visually (e.g., HIGHLIGHT_LINE, DETAIL_CROP)")
    lighting: Optional[str] = Field(None, description="Lighting intent for this shot (e.g., focused directional light, softer motivated light)")
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
    
    visual_type: Literal[
        "EVIDENCE_DOCUMENT", "EVIDENCE_ARTICLE", "EVIDENCE_PHOTO", "EVIDENCE_SCREENSHOT", "EVIDENCE_QUOTE",
        "RECONSTRUCTION", "GENERATED_IMAGE", "GENERATED_VIDEO", "MOTION_GRAPHIC", "TYPOGRAPHY_REVEAL", "BLACK_HOLD",
        "motion_graphics", "ai_video", "real_photo", "ai_image", "broll_video", "text_stat", "evidence"
    ] = Field(
        ..., description="First-class visual type to render"
    )
    fallback_type: Literal[
        "ClassifiedFile", "Newspaper", "ArchivalDocument", "EvidenceBoard", 
        "MapFallback", "PhotoWall", "Timeline", "CinematicText", 
        "PortraitCard", "TechnicalDiagram", "AnimatedDiagram", "EvidenceCard"
    ] = Field(default="EvidenceCard", description="React fallback component if generation fails or is specifically requested")
    
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
    information_gain: float = Field(default=0.5, description="Information gained compared to previous shot (0.0 to 1.0)")
    relationship_to_previous: Optional[str] = Field(default=None, description="Relationship logic to previous shot")
    viewer_question: Optional[str] = Field(default=None, description="The question this shot leaves the viewer with")
    is_restrained: bool = Field(default=False, description="Whether this shot enforces cinematic restraint (no motion/no sfx)")
    director_score: Optional[float] = Field(default=None, description="Director quality score from 0.0 to 10.0")
    
    continuity: ContinuityMetadata = Field(..., description="Continuity constraints for consistent generation")
    asset: Union[EvidenceAsset, AssetMetadata] = Field(default_factory=AssetMetadata, description="Asset tracking metadata")
    editorial_events: Optional[List[EditorialEvent]] = Field(None, description="Editorial events (SFX, Graphics, Color shifts) tied to narrative punctuation")
    visual_requirement: Optional[VisualRequirement] = Field(None, description="Normalized visual requirement specification")
    verification_result: Optional[VerificationResult] = Field(None, description="Semantic and pixel verification audit result")

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
    cinematic_blueprint: Optional[CinematicSceneBlueprint] = Field(default_factory=CinematicSceneBlueprint, description="Cinematic rules and blueprints for this story beat/scene")
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
