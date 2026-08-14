from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class VisualBible(BaseModel):
    era: str = Field(..., description="The primary time period (e.g., '1965', 'Late 19th Century')")
    locations: List[str] = Field(..., description="Key geographic locations featured in the story")
    lighting: str = Field(..., description="Lighting style (e.g., 'low-key, cold, cinematic')")
    color_language: str = Field(..., description="Color grading (e.g., 'teal_orange, bleak', 'warm archival')")
    film_texture: str = Field(..., description="Texture (e.g., 'subtle grain, 35mm', 'clean digital')")

class ProjectMeta(BaseModel):
    topic: str = Field(..., description="The main topic of the documentary")
    genre: str = Field(default="documentary", description="Genre style")
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

class Shot(BaseModel):
    shot_id: str = Field(..., description="Unique ID for this shot (e.g., 'n001_s001')")
    duration_mode: Literal["ratio", "fixed"] = Field(default="ratio", description="Whether duration is calculated via ratio of parent block or a fixed seconds count")
    duration_ratio: float = Field(default=1.0, description="If ratio mode, proportion of the parent narration block this shot occupies (0.0 to 1.0)")
    duration_seconds: Optional[float] = Field(None, description="If fixed mode, exact duration in seconds")
    
    shot_role: Literal["ESTABLISHING", "ACTION", "REACTION", "DETAIL", "INSERT", "EVIDENCE", "EXPLANATION", "TRANSITION", "REVEAL", "HOLD"] = Field(default="EXPLANATION", description="The grammatical role of this shot")
    asset_provenance: Literal["AUTHENTIC_PHOTO", "ARCHIVAL_FOOTAGE", "DOCUMENT", "STOCK", "AI_RECONSTRUCTION", "AI_ILLUSTRATION", "MOTION_GRAPHIC", "SEMANTIC_FALLBACK"] = Field(default="STOCK", description="The required provenance of the visual")
    
    shot_size: Literal["extreme_wide", "wide", "medium", "medium_close", "close", "extreme_close", "N/A"] = Field(default="N/A", description="Camera shot size. Do NOT use N/A unless it's a motion graphic.")
    camera_angle: Optional[str] = Field(None, description="Camera angle. Must NOT be blank or N/A for cinematic visual shots.")
    lens: Optional[str] = Field(None, description="Lens type. Must NOT be blank or N/A for cinematic visual shots.")
    composition: Optional[str] = Field(None, description="Composition rule. Must NOT be blank or N/A for cinematic visual shots.")
    foreground: Optional[str] = Field(None, description="What is in the foreground")
    background: Optional[str] = Field(None, description="What is in the background")
    subject_position: Optional[str] = Field(None, description="Position of the main subject")
    depth: Optional[str] = Field(None, description="Depth of field (e.g., shallow, deep)")
    
    source_name: Optional[str] = Field(None, description="Source of evidence (e.g., 'The New York Times', 'Court Document')")
    source_url: Optional[str] = Field(None, description="URL or reference for evidence")
    source_date: Optional[str] = Field(None, description="Date of the evidence")
    confidence: Optional[float] = Field(None, description="Confidence in authenticity of evidence (0.0 to 1.0)")
    generation_priority: float = Field(default=0.5, description="Priority for expensive AI generation (0.0 to 1.0). AI video requires >= 0.8.")
    
    visual_job: Literal[
        "SHOW_LOCATION", "SHOW_SCALE", "SHOW_TIME", "SHOW_PERSON", 
        "SHOW_OBJECT", "SHOW_ACTION", "SHOW_EVIDENCE", "EXPLAIN_MECHANISM", 
        "EXPLAIN_PROCESS", "COMPARE", "VISUALIZE_NUMBER", "CREATE_TENSION", 
        "CREATE_MYSTERY", "REVEAL_INFORMATION", "ESTABLISH_ENVIRONMENT", "TRANSITION"
    ] = Field(..., description="The precise visual job/purpose of this shot")
    
    visual_type: Literal["motion_graphics", "ai_video", "real_photo", "ai_image", "broll_video", "text_stat"] = Field(..., description="Type of visual to generate")
    fallback_type: Literal["ClassifiedFile", "Newspaper", "ArchivalDocument", "EvidenceBoard", "MapFallback", "PhotoWall", "Timeline", "CinematicText", "PortraitCard", "TechnicalDiagram", "AnimatedDiagram"] = Field(..., description="React fallback component if generation fails or is specifically requested")
    
    visual_description: str = Field(..., description="What happens visually in the shot")
    visual_query: str = Field(..., description="Structured search query for stock footage. Format: [SUBJECT] + [ACTION] + [LOCATION] + [ERA]. (e.g. '1960s scientists working in underground bunker')")
    ai_prompt: str = Field(..., description="Exact prompt for image/video generation. Format: [SUBJECT], [ERA], [LOCATION], [ENVIRONMENT], [LIGHTING], [CAMERA ANGLE]")
    camera_motion: str = Field(default="zoom_in", description="Camera movement (e.g., zoom_in, pan_right, slow_push_in, top_down, none)")
    motion_intensity: float = Field(default=0.3, description="Speed/intensity of the camera motion (0.1 to 1.0)")
    transition_in: Literal["hard_cut", "fade", "dissolve"] = Field(default="hard_cut", description="Transition into this shot")
    
    text_overlay: Optional[str] = Field(None, description="Text to display on screen (e.g., location names, dates, quotes). Null if none.")
    highlight: Optional[HighlightMetadata] = Field(None, description="Highlight instructions for the text_overlay")
    sound_design: Optional[str] = Field(None, description="SFX cue (e.g., 'subtle_whoosh', 'paper_rustle', 'deep_impact', 'wind_howl')")
    lut_filter: Optional[str] = Field(None, description="CSS color grade filter (e.g., 'sepia', 'vintage_film', 'noir', 'high_contrast')")
    overlay: Optional[str] = Field(None, description="Visual overlay effect (e.g., 'film_grain', 'vhs_glitch', 'dust_scratches', 'light_leaks')")
    
    cut_reason: str = Field(..., description="Why are we cutting to this shot? Must be highly specific (e.g. 'reveal_financial_consequence', 'bridge_luxury_to_collapse'). DO NOT USE generic reasons like 'introduce_information' or 'transition'.")
    visual_importance: float = Field(default=0.5, description="Scale of visual emphasis (0.0 to 1.0). High means intense motion/sound.")
    
    continuity: ContinuityMetadata = Field(..., description="Continuity constraints for consistent generation")
    asset: AssetMetadata = Field(default_factory=AssetMetadata, description="Asset tracking metadata (populated during pipeline execution)")

