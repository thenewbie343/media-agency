import os
import sys
import logging
from pathlib import Path

log = logging.getLogger("preflight")

def run_preflight_checks(mode="DRAFT"):
    """
    Validates all API keys, dependencies, and vision models before expensive generation.
    Returns: status string ("READY", "DEGRADED", "BLOCKED")
    """
    status = "READY"
    issues = []
    
    # 1. GenAI / Groq API Keys
    if not os.environ.get("GEMINI_KEY") and not os.environ.get("GROQ_API_KEY"):
        issues.append("Missing GEMINI_KEY or GROQ_API_KEY. Generation will fail.")
        status = "BLOCKED"
        
    # 2. Vision Model Smoke Test
    vision_status = "READY"
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_KEY", ""))
        vision_model_name = os.environ.get("VISION_MODEL", "gemini-2.0-flash")
        
        # Test availability
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # We don't strictly block on not finding the name in list_models because proxy endpoints 
        # sometimes hide them, but we do a tiny generation if possible.
        model = genai.GenerativeModel(vision_model_name)
        # Smoke test:
        resp = model.generate_content("Smoke test. Reply with 'OK'.")
        if not resp or not resp.text:
            vision_status = "UNAVAILABLE"
            issues.append(f"Vision model {vision_model_name} returned empty response.")
    except Exception as e:
        vision_status = "UNAVAILABLE"
        issues.append(f"Vision model smoke test failed: {e}")
        
    if vision_status == "UNAVAILABLE":
        if mode == "FINAL":
            status = "BLOCKED"
            issues.append("Vision unavailable in FINAL mode is a hard blocker.")
        else:
            status = "DEGRADED"
            
    os.environ["VISION_STATUS"] = vision_status

    # 3. YouTube config
    youtube_token = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not youtube_token:
        issues.append("YOUTUBE_TOKEN_JSON missing. YouTube discovery DEGRADED.")
        if status == "READY": status = "DEGRADED"
        
    # 4. AI Video Compatibility check
    wan_status = "READY"
    try:
        import torch
        # We do not load the full model here to save memory, just check if diffusers is available
        import diffusers
    except ImportError:
        wan_status = "UNAVAILABLE"
        issues.append("AI Video / Diffusers not installed.")
        
    os.environ["AI_VIDEO_HEALTH"] = wan_status

    if issues:
        log.warning("Preflight Issues Detected:")
        for issue in issues:
            log.warning(f" - {issue}")
            
    log.info(f"Preflight Final Status: {status}")
    return status

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"Preflight result: {run_preflight_checks('DRAFT')}")
