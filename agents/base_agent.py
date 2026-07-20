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
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model_name = model_name
        
        # Setup Gemini
        gemini_key = os.environ.get("GEMINI_KEY", "")
        if not gemini_key:
            log.warning("GEMINI_KEY not found in environment. Agent calls will fail.")
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
            
    def _extract_json(self, text):
        """Robustly extract JSON (array or object) from markdown/reasoning blocks."""
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"```json|```", "", text).strip()
        
        try:
            # First try parsing directly
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # Try to find array
        start_arr = text.find("[")
        start_obj = text.find("{")
        
        if start_arr != -1 and (start_obj == -1 or start_arr < start_obj):
            # Probably an array
            depth = 0
            for i in range(start_arr, len(text)):
                if text[i] == "[": depth += 1
                elif text[i] == "]":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start_arr:i+1])
                        except: pass
                        break
                        
        if start_obj != -1:
            # Probably an object
            depth = 0
            for i in range(start_obj, len(text)):
                if text[i] == "{": depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start_obj:i+1])
                        except: pass
                        break
                        
        raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")

    def call_llm(self, prompt, system_prompt="", retries=3, require_json=True):
        """Calls the LLM and returns the parsed JSON response."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{prompt}"
            
        for attempt in range(retries):
            try:
                log.info(f"[{self.__class__.__name__}] Calling LLM (Attempt {attempt+1}/{retries})")
                
                # We use the standard gemini model for complex reasoning
                response = self.model.generate_content(full_prompt)
                
                if not response or not response.text:
                    raise Exception("Empty response from LLM")
                    
                output = response.text
                
                if require_json:
                    return self._extract_json(output)
                return output
                
            except Exception as e:
                log.error(f"[{self.__class__.__name__}] LLM Call failed: {e}")
                if attempt < retries - 1:
                    time.sleep(5)
                else:
                    raise
                    
        return None
