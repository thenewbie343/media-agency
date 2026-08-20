import random
import copy
import math
import re

class VisualStoryPlanner:
    """
    Translates narrative intent and attention intensity into editorial decisions:
    - Sets coherent chapter-level color language (LUT).
    - Semantically decomposes continuous narration blocks into purposeful visual shot sequences.
    - Enforces strict sound design discipline (no transition spam, rare risers, global cooldowns).
    """
    
    def __init__(self):
        self.chapter_luts = {
            "historical": ["vintage_film", "sepia"],
            "cyber": ["noir", "high_contrast"],
            "crisis": ["noir", "high_contrast"],
            "reconstruction": ["teal_orange", "warm_cinema"],
            "aftermath": ["warm_cinema"],
            "modern": ["warm_cinema", "teal_orange"]
        }
        
        self.sizes = ["wide_shot", "medium_shot", "close_up", "extreme_close_up", "establishing_shot"]
        self.angles = ["eye_level", "low_angle", "high_angle", "dutch_angle", "overhead_shot"]
        self.lenses = ["standard_lens", "wide_angle_lens", "telephoto_lens", "macro_lens"]
        self.comps = ["rule_of_thirds", "center_framed", "leading_lines", "symmetry"]
        self.motions = ["pan_left", "pan_right", "zoom_in", "zoom_out", "dolly_in", "dolly_out", "static", "crane_up"]

        # Stateful global timeline tracking for sound design cooldowns
        self.current_timeline_time = 0.0
        self.last_transition_sfx_time = -999.0
        self.last_punctuation_time = -999.0
        self.last_riser_time = -999.0

    def reset_timeline(self):
        """Reset timeline state for a new documentary generation run."""
        self.current_timeline_time = 0.0
        self.last_transition_sfx_time = -999.0
        self.last_punctuation_time = -999.0
        self.last_riser_time = -999.0

    def determine_chapter_color(self, beat_intent: str, time_mode: str) -> str:
        """Assign a consistent LUT per chapter (StoryBeat) based on intent and time."""
        if time_mode == "historical":
            return random.choice(self.chapter_luts["historical"])
        if beat_intent in ["CONFLICT", "MYSTERY"]:
            return random.choice(self.chapter_luts["crisis"])
        if beat_intent == "RESOLUTION":
            return random.choice(self.chapter_luts["aftermath"])
        return random.choice(self.chapter_luts["reconstruction"])

    def decompose_narration_block(self, block: dict, actual_duration: float, beat_intent: str = "EXPLANATION", attention_intensity: float = 0.5, time_mode: str = "modern", chapter_lut: str = None) -> list:
        """
        Interprets narration meaning into narrative visual storytelling:
        - Extracts narrative opportunities (locations, statistics, money flow, cyber tension, anomalies, reveals).
        - Assigns distinct narrative visual jobs (ESTABLISH, VISUALIZE_DATA, SHOW_PROCESS, CREATE_TENSION, HIGHLIGHT_ANOMALY, REVEAL).
        - Selects the authentic visual modality (real_photo, motion_graphics, ai_video, stock_video).
        - Enforces chapter-level LUT persistence and contextual overlays.
        - Strictly throttles SFX with global cooldowns (~1-3 transition SFX per minute max).
        """
        if not chapter_lut:
            chapter_lut = self.determine_chapter_color(beat_intent, time_mode)

        voiceover = block.get("voiceover", "")
        caption = block.get("caption", "")
        full_text = f"{voiceover} {caption}"
        
        existing_shots = block.get("shots", [])
        base_shot = existing_shots[0] if existing_shots else {}
        topic_hint = base_shot.get("visual_query") or base_shot.get("ai_prompt") or "documentary"
        clean_topic = re.sub(r'(cinematic|dramatic|scene|4k|hd|footage|building|photo)', '', topic_hint, flags=re.IGNORECASE).strip()
        if not clean_topic: clean_topic = "historical event"
        
        # 1. Identify distinct semantic visual opportunities from narration text
        semantic_units = []
        
        # A. Location / Environment
        loc_match = re.search(r'\b(bank|headquarters|building|airport|palace|london|dhaka|mumbai|delhi|new york|moscow|switzerland|goa)\b', full_text, re.IGNORECASE)
        loc_name = loc_match.group(0).title() if loc_match else "Building"
        
        # B. Financial Data / Key Numbers
        fin_match = re.search(r'(\$?\d+[\d,\.]*\s*(?:million|billion|crore|lakh|percent|%|dollar|rupee|dollars|rupees))\b', full_text, re.IGNORECASE)
        year_match = re.search(r'\b(19\d\d|20\d\d)\b', full_text)
        stat_text = fin_match.group(0).strip().upper() if fin_match else (year_match.group(0).strip() if year_match else "")
        if "81" in full_text and "million" in full_text.lower() and not fin_match:
            stat_text = "$81 MILLION"
        
        # C. Anomaly / Typo / Evidence / Error
        has_error = bool(re.search(r'\b(typo|typographical|spelling|mistake|galti|error|flaw|discrepancy|fandation)\b', full_text, re.IGNORECASE))
        
        # D. Process / Flow / Accounts / Transactions
        has_process = bool(re.search(r'\b(transfer|account|accounts|paisa|money|bhejna|bheje|routed|swift|wire|transaction|system)\b', full_text, re.IGNORECASE))
        
        # E. Cyber / Tension / Crime / Secret Operation
        has_tension = bool(re.search(r'\b(hacker|hackers|cyber|attack|chor|chori|heist|secret|operation|target|dark|stole|robbery)\b', full_text, re.IGNORECASE))
        
        # F. Reveal / Expose / Alert / Arrest
        has_reveal = bool(re.search(r'\b(expose|exposed|pakda|caught|alert|warning|police|giraftaar|arrest|revealed|expose kar diya)\b', full_text, re.IGNORECASE))
        
        # G. Key Person
        has_person = bool(re.search(r'\b(businessman|governor|official|petrov|mallya|modi|minister|detective|investigator|witness)\b', full_text, re.IGNORECASE))

        # Build dynamic narrative visual sequence based purely on identified story beats in this block
        has_location_mention = bool(loc_match)
        
        # 1. Location / Establishing
        if has_location_mention or (block.get("block_id") in ("n001", "b001") and not has_tension and not has_error):
            semantic_units.append({
                "job": "ESTABLISH",
                "type": "real_photo",
                "provenance": "ARCHIVAL_FOOTAGE",
                "query": f"{clean_topic} {loc_name} exterior building archive",
                "prompt": f"Cinematic wide establishing shot of {clean_topic} {loc_name} exterior, authentic period lighting, architectural photography",
                "weight": 3.6,
                "overlay": "film_grain" if time_mode == "historical" else None
            })
            
        # 2. Data / Kinetic Typography if number or financial scale is present
        if stat_text and len(stat_text) > 1:
            semantic_units.append({
                "job": "VISUALIZE_DATA",
                "type": "motion_graphics",
                "provenance": "DATA_VISUALIZATION",
                "query": f"{stat_text} kinetic typography financial statistic graphic",
                "prompt": f"Editorial motion graphics screen displaying {stat_text} in bold typography with subtle data lines on dark parchment",
                "weight": 2.8,
                "overlay": None
            })
            
        # 3. Tension / Cyber Reconstruction
        if has_tension:
            semantic_units.append({
                "job": "CREATE_TENSION",
                "type": "ai_video",
                "provenance": "CINEMATIC_RECONSTRUCTION",
                "query": f"cyber attack hacker terminal screen typing in dark room",
                "prompt": f"Cinematic medium close-up of computer monitor displaying rapid terminal code in a dimly lit security room, moody atmospheric lighting, high tension",
                "weight": 3.8,
                "overlay": "vhs_glitch" if random.random() > 0.4 else None
            })
            
        # 4. Process / Flow (Money moving between accounts, global network)
        if has_process:
            semantic_units.append({
                "job": "SHOW_PROCESS",
                "type": "motion_graphics",
                "provenance": "DATA_VISUALIZATION",
                "query": f"global banking transaction network money flow account transfer map",
                "prompt": f"Clean editorial map diagram showing money routing across global banking systems between accounts",
                "weight": 3.2,
                "overlay": None
            })
            
        # 5. Anomaly / Evidence (Typo / Document)
        if has_error:
            semantic_units.append({
                "job": "HIGHLIGHT_ANOMALY",
                "type": "real_photo",
                "provenance": "ARCHIVAL_FOOTAGE",
                "query": f"misspelled wire transfer document bank typo error close up",
                "prompt": f"Macro detail shot of official banking telex document with highlighted misspelled word, macro lens, shallow depth of field",
                "weight": 3.2,
                "overlay": "dust_scratches" if random.random() > 0.5 else None
            })
            
        # 6. Reveal / Exposed / Alert
        if has_reveal:
            semantic_units.append({
                "job": "REVEAL",
                "type": "motion_graphics",
                "provenance": "DATA_VISUALIZATION",
                "query": f"red alert warning transaction blocked system expose graphic",
                "prompt": f"Dramatic editorial screen showing high-contrast security warning banner and transaction flag",
                "weight": 2.8,
                "overlay": "light_leaks"
            })
            
        # Fallback if no specific trigger matched
        if not semantic_units:
            if has_person:
                semantic_units.append({
                    "job": "SHOW_PERSON",
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "query": f"{clean_topic} portrait archival photograph",
                    "prompt": f"Authentic archival historical portrait of key figure in {clean_topic}",
                    "weight": 3.5,
                    "overlay": "film_grain" if time_mode == "historical" else None
                })
            else:
                semantic_units.append({
                    "job": "SHOW_EVIDENCE",
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "query": f"{clean_topic} official case file document evidence",
                    "prompt": f"Official case file document and investigative evidence from {clean_topic}, archival lighting",
                    "weight": 3.2,
                    "overlay": "dust_scratches" if time_mode == "historical" else None
                })

        # Ensure no shot exceeds 4.5s
        total_weight = max(0.1, sum(u["weight"] for u in semantic_units))
        while any((u["weight"] / total_weight) * actual_duration > 4.5 for u in semantic_units) or len(semantic_units) < math.ceil(actual_duration / 4.5):
            idx = len(semantic_units)
            if idx % 3 == 0:
                semantic_units.append({
                    "job": "MACRO_DETAIL",
                    "type": "ai_image",
                    "provenance": "CINEMATIC_RECONSTRUCTION",
                    "query": f"{clean_topic} banking terminal screen keyboard close up",
                    "prompt": f"Macro close-up details of financial terminal and glowing screen, cinematic depth of field",
                    "weight": 2.8,
                    "overlay": None
                })
            elif idx % 3 == 1:
                semantic_units.append({
                    "job": "SHOW_EVIDENCE",
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "query": f"{clean_topic} official transaction record document evidence",
                    "prompt": f"Close-up of official case file and wire transfer logs, authentic archival lighting",
                    "weight": 3.0,
                    "overlay": "dust_scratches" if time_mode == "historical" else None
                })
            else:
                semantic_units.append({
                    "job": "SHOW_PROCESS",
                    "type": "stock_video",
                    "provenance": "STOCK",
                    "query": f"server room data center lights flashing network",
                    "prompt": f"Cinematic shot of secure server room racks with blinking blue indicator lights",
                    "weight": 3.2,
                    "overlay": None
                })
            total_weight = sum(u["weight"] for u in semantic_units)

        # Calculate time allocation
        raw_durations = [(u["weight"] / total_weight) * actual_duration for u in semantic_units]
        durations = [round(d, 3) for d in raw_durations]
        diff = round(actual_duration - sum(durations), 3)
        durations[0] = round(durations[0] + diff, 3)

        # Assemble new decomposed shots with sound design discipline
        block_id = block.get("block_id", "n001")
        new_shots = []
        last_motion = None

        for i, (unit, dur) in enumerate(zip(semantic_units, durations)):
            shot = copy.deepcopy(base_shot)
            shot_id = f"{block_id}_s{i+1:03d}"
            shot["shot_id"] = shot_id
            shot["visual_job"] = unit["job"]
            shot["visual_type"] = unit["type"]
            shot["asset_provenance"] = unit["provenance"]
            shot["duration_seconds"] = dur
            shot["actual_duration"] = dur
            shot["duration_mode"] = "fixed"
            shot["duration_ratio"] = round(dur / max(0.1, actual_duration), 4)
            shot["visual_query"] = unit["query"]
            shot["ai_prompt"] = unit["prompt"]
            
            # Chapter-level LUT persistence
            shot["lut_filter"] = chapter_lut
            shot["overlay"] = unit.get("overlay")

            # ─── SOUND DESIGN DISCIPLINE & COOLDOWN LOGIC ───
            shot_sound = None
            shot_events = []
            shot_start_time = self.current_timeline_time

            job = unit["job"]

            # A. TRANSITION SFX (Maximum 1–3 per minute, only on major chapter/block transitions)
            # Only candidate is shot 0 of a block with >= 24s elapsed since last transition sound
            if i == 0 and (shot_start_time - self.last_transition_sfx_time) >= 24.0:
                if block.get("block_id") in ["n001", "b001"] or beat_intent in ["LOCATION_ESTABLISH", "HOOK"]:
                    shot_sound = "subtle_whoosh"
                    self.last_transition_sfx_time = shot_start_time

            # B. RISERS (RARE: only on major narrative climax/escalation, >= 45s cooldown)
            elif job == "CREATE_TENSION" and beat_intent == "CONFLICT" and attention_intensity >= 0.85:
                if (shot_start_time - self.last_riser_time) >= 45.0:
                    shot_sound = "riser"
                    shot_events.append({"type": "SFX", "cue": "riser", "timing_percent": 0.0, "intensity": 0.65})
                    self.last_riser_time = shot_start_time

            # C. NARRATIVE PUNCTUATION (Only on REVEAL, HIGHLIGHT_ANOMALY, or heavy data hit with >= 18s cooldown)
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

            # Standard cuts receive NO SFX (silence) to let voiceover and BGM breathe!
            shot["sound_design"] = shot_sound
            shot["editorial_events"] = shot_events

            # Update global timeline
            self.current_timeline_time += dur

            # Varied cinematography
            shot["shot_size"] = self.sizes[i % len(self.sizes)]
            shot["camera_angle"] = self.angles[i % len(self.angles)]
            shot["lens"] = self.lenses[i % len(self.lenses)]
            shot["composition"] = self.comps[i % len(self.comps)]
            
            # Varied camera motion
            m = self.motions[i % len(self.motions)]
            if m == last_motion:
                m = self.motions[(i + 1) % len(self.motions)]
            shot["camera_motion"] = m
            last_motion = m
            
            new_shots.append(shot)
            
        return new_shots

    def enforce_editorial_restraint(self, shot: dict, attention_intensity: float):
        """Ensures single shot does not contain stacked conflicting events."""
        events = shot.get("editorial_events") or []
        if len(events) > 2:
            events = events[:2]
        shot["editorial_events"] = events
        return shot

