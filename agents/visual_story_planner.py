import random
import copy

class VisualStoryPlanner:
    """
    Translates narrative intent and attention intensity into editorial decisions:
    - Sets chapter color language.
    - Generates and filters editorial events (SFX, graphics, etc.) based on restraint.
    - Ensures visual events are purposeful punctuation rather than decoration.
    """
    
    def __init__(self):
        self.chapter_luts = {
            "historical": ["Warm Cinema", "Teal and Orange", "VM Thermal Sunday", "sepia"],
            "reconstruction": ["Teal and Orange", "Warm Cinema", "VM Thermal Poolside", "cinematic"],
            "crisis": ["VM Thermal Vice", "VM Thermal Fahrenheit", "VM Thermal Crush", "high_contrast"],
            "aftermath": ["Warm Cinema", "VM Thermal Royalty", "Teal and Orange", "VM Thermal Dream"]
        }

    def determine_chapter_color(self, beat_intent: str, time_mode: str) -> str:
        """Assign a consistent LUT per chapter (StoryBeat) based on intent and time."""
        if time_mode == "historical":
            return random.choice(self.chapter_luts["historical"])
        if beat_intent in ["CONFLICT", "MYSTERY"]:
            return random.choice(self.chapter_luts["crisis"])
        if beat_intent == "RESOLUTION":
            return random.choice(self.chapter_luts["aftermath"])
        return random.choice(self.chapter_luts["reconstruction"])

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
