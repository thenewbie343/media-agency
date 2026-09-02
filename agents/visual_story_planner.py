"""
Visual Story Planner & Cinematic Shot Director (Part 2 & Part 3 Execution)
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
    NarrativeIntent,
    EditorialScene,
    VisualRequirement,
    HistoricalFidelity
)


class VisualStoryPlanner:
    """
    Visual Story Planner (Part 2 & Part 3 Execution).
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
        self.motions = ["slow_push_in", "pan_left", "pan_right", "zoom_out", "dolly_in", "static"]

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
        Directs the visual sequence for a continuous narration block (Part 2 & 3):
        - Ingests/Creates EditorialScene via VisualSequenceDirector.
        - Assigns 20 Editorial Visual Jobs and 12 Shot Relationships.
        - Enforces 7-Dimensional Contrast and Semantic Cinematography.
        - Attaches normalized VisualRequirements to drive Part 1 asset verification.
        - Enforces Cinematic Restraint and Strategic Silence.
        """
        if not chapter_lut:
            chapter_lut = self.determine_chapter_color(beat_intent, time_mode)

        voiceover = block.get("voiceover", "")
        caption = block.get("caption", "")

        # 1. Analyze Visual Intent & Dramatic Entities
        intent_info = self.intent_engine.analyze_block_intent(voiceover, caption, beat_intent)
        stat_text = intent_info["statistic_text"]
        has_anomaly = intent_info["has_anomaly"]
        has_evidence = intent_info["has_evidence"]

        existing_shots = block.get("shots", [])
        base_shot = existing_shots[0] if existing_shots else {}
        topic_hint = base_shot.get("visual_query") or base_shot.get("ai_prompt") or "documentary"
        clean_topic = re.sub(r'(cinematic|dramatic|scene|4k|hd|footage|building|photo|documentary)', '', topic_hint, flags=re.IGNORECASE).strip()
        if not clean_topic:
            clean_topic = "investigative documentary"

        # Register motifs if research package or vision is provided
        if research_package and "visual_motifs" in research_package:
            self.memory.register_motifs(research_package["visual_motifs"])

        # 2. Phase 2 Sequence Plan & Editorial Scene Orchestration
        plan_obj: Optional[VisualSequencePlan] = None
        if isinstance(sequence_plan, VisualSequencePlan):
            plan_obj = sequence_plan

        editorial_scene, generated_plan, initial_reqs = self.sequence_director.create_editorial_scene(
            block, research_package, None
        )
        if not plan_obj:
            plan_obj = generated_plan

        # 3. Formulate Purposeful Visual Semantic Units based on Phase 2 EditorialScene
        semantic_units = []

        # Unit 1: The Opening Visual (Setup / Establish World)
        semantic_units.append({
            "job": VisualJob.ESTABLISH_WORLD.value,
            "type": "ai_video" if attention_intensity > 0.6 else "ai_image",
            "provenance": "AI_RECONSTRUCTION" if time_mode == "historical" else "STOCK",
            "fallback_type": "PhotoWall",
            "visual_intent": editorial_scene.scene_intent,
            "subject_entity": editorial_scene.scene_world,
            "query": f"{clean_topic} {editorial_scene.scene_world} establishing wide",
            "prompt": editorial_scene.opening_visual or f"Cinematic wide establishing shot of {editorial_scene.scene_world}, {time_mode} lighting, atmospheric tension, shadows and contrast, ultra-detailed, film grain, {chapter_lut} color grade, visual counterpoint to spoken narrative",
            "weight": 3.0,
            "density": 0.40,
            "information_gain": 0.80,
            "cut_reason": "establish_scene_world"
        })

        # Unit 2: The Development / Human Anchor / Anomaly
        if has_anomaly or (has_evidence and beat_intent in ["FIRST_DISCOVERY", "REVELATION"]):
            semantic_units.append({
                "job": VisualJob.EXAMINE_EVIDENCE.value,
                "type": "real_photo",
                "provenance": "ARCHIVAL_FOOTAGE",
                "fallback_type": "ClassifiedFile",
                "visual_intent": "HIGHLIGHT_ANOMALY_DETAIL",
                "subject_entity": "Forensic case record",
                "query": f"{clean_topic} official confidential case file wire transfer document anomaly",
                "prompt": f"Macro top-down detail shot of an authentic archival document from {clean_topic}, highlighted discrepancy, warm desk lamp illumination, rich paper texture",
                "weight": 3.4,
                "density": 0.35,
                "information_gain": 0.85,
                "overlay": "dust_scratches" if time_mode == "historical" else None,
                "cut_reason": "examine_forensic_document_discrepancy"
            })
        elif editorial_scene.human_anchor and editorial_scene.human_anchor != "Unknown Subject":
            semantic_units.append({
                "job": VisualJob.HUMANIZE.value,
                "type": "ai_video",
                "provenance": "AI_RECONSTRUCTION",
                "fallback_type": "PortraitCard",
                "visual_intent": "GROUND_IN_HUMAN_ANCHOR",
                "subject_entity": editorial_scene.human_anchor,
                "query": f"{clean_topic} {editorial_scene.human_anchor} portrait reaction",
                "prompt": f"Intense close-up portrait of {editorial_scene.human_anchor} in {editorial_scene.scene_world}, expressing {editorial_scene.viewer_emotion}, atmospheric rim lighting",
                "weight": 2.8,
                "density": 0.30,
                "information_gain": 0.70,
                "cut_reason": "ground_in_human_anchor"
            })

        # Unit 3: The Reveal / Visual Argument / Typography Scale
        if stat_text and len(stat_text) > 1:
            semantic_units.append({
                "job": VisualJob.SHOW_SCALE.value,
                "type": "text_stat",
                "provenance": "MOTION_GRAPHIC",
                "fallback_type": "CinematicText",
                "visual_intent": "VISUALIZE_MAGNITUDE_SCALE",
                "subject_entity": stat_text,
                "query": f"{stat_text} kinetic typography financial statistic graphic",
                "prompt": f"Editorial motion graphics screen displaying {stat_text} in bold serif typography with subtle animated data lines on dark parchment",
                "weight": 2.6,
                "density": 0.80,
                "information_gain": 0.90,
                "statistic_text": stat_text,
                "cut_reason": "punctuate_dramatic_financial_scale"
            })
        elif editorial_scene.visual_argument:
            semantic_units.append({
                "job": VisualJob.CONTRAST.value,
                "type": "ai_image",
                "provenance": "AI_RECONSTRUCTION",
                "fallback_type": "TechnicalDiagram",
                "visual_intent": "VISUAL_DIALECTIC",
                "subject_entity": editorial_scene.visual_argument.split(" vs ")[0] if " vs " in editorial_scene.visual_argument else clean_topic,
                "query": f"{clean_topic} {editorial_scene.visual_argument.replace(' vs ', ' contrast ')}",
                "prompt": editorial_scene.reveal or f"Cinematic composition contrasting {editorial_scene.visual_argument} in {clean_topic}, documentary style",
                "weight": 3.5,
                "density": 0.50,
                "information_gain": 0.85,
                "cut_reason": "stage_visual_dialectic"
            })

        # Unit 4: The Consequence / Payoff
        semantic_units.append({
            "job": VisualJob.CONSEQUENCE.value,
            "type": "broll_video" if time_mode != "historical" else "ai_video",
            "provenance": "STOCK" if time_mode != "historical" else "AI_RECONSTRUCTION",
            "fallback_type": "ArchivalDocument",
            "visual_intent": "CONSEQUENCE",
            "subject_entity": clean_topic,
            "query": f"{clean_topic} aftermath consequence wide",
            "prompt": editorial_scene.consequence or f"Cinematic wide aftermath shot in {editorial_scene.scene_world}, emotional aftermath, human consequence not literal event, conveying {editorial_scene.knowledge_after}, atmospheric tension, visual counterpoint to narration",
            "weight": 3.0,
            "density": 0.40,
            "information_gain": 0.75,
            "cut_reason": "show_consequence"
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
                    "visual_intent": "ATMOSPHERIC_HUMAN_BREATHING_ROOM",
                    "subject_entity": "Forensic workspace desk",
                    "query": f"{clean_topic} hands examining document desk macro",
                    "prompt": f"Atmospheric macro detail shot of tired hands examining classified files on a cluttered desk in {clean_topic}, shallow depth of field, dramatic cinematic lighting",
                    "weight": 2.6,
                    "density": 0.25,
                    "information_gain": 0.50,
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
                    "subject_entity": "Investigative log detail",
                    "query": f"{clean_topic} official document record detail",
                    "prompt": f"Macro top-down detail shot of official case record and investigative logs from {clean_topic}",
                    "weight": 2.8,
                    "density": 0.40,
                    "information_gain": 0.65,
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
                    "subject_entity": "Institutional corridor",
                    "query": f"{clean_topic} empty office dark high contrast",
                    "prompt": f"High contrast wide shot of dark empty corridors during {clean_topic}, sharp shadows, cold fluorescent lighting",
                    "weight": 2.7,
                    "density": 0.30,
                    "information_gain": 0.60,
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
            shot["information_gain"] = unit.get("information_gain", 0.70)
            shot["viewer_question"] = editorial_scene.viewer_question
            shot["duration_seconds"] = dur
            shot["actual_duration"] = dur
            shot["duration_mode"] = "fixed"
            shot["duration_ratio"] = round(dur / max(0.1, actual_duration), 4)
            shot["visual_query"] = unit["query"]
            shot["ai_prompt"] = unit["prompt"]
            shot["lut_filter"] = chapter_lut
            shot["overlay"] = unit.get("overlay")
            shot["cut_reason"] = unit.get("cut_reason", f"execute_{unit['job'].lower()}")

            # Build normalized VisualRequirement for Part 1 Verification
            fidelity = HistoricalFidelity.ERA_ACCURATE if time_mode == "historical" else HistoricalFidelity.OPTIONAL
            if unit["provenance"] == "ARCHIVAL_FOOTAGE":
                fidelity = HistoricalFidelity.STRICT_ARCHIVAL

            shot["visual_requirement"] = VisualRequirement(
                shot_id=shot_id,
                visual_job=unit["job"],
                subject_entity=unit.get("subject_entity", clean_topic),
                time_period="1980s" if time_mode == "historical" else "modern",
                visual_type=unit["type"],
                visual_purpose=unit.get("visual_intent", "Advance scene visual argument"),
                historical_fidelity=fidelity
            ).model_dump()

            # Cinematography: Semantic Motion derived from Visual Job
            # Cinematography: Base Cinematography from Profile & Memory
            pref_sizes = self.style_profile.get("cinematography", {}).get("preferred_shot_sizes", self.sizes)
            pref_motions = self.style_profile.get("cinematography", {}).get("preferred_motions", self.motions)
            shot["shot_size"] = pref_sizes[i % len(pref_sizes)]
            shot["camera_angle"] = self.angles[i % len(self.angles)]
            shot["lens"] = self.lenses[i % len(self.lenses)]
            shot["composition"] = self.comps[i % len(self.comps)]
            shot["camera_motion"] = self.memory.suggest_diverse_motion(pref_motions)

            # Semantic Motion & Framing derived from Visual Job
            job = unit["job"]
            if job in [VisualJob.EXAMINE_EVIDENCE.value, "EXAMINE_EVIDENCE"]:
                shot["shot_size"] = "extreme_close"
                shot["camera_angle"] = "overhead_shot"
                shot["lens"] = "macro_lens"
                shot["camera_motion"] = "static"
            elif job in [VisualJob.SHOW_SCALE.value, VisualJob.SHOW_COMPARISON.value, "SHOW_SCALE", "SHOW_COMPARISON"]:
                shot["shot_size"] = "extreme_wide"
                shot["camera_angle"] = "low_angle"
                shot["lens"] = "wide_angle_lens"
                shot["camera_motion"] = "zoom_out"
            elif job in [VisualJob.HUMANIZE.value, "HUMANIZE"]:
                shot["shot_size"] = "close"
                shot["camera_angle"] = "eye_level"
                shot["lens"] = "telephoto_lens"
                if self.memory.motion_history and self.memory.motion_history[-1] == "slow_push_in":
                    shot["camera_motion"] = "static"
                else:
                    shot["camera_motion"] = "slow_push_in"
            elif job in [VisualJob.REVEAL.value, VisualJob.PAYOFF.value, "REVEAL", "PAYOFF"]:
                shot["shot_size"] = "medium"
                shot["camera_angle"] = "eye_level"
                shot["lens"] = "standard_lens"
                shot["camera_motion"] = "static"

            # Enforce 12 Shot Relationships & Relational Grammar
            shot = self.relationship_engine.determine_and_enforce_relationship(
                self.prev_shot,
                shot,
                sequence_plan=plan_obj
            )
            shot["relationship_to_previous"] = str(shot.get("shot_relationship") or "CONTINUATION")

            # ─── 5. CINEMATIC RESTRAINT & SOUND DESIGN ───
            shot_sound = None
            shot_events: List[Dict[str, Any]] = []
            shot_start_time = self.current_timeline_time
            is_restrained = shot.get("is_restrained", False)

            # Anomaly / Reveal Restraint: locked-off static hold
            if (
                (attention_intensity >= 0.85 and (job in [VisualJob.REVEAL.value, VisualJob.EXAMINE_EVIDENCE.value, VisualJob.PAYOFF.value, "HIGHLIGHT_ANOMALY", "REVEAL", "EXAMINE_EVIDENCE"] or beat_intent in ["REVELATION", "DEEPER_REVELATION", "FINAL_CONTRADICTION", "PAYOFF"]))
                or (shot.get("camera_motion") == "static" and attention_intensity >= 0.8)
                or shot.get("is_restrained") is True
            ):
                is_restrained = True
                if attention_intensity >= 0.85 and (job in [VisualJob.REVEAL.value, VisualJob.EXAMINE_EVIDENCE.value, "HIGHLIGHT_ANOMALY", "REVEAL"] or beat_intent in ["REVELATION", "DEEPER_REVELATION"]):
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

            # Anti-Camera Fatigue Safety Net: Prevent 3+ consecutive dynamic motions
            if self.memory.motion_history and len(self.memory.motion_history) >= 2:
                last_m = self.memory.motion_history[-1]
                prev_last_m = self.memory.motion_history[-2]
                if shot.get("camera_motion") == last_m == prev_last_m and shot.get("camera_motion") != "static":
                    shot["camera_motion"] = "static"

            shot["sound_design"] = shot_sound
            shot["editorial_events"] = shot_events
            shot["is_restrained"] = is_restrained

            # Record in Director Memory
            self.memory.record_shot(shot)
            self.prev_shot = shot
            self.current_timeline_time += dur

            shot = self._apply_visual_counterpoint(shot, voiceover)
            new_shots.append(shot)

        return new_shots

    def enforce_editorial_restraint(self, shot: dict, attention_intensity: float):
        """Ensures single shot does not contain stacked conflicting events."""
        events = shot.get("editorial_events") or []
        if len(events) > 2:
            events = events[:2]
        shot["editorial_events"] = events
        return shot

    def _apply_visual_counterpoint(self, shot: Dict[str, Any], voiceover: str) -> Dict[str, Any]:
        """Apply visual-audio counterpoint: ensure visuals show dramatic tension,
        not literal illustration of spoken words.
        
        Anti-Literal Rule: If narrator says 'explosion', don't show an explosion.
        Show the faces watching. Show the aftermath. Show the cause.
        If narrator says 'money', don't show money. Show what money bought or destroyed.
        """
        job = shot.get("visual_job", "")
        # These jobs SHOULD be literal — they show evidence and data
        literal_allowed_jobs = [
            "EXAMINE_EVIDENCE", "SHOW_EVIDENCE", "SHOW_SCALE",
            "SHOW_COMPARISON", "REVEAL_DETAIL"
        ]
        if job in literal_allowed_jobs:
            return shot
        
        # For all other jobs, add counterpoint guidance to the ai_prompt
        prompt = shot.get("ai_prompt", "")
        if prompt and "counterpoint" not in prompt.lower():
            # Add counterpoint instruction
            counterpoint_suffix = (
                ", visual counterpoint to narration"
                ", show the emotional consequence not the literal event"
                ", human reaction or atmospheric tension preferred over literal depiction"
            )
            shot["ai_prompt"] = prompt.rstrip() + counterpoint_suffix
        
        return shot
