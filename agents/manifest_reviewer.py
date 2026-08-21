import logging

log = logging.getLogger("agency")

class ManifestReviewerAgent:
    """Statically analyzes the generated ScriptManifest for editorial grammar, constraints, and anachronisms."""
    
    def __init__(self):
        pass

    def review_manifest(self, manifest):
        log.info("[*] ManifestReviewer analyzing editorial grammar and constraints...")
        
        errors = []
        warnings = []
        
        if not isinstance(manifest, dict) or "story_beats" not in manifest:
            return {"status": "FAILED", "errors": ["Invalid manifest structure, missing story_beats."]}

        
        all_shot_ids = set()
        shot_count = 0
        ai_video_count = 0
        prev_camera_motion = None
        consecutive_camera_motion = 0
        prev_cinematography = None
        consecutive_identical_shots = 0
        
        
        for beat in manifest.get("story_beats", []):
            beat_has_reset = False
            for block in beat.get("narration_blocks", []):
                shots = block.get("shots", [])
                
                if not shots:
                    errors.append(f"Block {block.get('block_id')} has no shots.")
                    
                prev_size = None
                
                for shot in shots:
                    shot_id = shot.get("shot_id")
                    if shot_id in all_shot_ids:
                        errors.append(f"DUPLICATE_ID: {shot_id}")
                    all_shot_ids.add(shot_id)
                    shot_count += 1
                    
                    # 1. Grammar check
                    size = shot.get("shot_size")
                    if size in ["WIDE_SHOT", "EXTREME_WIDE_SHOT"] or shot.get("shot_role") in ["ESTABLISHING", "RESET"]:
                        beat_has_reset = True
                        
                    if prev_size and size == prev_size and size != "N/A":
                        warnings.append(f"GRAMMAR_WARNING: Consecutive {size} shots at {shot_id}.")
                    prev_size = size
                    
                                        # 2. AI Video strictness
                    v_type = shot.get("visual_type")
                    if v_type == "ai_video":
                        ai_video_count += 1
                        priority = shot.get("generation_priority", 0.5)
                        if priority < 0.8:
                            warnings.append(f"AI_VIDEO_WARNING: {shot_id} uses ai_video but has low priority {priority}. Consider fallback/stock.")
                            
                    # 4. Cinematography Constraints
                    if v_type not in ["motion_graphics", "text_stat"]:
                        for field in ["shot_size", "camera_angle", "lens", "composition"]:
                            val = shot.get(field)
                            if not val or val == "N/A" or val.strip() == "":
                                errors.append(f"CINEMATOGRAPHY_FAIL: {shot_id} is missing required field '{field}' for visual_type '{v_type}'.")
                    
                    # 5. Generic cut_reason check
                    cut_reason = (shot.get("cut_reason") or "").lower()
                    generic_reasons = ["introduce_information", "show_fact", "transition", "change_scene", "next_shot"]
                    if cut_reason in generic_reasons:
                        errors.append(f"GENERIC_CUT_REASON: {shot_id} uses generic cut_reason '{cut_reason}'. Must be specific.")
                    
                    # 6. Camera Motion Diversity Tracking
                    cm = shot.get("camera_motion", "none")
                    if cm not in ["none", "static"]:
                        if prev_camera_motion == cm:
                            consecutive_camera_motion += 1
                        else:
                            consecutive_camera_motion = 1
                            
                        if consecutive_camera_motion >= 3:
                            errors.append(f"CAMERA_MOTION_FATIGUE: {shot_id} and previous shots use '{cm}' too many times consecutively.")
                    else:
                        consecutive_camera_motion = 0
                        
                    prev_camera_motion = cm
                    
                    # 7. Exact Match 3-Shot Tracking
                    current_cinematography = (cm, size, shot.get("camera_angle"))
                    if current_cinematography == prev_cinematography and cm not in ["none", "static"]:
                        consecutive_identical_shots += 1
                        if consecutive_identical_shots >= 3:
                            errors.append(f"IDENTICAL_CINEMATOGRAPHY: {shot_id} and previous 2 shots have identical size, angle, and motion.")
                    else:
                        consecutive_identical_shots = 1
                    
                    prev_cinematography = current_cinematography
                    
                            
                    # 3. Anachronism basic check
                    cont = shot.get("continuity", {})
                    start_year = cont.get("start_year")
                    end_year = cont.get("end_year")
                    if start_year and end_year and start_year > end_year:
                        errors.append(f"ANACHRONISM: {shot_id} start_year {start_year} > end_year {end_year}")
            
            if not beat_has_reset and beat.get("narration_blocks"):
                warnings.append(f"RESET_SHOT_WARNING: StoryBeat lacks a wide or establishing reset shot.")

        if shot_count == 0:
            errors.append("MANIFEST_EMPTY: No shots generated.")

        ai_percentage = (ai_video_count / max(1, shot_count)) * 100
        if ai_percentage > 40:
            warnings.append(f"OVERUSE_OF_AI: {ai_percentage:.1f}% of shots are AI video. Suggest utilizing more documents/stock.")
            
        
        if errors:
            status = "FAIL"
        elif warnings:
            status = "PASS_WITH_WARNINGS"
        else:
            status = "PASS"

        # Calculate 10-Dimension Director Score
        from .cinematic_qc import CinematicQCEngine
        qc_engine = CinematicQCEngine()
        director_eval = qc_engine.evaluate_manifest_director_score(manifest)
        
        result = {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "director_score": director_eval.get("overall_director_score", 8.0),
            "director_verdict": director_eval.get("verdict", "APPROVED"),
            "director_score_matrix": director_eval.get("director_score_matrix", {}),
            "metrics": {
                "total_shots": shot_count,
                "ai_video_count": ai_video_count,
                "ai_video_percentage": ai_percentage
            }
        }
        
        if errors:
            log.error(f"Manifest Review FAILED. {len(errors)} errors: {errors[0]}")
        else:
            log.info(f"Manifest Review PASSED. Director Score: {result['director_score']}/10.0 ({len(warnings)} warnings).")
            
        return result
