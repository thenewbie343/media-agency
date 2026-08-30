import json
from .researcher import ResearcherAgent
from .head_writer import HeadWriterAgent
from .scriptwriter import ScriptwriterAgent
from .director import DirectorAgent
from .qc_editor import QCEditorAgent
import logging

log = logging.getLogger(__name__)

def run_documentary_pipeline(cfg):
    """
    The orchestrator for the AI Studio.
    """
    topic = cfg["topic"]
    duration_minutes = int(cfg.get("duration_min") or cfg.get("duration") or 1)
    target_scenes = max(4, int(duration_minutes * 3.5))
    log.info(f"🎥 AI Studio Orchestrator starting for topic: {topic} ({duration_minutes}m -> target {target_scenes} scenes)")
    
    from .researcher import ResearcherAgent
    from .head_writer import HeadWriterAgent
    from .scriptwriter import ScriptwriterAgent
    from .director import DirectorAgent
    from .qc_editor import QCEditorAgent
    
    researcher = ResearcherAgent()
    head_writer = HeadWriterAgent()
    scriptwriter = ScriptwriterAgent()
    director = DirectorAgent()
    qc_editor = QCEditorAgent()
    
    log.info("1/5: Researcher gathering facts...")
    fact_sheet = researcher.research_topic(topic)
    
    log.info("2/5: Head Writer drafting outline...")
    outline_str = head_writer.write_outline(json.dumps(fact_sheet), duration_minutes=duration_minutes, target_scenes=target_scenes)
    
    try:
        outline_dict = outline_str if isinstance(outline_str, dict) else json.loads(outline_str)
    except Exception as e:
        log.error(f"Failed to parse outline: {e}. Falling back to single-shot generation.")
        outline_dict = {"act_1": [{"scene_desc": "Full video"}], "act_2": [], "act_3": []}

    act_keys = [k for k in outline_dict.keys() if k.startswith("act_")]
    if not act_keys:
        act_keys = ["act_1", "act_2", "act_3"]
        outline_dict = {k: outline_dict for k in act_keys}

    scenes_per_act = max(1, target_scenes // len(act_keys))
    
    master_beats = []
    context_so_far = ""
    global_scene_counter = 1
    
    # Generate Acts ONCE
    for idx, act_key in enumerate(act_keys):
        act_num = idx + 1
        log.info(f"3/5: Scriptwriter writing Act {act_num} (target {scenes_per_act} scenes)...")
        act_outline = outline_dict.get(act_key, [])
        
        act_scenes = scriptwriter.write_act(
            json.dumps(fact_sheet), 
            act_num, 
            json.dumps(act_outline), 
            target_scenes=scenes_per_act, 
            duration_minutes=duration_minutes,
            context_so_far=context_so_far
        )

        for scene in act_scenes:
            scene["scene_number"] = global_scene_counter
            global_scene_counter += 1

        log.info(f"4/5: Director adding metadata for Act {act_num}...")
        act_manifest = director.add_metadata(act_scenes)
        
        if "story_beats" in act_manifest:
            master_beats.extend(act_manifest["story_beats"])
            
        act_text_summary = "\n".join(
            f"Scene {s.get('scene_number')}: (Caption: {s.get('caption')})" for s in act_scenes
        )
        context_so_far += f"\n--- Act {act_num} generated script ---\n{act_text_summary}\n"

    # Unique ID Normalization & Re-indexing Pass
    beat_counter = 1
    block_counter = 1
    for beat in master_beats:
        new_beat_id = f"b{beat_counter:03d}"
        beat["beat_id"] = new_beat_id
        beat_counter += 1
        
        for block in beat.get("narration_blocks", []):
            new_block_id = f"n{block_counter:03d}"
            block["block_id"] = new_block_id
            
            shot_counter = 1
            for shot in block.get("shots", []):
                shot["shot_id"] = f"{new_block_id}_s{shot_counter:03d}"
                shot_counter += 1
                
                if "continuity" in shot and shot["continuity"]:
                    grp = shot["continuity"].get("group_id", "grp1")
                    shot["continuity"]["group_id"] = f"{new_beat_id}_{grp}"
            block_counter += 1

    final_script = {
        "schema_version": "2.0",
        "project_meta": {
            "title": outline_dict.get("title_idea", topic),
            "target_duration_seconds": duration_minutes * 60,
            "topic": topic
        },
        "story_beats": master_beats
    }
    
    # Global Directorial Harmonization across all assembled acts
    final_script = director.enforce_strict_rules(final_script)
    
    stats = {
        "initial_status": "PENDING",
        "schema_repair_count": 0,
        "repair_count": 0,
        "repaired_shot_ids": [],
        "qc_failures_count": 0,
        "final_status": "PENDING"
    }
    
    # Surgical QC Loop
    previous_states = {}
    
    for qc_attempt in range(3):
        log.info(f"5/5: QC Editor reviewing master script (Attempt {qc_attempt+1}/3)...")
        qc_result = qc_editor.review_script(final_script)
        
        if qc_attempt == 0:
            stats["initial_status"] = qc_result.get("status", "UNKNOWN")
            
        if qc_result.get("status") == "REJECTED":
            log.warning(f"⚠️ QC Rejected! Reason: {qc_result.get('feedback')}")
            failures = qc_result.get("failures", [])
            stats["qc_failures_count"] += len(failures)
            stats["final_status"] = "REJECTED"
            
            if not failures:
                log.warning("No specific surgical failures provided by QC. Skipping repair.")
                stats["final_status"] = "REJECTED_NO_REPAIR"
                break
                
            log.info(f"Executing surgical repair on {len(failures)} shots/beats...")
            for failure in failures:
                shot_id = failure.get("shot_id")
                if not shot_id: continue
                
                found = False
                for b_idx, beat in enumerate(final_script["story_beats"]):
                    for n_idx, block in enumerate(beat.get("narration_blocks", [])):
                        for s_idx, shot in enumerate(block.get("shots", [])):
                            if shot.get("shot_id") == shot_id:
                                log.info(f"Repairing shot {shot_id}...")
                                
                                # Regression check: If this shot failed again for a NEW reason, log it.
                                if shot_id not in previous_states:
                                    previous_states[shot_id] = dict(shot)
                                
                                repaired_shot = director.repair_manifest_section(shot, [failure])
                                
                                # Hard Constraint: Force preserve IDs and chronology to ensure convergence
                                repaired_shot["shot_id"] = shot.get("shot_id")
                                
                                final_script["story_beats"][b_idx]["narration_blocks"][n_idx]["shots"][s_idx] = repaired_shot
                                stats["repair_count"] += 1
                                if shot_id not in stats["repaired_shot_ids"]:
                                    stats["repaired_shot_ids"].append(shot_id)
                                found = True
                                break
                        if found: break
                    if found: break
            
            # Re-harmonize master script after repair
            final_script = director.enforce_strict_rules(final_script)
        else:
            log.info("✅ QC Approved master script!")
            stats["final_status"] = "APPROVED"
            break
            
    return final_script, fact_sheet, stats
