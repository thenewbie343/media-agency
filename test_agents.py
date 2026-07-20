import sys
import json
from agents.researcher import ResearcherAgent
from agents.head_writer import HeadWriterAgent
from agents.scriptwriter import ScriptwriterAgent
from agents.director import DirectorAgent
from agents.qc_editor import QCEditorAgent

def test_agents():
    topic = "The Fall of Nokia"
    print(f"Testing AI Studio for topic: {topic}\n")
    
    researcher = ResearcherAgent()
    head_writer = HeadWriterAgent()
    scriptwriter = ScriptwriterAgent()
    director = DirectorAgent()
    qc_editor = QCEditorAgent()
    
    print("--- 1. RESEARCH ---")
    fact_sheet = researcher.research_topic(topic)
    print(json.dumps(fact_sheet, indent=2))
    
    print("\n--- 2. HEAD WRITER ---")
    outline = head_writer.write_outline(json.dumps(fact_sheet))
    print(json.dumps(outline, indent=2))
    
    print("\n--- 3. SCRIPTWRITER ---")
    raw_script = scriptwriter.write_script(json.dumps(fact_sheet), json.dumps(outline))
    print(json.dumps(raw_script, indent=2))
    
    print("\n--- 4. DIRECTOR ---")
    director_script = director.add_metadata(raw_script)
    print(json.dumps(director_script, indent=2))
    
    print("\n--- 5. QC EDITOR ---")
    qc_result = qc_editor.review_script(director_script)
    print(json.dumps(qc_result, indent=2))
    
    print("\nTEST COMPLETE!")

if __name__ == "__main__":
    test_agents()
