from .base_agent import BaseAgent

class HeadWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def write_outline(self, fact_sheet):
        """Takes a fact sheet and writes a strict 3-Act Outline."""
        print("[*] HeadWriterAgent drafting outline...")
        
        system_prompt = """You are an elite YouTube Documentary Head Writer (style of James Jani or MagnatesMedia).
Your job is to take a Fact Sheet and create a 3-Act Outline.
The documentary will be in Hindi, but keep the outline in English.

RULES (The 5 Pillars):
1. A Central Conflict: The hook must establish the status quo and introduce the villain/obstacle within the first act.
2. The Information Drip: Withhold the climax or the biggest revelation until Act 3.
3. Stakes: The outro must connect the story to a universal human emotion (greed, triumph, injustice).

Output JSON strictly matching this schema:
{
  "title_idea": "...",
  "act_1_the_hook_and_rise": [
    {"scene_desc": "...", "purpose": "hook"},
    {"scene_desc": "...", "purpose": "context"}
  ],
  "act_2_the_conflict": [
    {"scene_desc": "...", "purpose": "rising action"},
    {"scene_desc": "...", "purpose": "the problem"}
  ],
  "act_3_the_fall_and_stakes": [
    {"scene_desc": "...", "purpose": "climax"},
    {"scene_desc": "...", "purpose": "universal stakes"}
  ]
}"""
        
        prompt = f"Fact Sheet:\n{fact_sheet}\n\nWrite the Outline."
        
        return self.call_llm(prompt, system_prompt)
