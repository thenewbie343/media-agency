import json
from duckduckgo_search import DDGS
from .base_agent import BaseAgent

class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def research_topic(self, topic):
        """Searches the web and compiles a fact sheet for the given topic."""
        print(f"[*] ResearcherAgent investigating: {topic}")
        
        # 1. Fetch raw facts via DuckDuckGo
        raw_facts = []
        try:
            with DDGS() as ddgs:
                results = ddgs.text(f"{topic} history rise fall facts", max_results=5)
                for r in results:
                    raw_facts.append(r.get("body", ""))
        except Exception as e:
            print(f"[!] DuckDuckGo search failed: {e}")
            raw_facts.append("Search failed, relying on LLM internal knowledge.")
            
        facts_text = "\n".join(raw_facts)
        
        # 2. Compile Fact Sheet via LLM
        system_prompt = """You are an elite Documentary Researcher.
Your job is to read raw search snippets and compile a structured 'Fact Sheet' for a documentary.
The documentary will be in Hindi, but keep the fact sheet in English.
Focus on identifying:
1. The Status Quo (how things were before).
2. The Protagonist/Antagonist.
3. The Rising Action (key milestones).
4. The Climax/Conflict (the big problem).
5. The Resolution/Fall.

Output JSON strictly matching this schema:
{
  "topic": "...",
  "status_quo": "...",
  "protagonist": "...",
  "conflict": "...",
  "key_events": ["event 1", "event 2", "event 3"],
  "the_fall": "..."
}"""
        
        prompt = f"Topic: {topic}\n\nRaw Search Snippets:\n{facts_text}\n\nCompile the Fact Sheet."
        
        return self.call_llm(prompt, system_prompt)
