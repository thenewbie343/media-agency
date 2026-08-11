import os
import json
import re
import logging
import time

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None

log = logging.getLogger("agency")

class BaseAgent:
    FORCE_GROQ = False

    def __init__(self, model_name="gemini-3.1-flash-lite"):
        self.model_name = model_name
        self.model = None
        
        # Setup Gemini
        gemini_key = os.environ.get("GEMINI_KEY", "")
        if not gemini_key:
            log.warning("GEMINI_KEY not found in environment. Agent calls will fail or use mock fallback.")
        else:
            if genai:
                genai.configure(api_key=gemini_key)
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )

    def _get_mock_fallback(self, prompt, system_prompt, require_json):
        cls_name = self.__class__.__name__
        log.warning(f"[{cls_name}] Operating without API keys. Returning mock data for test execution.")
        if cls_name == "ResearcherAgent":
            return {"topic": "The Fall of Nokia", "key_facts": ["Nokia dominated global mobile phones in the early 2000s.", "Failed to transition to smartphones effectively.", "Acquired by Microsoft in 2013."]}
        elif cls_name == "HeadWriterAgent":
            return {"title": "The Fall of Nokia", "acts": [{"act_number": 1, "title": "The Mobile Giant", "scenes": [1]}, {"act_number": 2, "title": "The Smartphone Crash", "scenes": [2]}]}
        elif cls_name == "ScriptwriterAgent":
            return [
                {"scene_number": 1, "voiceover": "एक समय नोकिया का मोबाइल बाज़ार पर राज था।", "caption": "Nokia once ruled the mobile market."},
                {"scene_number": 2, "voiceover": "लेकिन स्मार्टफोन की लहर में नोकिया पीछे छूट गया।", "caption": "But Nokia fell behind in the smartphone era."}
            ]
        elif cls_name == "DirectorAgent":
            scenes = []
            try:
                if "Raw Script:" in prompt:
                    script_json = prompt.split("Raw Script:\n")[1].split("\n\nAdd Director Metadata.")[0]
                    scenes = json.loads(script_json)
            except Exception:
                pass
            if not scenes:
                scenes = [
                    {"scene_number": 1, "voiceover": "Nokia dominated the market.", "caption": "Nokia dominated."},
                    {"scene_number": 2, "voiceover": "Apple launched the iPhone.", "caption": "iPhone arrived."}
                ]
            
            director_scenes = []
            env_anchor = "dimly lit corporate executive office with mahogany desk"
            style_anchor = "19th-century matte historical illustration, low-key lighting, archival museum quality"
            v_types = ["motion_graphics", "ai_video", "real_photo", "ai_image", "broll_video"]
            
            for idx, sc in enumerate(scenes):
                v_type = v_types[idx % len(v_types)]
                shot_angle = "Wide shot camera zoom in" if idx % 2 == 0 else "Close-up shot slow pan"
                enriched = dict(sc)
                enriched.update({
                    "visual_type": v_type,
                    "visual_query": f"Archival historical scene {sc.get('scene_number', idx+1)}",
                    "ai_prompt": f"corporate leadership in discussion, {env_anchor}, {shot_angle}, {style_anchor}",
                    "camera_movement": "ken_burns_zoom_in",
                    "lut": "dark_noir",
                    "overlay": "vhs_glitch",
                    "sfx": "deep_impact",
                    "bgm_mood": "dark suspense",
                    "strategic_silence_seconds": 1.5,
                    "transition_in": "hard_cut",
                    "duration_hint": 4.5
                })
                director_scenes.append(enriched)
            return director_scenes
        elif cls_name == "QCEditorAgent":
            return {"status": "APPROVED", "score": 9, "feedback": "Excellent script structure and director metadata."}
        return {"status": "ok"}
            
    def _extract_json(self, text):
        """Robustly extract JSON (array or object) from markdown/reasoning blocks."""
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"```json|```", "", text).strip()
        
        # Handle trailing commas
        text = re.sub(r",(\s*[}\]])", r"\1", text)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except: pass
                        
        raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")

    def _call_groq(self, prompt, system_prompt, require_json):
        groq_key = os.environ.get("GROQ_KEY", "")
        if not groq_key:
            raise Exception("GROQ_KEY not found for fallback")
        from groq import Groq
        client = Groq(api_key=groq_key)
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=msgs,
            temperature=0.8, max_tokens=4000
        )
        output = r.choices[0].message.content.strip()
        if require_json:
            return self._extract_json(output)
        return output

    def call_llm(self, prompt, system_prompt="", retries=4, require_json=True):
        """Calls the LLM and returns the parsed JSON response."""
        
        if BaseAgent.FORCE_GROQ:
            log.info(f"[{self.__class__.__name__}] Bypassing Gemini (Force Groq is active)")
            try:
                return self._call_groq(prompt, system_prompt, require_json)
            except Exception as e:
                log.error(f"[{self.__class__.__name__}] Groq call failed: {e}")
                if not os.environ.get("GEMINI_KEY") and not os.environ.get("GROQ_KEY"):
                    return self._get_mock_fallback(prompt, system_prompt, require_json)
                raise e

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{prompt}"
            
        gemini_key_1 = os.environ.get("GEMINI_KEY", "")
        gemini_key_2 = os.environ.get("GEMINI_KEY_2", "")
        current_key = gemini_key_1
            
        if not gemini_key_1 and not os.environ.get("GROQ_KEY"):
            return self._get_mock_fallback(prompt, system_prompt, require_json)

        for attempt in range(retries):
            try:
                log.info(f"[{self.__class__.__name__}] Calling LLM (Attempt {attempt+1}/{retries})")
                
                if not self.model:
                    raise Exception("Gemini model not initialized (no key)")
                response = self.model.generate_content(full_prompt)
                
                if not response or not response.text:
                    raise Exception("Empty response from LLM")
                    
                output = response.text
                
                if require_json:
                    return self._extract_json(output)
                return output
                
            except Exception as e:
                err_str = str(e)
                log.error(f"[{self.__class__.__name__}] LLM Call failed: {err_str}")
                if attempt < retries - 1:
                    sleep_time = 5
                    match = re.search(r"retry in ([\d\.]+)s", err_str)
                    if match:
                        sleep_time = float(match.group(1)) + 1.5
                        log.info(f"Rate limited. Detected required sleep: {sleep_time:.1f}s")
                    
                    log.info(f"[{self.__class__.__name__}] Waiting {sleep_time:.1f}s for rate limit reset...")
                    time.sleep(sleep_time)
                else:
                    # Worst-case scenario: Gemini exhausted all retries. Try Groq.
                    log.warning(f"[{self.__class__.__name__}] Gemini exhausted all retries! Falling back to Groq Llama-3.3-70B (Worst-case)...")
                    try:
                        res = self._call_groq(prompt, system_prompt, require_json)
                        BaseAgent.FORCE_GROQ = True # Flip switch for subsequent agents
                        return res
                    except Exception as groq_e:
                        log.error(f"[{self.__class__.__name__}] Groq fallback also failed: {groq_e}")
                        if not os.environ.get("GEMINI_KEY") and not os.environ.get("GROQ_KEY"):
                            return self._get_mock_fallback(prompt, system_prompt, require_json)
                        raise e
                    
        return None
