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
    outline = head_writer.write_outline(json.dumps(fact_sheet), duration_minutes=duration_minutes, target_scenes=target_scenes)
    
    # 4. Scriptwriting (Scriptwriter)
    log.info("3/5: Scriptwriter writing Hindi VO & Hinglish captions...")
    raw_script = scriptwriter.write_script(json.dumps(fact_sheet), json.dumps(outline), duration_minutes=duration_minutes, target_scenes=target_scenes)
    
    # 5. Metadata (Director)
    log.info("4/5: Director adding cinematic visual metadata...")
    director_script = director.add_metadata(raw_script)
    
    # 6. Quality Control (QC Editor)
    log.info("5/5: QC Editor reviewing (Python Validator)...")
    qc_result = qc_editor.review_script(director_script)
    
    if qc_result.get("status") == "REJECTED":
        log.warning(f"QC Rejected! Reason: {qc_result.get('feedback')}.")
    else:
        log.info("QC Approved script!")
        
    final_script = director_script
    return final_script, fact_sheet

