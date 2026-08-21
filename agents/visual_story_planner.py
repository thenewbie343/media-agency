"""
Visual Story Planner & Cinematic Shot Director
Orchestrates Visual Intent, Shot Relationships, Director Memory, Dynamic Pacing,
and Cinematic Restraint across the narrative timeline.
"""

import random
import copy
import math
import re
from typing import Dict, Any, List, Optional

from .style_profiles import get_style_profile, select_profile_for_topic
from .director_memory import DirectorMemory
from .visual_intent import VisualIntentEngine
from .shot_relationship import ShotRelationshipEngine

class VisualStoryPlanner:
    def __init__(self, style_profile_name: str = "DOCUMENTARY_INVESTIGATIVE"):
        self.style_profile = get_style_profile(style_profile_name)
        self.memory = DirectorMemory()
        self.intent_engine = VisualIntentEngine()
        self.relationship_engine = ShotRelationshipEngine()
        
        self.sizes = ["establishing_shot", "wide", "medium", "close", "extreme_close"]
        self.angles = ["eye_level", "low_angle", "high_angle", "dutch_angle", "overhead_shot"]
        self.lenses = ["standard_lens", "wide_angle_lens", "telephoto_lens", "macro_lens"]
        self.comps = ["rule_of_thirds", "center_framed", "leading_lines", "symmetry"]
        self.motions = ["slow_push_in", "pan_left", "pan_right", "zoom_in", "zoom_out", "dolly_in", "static"]

        # Timeline state for sound design & silence
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
        """Assign a consistent LUT per chapter based on style profile, intent, and time."""
        profile_luts = self.style_profile.get("color_and_lighting", {}).get("chapter_luts", ["warm_cinema"])
        if time_mode == "historical":
            return "vintage_film" if "vintage_film" in profile_luts else "sepia"
        if beat_intent in ["CONFLICT", "MYSTERY"]:
            return "noir" if "noir" in profile_luts else "high_contrast"
        if beat_intent == "RESOLUTION":
            return "warm_cinema"
        return random.choice(profile_luts)

    def decompose_narration_block(self, block: dict, actual_duration: float, beat_intent: str = "EXPLANATION", attention_intensity: float = 0.5, time_mode: str = "modern", chapter_lut: str = None) -> list:
        """
        Directs the visual sequence for a continuous narration block:
        - Visual Intent analysis (banning literal sentence-to-image translation).
        - Dynamic Pacing (allowing impact cuts and cinematic holds based on style profile).
        - Triad Shot Relationship (scale progression, camera vector harmony, density alternation).
        - Director Memory (tracking and penalizing repetitive visual motifs).
        - Cinematic Restraint (intentional static frames and silence).
        """
        if not chapter_lut:
            chapter_lut = self.determine_chapter_color(beat_intent, time_mode)

        voiceover = block.get("voiceover", "")
        caption = block.get("caption", "")
        
        # 1. Analyze Visual Intent
        intent_info = self.intent_engine.analyze_block_intent(voiceover, caption, beat_intent)
        visual_intent = intent_info["visual_intent"]
        stat_text = intent_info["statistic_text"]
        has_anomaly = intent_info["has_anomaly"]
        has_cyber = intent_info["has_cyber"]
        has_process = intent_info["has_process"]
        has_reveal = intent_info["has_reveal"]
        has_person = intent_info["has_person"]

        existing_shots = block.get("shots", [])
        base_shot = existing_shots[0] if existing_shots else {}
        topic_hint = base_shot.get("visual_query") or base_shot.get("ai_prompt") or "documentary"
        clean_topic = re.sub(r'(cinematic|dramatic|scene|4k|hd|footage|building|photo)', '', topic_hint, flags=re.IGNORECASE).strip()
        if not clean_topic: clean_topic = "historical event"

        # 2. Formulate Purposeful Visual Strategies
        semantic_units = []

        # A. Anomaly / Document Evidence
        if has_anomaly:
            semantic_units.append({
                "job": "HIGHLIGHT_ANOMALY",
                "type": "real_photo",
                "provenance": "ARCHIVAL_FOOTAGE",
                "visual_intent": "HIGHLIGHT_ANOMALY_DETAIL",
                "query": f"{clean_topic} official case file wire transfer document typo close up",
                "prompt": f"Authentic archival macro shot of official telex document highlighting typographical error in {clean_topic}, macro lens, period lighting",
                "weight": 3.4,
                "density": 0.35, # Simple, focused
                "overlay": "dust_scratches" if time_mode == "historical" else None
            })

        # B. Data / Statistic Callout
        if stat_text and len(stat_text) > 1:
            semantic_units.append({
                "job": "VISUALIZE_DATA",
                "type": "motion_graphics",
                "provenance": "DATA_VISUALIZATION",
                "visual_intent": "VISUALIZE_MAGNITUDE_SCALE",
                "query": f"{stat_text} kinetic typography financial statistic graphic",
                "prompt": f"Editorial motion graphics screen displaying {stat_text} in bold serif typography with subtle data lines on dark parchment",
                "weight": 2.8,
                "density": 0.80, # High information punch
                "overlay": None
            })

        # C. Tension / Covert Operation (check memory to avoid repetitive computer screens)
        if has_cyber:
            if not self.memory.is_subject_overused("computer_screen"):
                semantic_units.append({
                    "job": "CREATE_TENSION",
                    "type": "ai_video",
                    "provenance": "CINEMATIC_RECONSTRUCTION",
                    "visual_intent": "DRAMATIZE_COVERT_OPERATION",
                    "query": f"{clean_topic} cyber attack terminal monitor dark security room",
                    "prompt": f"Cinematic medium close-up of computer monitor displaying rapid terminal code in a dimly lit security room, moody atmospheric lighting, high tension",
                    "weight": 3.8,
                    "density": 0.65,
                    "overlay": "vhs_glitch" if random.random() > 0.4 else None
                })
            else:
                # Memory variety guard: substitute server rack or building power substation instead
                semantic_units.append({
                    "job": "CREATE_TENSION",
                    "type": "stock_video",
                    "provenance": "STOCK",
                    "visual_intent": "DRAMATIZE_COVERT_OPERATION",
                    "query": f"{clean_topic} secure data center cables blue server lights",
                    "prompt": f"Low-angle shot of humming server racks and blinking communication indicators in cold data vault",
                    "weight": 3.2,
                    "density": 0.50,
                    "overlay": None
                })

        # D. Process / Transaction Flow
        if has_process:
            semantic_units.append({
                "job": "SHOW_PROCESS",
                "type": "motion_graphics",
                "provenance": "DATA_VISUALIZATION",
                "visual_intent": "TRACE_TRANSACTION_NETWORK",
                "query": f"global banking transaction network money routing map",
                "prompt": f"Clean editorial map diagram showing money routing across global banking systems between international accounts",
                "weight": 3.2,
                "density": 0.75,
                "overlay": None
            })

        # E. Reveal / System Flag
        if has_reveal:
            semantic_units.append({
                "job": "REVEAL",
                "type": "motion_graphics",
                "provenance": "DATA_VISUALIZATION",
                "visual_intent": "IMPACT_REVEAL_AND_FLAG",
                "query": f"red alert warning transaction blocked system flag graphic",
                "prompt": f"Dramatic editorial screen showing high-contrast security warning banner and transaction flag",
                "weight": 2.6,
                "density": 0.70,
                "overlay": "light_leaks"
            })

        # F. Establishing / Subject fallback (with memory variety check)
        if not semantic_units:
            if has_person:
                semantic_units.append({
                    "job": "SHOW_PERSON",
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "visual_intent": "ISOLATE_CENTRAL_FIGURE",
                    "query": f"{clean_topic} portrait archival photograph",
                    "prompt": f"Authentic archival historical portrait of central figure in {clean_topic}, documentary lighting",
                    "weight": 3.5,
                    "density": 0.40,
                    "overlay": "film_grain" if time_mode == "historical" else None
                })
            else:
                if not self.memory.is_subject_overused("building_exterior") and block.get("block_id") in ["n001", "b001"]:
                    semantic_units.append({
                        "job": "ESTABLISH",
                        "type": "real_photo",
                        "provenance": "ARCHIVAL_FOOTAGE",
                        "visual_intent": "ESTABLISH_SPECIFIC_ENVIRONMENT",
                        "query": f"{clean_topic} exterior building architecture archive",
                        "prompt": f"Cinematic wide establishing shot of {clean_topic} exterior, authentic period lighting, architectural photography",
                        "weight": 3.6,
                        "density": 0.30,
                        "overlay": "film_grain" if time_mode == "historical" else None
                    })
                else:
                    semantic_units.append({
                        "job": "SHOW_EVIDENCE",
                        "type": "real_photo",
                        "provenance": "ARCHIVAL_FOOTAGE",
                        "visual_intent": "AUTHENTIC_DOCUMENTARY_EVIDENCE",
                        "query": f"{clean_topic} official case file document evidence",
                        "prompt": f"Official case file document and investigative evidence from {clean_topic}, archival lighting",
                        "weight": 3.2,
                        "density": 0.35,
                        "overlay": "dust_scratches" if time_mode == "historical" else None
                    })

        # Ensure no shot exceeds 4.5s (dynamic pacing allocation)
        max_shot_dur = self.style_profile.get("pacing", {}).get("max_shot_duration", 4.5)
        total_weight = max(0.1, sum(u["weight"] for u in semantic_units))
        while any((u["weight"] / total_weight) * actual_duration > max_shot_dur for u in semantic_units) or len(semantic_units) < math.ceil(actual_duration / max_shot_dur):
            idx = len(semantic_units)
            if idx % 2 == 0:
                semantic_units.append({
                    "job": "MACRO_DETAIL",
                    "type": "ai_image",
                    "provenance": "CINEMATIC_RECONSTRUCTION",
                    "visual_intent": "ATMOSPHERIC_BREATHING_ROOM",
                    "query": f"{clean_topic} detail macro shallow depth of field",
                    "prompt": f"Atmospheric macro detail shot from {clean_topic}, shallow depth of field, dramatic cinematic lighting",
                    "weight": 2.5,
                    "density": 0.20, # Minimal breathing room
                    "overlay": None
                })
            else:
                semantic_units.append({
                    "job": "SHOW_EVIDENCE",
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "visual_intent": "AUTHENTIC_DOCUMENTARY_EVIDENCE",
                    "query": f"{clean_topic} official document record",
                    "prompt": f"Close-up of official case record and investigative logs from {clean_topic}",
                    "weight": 2.8,
                    "density": 0.40,
                    "overlay": "dust_scratches" if time_mode == "historical" else None
                })
            total_weight = sum(u["weight"] for u in semantic_units)

        # Dynamic Pacing & Durations Calculation
        raw_durations = [(u["weight"] / total_weight) * actual_duration for u in semantic_units]
        durations = [round(d, 3) for d in raw_durations]
        diff = round(actual_duration - sum(durations), 3)
        durations[0] = round(durations[0] + diff, 3)

        # Assemble new decomposed shots with triad continuity & memory
        block_id = block.get("block_id", "n001")
        new_shots = []

        for i, (unit, dur) in enumerate(zip(semantic_units, durations)):
            shot = copy.deepcopy(base_shot)
            shot_id = f"{block_id}_s{i+1:03d}"
            shot["shot_id"] = shot_id
            shot["visual_job"] = unit["job"]
            shot["visual_type"] = unit["type"]
            shot["asset_provenance"] = unit["provenance"]
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

            # Default cinematography from style profile
            pref_sizes = self.style_profile.get("cinematography", {}).get("preferred_shot_sizes", self.sizes)
            pref_motions = self.style_profile.get("cinematography", {}).get("preferred_motions", self.motions)
            
            shot["shot_size"] = pref_sizes[i % len(pref_sizes)]
            shot["camera_angle"] = self.angles[i % len(self.angles)]
            shot["lens"] = self.lenses[i % len(self.lenses)]
            shot["composition"] = self.comps[i % len(self.comps)]
            shot["camera_motion"] = self.memory.suggest_diverse_motion(pref_motions)

            # Enforce Triad Continuity & Scale Progression
            shot = self.relationship_engine.enforce_triad_grammar(self.prev_shot, shot)

            # ─── CINEMATIC RESTRAINT & SOUND DESIGN ───
            shot_sound = None
            shot_events = []
            shot_start_time = self.current_timeline_time
            is_restrained = False

            # Check if this shot triggers cinematic restraint (static frame, silence)
            if attention_intensity >= 0.85 and unit["job"] in ["HIGHLIGHT_ANOMALY", "REVEAL"] and dur >= 2.0:
                is_restrained = True
                shot["camera_motion"] = "static"

            job = unit["job"]

            # A. Transition SFX (Max 1–3/min, >= 24s cooldown)
            if i == 0 and (shot_start_time - self.last_transition_sfx_time) >= 24.0:
                if block.get("block_id") in ["n001", "b001"] or beat_intent in ["LOCATION_ESTABLISH", "HOOK"]:
                    shot_sound = "subtle_whoosh"
                    self.last_transition_sfx_time = shot_start_time

            # B. Risers (Rare, >= 45s cooldown)
            elif job == "CREATE_TENSION" and beat_intent == "CONFLICT" and attention_intensity >= 0.85:
                if (shot_start_time - self.last_riser_time) >= 45.0:
                    shot_sound = "riser"
                    shot_events.append({"type": "SFX", "cue": "riser", "timing_percent": 0.0, "intensity": 0.65})
                    self.last_riser_time = shot_start_time

            # C. Narrative Punctuation (Only on REVEAL, HIGHLIGHT_ANOMALY, or data hit with >= 18s cooldown)
            elif job == "REVEAL" and (shot_start_time - self.last_punctuation_time) >= 18.0:
                shot_sound = "deep_impact"
                shot_events.append({"type": "IMPACT", "cue": "deep_impact", "timing_percent": 0.0, "intensity": 0.8})
                shot_events.append({"type": "OVERLAY", "cue": "flash", "timing_percent": 0.0, "duration": 0.4})
                self.last_punctuation_time = shot_start_time

            elif job == "HIGHLIGHT_ANOMALY" and (shot_start_time - self.last_punctuation_time) >= 15.0:
                shot_sound = "paper_rustle"
                shot_events.append({"type": "SFX", "cue": "paper_rustle", "timing_percent": 0.0, "intensity": 0.6})
                self.last_punctuation_time = shot_start_time

            elif job == "VISUALIZE_DATA" and attention_intensity >= 0.8 and (shot_start_time - self.last_punctuation_time) >= 18.0:
                shot_sound = "impact"
                shot_events.append({"type": "IMPACT", "cue": "deep_impact", "timing_percent": 15.0, "intensity": 0.65})
                self.last_punctuation_time = shot_start_time

            shot["sound_design"] = shot_sound
            shot["editorial_events"] = shot_events
            shot["is_restrained"] = is_restrained

            # Record shot in Director Memory
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
