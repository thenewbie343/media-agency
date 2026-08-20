import random
import copy
import math
import re

class VisualStoryPlanner:
    """
    Translates narrative intent and attention intensity into editorial decisions:
    - Sets chapter color language.
    - Semantically decomposes continuous narration blocks into purposeful visual shot sequences.
    - Enforces editorial event restraint (SFX, graphics, etc.).
    """
    
    def __init__(self):
        self.chapter_luts = {
            "historical": ["Warm Cinema", "Teal and Orange", "VM Thermal Sunday", "sepia"],
            "reconstruction": ["Teal and Orange", "Warm Cinema", "VM Thermal Poolside", "cinematic"],
            "crisis": ["VM Thermal Vice", "VM Thermal Fahrenheit", "VM Thermal Crush", "high_contrast"],
            "aftermath": ["Warm Cinema", "VM Thermal Royalty", "Teal and Orange", "VM Thermal Dream"]
        }
        
        self.sizes = ["wide_shot", "medium_shot", "close_up", "extreme_close_up", "establishing_shot"]
        self.angles = ["eye_level", "low_angle", "high_angle", "dutch_angle", "overhead_shot"]
        self.lenses = ["standard_lens", "wide_angle_lens", "telephoto_lens", "macro_lens"]
        self.comps = ["rule_of_thirds", "center_framed", "leading_lines", "symmetry"]
        self.motions = ["pan_left", "pan_right", "zoom_in", "zoom_out", "dolly_in", "dolly_out", "static", "crane_up"]

    def determine_chapter_color(self, beat_intent: str, time_mode: str) -> str:
        """Assign a consistent LUT per chapter (StoryBeat) based on intent and time."""
        if time_mode == "historical":
            return random.choice(self.chapter_luts["historical"])
        if beat_intent in ["CONFLICT", "MYSTERY"]:
            return random.choice(self.chapter_luts["crisis"])
        if beat_intent == "RESOLUTION":
            return random.choice(self.chapter_luts["aftermath"])
        return random.choice(self.chapter_luts["reconstruction"])

    def decompose_narration_block(self, block: dict, actual_duration: float, beat_intent: str = "EXPLANATION", attention_intensity: float = 0.5) -> list:
        """
        Interprets narration meaning into narrative visual storytelling:
        - Extracts narrative opportunities (locations, statistics, money flow, cyber tension, anomalies, reveals).
        - Assigns distinct narrative visual jobs (ESTABLISH, VISUALIZE_DATA, SHOW_PROCESS, CREATE_TENSION, HIGHLIGHT_ANOMALY, REVEAL).
        - Selects the authentic visual modality (real_photo, motion_graphics, ai_video, stock_video).
        - Dynamically distributes time so sum(shot.duration) == actual_duration without fixed rigid counts.
        """
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
        
        # B. Financial Data / Key Numbers (prioritize financial scale like $81 Million over 4-digit years)
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
        
        # 1. Location / Establishing (only if explicit location mentioned or block is introductory)
        if has_location_mention or (block.get("block_id") in ("n001", "b001") and not has_tension and not has_error):
            semantic_units.append({
                "job": "ESTABLISH",
                "type": "real_photo",
                "provenance": "ARCHIVAL_FOOTAGE",
                "query": f"{clean_topic} {loc_name} exterior building archive",
                "prompt": f"Cinematic wide establishing shot of {clean_topic} {loc_name} exterior, authentic period lighting, architectural photography",
                "weight": 3.6,
                "lut_filter": "warm_cinema",
                "overlay": "film_grain",
                "sound_design": "subtle_whoosh",
                "events": [{"type": "SFX", "cue": "subtle_whoosh", "timing_percent": 0.0, "intensity": 0.5}]
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
                "lut_filter": "high_contrast",
                "overlay": None,
                "sound_design": "impact",
                "events": [{"type": "IMPACT", "cue": "deep_impact", "timing_percent": 15.0, "intensity": 0.7}]
            })
            
        # 3. Tension / Cyber Reconstruction (covert operation / hackers)
        if has_tension:
            semantic_units.append({
                "job": "CREATE_TENSION",
                "type": "ai_video",
                "provenance": "CINEMATIC_RECONSTRUCTION",
                "query": f"cyber attack hacker terminal screen typing in dark room",
                "prompt": f"Cinematic medium close-up of computer monitor displaying rapid terminal code in a dimly lit security room, moody atmospheric lighting, high tension",
                "weight": 3.8,
                "lut_filter": "noir",
                "overlay": "dust_scratches",
                "sound_design": "riser",
                "events": [{"type": "SFX", "cue": "riser", "timing_percent": 0.0, "intensity": 0.7}]
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
                "lut_filter": "teal_orange",
                "overlay": "light_leaks",
                "sound_design": "cinematic_whoosh",
                "events": [{"type": "SFX", "cue": "cinematic_whoosh", "timing_percent": 0.0, "intensity": 0.6}]
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
                "lut_filter": "vintage_film",
                "overlay": "vhs_glitch",
                "sound_design": "paper_rustle",
                "events": [{"type": "SFX", "cue": "paper_rustle", "timing_percent": 0.0, "intensity": 0.7}]
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
                "lut_filter": "high_contrast",
                "overlay": "light_leaks",
                "sound_design": "deep_impact",
                "events": [
                    {"type": "IMPACT", "cue": "deep_impact", "timing_percent": 0.0, "intensity": 0.85},
                    {"type": "OVERLAY", "cue": "flash", "timing_percent": 0.0, "duration": 0.5}
                ]
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
                    "lut_filter": "sepia",
                    "overlay": "film_grain",
                    "sound_design": "subtle_whoosh",
                    "events": []
                })
            else:
                semantic_units.append({
                    "job": "SHOW_EVIDENCE",
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "query": f"{clean_topic} official case file document evidence",
                    "prompt": f"Official case file document and investigative evidence from {clean_topic}, archival lighting",
                    "weight": 3.2,
                    "lut_filter": "vintage_film",
                    "overlay": "dust_scratches",
                    "sound_design": "paper_rustle",
                    "events": [{"type": "SFX", "cue": "paper_rustle", "timing_percent": 0.0, "intensity": 0.6}]
                })

        # If total duration is long, ensure enough semantic units so no shot exceeds 4.5s
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
                    "lut_filter": "noir",
                    "overlay": "film_grain",
                    "sound_design": "subtle_whoosh",
                    "events": []
                })
            elif idx % 3 == 1:
                semantic_units.append({
                    "job": "SHOW_EVIDENCE",
                    "type": "real_photo",
                    "provenance": "ARCHIVAL_FOOTAGE",
                    "query": f"{clean_topic} official transaction record document evidence",
                    "prompt": f"Close-up of official case file and wire transfer logs, authentic archival lighting",
                    "weight": 3.0,
                    "lut_filter": "vintage_film",
                    "overlay": "dust_scratches",
                    "sound_design": "paper_rustle",
                    "events": [{"type": "SFX", "cue": "paper_rustle", "timing_percent": 0.0, "intensity": 0.6}]
                })
            else:
                semantic_units.append({
                    "job": "SHOW_PROCESS",
                    "type": "stock_video",
                    "provenance": "STOCK",
                    "query": f"server room data center lights flashing network",
                    "prompt": f"Cinematic shot of secure server room racks with blinking blue indicator lights",
                    "weight": 3.2,
                    "lut_filter": "teal_orange",
                    "overlay": "light_leaks",
                    "sound_design": "cinematic_whoosh",
                    "events": [{"type": "SFX", "cue": "cinematic_whoosh", "timing_percent": 0.0, "intensity": 0.6}]
                })
            total_weight = sum(u["weight"] for u in semantic_units)

        # Calculate time allocation: sum(durations) == actual_duration
        raw_durations = [(u["weight"] / total_weight) * actual_duration for u in semantic_units]
        
        # Round and adjust remainder
        durations = [round(d, 3) for d in raw_durations]
        diff = round(actual_duration - sum(durations), 3)
        durations[0] = round(durations[0] + diff, 3)

        # Assemble new decomposed shots
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
            shot["lut_filter"] = unit.get("lut_filter", "warm_cinema")
            shot["overlay"] = unit.get("overlay")
            shot["sound_design"] = unit.get("sound_design")
            shot["editorial_events"] = unit.get("events", [])
            
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
            
            # Punctuation & Editorial Restraint
            shot = self.enforce_editorial_restraint(shot, attention_intensity)
            new_shots.append(shot)
            
        return new_shots

    def enforce_editorial_restraint(self, shot: dict, attention_intensity: float):
        """
        Ensures the shot does not have "too many effects".
        High attention intensity = purposeful editorial decisions (e.g. hard cut or silence).
        """
        events = shot.get("editorial_events") or []
        
        # 1. Deduplicate similar events
        types_seen = set()
        restrained_events = []
        for e in events:
            evt_type = e.get("type")
            if evt_type not in types_seen:
                restrained_events.append(e)
                types_seen.add(evt_type)
        
        # 2. Hard Limits: Max 2 events per shot to avoid chaos
        if len(restrained_events) > 2:
            restrained_events = restrained_events[:2]
            
        # 3. Add default punctuation for high intensity if none exists
        if attention_intensity >= 0.8 and not restrained_events:
            restrained_events.append({
                "type": "IMPACT" if random.random() > 0.5 else "HARD_CUT",
                "cue": "deep_impact",
                "timing_percent": 0.0,
                "intensity": 0.8,
                "reason": "High attention intensity requires strong visual punctuation."
            })
            
        # 4. Handle SFX defaults
        for e in restrained_events:
            if e.get("type") == "SFX" and not e.get("cue"):
                e["cue"] = "subtle_whoosh"
            if e.get("timing_percent") is None:
                e["timing_percent"] = 50.0 if e.get("type") == "GRAPHIC" else 0.0
                
        shot["editorial_events"] = restrained_events
        return shot
