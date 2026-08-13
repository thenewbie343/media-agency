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

1. VISUAL DIVERSITY & VISUAL_TYPE RULES (CRITICAL):
   Do NOT default to `ai_video` for everything. You MUST select the most authentic and high-quality visual type:
   - `real_photo`: Use this whenever the scene mentions a real-world historical figure (e.g., "Vijay Mallya", "Lalit Modi", "Richard Nixon", "Narendra Modi"), real companies, or real historical products. This triggers a web search to fetch their actual face! (Example: Depicting Vijay Mallya).
   - `broll_video`: Use this for generic real-world actions, settings, or physical items (e.g., "aeroplane taking off", "pouring whiskey into a glass", "luxury yacht sailing", "courtroom gavel hitting", "stacking Indian Rupees", "spinning casino roulette", "crowd cheering", "police sirens flashing"). This downloads high-quality real stock video.
   - `motion_graphics` or `text_stat`: Use this for maps (e.g., showing flight paths, escape routes), timelines of dates, lists, percentages, or major numbers (e.g., "9,000 Crores").
   - `ai_video` or `ai_image`: Use ONLY for highly stylized, metaphorical, or hypothetical scenes (e.g., "secret meeting in a dark room", "a shadow falling over a map", "a businessman in handcuffs walking away in a dark alley") where real photos/videos absolutely do not exist.

2. LOOPS & SHOT-SPLITTING LIMITS (CRITICAL):
   No single shot of ANY type (ai_video, real_photo, broll_video) may cover more than 4.5 seconds of screen time.
   If a narration block's `duration_hint` is greater than 4.5 seconds, you MUST define MULTIPLE shots for that block (using `duration_ratio` like 0.5, 0.5 or 0.3, 0.3, 0.4) so they alternate visuals.
   For example, if a narration block is 9 seconds long, you must define at least 2 shots (e.g., Shot 1: `real_photo` of Mallya, Shot 2: `broll_video` of a private jet). If a block is 13 seconds, you must define 3-4 shots. NEVER leave a single shot to cover 5+ seconds, otherwise the video will loop terribly!

3. DETAILED AI PROMPTS:
   `ai_prompt` MUST be formatted exactly as: [SUBJECT], [ERA], [LOCATION], [ENVIRONMENT], [LIGHTING], [CAMERA ANGLE].
   Every prompt MUST be highly specific and detailed (35-50 words). 
   - BANNED: Short 3-word prompts like "Vijay Mallya in tuxedo" are strictly forbidden. 
   - GOOD Example: "Close-up portrait of Vijay Mallya, 2000s, luxury yacht deck, warm sunset lighting, shallow depth of field, dramatic cinematic camera angle."

4. STOCK FOOTAGE QUERY:
   Provide a clean `visual_query` for every shot formatted as: [SUBJECT] + [ACTION] + [LOCATION] + [ERA]. (e.g., "private jet taking off airport runway runway sunset").

5. NO ANACHRONISTIC MODERN IMAGERY:
   Never use modern digital gadgets or 21st-century assets in historical settings unless explicitly representing present-day context.

6. CAMERA MOTION:
   Set `camera_motion` strictly based on the shot's need. Use 'none' for stable shots. Alternate motion vectors (e.g., pan_left, zoom_in, pan_right) between adjacent shots.

7. TRANSITIONS & CUT REASONS:
   Set `transition_in` to 'hard_cut' by default. Only use 'fade' or 'dissolve' when passing time or changing major locations. Ensure `cut_reason` explicitly justifies the edit!

8. SEMANTIC FALLBACK MAPPING:
   Set `fallback_type` according to `visual_job`:
   - SHOW_LOCATION -> MapFallback
   - SHOW_EVIDENCE -> ClassifiedFile or ArchivalDocument
   - SHOW_PERSON -> PortraitCard
   - SHOW_OBJECT -> TechnicalDiagram
   - EXPLAIN_MECHANISM / EXPLAIN_PROCESS -> AnimatedDiagram
   - SHOW_TIME -> Timeline
   - CREATE_MYSTERY -> CinematicText

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


