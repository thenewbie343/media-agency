import re
with open("pipeline.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"if is_test_mode:.*?url = stage_9_publish\(final_video, script, cfg\)\s*elapsed = int\(time\.time\(\)-start\)"

replacement = """import shutil
        import json
        
        flat_shots = []
        if isinstance(script, dict) and "story_beats" in script:
            for b in script.get("story_beats", []):
                for n in b.get("narration_blocks", []):
                    for s in n.get("shots", []):
                        flat_shots.append(s)

        archive_ct = sum(1 for s in flat_shots if s.get("asset_provenance") in ["AUTHENTIC_ARCHIVE", "AUTHENTIC_PHOTO", "HISTORICAL_DOCUMENT"])
        recon_ct = sum(1 for s in flat_shots if s.get("asset_provenance") in ["AI_RECONSTRUCTION", "RECONSTRUCTION"])
        generic_ct = sum(1 for s in flat_shots if s.get("asset_provenance") in ["STOCK", "GENERIC"] or s.get("visual_type") == "fallback")

        asset_health = {
            "total_shots": num_scenes,
            "archive_rate": f"{(archive_ct / max(num_scenes, 1))*100:.1f}%",
            "reconstruction_rate": f"{(recon_ct / max(num_scenes, 1))*100:.1f}%",
            "generic_rate": f"{(generic_ct / max(num_scenes, 1))*100:.1f}%",
            "audit_passed": audit_passed if "audit_passed" in locals() else "N/A"
        }

        build_health = {
            "mode": "FINAL" if final_mode else "DRAFT",
            "initial_manifest_status": stats.get("initial_status", "UNKNOWN"),
            "qc_failures_count": stats.get("qc_failures_count", 0),
            "repair_count": stats.get("repair_count", 0),
            "repaired_shot_ids": stats.get("repaired_shot_ids", []),
            "schema_repair_count": stats.get("schema_repair_count", 0),
            "final_manifest_status": stats.get("final_status", "UNKNOWN"),
            "average_shot_duration": total_dur / max(num_scenes, 1),
            "asset_pipeline_health": asset_health
        }
        
        with open("documentary_build_health.json", "w", encoding="utf-8") as f:
            json.dump(build_health, f, indent=2)
            
        print("\\n=== DOCUMENTARY BUILD HEALTH ===")
        print(json.dumps(build_health, indent=2))
        print("================================\\n")

        if is_test_mode:
            log.info("🎬 TEST_MODE: Halting before publish. Test successful.")
            url = "TEST_MODE_NO_URL"
            elapsed = int(time.time()-start)
            
            if os.path.exists("remotion/test_out.mp4"):
                shutil.copy("remotion/test_out.mp4", "test_video.mp4")
                
        else:
            url     = stage_9_publish(final_video, script, cfg)
            elapsed = int(time.time()-start)"""

new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
if count > 0:
    with open("pipeline.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Patched by regex!")
else:
    print("Regex Target not found.")
