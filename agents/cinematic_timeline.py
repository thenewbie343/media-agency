"""
Authoritative Pre-Render Cinematic Timeline Compiler
Compiles all directorial, visual, audio, and color decisions into a single deterministic timeline.
"""

from typing import Dict, Any, List

class CinematicTimelineCompiler:
    def __init__(self):
        pass

    def compile_timeline(self, manifest: Dict[str, Any], fps: int = 30) -> Dict[str, Any]:
        """Compiles story_beats into a flat, deterministic frame-accurate timeline."""
        timeline_segments = []
        current_time_sec = 0.0
        current_frame = 0

        for b_idx, beat in enumerate(manifest.get("story_beats", [])):
            beat_id = beat.get("beat_id", f"b{b_idx+1}")
            chapter_lut = beat.get("chapter_color_language", "warm_cinema")
            intent = beat.get("narrative_intent", "EXPLANATION")

            for n_idx, block in enumerate(beat.get("narration_blocks", [])):
                block_id = block.get("block_id", f"n{n_idx+1}")
                audio_file = block.get("audio_file")

                for s_idx, shot in enumerate(block.get("shots", [])):
                    dur_sec = float(shot.get("actual_duration") or shot.get("duration_seconds") or 3.0)
                    dur_frames = max(1, int(round(dur_sec * fps)))
                    start_sec = current_time_sec
                    end_sec = current_time_sec + dur_sec
                    start_frame = current_frame
                    end_frame = current_frame + dur_frames

                    segment = {
                        "shot_id": shot.get("shot_id"),
                        "beat_id": beat_id,
                        "block_id": block_id,
                        "start_time_sec": round(start_sec, 3),
                        "end_time_sec": round(end_sec, 3),
                        "duration_sec": round(dur_sec, 3),
                        "start_frame": start_frame,
                        "end_frame": end_frame,
                        "duration_frames": dur_frames,
                        "narrative_intent": intent,
                        "visual_job": shot.get("visual_job"),
                        "visual_type": shot.get("visual_type"),
                        "shot_size": shot.get("shot_size"),
                        "camera_angle": shot.get("camera_angle"),
                        "camera_motion": shot.get("camera_motion"),
                        "visual_density": shot.get("visual_density", 0.5),
                        "lut_filter": chapter_lut,
                        "overlay": shot.get("overlay"),
                        "sound_design": shot.get("sound_design"),
                        "editorial_events": shot.get("editorial_events", []),
                        "asset": shot.get("asset", {})
                    }
                    timeline_segments.append(segment)
                    current_time_sec = end_sec
                    current_frame = end_frame

        return {
            "total_duration_sec": round(current_time_sec, 3),
            "total_frames": current_frame,
            "fps": fps,
            "segments": timeline_segments
        }