class StrategicSilence(BaseModel):
    duration_seconds: float = Field(default=0.0, description="Seconds of silence to add")
    position: Literal["start", "end"] = Field(default="end", description="Where the silence occurs relative to the voiceover")
    ambient_level: int = Field(default=-35, description="Ambient noise dB level during silence")
    visual_behavior: str = Field(default="continue", description="What visually happens during silence (e.g., 'hold_frame', 'slow_pan', 'fade_to_black')")

class AudioMetadata(BaseModel):
    music_energy: float = Field(default=0.5, description="Energy of the background music (0.0 to 1.0)")
    music_duck_amount: int = Field(default=0, description="Amount to duck music by in dB")

class NarrationBlock(BaseModel):
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
    
    shots: List[Shot] = Field(..., description="Visual shots that occur during this narration block")


class TimeContext(BaseModel):
    year: str = Field(..., description="The year or era of this beat (e.g., '2016', '1990s', 'Present Day')")
    mode: Literal["historical", "present_day", "future_projection"] = Field(..., description="The temporal mode")
    location: str = Field(..., description="The primary location for this beat")
    transition_reason: Optional[str] = Field(None, description="Mandatory if transitioning time periods. Why did we jump in time?")

class StoryBeat(BaseModel):
    beat_id: str = Field(..., description="Unique ID for this story beat (e.g., 'b001')")
    time_context: TimeContext = Field(..., description="The global time and location context for this beat")
    narrative_intent: Literal["HOOK", "EVIDENCE", "MYSTERY", "EXPLANATION", "CONFLICT", "RESOLUTION", "LOCATION_ESTABLISH"] = Field(..., description="The narrative purpose of this beat")
    description: str = Field(..., description="Description of the story beat")
    attention_intensity: float = Field(default=0.5, description="Expected audience attention curve intensity (0.0 to 1.0). Hook=0.8, Revelation=1.0")
    narration_blocks: List[NarrationBlock] = Field(..., description="Narration blocks within this story beat")

class ScriptManifest(BaseModel):
    schema_version: str = Field(default="2.0", description="Version of the script schema")
    project_meta: ProjectMeta = Field(..., description="Project metadata")
    story_beats: List[StoryBeat] = Field(..., description="The story beats containing narration and shots")
