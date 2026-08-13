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
    Replaces the legacy Stage 1 and Stage 2 of the pipeline.
    """
    topic = cfg["topic"]
    duration_minutes = int(cfg.get("duration_min") or cfg.get("duration") or 1)
    target_scenes = max(6, int(duration_minutes * 6)) # 6 scenes per minute (10s per scene) ensures accurate duration without token limits
    log.info(f"🎥 AI Studio Orchestrator starting for topic: {topic} ({duration_minutes}m -> target {target_scenes} scenes)")
    
    # 1. Initialization
    researcher = ResearcherAgent()
    head_writer = HeadWriterAgent()
    scriptwriter = ScriptwriterAgent()
    director = DirectorAgent()
    qc_editor = QCEditorAgent()
    
    # 2. Fact Gathering (Researcher)
    log.info("1/5: Researcher gathering facts...")
    fact_sheet = researcher.research_topic(topic)
    
    # 3. Outline (Head Writer)
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
        outline_dict = {k: outline_dict for k in act_keys} # rough fallback

    scenes_per_act = max(1, target_scenes // len(act_keys))
    master_beats = []
    context_so_far = ""
    global_scene_counter = 1

    for idx, act_key in enumerate(act_keys):
        act_num = idx + 1
        log.info(f"3/5: Scriptwriter writing Act {act_num} (target {scenes_per_act} scenes)...")
        act_outline = outline_dict.get(act_key, [])
        
        # Write Act
        act_scenes = scriptwriter.write_act(
            json.dumps(fact_sheet), 
            act_num, 
            json.dumps(act_outline), 
            target_scenes=scenes_per_act, 
            context_so_far=context_so_far
        )

        # Fix Scene Numbers to ensure strict continuity across acts
        for scene in act_scenes:
            scene["scene_number"] = global_scene_counter
            global_scene_counter += 1

        log.info(f"4/5: Director adding metadata for Act {act_num}...")
        # Director processes just this act's scenes
        act_manifest = director.add_metadata(act_scenes)
        
        if "story_beats" in act_manifest:
            master_beats.extend(act_manifest["story_beats"])
            
        context_so_far += f"Act {act_num} completed with {len(act_scenes)} scenes.\n"

    # Assemble Final ScriptManifest manually
    final_script = {
        "schema_version": "2.0",
        "project_meta": {
            "title": outline_dict.get("title_idea", topic),
            "target_duration_seconds": duration_minutes * 60
        },
        "story_beats": master_beats
    }
    
    # 6. Quality Control (QC Editor)
    log.info("5/5: QC Editor reviewing full master script...")
    qc_result = qc_editor.review_script(final_script)
    
    if qc_result.get("status") == "REJECTED":
        log.warning(f"QC Rejected! Reason: {qc_result.get('feedback')}.")
    else:
        log.info("QC Approved master script!")
        
    return final_script, fact_sheet

