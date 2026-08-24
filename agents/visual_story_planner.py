"""
Visual Story Planner & Cinematic Shot Director
Orchestrates Visual Sequence Plans, 20 Editorial Visual Jobs, 12 Shot Relationships,
7-Dimensional Visual Contrast, Dramatic Number Typography Punctuation,
Cross-Chapter Motif Escalation, and Human Consequence Grounding.
"""

import copy
import math
import random
import re
from typing import Dict, Any, List, Optional, Union

from .style_profiles import get_style_profile, select_profile_for_topic
from .director_memory import DirectorMemory
from .visual_intent import VisualIntentEngine
from .shot_relationship import ShotRelationshipEngine
from .visual_sequence_director import VisualSequenceDirector
from .schema import (
    VisualJob,
    ShotRelationship,
    VisualSequencePlan,
    EditorialEvent,
    NarrativeIntent
)


class VisualStoryPlanner:
    """
    Visual Story Planner (R4 & R5).
    Transforms narrative voiceover into an authoritative, cinematic sequence of shots,
    assigning the 20 Editorial Visual Jobs and 12 Shot Relationships while enforcing
    the 7-dimensional contrast engine and cinematic restraint.
    """

    def __init__(self, style_profile_name: str = "DOCUMENTARY_INVESTIGATIVE"):
        self.style_profile = get_style_profile(style_profile_name)
        self.memory = DirectorMemory()
        self.intent_engine = VisualIntentEngine()
        self.relationship_engine = ShotRelationshipEngine()
        self.sequence_director = VisualSequenceDirector()

        self.sizes = ["extreme_wide", "wide", "medium", "medium_close", "close", "extreme_close"]
        self.angles = ["eye_level", "low_angle", "high_angle", "dutch_angle", "overhead_shot"]
        self.lenses = ["standard_lens", "wide_angle_lens", "telephoto_lens", "macro_lens"]
        self.comps = ["rule_of_thirds", "center_framed", "leading_lines", "symmetry"]
        self.motions = ["slow_push_in", "pan_left", "pan_right", "zoom_in", "zoom_out", "dolly_in", "static"]

        # Timeline state for sound design & silence pacing
        self.current_timeline_time = 0.0
        self.last_transition_sfx_time = -999.0
        self.last_punctuation_time = -999.0
        self.last_riser_time = -999.0
        self.prev_shot: Optional[Dict[str, Any]] = None

    def reset_timeline(self, topic: str = "", genre: str = "documentary"):
        """Reset timeline state and memory for a new documentary generation run."""
        profile_name = select_profile_for_topic(topic, genre)
        self.style_profile = get_style_profile(profile_name)
        self.memory.reset()
        self.current_timeline_time = 0.0
        self.last_transition_sfx_time = -999.0
        self.last_punctuation_time = -999.0
        self.last_riser_time = -999.0
        self.prev_shot = None

    def determine_chapter_color(self, beat_intent: str, time_mode: str) -> str:
        """Assign a consistent LUT per chapter based on style profile, intent, and temporal mode."""
        profile_luts = self.style_profile.get("color_and_lighting", {}).get("chapter_luts", ["warm_cinema"])
        if time_mode == "historical":
            return "vintage_film" if "vintage_film" in profile_luts else "sepia"
        if beat_intent in ["CONFLICT", "MYSTERY", "ESCALATION", "REVELATION"]:
            return "noir" if "noir" in profile_luts else "high_contrast"
        if beat_intent in ["RESOLUTION", "PAYOFF", "FINAL_CONTRADICTION"]:
            return "warm_cinema"
        return random.choice(profile_luts)

    def decompose_narration_block(
        self,
        block: dict,
        actual_duration: float,
        beat_intent: str = "EXPLANATION",
        attention_intensity: float = 0.5,
        time_mode: str = "modern",
        chapter_lut: str = None,
        sequence_plan: Optional[Union[Dict[str, Any], VisualSequencePlan]] = None,
        research_package: Optional[Dict[str, Any]] = None,
        act_num: int = 1
    ) -> list:
        """
        Directs the visual sequence for a continuous narration block:
        - Ingests VisualSequencePlan (or formulates one via VisualSequenceDirector).
        - Assigns 20 Editorial Visual Jobs and 12 Shot Relationships.
        - Enforces 7-Dimensional Contrast (Pacing, Motion/Static, Scale, Medium, Sound/Silence, Lighting, Density).
        - Executes Dramatic Number Typography Punctuation + NUMBER_TO_SCALE relational shots.
        - Escalates recurring visual motifs across chapters via DirectorMemory.
        - Grounds abstract systems in human consequence (HUMANIZE shots).
        - Enforces Cinematic Restraint (locked-off static frames on reveals & intentional silence).
        """
        if not chapter_lut:
            chapter_lut = self.determine_chapter_color(beat_intent, time_mode)

        voiceover = block.get("voiceover", "")
        caption = block.get("caption", "")

        # 1. Analyze Visual Intent & Dramatic Entities
        intent_info = self.intent_engine.analyze_block_intent(voiceover, caption, beat_intent)
        visual_intent = intent_info["visual_intent"]
        stat_text = intent_info["statistic_text"]
        timestamp_text = intent_info["timestamp_text"]
        has_anomaly = intent_info["has_anomaly"]
        has_cyber = intent_info["has_cyber"]
        has_process = intent_info["has_process"]
        has_reveal = intent_info["has_reveal"]
        has_person = intent_info["has_person"]
        has_evidence = intent_info["has_evidence"]
        has_human_anchor = intent_info["has_human_anchor"]
        has_comparison = intent_info["has_comparison"]

        existing_shots = block.get("shots", [])
        base_shot = existing_shots[0] if existing_shots else {}
        topic_hint = base_shot.get("visual_query") or base_shot.get("ai_prompt") or "documentary"
        clean_topic = re.sub(r'(cinematic|dramatic|scene|4k|hd|footage|building|photo|documentary)', '', topic_hint, flags=re.IGNORECASE).strip()
        if not clean_topic:
            clean_topic = "investigative documentary"

        # Register motifs if research package or vision is provided
        if research_package and "visual_motifs" in research_package:
            self.memory.register_motifs(research_package["visual_motifs"])

        # 2. Sequence Plan Ingestion
        plan_obj: Optional[VisualSequencePlan] = None
        if isinstance(sequence_plan, VisualSequencePlan):
            plan_obj = sequence_plan
        elif isinstance(sequence_plan, dict):
            try:
                plan_obj = VisualSequencePlan.model_validate(sequence_plan)
            except Exception:
                pass

        if not plan_obj:
            # Generate deterministic sequence plan for this block/beat
            plan_obj = self.sequence_director._generate_deterministic_plan(
                beat_intent,
                block.get("description", voiceover[:60]),
                f"{voiceover} {caption}",
                research_package or {},
                {}
            )

        # 3. Formulate Purposeful Visual Semantic Units
        semantic_units = []

        # ── Unit A: Anomaly / Document Evidence (EXAMINE_EVIDENCE / REVEAL_DETAIL) ──
        if has_anomaly or (has_evidence and beat_intent in ["FIRST_DISCOVERY", "REVELATION"]):
            semantic_units.append({
                "job": VisualJob.EXAMINE_EVIDENCE.value,
                "type": "real_photo",
                "provenance": "ARCHIVAL_FOOTAGE",
                "fallback_type": "ClassifiedFile",
                "visual_intent": "HIGHLIGHT_ANOMALY_DETAIL",
                "query": f"{clean_topic} official confidential case file wire transfer document anomaly",
                "prompt": f"Macro top-down detail shot of an authentic archival document and telex record from {clean_topic}, highlighted discrepancy, warm desk lamp illumination, rich paper texture, 35mm photograph",
                "weight": 3.6,
                "density": 0.35,  # Simple, focused forensic detail
                "overlay": "dust_scratches" if time_mode == "historical" else None,
                "cut_reason": "examine_forensic_document_discrepancy"
            })

        # ── Unit B: Dramatic Number Typography Punctuation (SHOW_SCALE) ──
        if stat_text and len(stat_text) > 1:
            semantic_units.append({
                "job": VisualJob.SHOW_SCALE.value,
                "type": "text_stat",
                "provenance": "MOTION_GRAPHIC",
                "fallback_type": "CinematicText",
                "visual_intent": "VISUALIZE_MAGNITUDE_SCALE",
                "query": f"{stat_text} kinetic typography financial statistic graphic",
                "prompt": f"Editorial motion graphics screen displaying {stat_text} in bold serif typography with subtle animated data lines on dark parchment",
                "weight": 2.6,
                "density": 0.80,  # High information punch
                "overlay": None,
                "statistic_text": stat_text,
                "cut_reason": "punctuate_dramatic_financial_scale"
            })
            # Relational Follow-up: Tangible Real-World Scale
            semantic_units.append({
                "job": VisualJob.SHOW_COMPARISON.value,
                "type": "ai_image",
                "provenance": "AI_RECONSTRUCTION",
                "fallback_type": "TechnicalDiagram",
                "visual_intent": "GROUND_STATISTIC_IN_PHYSICAL_SCALE",
                "query": f"{clean_topic} colossal scale comparison wide angle",
                "prompt": f"Cinematic wide angle shot illustrating the physical scale of {stat_text} in {clean_topic}, towering container ships and massive logistics hub, atmospheric haze, 35mm film still",
                "weight": 3.4,
                "density": 0.40,  # Experiential scale breathing room
                "overlay": None,
                "cut_reason": "ground_abstract_number_in_physical_scale"
            })

        # ── Unit C: Timestamp / Chronology Punctuation (BUILD_MYSTERY / ESTABLISH_WORLD) ──
        if timestamp_text and not stat_text:
            semantic_units.append({
                "job": VisualJob.BUILD_MYSTERY.value,
                "type": "motion_graphics",
                "provenance": "MOTION_GRAPHIC",
                "fallback_type": "Timeline",
                "visual_intent": "CHRONOLOGICAL_TIMELINE_ANCHOR",
                "query": f"{timestamp_text} timeline graphic clock log",
                "prompt": f"Minimalist editorial timeline graphic displaying {timestamp_text} on dark monochromatic grid, subtle pulsing time marker",
                "weight": 2.5,
                "density": 0.65,
                "overlay": None,
                "cut_reason": "anchor_chronological_timestamp"
            })

        # ── Unit D: Human Consequence / Human Anchor Injection (HUMANIZE) ──
        if has_human_anchor or self.memory.needs_human_anchor():
            semantic_units.append({
                "job": VisualJob.HUMANIZE.value,
                "type": "ai_image",
                "provenance": "AI_RECONSTRUCTION",
                "fallback_type": "PortraitCard",
                "visual_intent": "HUMAN_VULNERABILITY_CONSEQUENCE",
                "query": f"{clean_topic} workers hands nervous reaction office consequence",
                "prompt": f"Intimate cinematic close-up of nervous trembling hands at an empty desk in {clean_topic}, cold dawn window light, atmospheric depth of field, documentary realism",
                "weight": 3.4,
                "density": 0.30,  # Human breathing room
                "overlay": "film_grain",
                "cut_reason": "ground_system_in_human_vulnerability"
            })

        # ── Unit E: Covert / Cyber / System Breakdown (ESCALATE) ──
        if has_cyber and not has_anomaly:
            if not self.memory.is_subject_overused("computer_screen"):
                semantic_units.append({
                    "job": VisualJob.ESCALATE.value,
                    "type": "ai_video",
                    "provenance": "AI_RECONSTRUCTION",
                    "fallback_type": "EvidenceBoard",
                    "visual_intent": "DRAMATIZE_COVERT_OPERATION",
                    "query": f"{clean_topic} cyber security hacker terminal server room",
                    "prompt": f"Cinematic wide shot of a dark high-tech operations center during {clean_topic}, glowing server racks, illuminated monitors, moody low-key lighting, atmospheric haze, 35mm film grain, photorealistic",
                    "weight": 3.8,
                    "density": 0.65,
                    "overlay": "vhs_glitch" if random.random() > 0.4 else None,
                    "cut_reason": "dramatize_mounting_covert_pressure"
                })
            else:
                semantic_units.append({
                    "job": VisualJob.ESCALATE.value,
                    "type": "stock_video",
                    "provenance": "STOCK",
                    "fallback_type": "TechnicalDiagram",
                    "visual_intent": "DRAMATIZE_COVERT_OPERATION",
                    "query": f"{clean_topic} data center server racks blue glowing lights",
                    "prompt": f"Cinematic low-angle dolly shot of secure humming server racks and blinking network indicators in cold data vault, directional blue lighting, anamorphic lens flare",
                    "weight": 3.2,
                    "density": 0.50,
                    "overlay": None,
                    "cut_reason": "reveal_infrastructure_under_stress"
                })

        # ── Unit F: Process / Transaction Flow (VISUALIZE_ABSTRACT_CONCEPT) ──
        if has_process and not has_anomaly and not stat_text:
            semantic_units.append({
                "job": VisualJob.VISUALIZE_ABSTRACT_CONCEPT.value,
                "type": "motion_graphics",
                "provenance": "MOTION_GRAPHIC",
                "fallback_type": "TechnicalDiagram",
                "visual_intent": "TRACE_TRANSACTION_NETWORK",
                "query": f"global banking transaction routing network map",
                "prompt": f"Clean editorial map diagram showing money routing across global banking systems between international accounts",
                "weight": 3.2,
                "density": 0.75,
                "overlay": None,
                "cut_reason": "visualize_interconnected_transaction_flow"
            })

        # ── Unit G: Impact Reveal / Smoking Gun (REVEAL) ──
        if has_reveal and not has_anomaly:
            semantic_units.append({
                "job": VisualJob.REVEAL.value,
                "type": "real_photo",
                "provenance": "ARCHIVAL_FOOTAGE",
                "fallback_type": "ArchivalDocument",
                "visual_intent": "IMPACT_REVEAL_AND_FLAG",
                "query": f"{clean_topic} smoking gun document unmasked reveal",
                "prompt": f"Dramatic locked-off macro photograph of the unredacted classified memorandum in {clean_topic}, sharp directional tungsten illumination",
                "weight": 3.8,
                "density": 0.40,
                "overlay": "light_leaks",
                "cut_reason": "expose_smoking_gun_evidence"
            })

        # ── Unit H: Cross-Chapter Visual Motif Escalation ──
        if self.memory.registered_motifs and len(semantic_units) < 2 and random.random() > 0.35:
            active_motif = self.memory.registered_motifs[0]
            motif_data = self.memory.get_escalated_motif_prompt(active_motif, act_num, clean_topic)
            semantic_units.append({
                "job": motif_data["visual_job"],
                "type": "ai_image",
                "provenance": "AI_RECONSTRUCTION",
                "fallback_type": "EvidenceBoard",
                "visual_intent": "RECURRING_VISUAL_MOTIF_ESCALATION",
                "query": motif_data["query"],
                "prompt": motif_data["prompt"],
                "weight": 3.3,
                "density": 0.45,
                "overlay": "film_grain",
                "motif_name": active_motif,
                "motif_treatment": motif_data["treatment"],
                "cut_reason": f"stage_recurring_motif_{motif_data['treatment'].lower()}"
            })

        # ── Unit I: Establishing & Character Baseline Fallback ──
        if not semantic_units:
            if has_person:
                semantic_units.append({
                    "job": VisualJob.INTRODUCE_CHARACTER.value,
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "fallback_type": "PortraitCard",
                    "visual_intent": "ISOLATE_CENTRAL_FIGURE",
                    "query": f"{clean_topic} central figure archival portrait photograph",
                    "prompt": f"Authentic archival historical portrait of key individual in {clean_topic}, documentary lighting, natural 35mm grain, shallow depth of field",
                    "weight": 3.5,
                    "density": 0.40,
                    "overlay": "film_grain" if time_mode == "historical" else None,
                    "cut_reason": "introduce_investigative_protagonist"
                })
            else:
                if not self.memory.is_subject_overused("building_exterior") and block.get("block_id") in ["n001", "b001"]:
                    semantic_units.append({
                        "job": VisualJob.ESTABLISH_WORLD.value,
                        "type": "real_photo",
                        "provenance": "ARCHIVAL_FOOTAGE",
                        "fallback_type": "MapFallback",
                        "visual_intent": "ESTABLISH_SPECIFIC_ENVIRONMENT",
                        "query": f"{clean_topic} exterior building architecture landscape",
                        "prompt": f"Cinematic wide establishing shot of {clean_topic} exterior building, authentic period lighting, architectural photography, Kodak Portra color tones",
                        "weight": 3.6,
                        "density": 0.30,
                        "overlay": "film_grain" if time_mode == "historical" else None,
                        "cut_reason": "establish_geographic_epicenter"
                    })
                else:
                    semantic_units.append({
                        "job": VisualJob.SHOW_EVIDENCE.value,
                        "type": "real_photo",
                        "provenance": "ARCHIVAL_FOOTAGE",
                        "fallback_type": "ArchivalDocument",
                        "visual_intent": "AUTHENTIC_DOCUMENTARY_EVIDENCE",
                        "query": f"{clean_topic} official case file document record",
                        "prompt": f"Official investigative case file and documentary evidence from {clean_topic}, archival warm desk lamp lighting, Leica 50mm lens texture",
                        "weight": 3.2,
                        "density": 0.35,
                        "overlay": "dust_scratches" if time_mode == "historical" else None,
                        "cut_reason": "reveal_official_case_record"
                    })

        # ── Dynamic Pacing & Split Loop: Ensure <= 4.5s max duration per shot ──
        max_shot_dur = self.style_profile.get("pacing", {}).get("max_shot_duration", 4.5)
        total_weight = max(0.1, sum(u["weight"] for u in semantic_units))

        while any((u["weight"] / total_weight) * actual_duration > max_shot_dur for u in semantic_units) or len(semantic_units) < math.ceil(actual_duration / max_shot_dur):
            idx = len(semantic_units)
            if idx % 3 == 0:
                semantic_units.append({
                    "job": VisualJob.HUMANIZE.value,
                    "type": "ai_image",
                    "provenance": "AI_RECONSTRUCTION",
                    "fallback_type": "PortraitCard",
                    "visual_intent": "ATMOSPHERIC_BREATHING_ROOM",
                    "query": f"{clean_topic} human reaction desk coffee cup macro",
                    "prompt": f"Atmospheric macro detail shot of a lone coffee cup on a cluttered desk in {clean_topic}, shallow depth of field, dramatic cinematic lighting",
                    "weight": 2.6,
                    "density": 0.25,  # Breathing room
                    "overlay": None,
                    "cut_reason": "inject_atmospheric_breathing_room"
                })
            elif idx % 3 == 1:
                semantic_units.append({
                    "job": VisualJob.REVEAL_DETAIL.value,
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "fallback_type": "ClassifiedFile",
                    "visual_intent": "AUTHENTIC_DOCUMENTARY_EVIDENCE",
                    "query": f"{clean_topic} official document record detail",
                    "prompt": f"Macro top-down detail shot of official case record and investigative logs from {clean_topic}",
                    "weight": 2.8,
                    "density": 0.40,
                    "overlay": "dust_scratches" if time_mode == "historical" else None,
                    "cut_reason": "reveal_critical_forensic_detail"
                })
            else:
                semantic_units.append({
                    "job": VisualJob.CONTRAST.value,
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "fallback_type": "EvidenceBoard",
                    "visual_intent": "DIALECTICAL_VISUAL_CONTRAST",
                    "query": f"{clean_topic} empty office dark high contrast",
                    "prompt": f"High contrast wide shot of dark empty office corridors during {clean_topic}, sharp shadows, cold fluorescent lighting",
                    "weight": 2.7,
                    "density": 0.30,
                    "overlay": None,
                    "cut_reason": "contrast_institutional_grandeur_with_decay"
                })
            total_weight = sum(u["weight"] for u in semantic_units)

        # Calculate exact frame-accurate durations summing precisely to actual_duration
        raw_durations = [(u["weight"] / total_weight) * actual_duration for u in semantic_units]
        durations = [round(d, 3) for d in raw_durations]
        diff = round(actual_duration - sum(durations), 3)
        durations[0] = round(durations[0] + diff, 3)

        # 4. Assemble Decomposed Shots with Relational Grammar, 7D Contrast, and Restraint
        block_id = block.get("block_id", "n001")
        new_shots = []

        for i, (unit, dur) in enumerate(zip(semantic_units, durations)):
            shot = copy.deepcopy(base_shot)
            shot_id = f"{block_id}_s{i+1:03d}"
            shot["shot_id"] = shot_id
            shot["visual_job"] = unit["job"]
            shot["visual_type"] = unit["type"]
            shot["asset_provenance"] = unit["provenance"]
            shot["fallback_type"] = unit.get("fallback_type", "ArchivalDocument")
            shot["visual_intent"] = unit.get("visual_intent")
            shot["visual_density"] = unit.get("density", 0.5)
            shot["duration_seconds"] = dur
            shot["actual_duration"] = dur
            shot["duration_mode"] = "fixed"
            shot["duration_ratio"] = round(dur / max(0.1, actual_duration), 4)
            shot["visual_query"] = unit["query"]
            shot["ai_prompt"] = unit["prompt"]
            shot["lut_filter"] = chapter_lut
            shot["overlay"] = unit.get("overlay")
            shot["cut_reason"] = unit.get("cut_reason", f"execute_{unit['job'].lower()}")

            # Cinematography from style profile
            pref_sizes = self.style_profile.get("cinematography", {}).get("preferred_shot_sizes", self.sizes)
            pref_motions = self.style_profile.get("cinematography", {}).get("preferred_motions", self.motions)

            shot["shot_size"] = pref_sizes[i % len(pref_sizes)]
            shot["camera_angle"] = self.angles[i % len(self.angles)]
            shot["lens"] = self.lenses[i % len(self.lenses)]
            shot["composition"] = self.comps[i % len(self.comps)]
            shot["camera_motion"] = self.memory.suggest_diverse_motion(pref_motions)

            # Enforce 12 Shot Relationships & Relational Grammar
            shot = self.relationship_engine.determine_and_enforce_relationship(
                self.prev_shot,
                shot,
                sequence_plan=plan_obj
            )

            # Record Motif Usage if applicable
            if "motif_name" in unit:
                self.memory.record_motif_usage(
                    unit["motif_name"],
                    act_num,
                    shot_id,
                    unit.get("motif_treatment", "GROUNDING")
                )

            # ─── 5. CINEMATIC RESTRAINT & SOUND DESIGN ───
            shot_sound = None
            shot_events: List[Dict[str, Any]] = []
            shot_start_time = self.current_timeline_time
            is_restrained = shot.get("is_restrained", False)

            job = unit["job"]

            # Anomaly / Reveal Restraint: locked-off static hold
            if attention_intensity >= 0.85 and job in [VisualJob.REVEAL.value, VisualJob.EXAMINE_EVIDENCE.value, "HIGHLIGHT_ANOMALY", "REVEAL"] and dur >= 2.0:
                is_restrained = True
                shot["camera_motion"] = "static"

            # A. Number Reveal Typography Editorial Event
            if "statistic_text" in unit:
                shot_events.append({
                    "type": "NUMBER_REVEAL",
                    "cue": unit["statistic_text"],
                    "timing_percent": 10.0,
                    "intensity": 0.85,
                    "reason": "editorial_kinetic_typography_punctuation"
                })
                if (shot_start_time - self.last_punctuation_time) >= 18.0:
                    shot_sound = "deep_impact"
                    self.last_punctuation_time = shot_start_time

            # B. Transition SFX (Restrained: >= 24s cooldown)
            elif i == 0 and (shot_start_time - self.last_transition_sfx_time) >= 24.0:
                if block.get("block_id") in ["n001", "b001"] or beat_intent in ["LOCATION_ESTABLISH", "HOOK"]:
                    shot_sound = "subtle_whoosh"
                    self.last_transition_sfx_time = shot_start_time

            # C. Risers (Rare: >= 45s cooldown)
            elif job in [VisualJob.ESCALATE.value, "CREATE_TENSION"] and beat_intent in ["CONFLICT", "ESCALATION"] and attention_intensity >= 0.85:
                if (shot_start_time - self.last_riser_time) >= 45.0:
                    shot_sound = "riser"
                    shot_events.append({
                        "type": "SFX",
                        "cue": "riser",
                        "timing_percent": 0.0,
                        "intensity": 0.65,
                        "reason": "amplify_mounting_investigative_tension"
                    })
                    self.last_riser_time = shot_start_time

            # D. Narrative Punctuation / Reveal Impact (>= 18s cooldown)
            elif job in [VisualJob.REVEAL.value, VisualJob.PAYOFF.value] and (shot_start_time - self.last_punctuation_time) >= 18.0:
                shot_sound = "deep_impact"
                shot_events.append({
                    "type": "IMPACT",
                    "cue": "deep_impact",
                    "timing_percent": 0.0,
                    "intensity": 0.80,
                    "reason": "punctuate_smoking_gun_revelation"
                })
                shot_events.append({
                    "type": "OVERLAY",
                    "cue": "flash",
                    "timing_percent": 0.0,
                    "duration": 0.4,
                    "reason": "visual_reveal_emphasis"
                })
                self.last_punctuation_time = shot_start_time

            elif job == VisualJob.EXAMINE_EVIDENCE.value and (shot_start_time - self.last_punctuation_time) >= 15.0:
                shot_sound = "paper_rustle"
                shot_events.append({
                    "type": "SFX",
                    "cue": "paper_rustle",
                    "timing_percent": 0.0,
                    "intensity": 0.60,
                    "reason": "forensic_paper_evidence_handling"
                })
                self.last_punctuation_time = shot_start_time

            shot["sound_design"] = shot_sound
            shot["editorial_events"] = shot_events
            shot["is_restrained"] = is_restrained

            # Record in Director Memory
            self.memory.record_shot(shot)
            self.prev_shot = shot
            self.current_timeline_time += dur

            new_shots.append(shot)

        return new_shots

    def enforce_editorial_restraint(self, shot: dict, attention_intensity: float):
        """Ensures single shot does not contain stacked conflicting events."""
        events = shot.get("editorial_events") or []
        if len(events) > 2:
            events = events[:2]
        shot["editorial_events"] = events
        return shot
