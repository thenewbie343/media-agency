import json
from .base_agent import BaseAgent
from .schema import ScriptManifest

class DirectorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        
    def add_metadata(self, raw_script):
        """Acts as the Video Director, adding visual and audio metadata to the hierarchical script."""
        print("[*] DirectorAgent adding cinematic metadata (v2.0 Schema)...")
        
        schema_json = json.dumps(ScriptManifest.model_json_schema(), indent=2)
        
        system_prompt = f"""You are an elite Video Director for YouTube documentaries.
Your job is to take a basic script (array of scenes) and upgrade it into a professional cinematic shot manifest following a strict hierarchical architecture:
Story Beat -> Narration Block -> Shots[].

CRITICAL DIRECTIVES:
1. EVERY SHOT MUST HAVE A VISUAL JOB: First determine the `visual_job` (e.g. SHOW_LOCATION, SHOW_PERSON, SHOW_EVIDENCE, EXPLAIN_MECHANISM, SHOW_TIME, CREATE_TENSION), then choose the asset type.
2. NARRATIVE INTENT: Map every story beat to an intent (HOOK, EVIDENCE, MYSTERY, etc.).
3. HARD QC RULE: No shot may exist only because you want visual variety. Every shot must answer: "What does this shot communicate that the previous shot did not?" If the answer is "nothing", omit/delete the shot.
4. SIX CONTINUITY LOCKS:
   - ERA LOCK: Maintain consistent year/time tags across sequential historical shots.
   - LOCATION LOCK: Sequential shots in the same place must share identical environment details.
   - CHARACTER CONTINUITY: Keep physical descriptions and outfits identical for recurring figures.
   - OBJECT CONTINUITY: Keep key items (weapons, documents, tools) visually identical.
   - WEATHER CONTINUITY: Maintain consistent weather conditions within scenes.
5. NO ANACHRONISTIC MODERN IMAGERY: Never use modern steel skyscrapers, digital gadgets, or 21st-century cars in historical settings unless explicitly representing present-day context.
6. CINEMATOGRAPHY & DETAILED PROMPTS: `ai_prompt` MUST be formatted as: [SUBJECT], [ERA], [LOCATION], [ENVIRONMENT], [LIGHTING], [CAMERA ANGLE]. Every prompt MUST be highly specific and detailed (35-50 words).
7. STOCK FOOTAGE QUERY: Provide a `visual_query` for every shot formatted as: [SUBJECT] + [ACTION] + [LOCATION] + [ERA]. (e.g. '1960s scientists working in underground bunker').
7. CAMERA MOTION: Set `camera_motion` strictly based on the shot's need. Use 'none' for stable shots. Do NOT rely on global zoom loops!
8. TRANSITIONS & CUT REASONS: Set `transition_in` to 'hard_cut' by default. Only use 'fade' or 'dissolve' when passing time or changing major locations. Ensure `cut_reason` explicitly justifies the edit!
9. SEMANTIC FALLBACK MAPPING: Set `fallback_type` according to `visual_job`:
   - SHOW_LOCATION -> MapFallback
   - SHOW_EVIDENCE -> ClassifiedFile or ArchivalDocument
   - SHOW_PERSON -> PortraitCard
   - SHOW_OBJECT -> TechnicalDiagram
   - EXPLAIN_MECHANISM / EXPLAIN_PROCESS -> AnimatedDiagram
   - SHOW_TIME -> Timeline
   - CREATE_MYSTERY -> CinematicText
10. METAPHOR BAN: Do not literally translate metaphors (e.g., "financial meltdown" should be a panicked stock floor, not melting coins).
11. AI VIDEO DURATION LIMIT (CRITICAL): The `ai_video` generator only creates ~3-second clips. Therefore, NO single `ai_video` shot may cover more than 4 seconds of screen time. If a narration block's `duration_hint` is greater than 4 seconds, you MUST define MULTIPLE shots for that block (using `duration_ratio` like 0.3, 0.3, 0.4) so that no single `ai_video` shot exceeds 4 seconds. Failure to do this will result in terrible looping videos!

You must return a valid JSON object matching this exact JSON schema:
{schema_json}
"""
        
        prompt = f"Raw Script:\n{json.dumps(raw_script, ensure_ascii=False, indent=2)}\n\nGenerate the complete ScriptManifest JSON."
        
        # Call LLM and get the raw dict
        output_dict = self.call_llm(prompt, system_prompt)
        
        # Validate against Pydantic model (will raise ValidationError if invalid)
        print("[*] Validating output against Pydantic schema...")
        manifest = ScriptManifest.model_validate(output_dict)
        print("[*] Schema validation successful!")
        
        return manifest.model_dump()


