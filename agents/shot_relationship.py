"""
Shot Relationship Engine & Triad Continuity
Reasons about triads [previous_shot, current_shot, next_shot] to enforce hard cinematic constraints:
scale progression, camera vector harmony, density alternation, and cinematic restraint.
"""

from typing import Dict, Any, List, Optional

class ShotRelationshipEngine:
    def __init__(self):
        self.sizes = ["establishing_shot", "wide", "medium", "close", "extreme_close"]
        self.motions = ["slow_push_in", "pan_left", "pan_right", "dolly_in", "dolly_out", "static"]

    def enforce_triad_grammar(self, prev_shot: Optional[Dict[str, Any]], current_shot: Dict[str, Any], next_intent: Optional[str] = None) -> Dict[str, Any]:
        """Evaluates and refines current_shot in the context of previous and upcoming shots."""
        if not prev_shot:
            # Opening shot of sequence: establish environment or clear focus
            if current_shot.get("shot_size") not in ["establishing_shot", "wide", "medium"]:
                current_shot["shot_size"] = "establishing_shot"
            return current_shot

        prev_size = prev_shot.get("shot_size", "medium")
        prev_motion = prev_shot.get("camera_motion", "static")
        prev_density = float(prev_shot.get("visual_density", 0.5))
        
        # 1. Scale Progression: Avoid identical scale repetition (e.g. medium -> medium)
        curr_size = current_shot.get("shot_size", "medium")
        if curr_size == prev_size:
            # Alternate scale: if previous was medium, jump to close or wide
            if prev_size in ["medium", "medium_close"]:
                current_shot["shot_size"] = "close" if current_shot.get("visual_job") in ["HIGHLIGHT_ANOMALY", "SHOW_PERSON"] else "wide"
            elif prev_size in ["wide", "establishing_shot"]:
                current_shot["shot_size"] = "close"
            else:
                current_shot["shot_size"] = "medium"

        # 2. Camera Vector Harmony: Prevent jarring opposing motions (e.g. pan_left immediately following pan_right)
        curr_motion = current_shot.get("camera_motion", "static")
        if prev_motion == "pan_right" and curr_motion == "pan_left":
            current_shot["camera_motion"] = "slow_push_in"
        elif prev_motion == "pan_left" and curr_motion == "pan_right":
            current_shot["camera_motion"] = "static"
        elif prev_motion == curr_motion and curr_motion != "static":
            # Alternate motion to prevent fatigue
            current_shot["camera_motion"] = "static" if prev_motion == "slow_push_in" else "slow_push_in"

        # 3. Visual Density Alternation: If previous was very dense, create breathing room
        if prev_density >= 0.75:
            current_shot["visual_density"] = 0.25 # Breathing room
        elif prev_density <= 0.30 and current_shot.get("visual_job") in ["VISUALIZE_DATA", "SHOW_PROCESS"]:
            current_shot["visual_density"] = 0.80 # Information punch
        else:
            current_shot["visual_density"] = 0.50 # Balanced

        return current_shot
