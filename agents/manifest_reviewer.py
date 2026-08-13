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
            
        status = "FAILED" if errors else "PASSED"
        
        result = {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "metrics": {
                "total_shots": shot_count,
                "ai_video_count": ai_video_count,
                "ai_video_percentage": ai_percentage
            }
        }
        
        if errors:
            log.error(f"Manifest Review FAILED. {len(errors)} errors: {errors[0]}")
        else:
            log.info(f"Manifest Review PASSED. {len(warnings)} warnings.")
            
        return result
