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
        Semantically decomposes a continuous narration block into a sequence of distinct visual shots.
        The narration remains 1 continuous audio track for actual_duration, while visual shots
        change purposefully underneath based on narrative clues (people, data, actions, locations).
        
        Guarantees: sum(shot.duration) == actual_duration and each shot.duration <= 5.0s.
        """
        voiceover = block.get("voiceover", "")
        caption = block.get("caption", "")
        text = f"{voiceover} {caption}"
        
        existing_shots = block.get("shots", [])
        base_shot = existing_shots[0] if existing_shots else {}
        topic_hint = base_shot.get("visual_query") or base_shot.get("ai_prompt") or "cinematic documentary"
        
        # Determine number of shots needed based on narrative density and 4.5s max shot duration limit
        # Minimum 1 shot, minimum ~3s per shot, maximum 5s per shot
        target_num_shots = max(1, math.ceil(actual_duration / 4.2))
        if actual_duration <= 4.5:
            target_num_shots = 1
            
        # Detect semantic entities and visual opportunities in narration text
        has_numbers = bool(re.search(r'\d+|crore|million|billion|percent|%|rupee|dollar', text, re.IGNORECASE))
        has_questions_or_mystery = '?' in text or any(w in text.lower() for w in ['kyun', 'kaise', 'mystery', 'secret', 'sach', 'truth', 'revealed'])
        has_action = any(w in text.lower() for w in ['bhag', 'giraftaar', 'escape', 'police', 'raid', 'crash', 'attack', 'strike', 'chori', 'heist'])
        
        # Build semantic shot blueprints
        semantic_roles = []
        if target_num_shots == 1:
            semantic_roles.append({
                "job": "EXPLAIN",
                "type": base_shot.get("visual_type", "ai_image"),
                "provenance": base_shot.get("asset_provenance", "CINEMATIC_RECONSTRUCTION"),
                "base_weight": 1.0
            })
        else:
            # Shot 1: Establishing / Environment or Person Context
            semantic_roles.append({
                "job": "ESTABLISH_LOCATION" if not base_shot.get("visual_job") == "SHOW_PERSON" else "SHOW_PERSON",
                "type": "real_photo" if "photo" in base_shot.get("visual_type", "") else "stock_video",
                "provenance": "ARCHIVAL_FOOTAGE" if "photo" in base_shot.get("visual_type", "") else "STOCK",
                "base_weight": 3.8
            })
            
            # Middle shots: Evidence, Data, or Dynamic AI Reconstruction
            if target_num_shots >= 2:
                if has_numbers:
                    semantic_roles.append({
                        "job": "VISUALIZE_DATA",
                        "type": "motion_graphics",
                        "provenance": "DATA_VISUALIZATION",
                        "base_weight": 2.6
                    })
                elif has_questions_or_mystery:
                    semantic_roles.append({
                        "job": "BUILD_TENSION",
                        "type": "ai_video",
                        "provenance": "CINEMATIC_RECONSTRUCTION",
                        "base_weight": 4.0
                    })
                elif has_action:
                    semantic_roles.append({
                        "job": "SHOW_ACTION",
                        "type": "stock_video",
                        "provenance": "STOCK",
                        "base_weight": 3.2
                    })
                else:
                    semantic_roles.append({
                        "job": "SHOW_EVIDENCE",
                        "type": "real_photo",
                        "provenance": "ARCHIVAL_FOOTAGE",
                        "base_weight": 3.0
                    })

            # Additional shots if duration requires 3+ or 4+ shots
            while len(semantic_roles) < target_num_shots:
                idx = len(semantic_roles)
                if idx % 3 == 0:
                    semantic_roles.append({
                        "job": "MACRO_DETAIL",
                        "type": "ai_image",
                        "provenance": "CINEMATIC_RECONSTRUCTION",
                        "base_weight": 3.2
                    })
                elif idx % 3 == 1:
                    semantic_roles.append({
                        "job": "BUILD_TENSION",
                        "type": "ai_video",
                        "provenance": "CINEMATIC_RECONSTRUCTION",
                        "base_weight": 4.0
                    })
                else:
                    semantic_roles.append({
                        "job": "SHOW_PERSON",
                        "type": "real_photo",
                        "provenance": "ARCHIVAL_FOOTAGE",
                        "base_weight": 3.5
                    })

        # Calculate exact duration weights so sum(durations) == actual_duration
        total_weight = sum(r["base_weight"] for r in semantic_roles)
        raw_durations = [(r["base_weight"] / total_weight) * actual_duration for r in semantic_roles]
        
        # Round and ensure no shot exceeds 5.0s while keeping exact sum
        durations = [round(d, 3) for d in raw_durations]
        # Assign remainder to first or middle shot
        diff = round(actual_duration - sum(durations), 3)
        durations[0] = round(durations[0] + diff, 3)

        # Assemble new decomposed shots
        block_id = block.get("block_id", "n001")
        new_shots = []
        
        last_motion = None
        for i, (role, dur) in enumerate(zip(semantic_roles, durations)):
            shot = copy.deepcopy(base_shot)
            shot_id = f"{block_id}_s{i+1:03d}"
            shot["shot_id"] = shot_id
            shot["visual_job"] = role["job"]
            shot["visual_type"] = role["type"]
            shot["asset_provenance"] = role["provenance"]
            shot["duration_seconds"] = dur
            shot["actual_duration"] = dur
            shot["duration_mode"] = "fixed"
            shot["duration_ratio"] = round(dur / max(0.1, actual_duration), 4)
            
            # Varied cinematography
            shot["shot_size"] = self.sizes[i % len(self.sizes)]
            shot["camera_angle"] = self.angles[i % len(self.angles)]
            shot["lens"] = self.lenses[i % len(self.lenses)]
            shot["composition"] = self.comps[i % len(self.comps)]
            
            # Varied motion
            m = self.motions[i % len(self.motions)]
            if m == last_motion:
                m = self.motions[(i + 1) % len(self.motions)]
            shot["camera_motion"] = m
            last_motion = m
            
            # Semantic search query tailored to role
            clean_topic = topic_hint.replace("cinematic", "").replace("dramatic", "").strip()
            if role["job"] == "VISUALIZE_DATA":
                shot["visual_query"] = f"{clean_topic} financial data chart graph"
            elif role["job"] == "SHOW_EVIDENCE":
                shot["visual_query"] = f"{clean_topic} document official file evidence"
            elif role["job"] == "SHOW_PERSON":
                shot["visual_query"] = f"{clean_topic} portrait archive photo"
            elif role["job"] == "ESTABLISH_LOCATION":
                shot["visual_query"] = f"{clean_topic} location building environment"
            else:
                shot["visual_query"] = f"{clean_topic} {role['job'].lower()}"
                
            # Restraint on editorial events
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
