"""
Director Memory & Cross-Chapter Variety Guard
Maintains stateful memory across chapters and the timeline to track and escalate visual motifs,
enforce human anchor cadence, maintain 7-dimensional contrast, and eliminate AI slideshow monotony.
"""

from collections import Counter
from typing import Dict, List, Any, Optional
from .schema import VisualJob, ShotRelationship


class DirectorMemory:
    def __init__(self):
        self.reset()

    def reset(self):
        # Subject & Category History
        self.subject_history: List[str] = []
        self.subject_counts = Counter()
        
        # 7-Dimensional Contrast History
        self.duration_history: List[float] = []
        self.motion_history: List[str] = []
        self.size_history: List[str] = []
        self.angle_history: List[str] = []
        self.lens_history: List[str] = []
        self.composition_history: List[str] = []
        self.visual_type_history: List[str] = []
        self.provenance_history: List[str] = []
        self.lut_history: List[str] = []
        self.sound_history: List[Optional[str]] = []
        self.density_history: List[float] = []
        self.restraint_history: List[bool] = []
        self.visual_job_history: List[str] = []
        self.relationship_history: List[str] = []
        
        # Narrative Motif Escalation Tracking
        self.registered_motifs: List[str] = []
        self.motif_usage: Dict[str, List[Dict[str, Any]]] = {}
        
        # Human Anchor Cadence Tracking
        self.shots_since_human_anchor: int = 0
        self.total_human_anchors: int = 0
        
        self.total_shots: int = 0

    def register_motifs(self, motifs: List[str]):
        """Registers recurring symbolic motifs from the research package or vision."""
        if not motifs:
            return
        for m in motifs:
            clean_m = m.strip()
            if clean_m and clean_m not in self.registered_motifs:
                self.registered_motifs.append(clean_m)
                if clean_m not in self.motif_usage:
                    self.motif_usage[clean_m] = []

    def record_motif_usage(self, motif: str, act_num: int, shot_id: str, treatment: str = "grounding"):
        """Records the staging of a motif in a specific act."""
        if motif not in self.motif_usage:
            self.motif_usage[motif] = []
        self.motif_usage[motif].append({
            "act_num": act_num,
            "shot_id": shot_id,
            "treatment": treatment,
            "shot_index": self.total_shots
        })

    def get_escalated_motif_prompt(self, motif: str, act_num: int, topic: str = "") -> Dict[str, str]:
        """
        Escalates a recurring visual motif across acts:
        - Act 1: Grounding / Subtle introduction in pristine/functional state.
        - Act 2: Escalation / Distortion under intense crisis lighting.
        - Act 3: Payoff / Haunting aftermath and permanent consequence.
        """
        clean_topic = topic or "documentary narrative"
        clean_motif = motif or "symbolic artifact"
        
        if act_num <= 1:
            return {
                "treatment": "GROUNDING",
                "visual_job": VisualJob.BUILD_MYSTERY.value,
                "prompt": f"Authentic documentary close-up introducing {clean_motif} in pristine condition, subtle warm daylight, establishing initial baseline in {clean_topic}, 35mm film still",
                "query": f"{clean_motif} detail close up authentic"
            }
        elif act_num == 2:
            return {
                "treatment": "ESCALATION_DISTORTION",
                "visual_job": VisualJob.ESCALATE.value,
                "prompt": f"Dramatic cinematic high-contrast shot of {clean_motif} under extreme tension during {clean_topic} crisis, sharp directional shadows, moody noir lighting, anamorphic lens flare",
                "query": f"{clean_motif} dramatic shadow high contrast"
            }
        else:
            return {
                "treatment": "PAYOFF_AFTERMATH",
                "visual_job": VisualJob.PAYOFF.value,
                "prompt": f"Haunting static hold on {clean_motif} abandoned in empty room during the aftermath of {clean_topic}, cold dim lighting, dust particles, permanent symbolic consequence",
                "query": f"{clean_motif} abandoned aftermath dim lighting"
            }

    def record_shot(self, shot: Dict[str, Any]):
        """Records all cinematographic, semantic, and contrast parameters of a shot."""
        self.total_shots += 1
        
        # 1. Subject category extraction
        query = (shot.get("visual_query") or shot.get("ai_prompt") or shot.get("visual_description") or "").lower()
        job = str(shot.get("visual_job", "ESTABLISH_WORLD"))
        
        subject_category = "other"
        if any(w in query for w in ["laptop", "terminal", "screen", "keyboard", "code", "monitor"]):
            subject_category = "computer_screen"
        elif any(w in query for w in ["office", "building", "headquarters", "exterior", "tower", "facade"]):
            subject_category = "building_exterior"
        elif any(w in query for w in ["server", "data center", "cables", "racks"]):
            subject_category = "server_room"
        elif any(w in query for w in ["portrait", "person", "man", "woman", "face", "official", "worker"]):
            subject_category = "person_portrait"
        elif any(w in query for w in ["document", "telex", "case file", "paper", "signature", "memo"]):
            subject_category = "case_document"
        elif any(w in query for w in ["map", "route", "globe", "geography", "network map"]):
            subject_category = "geographic_map"
        elif any(w in query for w in ["money", "cash", "dollar", "rupee", "banknote", "vault"]):
            subject_category = "currency_flow"
        elif any(w in query for w in ["hand", "hands", "fingers", "sweat", "coffee cup", "desk"]):
            subject_category = "human_detail"
            
        self.subject_history.append(subject_category)
        self.subject_counts[subject_category] += 1
        
        # 2. Cinematography & 7D Contrast Tracking
        dur = float(shot.get("duration_seconds") or shot.get("actual_duration") or 3.0)
        self.duration_history.append(dur)
        self.motion_history.append(shot.get("camera_motion", "static"))
        self.size_history.append(shot.get("shot_size", "medium"))
        self.angle_history.append(shot.get("camera_angle", "eye_level"))
        self.lens_history.append(shot.get("lens", "standard_lens"))
        self.composition_history.append(shot.get("composition", "rule_of_thirds"))
        self.visual_type_history.append(shot.get("visual_type", "real_photo"))
        self.provenance_history.append(shot.get("asset_provenance", "STOCK"))
        self.lut_history.append(shot.get("lut_filter", "warm_cinema"))
        self.sound_history.append(shot.get("sound_design"))
        self.density_history.append(float(shot.get("visual_density", 0.5)))
        self.restraint_history.append(bool(shot.get("is_restrained", False)))
        self.visual_job_history.append(job)
        self.relationship_history.append(str(shot.get("shot_relationship") or ""))

        # 3. Human Anchor Cadence
        is_human = (
            job in [VisualJob.HUMANIZE.value, VisualJob.INTRODUCE_CHARACTER.value, "SHOW_PERSON", "HUMANIZE"]
            or subject_category in ["person_portrait", "human_detail"]
            or shot.get("shot_relationship") in [ShotRelationship.PERSON_TO_CONSEQUENCE.value, ShotRelationship.OBJECT_TO_PERSON.value]
        )
        if is_human:
            self.shots_since_human_anchor = 0
            self.total_human_anchors += 1
        else:
            self.shots_since_human_anchor += 1

    def needs_human_anchor(self, threshold: int = 4) -> bool:
        """Returns True if the timeline has run for several shots without grounding in human consequence."""
        return self.shots_since_human_anchor >= threshold

    def is_subject_overused(self, candidate_category: str) -> bool:
        """Returns True if the candidate subject has appeared too frequently."""
        if not candidate_category or candidate_category == "other":
            return False
            
        # Hard check: same subject category in last 2 consecutive shots
        if len(self.subject_history) >= 1 and self.subject_history[-1] == candidate_category:
            return True
        if len(self.subject_history) >= 2 and self.subject_history[-2] == candidate_category and candidate_category in ["computer_screen", "building_exterior", "server_room"]:
            return True
            
        # Frequency check: max 25% of total shots
        if self.total_shots >= 4 and (self.subject_counts[candidate_category] / self.total_shots) > 0.25:
            return True
            
        return False

    def is_visual_job_overused(self, candidate_job: str) -> bool:
        """Prevents consecutive duplicate visual jobs unless intentionally continuing."""
        if not self.visual_job_history:
            return False
        return len(self.visual_job_history) >= 2 and self.visual_job_history[-1] == candidate_job and self.visual_job_history[-2] == candidate_job

    def suggest_diverse_motion(self, preferred_motions: List[str]) -> str:
        """Suggests a camera motion that avoids consecutive duplicates and camera motion fatigue."""
        if not self.motion_history:
            return preferred_motions[0] if preferred_motions else "slow_push_in"
            
        last_motion = self.motion_history[-1]
        avoid_motions = {last_motion}
        if len(self.motion_history) >= 2 and self.motion_history[-1] != "static":
            avoid_motions.add(self.motion_history[-2])

        available = [m for m in preferred_motions if m not in avoid_motions]
        if not available:
            available = [m for m in preferred_motions if m != last_motion]
        if not available:
            all_motions = ["pan_left", "pan_right", "slow_push_in", "dolly_in", "dolly_out", "static"]
            available = [m for m in all_motions if m not in avoid_motions]
            if not available:
                available = [m for m in all_motions if m != last_motion]
            
        return available[0] if available else "static"

    def suggest_diverse_size(self, preferred_sizes: List[str]) -> str:
        """Suggests a camera shot size that avoids consecutive identical scales."""
        if not self.size_history:
            return preferred_sizes[0] if preferred_sizes else "wide"
        last_size = self.size_history[-1]
        available = [s for s in preferred_sizes if s != last_size]
        return available[0] if available else ("close" if last_size in ["wide", "establishing_shot"] else "wide")

    def suggest_contrast_density(self, prev_density: float) -> float:
        """Enforces complexity / density breathing room contrast."""
        if prev_density >= 0.70:
            return 0.25 # Breathing room
        elif prev_density <= 0.35:
            return 0.75 # High information density
        return 0.50

    def get_summary(self) -> Dict[str, Any]:
        """Provides a statistical summary for director review and cinematic QC."""
        return {
            "total_shots_recorded": self.total_shots,
            "total_human_anchors": self.total_human_anchors,
            "shots_since_human_anchor": self.shots_since_human_anchor,
            "subject_breakdown": dict(self.subject_counts),
            "restraint_shots_count": sum(1 for r in self.restraint_history if r),
            "static_camera_count": sum(1 for m in self.motion_history if m == "static"),
            "unique_visual_jobs": len(set(self.visual_job_history)),
            "average_visual_density": round(sum(self.density_history) / max(1, len(self.density_history)), 2),
            "registered_motifs_count": len(self.registered_motifs),
            "motif_usage_breakdown": {k: len(v) for k, v in self.motif_usage.items()}
        }
