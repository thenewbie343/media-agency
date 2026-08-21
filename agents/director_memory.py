"""
Director Memory & Variety Guard
Maintains stateful memory across the timeline to prevent visual motif repetition,
camera fatigue, and AI slideshow monotony.
"""

from collections import Counter
from typing import Dict, List, Any, Optional

class DirectorMemory:
    def __init__(self):
        self.reset()

    def reset(self):
        self.subject_history: List[str] = []
        self.subject_counts = Counter()
        self.motion_history: List[str] = []
        self.size_history: List[str] = []
        self.angle_history: List[str] = []
        self.visual_type_history: List[str] = []
        self.graphic_type_history: List[str] = []
        self.density_history: List[float] = []
        self.restraint_history: List[bool] = []
        self.total_shots = 0

    def record_shot(self, shot: Dict[str, Any]):
        self.total_shots += 1
        
        # Track subject category
        job = shot.get("visual_job", "SHOW_ACTION")
        query = (shot.get("visual_query") or shot.get("ai_prompt") or "").lower()
        
        subject_category = "other"
        if any(w in query for w in ["laptop", "terminal", "screen", "keyboard", "code"]):
            subject_category = "computer_screen"
        elif any(w in query for w in ["office", "building", "headquarters", "exterior", "tower"]):
            subject_category = "building_exterior"
        elif any(w in query for w in ["server", "data center", "cables"]):
            subject_category = "server_room"
        elif any(w in query for w in ["portrait", "person", "man", "woman", "face", "official"]):
            subject_category = "person_portrait"
        elif any(w in query for w in ["document", "telex", "case file", "paper", "signature"]):
            subject_category = "case_document"
        elif any(w in query for w in ["map", "route", "globe", "geography"]):
            subject_category = "geographic_map"
        elif any(w in query for w in ["money", "cash", "dollar", "rupee", "banknote"]):
            subject_category = "currency_flow"
            
        self.subject_history.append(subject_category)
        self.subject_counts[subject_category] += 1
        
        # Track cinematography
        self.motion_history.append(shot.get("camera_motion", "static"))
        self.size_history.append(shot.get("shot_size", "medium"))
        self.angle_history.append(shot.get("camera_angle", "eye_level"))
        self.visual_type_history.append(shot.get("visual_type", "real_photo"))
        
        if shot.get("visual_type") in ["motion_graphics", "text_stat"]:
            self.graphic_type_history.append(shot.get("fallback_type", "MotionGraphic"))
            
        self.density_history.append(float(shot.get("visual_density", 0.5)))
        self.restraint_history.append(bool(shot.get("is_restrained", False)))

    def is_subject_overused(self, candidate_category: str) -> bool:
        """Returns True if the candidate subject has appeared too frequently."""
        if not candidate_category or candidate_category == "other":
            return False
            
        # Hard check: same subject category in last 2 consecutive shots
        if len(self.subject_history) >= 1 and self.subject_history[-1] == candidate_category:
            return True
        if len(self.subject_history) >= 2 and self.subject_history[-2] == candidate_category and candidate_category in ["computer_screen", "building_exterior"]:
            return True
            
        # Frequency check: max 25% of total shots
        if self.total_shots >= 4 and (self.subject_counts[candidate_category] / self.total_shots) > 0.25:
            return True
            
        return False

    def suggest_diverse_motion(self, preferred_motions: List[str]) -> str:
        """Suggests a camera motion that avoids consecutive duplicates."""
        if not self.motion_history:
            return preferred_motions[0] if preferred_motions else "slow_push_in"
            
        last_motion = self.motion_history[-1]
        available = [m for m in preferred_motions if m != last_motion]
        if not available:
            all_motions = ["pan_left", "pan_right", "slow_push_in", "zoom_out", "dolly_in", "static"]
            available = [m for m in all_motions if m != last_motion]
            
        return available[0] if available else "static"

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_shots_recorded": self.total_shots,
            "subject_breakdown": dict(self.subject_counts),
            "restraint_shots_count": sum(1 for r in self.restraint_history if r),
            "average_visual_density": round(sum(self.density_history) / max(1, len(self.density_history)), 2)
        }
