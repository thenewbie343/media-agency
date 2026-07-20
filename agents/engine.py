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
    log.info(f"🎬 AI Studio Orchestrator starting for topic: {topic}")
    
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
    outline = head_writer.write_outline(json.dumps(fact_sheet))
    
    # 4. Scriptwriting (Scriptwriter)
    log.info("3/5: Scriptwriter writing Hindi VO & Hinglish captions...")
    raw_script = scriptwriter.write_script(json.dumps(fact_sheet), json.dumps(outline))
    
    # 5. Metadata (Director)
    log.info("4/5: Director adding cinematic visual metadata...")
    director_script = director.add_metadata(raw_script)
    
    # 6. Quality Control (QC Editor)
    log.info("5/5: QC Editor reviewing...")
    qc_result = qc_editor.review_script(director_script)
    
    if qc_result.get("status") == "REJECTED":
        log.warning(f"QC Rejected! Reason: {qc_result.get('feedback')}. Applying fixes...")
        final_script = qc_result.get("fixed_script", director_script)
    else:
        log.info("QC Approved script!")
        final_script = director_script
        
    # Ensure scene keys exist just in case QC LLM dropped them
    for i, scene in enumerate(final_script):
        if "scene" not in scene:
            scene["scene"] = i + 1
            
    return final_script

