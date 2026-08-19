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
            return {
                "schema_version": "2.0",
                "project_meta": {
                    "topic": "The Fall of Nokia",
                    "genre": "documentary",
                    "language": "hindi",
                    "visual_bible": {
                        "era": "2000s",
                        "locations": ["Espoo, Finland", "USA"],
                        "lighting": "cinematic dramatic",
                        "color_language": "cool tones",
                        "film_texture": "clean digital"
                    }
                },
                "story_beats": [
                    {
                        "beat_id": "b001",
                        "time_context": {
                            "year": "2000s",
                            "mode": "historical",
                            "location": "Espoo, Finland",
                            "transition_reason": "Establishing historical market dominance"
                        },
                        "narrative_intent": "HOOK",
                        "description": "The Mobile Giant",
                        "attention_intensity": 0.8,
                        "chapter_color_language": "cool tones",
                        "narration_blocks": [
                            {
                                "block_id": "n001",
                                "voiceover": "एक समय नोकिया का मोबाइल बाज़ार पर राज था।",
                                "caption": "Nokia once ruled the mobile market.",
                                "duration_hint": 4.0,
                                "strategic_silence": {
                                    "duration_seconds": 0.5,
                                    "position": "end",
                                    "ambient_level": -35,
                                    "visual_behavior": "hold_frame"
                                },
                                "audio_metadata": {
                                    "music_energy": 0.5,
                                    "music_duck_amount": -15
                                },
                                "shots": [
                                    {
                                        "shot_id": "n001_s001",
                                        "duration_mode": "ratio",
                                        "duration_ratio": 1.0,
                                        "shot_role": "ESTABLISHING",
                                        "asset_provenance": "STOCK",
                                        "shot_size": "wide",
                                        "camera_angle": "eye_level",
                                        "lens": "wide_angle_lens",
                                        "composition": "rule_of_thirds",
                                        "visual_job": "SHOW_LOCATION",
                                        "visual_type": "ai_image",
                                        "fallback_type": "MapFallback",
                                        "visual_description": "Wide view of Nokia headquarters in Finland.",
                                        "visual_query": "Nokia headquarters Finland 2000s",
                                        "ai_prompt": "Nokia headquarters, 2000s, Finland, exterior office, dramatic lighting, wide shot",
                                        "camera_motion": "zoom_in",
                                        "motion_intensity": 0.3,
                                        "transition_in": "hard_cut",
                                        "cut_reason": "establish_nokia_headquarters",
                                        "visual_importance": 0.7,
                                        "continuity": {
                                            "group_id": "grp1",
                                            "characters": [],
                                            "location": "Espoo, Finland",
                                            "environment": "exterior corporate headquarters",
                                            "time_period": "2000s",
                                            "lighting": "daylight"
                                        }
                                    }
                                ]
                            },
                            {
                                "block_id": "n002",
                                "voiceover": "लेकिन स्मार्टफोन की लहर में नोकिया पीछे छूट गया।",
                                "caption": "But Nokia fell behind in the smartphone era.",
                                "duration_hint": 4.0,
                                "strategic_silence": {
                                    "duration_seconds": 0.5,
                                    "position": "end",
                                    "ambient_level": -35,
                                    "visual_behavior": "hold_frame"
                                },
                                "audio_metadata": {
                                    "music_energy": 0.5,
                                    "music_duck_amount": -15
                                },
                                "shots": [
                                    {
                                        "shot_id": "n002_s001",
                                        "duration_mode": "ratio",
                                        "duration_ratio": 1.0,
                                        "shot_role": "ACTION",
                                        "asset_provenance": "STOCK",
                                        "shot_size": "medium",
                                        "camera_angle": "low_angle",
                                        "lens": "standard_lens",
                                        "composition": "center_framed",
                                        "visual_job": "SHOW_OBJECT",
                                        "visual_type": "ai_image",
                                        "fallback_type": "Timeline",
                                        "visual_description": "Classic Nokia mobile phone on an office desk.",
                                        "visual_query": "classic Nokia phone desk 2000s",
                                        "ai_prompt": "Classic Nokia mobile phone, 2000s, office desk, dramatic lighting, medium shot",
                                        "camera_motion": "pan_right",
                                        "motion_intensity": 0.3,
                                        "transition_in": "hard_cut",
                                        "cut_reason": "showcase_mobile_phone",
                                        "visual_importance": 0.7,
                                        "continuity": {
                                            "group_id": "grp1",
                                            "characters": [],
                                            "location": "Espoo, Finland",
                                            "environment": "corporate office",
                                            "time_period": "2000s",
                                            "lighting": "indoor fluorescent"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
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
