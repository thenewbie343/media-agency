"""
=============================================================
  ULTIMATE HINDI CHANNEL — pipeline.py v5.2 DUAL-SCRIPT
=============================================================
TWO MODES:
  Mode 1 (Daily Auto): Reads topics.json → 3 videos/day
                        Finance | Tech | Crime in Hindi
  Mode 2 (Manual):     /make command or GitHub workflow
                        Any genre/lang/duration

WHAT'S IN v5.2:
  - Dual-script engine: Devanagari voiceover + Hinglish captions
  - Kokoro Hindi voices: hm_omega (male) / hf_alpha (female)
  - Fixed audio: proper float32→int16 conversion, no static
  - English captions on screen, Hindi audio from Kokoro
  - Niche engine: finance/tech/crime auto-settings
  - 3-layer audio: voice + music + SFX
  - Freesound SFX per scene emotion
  - freepd.com/incompetech background music (CC licensed)
  - Rebuilt captions: drawtext, lower-third, 2-3 words
  - Key word yellow highlighting in captions
  - Topic-locked Pexels (no more Dubai waterpark)
  - Film grain + LUT per genre
  - Gemini key rotation (2 keys)
  - Working Groq models (June 2026)
  - Full fallback chain at every stage
=============================================================
"""

import os, json, time, asyncio, logging, requests, subprocess
import random, re, shutil, tempfile
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agency")

def extract_json_array(text):
    """Robustly extract a JSON array even if the model added reasoning text before/after."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```json|```", "", text)
    start = text.find("[")
    if start == -1:
        raise ValueError("No JSON array found in response")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return _salvage_truncated_array(text[start:])

def _salvage_truncated_array(fragment):
    objects = []
    depth = 0
    obj_start = None
    for i, ch in enumerate(fragment):
        if ch == "{":
            if depth == 0: obj_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and obj_start is not None:
                objects.append(fragment[obj_start:i+1])
                obj_start = None
    if not objects:
        raise ValueError("Truncated response contained no complete objects")
    return "[" + ",".join(objects) + "]"

# ─── Secrets ────────────────────────────────────────────────
GROQ_KEY        = os.environ.get("GROQ_KEY", "")
GEMINI_KEY      = os.environ.get("GEMINI_KEY", "")
GEMINI_KEY_2    = os.environ.get("GEMINI_KEY_2", "")
PEXELS_KEY      = os.environ.get("PEXELS_KEY", "")
PIXABAY_KEY     = os.environ.get("PIXABAY_KEY", "")
FREESOUND_KEY   = os.environ.get("FREESOUND_KEY", "")
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT   = os.environ.get("TELEGRAM_CHAT_ID", "")
RAW_INPUT       = os.environ.get("TOPIC", "")
NICHE_INPUT     = os.environ.get("NICHE", "")
SCRIPT_INPUT    = os.environ.get("SCRIPT", "")

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "moonshotai/kimi-k2-instruct",
]

# ─── Niche presets ──────────────────────────────────────────
NICHE_PRESETS = {
    "finance": {
        "genre": "documentary",
        "lang": "hindi",
        "default_duration": 8,
        "voice": "hi-IN-MadhurNeural",
        "style": "Professional Hindi finance narrator. Serious, data-driven, authoritative like CNBC Awaaz. Build suspense around money facts.",
        "hook_type": "shocking money fact or financial disaster",
        "music_mood": "serious corporate dramatic",
        "visual_prefix": "finance money India business",
        "sfx_default": "deep_impact",
        "color_grade": "teal_orange",
        "scenes_per_min": 12,
    },
    "tech": {
        "genre": "study",
        "lang": "hindi",
        "default_duration": 7,
        "voice": "hi-IN-MadhurNeural",
        "style": "Simple Hindi tech explainer. Friendly, clear, like Tech Burner in Hindi. Make complex tech feel easy and fun.",
        "hook_type": "surprising fact about technology people use daily",
        "music_mood": "calm lo-fi focus",
        "visual_prefix": "technology digital modern",
        "sfx_default": "click",
        "color_grade": "cool_blue",
        "scenes_per_min": 12,
    },
    "crime": {
        "genre": "documentary",
        "lang": "hindi",
        "default_duration": 10,
        "voice": "hi-IN-MadhurNeural",
        "style": "Gripping Hindi true crime narrator. Dark, suspenseful, building tension like CrimeTak. Every line must make the viewer afraid to blink.",
        "hook_type": "shocking crime fact or terrifying moment that happened",
        "music_mood": "dark suspense thriller",
        "visual_prefix": "crime mystery dark dramatic",
        "sfx_default": "riser",
        "color_grade": "dark_noir",
        "scenes_per_min": 15,
    },
}

# ─── Genre presets (manual mode) ─────────────────────────────
GENRE_PRESETS = {
    "documentary": {"style":"BBC/Netflix documentary. Cinematic, authoritative.","scenes_per_min":12,"default_dur":5},
    "shorts":      {"style":"Viral YouTube Shorts. Ultra-fast, max energy.","scenes_per_min":20,"default_dur":1},
    "cartoon":     {"style":"Fun animated YouTube. Energetic, playful, uses Whoa!","scenes_per_min":15,"default_dur":4},
    "study":       {"style":"Clear educational explainer. Simple, structured.","scenes_per_min":12,"default_dur":8},
    "ad":          {"style":"30-second brand ad. Hook in 3s. Problem→Solution→CTA.","scenes_per_min":20,"default_dur":1},
    "typography":  {"style":"Ultra-short punchy phrases. Max 5 words per line.","scenes_per_min":15,"default_dur":2},
}

VOICE_MAP = {
    "hindi":   ["hi-IN-MadhurNeural",      "hi-IN-SwaraNeural"],
    "english": ["en-GB-RyanNeural",         "en-US-ChristopherNeural"],
    "spanish": ["es-ES-AlvaroNeural",       "es-MX-JorgeNeural"],
    "french":  ["fr-FR-HenriNeural",        "fr-FR-DeniseNeural"],
    "german":  ["de-DE-ConradNeural",       "de-DE-KatjaNeural"],
}

WORKSPACE = Path(f"workspace_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
WORKSPACE.mkdir(exist_ok=True)

# ─── Helpers ──────────────────────────────────────────────────
def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id":TELEGRAM_CHAT,"text":f"🎬 {msg}"}, timeout=10)
    except: pass

def _save(data, name):
    with open(WORKSPACE/name,"w",encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

_gem_idx = 0
def gemini(prompt, model="gemini-2.5-flash"):
    global _gem_idx
    import google.generativeai as genai
    keys = [k for k in [GEMINI_KEY, GEMINI_KEY_2] if k]
    if not keys: raise ValueError("No Gemini keys")
    for _ in range(len(keys)):
        try:
            genai.configure(api_key=keys[_gem_idx % len(keys)])
            return genai.GenerativeModel(model).generate_content(prompt).text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                log.warning(f"Gemini key {_gem_idx} quota hit, rotating...")
                _gem_idx += 1; time.sleep(2)
            else: raise
    raise RuntimeError("All Gemini keys exhausted")

def groq(prompt, max_tokens=4000):
    from groq import Groq
    client = Groq(api_key=GROQ_KEY)
    for model in GROQ_MODELS:
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content":prompt}],
                temperature=0.8, max_tokens=max_tokens)
            return r.choices[0].message.content.strip()
        except Exception as e:
            log.warning(f"Groq {model}: {e}")
            time.sleep(2)
    raise RuntimeError("All Groq models failed")

# ═══════════════════════════════════════════════════════════
#  DUAL-SCRIPT INSTRUCTIONS
#  voiceover = Devanagari for Kokoro Hindi TTS
#  caption   = Hinglish for on-screen English text
# ═══════════════════════════════════════════════════════════

DEVANAGARI_VOICE_INSTRUCTION = """Write voiceover in NATURAL HINGLISH vocabulary using Devanagari script.
CRITICAL RULES:
- Use Devanagari script, but write the HINGLISH words Indians actually speak — NOT pure formal Hindi
- English loanwords must be written in Devanagari phonetically exactly as Indians pronounce them:
  "stock" = "स्टॉक", "crash" = "क्रैश", "app" = "ऐप", "bank" = "बैंक", "company" = "कंपनी"
  "fraud" = "फ्रॉड", "scam" = "स्कैम", "digital" = "डिजिटल", "mobile" = "मोबाइल"
  "money" = "मनी", "market" = "मार्केट", "loss" = "लॉस", "profit" = "प्रॉफिट"
  "reality" = "रियलिटी", "exposed" = "एक्सपोज्ड", "truth" = "सच्चाई"
- Use common spoken Hindi words, NOT formal news Hindi:
  GOOD: "बरबाद" (not "विनाश"), "उड़ गया" (not "नष्ट"), "पैसा" (not "धन"), "झटका" (not "आघात")
  GOOD: "झूठ" (not "मिथ्या"), "चोरी" (not "अपहरण"), "पकड़ा" (not "गिरफ्तार")
- Each scene must say ONE new thing. NEVER repeat the same fact twice.
- If you run out of facts, STOP. Do not pad. Better 8 strong scenes than 20 repetitive ones.
- Spoken grammar only — like a YouTuber talking to a friend, not a news anchor
- Max 12 words per scene

Example GOOD: "पेटीएम का स्टॉक रातों रात क्रैश हो गया, कंपनी का मार्केट कैप उड़ गया।"
Example BAD (pure formal Hindi): "पेटीएम के शेयरों में भारी गिरावट दर्ज की गई, संस्था का पूंजी मूल्य नष्ट हो गया।"
Example BAD (Roman): "Paytm ka stock crash ho gaya"
"""

HINGLISH_CAPTION_INSTRUCTION = """Write caption in HINGLISH — natural Hindi-English code-mixed in ROMAN/ENGLISH ALPHABET.
- Match the meaning of the Devanagari voiceover but in casual Hinglish
- Use the same English loanwords as the voiceover: stock, crash, app, bank, scam, fraud
- Keep it short and punchy for on-screen text
- Max 10 words per caption

Example voiceover: "पेटीएम का स्टॉक रातों रात क्रैश हो गया, कंपनी का मार्केट कैप उड़ गया।"
Example caption: "Paytm ka stock crash ho gaya, company ka market cap ud gaya!"
"""
# Legacy instruction for non-Hindi or fallback
HINGLISH_INSTRUCTION = """Write ALL voiceover in HINGLISH — natural Hindi-English code-mixed
language written ENTIRELY IN ROMAN/ENGLISH ALPHABET, exactly like popular Indian YouTubers
speak (Tech Burner, Ashish Chanchlani, Finance with Sharan). 

CRITICAL RULES:
- NEVER use Devanagari script (देवनागरी). Every word must be spelled in Roman letters.
- Mix Hindi and English naturally: "Yeh dekh ke aapka dimaag ghoom jayega" not pure English,
  not pure Hindi.
- Use common Hinglish spellings: "kya", "hai", "nahi", "matlab", "bilkul", "paisa", "sach",
  written in Roman letters exactly like that.
- Keep it casual and punchy, like a viral reel script, not formal news Hindi.

Example GOOD line: "Paytm ka stock crash ho gaya raatों raat, aur kisi ko pata nahi chala kyun."
Example BAD line (pure Devanagari, DO NOT DO THIS): "पेटीएम का स्टॉक रातों रात क्रैश हो गया"
Example BAD line (too formal/textbook Hindi): "पेटीएम के शेयरों में भारी गिरावट दर्ज की गई।"
"""

ASSETS_DIR = Path("assets")

def pick_asset(subfolder, extension=None):
    """Returns a random file path from assets/<subfolder>/, or None if empty/missing."""
    folder = ASSETS_DIR / subfolder
    if not folder.exists():
        return None
    if extension:
        files = list(folder.glob(f"*.{extension}"))
    else:
        files = [f for f in folder.iterdir() if f.is_file()]
    return str(random.choice(files)) if files else None

def get_caption_font(bold=False):
    """Real premium font if uploaded, otherwise safe system fallback."""
    folder = ASSETS_DIR / "fonts" / "caption"
    if folder.exists():
        files = list(folder.glob("*.ttf")) + list(folder.glob("*.otf"))
        if files:
            bold_kw = ("bold", "black", "heavy", "juice", "cdhv")
            if bold:
                matches = [f for f in files if any(k in f.stem.lower() for k in bold_kw)]
            else:
                matches = [f for f in files if not any(k in f.stem.lower() for k in bold_kw)]
            pool = matches if matches else files
            return str(random.choice(pool))
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

LUT_KEYWORD_MAP = {
    "teal_orange": ["warm cinema", "kodak", "clean straight", "gold rush"],
    "cool_blue":   ["blue cold", "blue moon", "blue ice", "blue steel", "matrix green"],
    "dark_noir":   ["noir", "iron", "bleach"],
    "cinematic":   ["warm cinema", "clean straight", "big"],
    "cartoon":     ["thermal royalty", "thermal picasso", "thermal plastic", "gold rush"],
    "energetic":   ["thermal vice", "thermal crush", "cross"],
}

def get_lut_file(color_grade):
    """Finds a real .cube LUT matching the genre mood."""
    folder = ASSETS_DIR / "luts"
    if not folder.exists():
        return None
    all_luts = list(folder.glob("*.cube"))
    if not all_luts:
        return None
    keywords = LUT_KEYWORD_MAP.get(color_grade, [])
    matches = [f for f in all_luts if any(kw in f.stem.lower() for kw in keywords)]
    if not matches:
        return None
    return str(random.choice(matches))

def get_overlay_video():
    """Random VHS/glitch video overlay (.mp4) if uploaded."""
    return pick_asset("overlays", "mp4")

def extract_json_object(text):
    """Robust extraction for a single {...} object."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```json|```", "", text)
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return _salvage_truncated_object(text[start:])

def _salvage_truncated_object(fragment):
    last_complete = fragment.rfind('",')
    if last_complete == -1:
        last_complete = fragment.rfind('"}')
        if last_complete == -1:
            raise ValueError("Cannot salvage truncated object")
        return fragment[:last_complete+2]
    trimmed = fragment[:last_complete+1].rstrip(',')
    return trimmed + "}"

def extract_english_prefix(topic, genre="documentary"):
    """Pulls out English/ASCII words for stock search."""
    english_words = re.findall(r'[A-Za-z][A-Za-z0-9]*', topic)
    if english_words:
        return " ".join(english_words[:4])
    fallback = {
        "documentary": "news report cinematic",
        "study": "technology explainer",
        "cartoon": "colorful illustration",
        "shorts": "dramatic breaking news",
        "ad": "modern product",
        "typography": "abstract background",
    }
    return fallback.get(genre, "cinematic dramatic scene")

def sanitize_visual_term(term, vprefix, niche="", is_prompt=False):
    """Strip Devanagari, ensure English-only for stock APIs."""
    if not term:
        term = vprefix
    cleaned = re.sub(r'[ऀ-ॿ]+', ' ', term)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    if len(cleaned) < 3:
        generic_pool = {
            "finance": ["bank building interior", "stock market chart", "worried person office", "indian currency notes"],
            "tech":    ["modern office technology", "smartphone screen closeup", "data center servers", "digital network graphic"],
            "crime":   ["dark city street night", "police investigation scene", "courtroom dramatic", "newspaper headline dramatic"],
        }
        pool = generic_pool.get(niche, ["cinematic dramatic scene", "modern city aerial", "dramatic lighting interior"])
        cleaned = random.choice(pool)
    if is_prompt:
        cleaned += ", no text, no logos, no brand names, no faces"
    return cleaned

def parse_input():
    """Returns unified config dict."""
    log.info(f"parse_input: SCRIPT_INPUT length={len(SCRIPT_INPUT)} chars")
    if SCRIPT_INPUT:
        log.info(f"parse_input: Script provided (first 80 chars): {SCRIPT_INPUT[:80]}...")
    else:
        log.info("parse_input: No script provided — will generate with AI")

    if NICHE_INPUT and NICHE_INPUT in NICHE_PRESETS:
        preset = NICHE_PRESETS[NICHE_INPUT]
        topic = RAW_INPUT or f"Latest {NICHE_INPUT} news"
        parts = topic.strip().split()
        sched = "18:00"
        if parts and re.match(r'^\d{1,2}:\d{2}$', parts[-1]):
            sched = parts[-1]; topic = " ".join(parts[:-1])
        return {
            "mode": "auto",
            "niche": NICHE_INPUT,
            "topic": topic.strip(),
            "genre": preset["genre"],
            "lang": preset["lang"],
            "duration_min": preset["default_duration"],
            "schedule": sched,
            "style": preset["style"],
            "hook_type": preset["hook_type"],
            "music_mood": preset["music_mood"],
            "visual_prefix": preset["visual_prefix"],
            "sfx_default": preset["sfx_default"],
            "color_grade": preset["color_grade"],
            "scenes_per_min": preset["scenes_per_min"],
            "voice": preset["voice"],
            "provided_script": SCRIPT_INPUT or None,
        }

    raw = RAW_INPUT.strip()
    genre = lang = duration = None
    for pat,key in [(r'--genre\s+(\w+)','g'),(r'--lang\s+(\w+)','l'),(r'--duration\s+(\d+)','d')]:
        m = re.search(pat, raw, re.I)
        if m:
            v = m.group(1).lower()
            if key=='g': genre=v
            elif key=='l': lang=v
            else: duration=int(v)
            raw = raw[:m.start()]+raw[m.end():]
    parts = raw.strip().split()
    sched = "18:00"
    if parts and re.match(r'^\d{1,2}:\d{2}$', parts[-1]):
        sched=parts[-1]; parts=parts[:-1]
    topic = " ".join(parts).strip() or "Interesting Topic"
    genre = genre or "documentary"
    lang  = lang  or "hindi"
    dur   = duration or 5
    gp    = GENRE_PRESETS.get(genre, GENRE_PRESETS["documentary"])
    return {
        "mode": "manual",
        "niche": None,
        "topic": topic,
        "genre": genre,
        "lang": lang,
        "duration_min": dur,
        "schedule": sched,
        "style": gp["style"],
        "hook_type": "shocking or surprising fact",
        "music_mood": "cinematic dramatic",
        "visual_prefix": extract_english_prefix(topic, genre),
        "sfx_default": "whoosh",
        "color_grade": "cinematic",
        "scenes_per_min": gp["scenes_per_min"],
        "voice": VOICE_MAP.get(lang, VOICE_MAP["hindi"])[0],
        "provided_script": None,
    }

# ═══════════════════════════════════════════════════════════
#  STAGE 1 — RESEARCH
# ═══════════════════════════════════════════════════════════
def stage_1_research(cfg):
    topic = cfg["topic"]
    lang  = cfg["lang"]
    log.info(f"Stage 1: Research — {topic}")
    tg(f"📚 Researching: {topic}")
    lang_note = HINGLISH_INSTRUCTION if lang == "hindi" else (f"Write ALL content in {lang} language." if lang != "english" else "")
    try:
        text = gemini(f"""Research: "{topic}"
{lang_note}
Return ONLY valid JSON (no markdown):
{{"hook":"single most shocking fact about this topic in {lang}",
  "hook_question":"mystery question that creates curiosity in {lang}",
  "key_facts":["fact1","fact2","fact3","fact4","fact5","fact6","fact7","fact8"],
  "statistics":["stat with number 1","stat with number 2","stat with number 3"],
  "timeline":["earliest event","event2","event3","recent event"],
  "visual_themes":["visual keyword 1","visual keyword 2","visual keyword 3"]
}}""")
        text = text.strip().replace("```json","").replace("```","").strip()
        r = json.loads(text)
        log.info(f"Stage 1 done. Hook: {r.get('hook','')[:60]}")
        return r
    except Exception as e:
        log.warning(f"Stage 1 Gemini failed: {e}")
    try:
        from bs4 import BeautifulSoup
        resp = requests.get(f"https://html.duckduckgo.com/html/?q={quote(topic)}",
            headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        snips = [s.get_text() for s in BeautifulSoup(resp.text,"html.parser").select(".result__snippet")][:8]
        return {"hook":snips[0] if snips else f"The truth about {topic}",
                "hook_question":f"What really happened with {topic}?",
                "key_facts":snips,"statistics":[],"timeline":[],"visual_themes":[topic]}
    except:
        return {"hook":f"Everything you know about {topic} is wrong.","hook_question":f"The real story of {topic}?",
                "key_facts":[f"Incredible truth about {topic}"],"statistics":[],"timeline":[],"visual_themes":[topic]}

# ═══════════════════════════════════════════════════════════
#  STAGE 2 — SCRIPT (DUAL-SCRIPT: Devanagari + Hinglish)
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
#  STAGE 2 — SCRIPT (DUAL-SCRIPT: Devanagari + Hinglish)
#  v5.3 FIXES: research-driven length, deduplication, anti-pad
# ═══════════════════════════════════════════════════════════

def _semantic_similarity(text1, text2):
    """Word-overlap similarity to detect repeated scenes."""
    if not text1 or not text2:
        return 0.0
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    if not words1 or not words2:
        return 0.0
    overlap = len(words1 & words2)
    return overlap / max(len(words1), len(words2))


def parse_provided_script(script_text, cfg):
    """Convert user-provided script into scene JSON with dual fields."""
    log.info("Stage 2: Parsing provided script...")
    topic   = cfg["topic"]
    sfx_def = cfg.get("sfx_default","whoosh")
    vprefix = cfg.get("visual_prefix", topic)
    try:
        text = groq(f"""Parse this script into video scenes.
Script:
{script_text[:3000]}

Topic: {topic}
Language: {cfg['lang']}

Return ONLY JSON array (no markdown):
[{{"scene":1,"voiceover":"Devanagari Hindi for TTS","caption":"Hinglish for screen","visual_type":"stock_video","visual_search":"English keyword only","ai_prompt":"English cinematic description only","emotion":"dramatic","sfx":"{sfx_def}","duration_hint":4}}]

Rules:
- Split at natural pause/sentence boundaries
- voiceover: HINGLISH vocabulary in Devanagari — "स्टॉक" not "शेयर", "क्रैश" not "दुर्घटना"
- caption: Hinglish (Roman) for on-screen text
- Max 12 words per voiceover, max 10 words per caption
- visual_search and ai_prompt MUST BE IN ENGLISH ONLY
- sfx: deep_impact|whoosh|click|riser|none""", max_tokens=3000)
        scenes = json.loads(extract_json_array(text))
        t = 0.0
        for s in scenes:
            s["start_time"] = t; t += float(s.get("duration_hint",4))
            s["visual_search"] = sanitize_visual_term(s.get("visual_search",""), vprefix, cfg.get("niche",""))
            s["ai_prompt"] = sanitize_visual_term(s.get("ai_prompt",""), vprefix, cfg.get("niche",""), is_prompt=True)
        log.info(f"Stage 2: Parsed {len(scenes)} scenes from provided script")
        return scenes
    except Exception as e:
        log.warning(f"Script parse failed: {e}")
        sentences = [s.strip() for s in re.split(r'[।\.\!\?]+', script_text) if len(s.strip()) > 10]
        t = 0.0; scenes = []
        for i, sent in enumerate(sentences[:40]):
            vt = "text_stat" if i % 10 == 9 else "stock_video" if i % 3 == 1 else "ai_image"
            s = {"scene":i+1,"voiceover":sent[:80],"caption":sent[:80],
                 "visual_type":vt,"visual_search":f"{vprefix} cinematic",
                 "ai_prompt":f"cinematic {topic} scene","emotion":"dramatic",
                 "sfx":sfx_def,"duration_hint":4,"start_time":t}
            scenes.append(s); t += 4
        return scenes


def stage_2_script(research, cfg):
    topic       = cfg["topic"]
    lang        = cfg["lang"]
    style       = cfg["style"]
    hook_type   = cfg["hook_type"]
    dur         = cfg["duration_min"]
    scenes_pm   = cfg["scenes_per_min"]
    vprefix     = cfg.get("visual_prefix", topic)
    sfx_def     = cfg.get("sfx_default","whoosh")
    niche       = cfg.get("niche","")

    if cfg.get("provided_script"):
        return parse_provided_script(cfg["provided_script"], cfg)

    log.info(f"Stage 2: Writing dual script for {topic}")
    tg(f"✍️ Writing script...")

    # FIX v5.3: Cap target based on research depth, not blind duration
    unique_facts = len([f for f in research.get("key_facts", []) if len(f) > 15])
    unique_stats = len(research.get("statistics", []))
    unique_timeline = len(research.get("timeline", []))
    total_angles = max(4, unique_facts + unique_stats + unique_timeline)
    
    # Each angle gets 2 scenes (setup + payoff), plus hook and conclusion
    target = min(max(10, int(dur * scenes_pm)), total_angles * 2 + 4)
    log.info(f"Stage 2: Research depth = {total_angles} angles → {target} scenes max")

    # Use dual-script instructions for Hindi
    if lang == "hindi":
        voice_note = DEVANAGARI_VOICE_INSTRUCTION
        caption_note = HINGLISH_CAPTION_INSTRUCTION
    else:
        voice_note = HINGLISH_INSTRUCTION if lang == "hindi" else (f"ALL voiceover in {lang}." if lang != "english" else "")
        caption_note = ""

    hook      = research.get("hook","")
    hook_q    = research.get("hook_question","")
    facts_str = "\n".join(f"- {f}" for f in research.get("key_facts",[])[:7])
    stats_str = "\n".join(f"- {s}" for s in research.get("statistics",[])[:3])

    niche_note = ""
    if niche == "finance":
        niche_note = "Include real numbers, percentages, losses/gains. Mention specific amounts in rupees. Make viewers worried about their money."
    elif niche == "tech":
        niche_note = "Use simple analogies. Every technical term must be explained immediately. Make it feel like talking to a friend."
    elif niche == "crime":
        niche_note = "Build tension slowly. Use dramatic pauses. Reveal information bit by bit. Make the viewer feel like they are watching a thriller."

    log.info("Stage 2: Generating story outline first...")
    num_beats = max(6, min(15, target // 8))
    try:
        outline_text = groq(f"""You are a world-class viral Hindi YouTube scriptwriter.
Style: {style}
{niche_note}

Topic: "{topic}"
Hook fact: {hook}
Hook question: {hook_q}
Key facts:
{facts_str}
Stats:
{stats_str}

Write a {num_beats}-point STORY OUTLINE for this video — one clear, connected story
that builds from hook to conclusion, not a list of random facts.
Each point = one beat of the story in ONE short sentence (English is fine here).
Point 1 MUST be the shocking hook. Points must flow in logical order.

Return ONLY a JSON array of {num_beats} short strings, no markdown:
["beat 1 sentence", "beat 2 sentence", ...]""", max_tokens=1000)
        outline = json.loads(extract_json_array(outline_text))
        if not outline or len(outline) < 4:
            raise ValueError("Outline too short")
        outline_str = "\n".join(f"{i+1}. {b}" for i, b in enumerate(outline))
        log.info(f"Stage 2: Outline has {len(outline)} beats")
    except Exception as e:
        log.warning(f"Outline generation failed ({e}), scenes may be less connected")
        outline_str = f"1. {hook}\n2. Explore the key facts about {topic}\n3. Wrap up with the significance of {topic}"
        outline = None

    # FIX v5.3: Smaller batches, deduplication, early stop
    BATCH_SIZE = 6
    full_script = []
    stalled = 0
    max_stalled = 2

    while len(full_script) < target and stalled < max_stalled:
        remaining = target - len(full_script)
        batch_n = min(BATCH_SIZE, remaining)
        start_num = len(full_script) + 1

        # Build context from ALL previous scenes, not just the last one
        prev_scenes_text = ""
        if len(full_script) >= 3:
            covered_topics = []
            for s in full_script[-6:]:
                covered_topics.append(s.get("voiceover", "")[:40])
            prev_scenes_text = "ALREADY COVERED (do NOT repeat these angles):\n" + "\n".join(f"- {c}" for c in covered_topics)
        elif full_script:
            prev_scenes_text = f'Previous scene: "{full_script[-1].get("voiceover", "")[:80]}"'

        continuity = (
            f"STORY OUTLINE:\n{outline_str}\n\n"
            f"{prev_scenes_text}\n\n"
            f"Write scenes {start_num} to {start_num + batch_n - 1}. "
            f"CRITICAL: Each scene must cover a NEW angle not listed above. "
            f"NEVER repeat information already stated. If you run out of facts, end early."
        )

        prompt = f"""You are a world-class viral Hindi YouTube scriptwriter.
Style: {style}
{voice_note}
{caption_note}
{niche_note}

Topic: "{topic}"

{continuity}

STRICT RULES:
- voiceover: HINGLISH vocabulary in Devanagari — "स्टॉक" not "शेयर", "क्रैश" not "दुर्घटना", "ऐप" not "अनुप्रयोग"
- AVOID pure formal Hindi: no "विनाश", no "नष्ट", no "अपहरण", no "मिथ्यापराण"
- caption: Hinglish in Roman
- Each scene = ONE new fact or angle. NO repetition.
- If facts run out, write fewer scenes. NEVER pad with filler.
- Max 12 words voiceover, max 10 words caption
- visual_search and ai_prompt: ENGLISH ONLY
- sfx: deep_impact|whoosh|click|riser|none

Return ONLY JSON array. No markdown.
[{{"scene":{start_num},"voiceover":"...","caption":"...","visual_type":"stock_video","visual_search":"...","ai_prompt":"...","emotion":"dramatic","sfx":"{sfx_def}","duration_hint":4}}]"""

        try:
            try:
                text = gemini(prompt)
            except Exception as gem_err:
                log.warning(f"  Gemini failed for this batch ({gem_err}), falling back to Groq")
                text = groq(prompt, max_tokens=2500)
            
            batch = json.loads(extract_json_array(text))
            if not batch:
                raise ValueError("Empty batch")

            # FIX v5.3: Deduplication — reject scenes too similar to existing ones
            filtered_batch = []
            for s in batch:
                voice = s.get("voiceover", "")
                
                # Check similarity against ALL previous scenes
                is_duplicate = False
                for prev in full_script:
                    sim = _semantic_similarity(voice, prev.get("voiceover", ""))
                    if sim > 0.65:
                        log.warning(f"  Rejected duplicate (sim={sim:.0%}): {voice[:50]}...")
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    s["scene"] = start_num + len(filtered_batch)
                    s["visual_search"] = sanitize_visual_term(s.get("visual_search", ""), vprefix, niche)
                    s["ai_prompt"] = sanitize_visual_term(s.get("ai_prompt", ""), vprefix, niche, is_prompt=True)
                    if "caption" not in s:
                        s["caption"] = s.get("voiceover", "")
                    filtered_batch.append(s)

            if not filtered_batch:
                stalled += 1
                log.warning(f"  Batch produced only duplicates, stalled={stalled}")
                time.sleep(5)
                continue

            full_script.extend(filtered_batch)
            log.info(f"  Batch OK: +{len(filtered_batch)} scenes ({len(full_script)}/{target})")
            stalled = 0
            time.sleep(3)

        except Exception as e:
            log.warning(f"  Batch failed: {e}")
            stalled += 1
            time.sleep(8)

    # v5.3: Early stop is fine — better short than repetitive
    actual_scenes = len(full_script)
    if actual_scenes < target * 0.7:
        log.info(f"Stage 2: Ended early at {actual_scenes} scenes (research exhausted, no padding)")

    if len(full_script) >= 10:
        max_text_stat = max(1, int(len(full_script) * 0.15))
        text_stat_indices = [i for i, s in enumerate(full_script) if s.get("visual_type") == "text_stat"]
        if len(text_stat_indices) > max_text_stat:
            excess = text_stat_indices[max_text_stat:]
            for idx in excess:
                full_script[idx]["visual_type"] = "ai_image" if idx % 2 == 0 else "stock_video"
            log.info(f"  Capped text_stat: {len(text_stat_indices)} → {max_text_stat}")

    t = 0.0
    for s in full_script:
        s["start_time"] = t; t += float(s.get("duration_hint",4))
        if vprefix.lower() not in s.get("visual_search","").lower():
            s["visual_search"] = f"{vprefix} {s.get('visual_search','')}"
        if "caption" not in s:
            s["caption"] = s.get("voiceover", "")
    
    log.info(f"Stage 2: {len(full_script)} scenes written")
    return full_script
# ═══════════════════════════════════════════════════════════
#  STAGE 3 — VOICE
# ═══════════════════════════════════════════════════════════

async def _edge_tts(text, path, voice, rate="+8%", pitch="+0Hz"):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(path)

EMOTION_VOICE_MAP = {
    "dramatic":   ("+6%",  "+0Hz"),
    "shocking":   ("+14%", "+15Hz"),
    "mysterious": ("+2%",  "-15Hz"),
    "inspiring":  ("+10%", "+10Hz"),
    "calm":       ("-4%",  "-5Hz"),
    "energetic":  ("+18%", "+20Hz"),
}

def stage_3_voice(script, cfg):
    lang = cfg["lang"]
    use_kokoro = os.environ.get("USE_KOKORO", "true").lower() in ("true", "1", "yes")
    log.info(f"Stage 3: Voice (Kokoro: {use_kokoro})...")
    tg(f"🎙️ Generating voice...")
    audio_dir = WORKSPACE / "audio"
    audio_dir.mkdir(exist_ok=True)
    failed_scenes = 0

    for idx, scene in enumerate(script):
        n = scene["scene"]
        # Use voiceover (Devanagari) for TTS audio generation
        text = scene.get("voiceover", "").strip()
        if not text:
            scene["audio_file"] = None
            continue
        emotion = scene.get("emotion", "dramatic")
        out = str(audio_dir / f"scene_{n:03d}.mp3")
        done = False

        # Try Kokoro first if enabled
        if use_kokoro:
            try:
                done = generate_kokoro_voice(text, out, lang, emotion)
                if done:
                    scene["audio_file"] = out
                    log.info(f"  Scene {n}: Kokoro TTS ✓")
            except Exception as e:
                log.warning(f"  Scene {n}: Kokoro failed: {e}")

        # Fallback to Edge-TTS
        if not done:
            voice = cfg.get("voice", VOICE_MAP.get(lang, VOICE_MAP["hindi"])[0])
            fallback = VOICE_MAP.get(lang, VOICE_MAP["hindi"])
            rate, pitch = EMOTION_VOICE_MAP.get(emotion, ("+8%", "+0Hz"))
            for v in fallback:
                for attempt in range(2):
                    try:
                        asyncio.run(_edge_tts(text, out, v, rate=rate, pitch=pitch))
                        if os.path.exists(out) and os.path.getsize(out) > 500:
                            scene["audio_file"] = out
                            done = True
                        break
                    except Exception as e:
                        log.warning(f"  Scene {n} {v} attempt {attempt+1}: {e}")
                        time.sleep(1.5)
                if done:
                    break

        # Fallback to gTTS
        if not done:
            try:
                from gtts import gTTS
                lc = {"hindi":"hi","english":"en","spanish":"es","french":"fr","german":"de"}.get(lang,"hi")
                gTTS(text=text,lang=lc).save(out)
                if os.path.exists(out) and os.path.getsize(out) > 500:
                    scene["audio_file"] = out
                    done = True
            except Exception as e:
                log.error(f"  Scene {n}: gTTS also failed: {e}")

        if not done:
            failed_scenes += 1
            scene["audio_file"] = None

        if idx % 5 == 4:
            time.sleep(1)

    if failed_scenes:
        log.warning(f"Stage 3: {failed_scenes}/{len(script)} scenes have NO audio")
    return script


def generate_kokoro_voice(text, out_path, lang, emotion):
    """Generate voice using Kokoro TTS — FIXED for proper Hindi audio"""
    # FIXED: Use actual Hindi voices for Hindi, not American fallback
    voice_map = {
        "hindi": "hm_omega",      # Hindi Male — natural, authoritative
        # "hindi": "hf_alpha",    # Hindi Female — alternative
        "english": "af_heart",    # American Female
        "spanish": "af_heart",    # Fallback
        "french": "af_heart",     # Fallback
        "german": "af_heart"      # Fallback
    }

    # FIXED: Use correct language code for phoneme generation
    lang_code_map = {
        "hindi": "h",      # 'h' triggers espeak-ng hi + Hindi G2P
        "english": "a",    # 'a' = American English
        "spanish": "a",    # Fallback
        "french": "a",     # Fallback  
        "german": "a"      # Fallback
    }

    voice = voice_map.get(lang, "af_heart")
    lang_code = lang_code_map.get(lang, "a")

    speed_map = {
        "dramatic": 1.0,
        "shocking": 1.3,
        "mysterious": 0.9,
        "inspiring": 1.1,
        "calm": 0.85,
        "energetic": 1.2
    }
    speed = speed_map.get(emotion, 1.0)

    try:
        from kokoro import KPipeline
        import numpy as np

        # FIXED: Correct language code for phoneme dictionary
        pipeline = KPipeline(lang_code=lang_code)
        generator = pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+')

        audio_segments = []
        sample_rate = 24000

        for i, (gs, ps, audio) in enumerate(generator):
            audio_segments.append(audio)

        if not audio_segments:
            return False

        full_audio = np.concatenate(audio_segments)

        # FIX 1: Remove NaN/Inf that corrupt output
        full_audio = np.nan_to_num(full_audio, nan=0.0, posinf=0.0, neginf=0.0)

        # FIX 2: float32 [-1.0, 1.0] → int16 [-32768, 32767] with clipping
        audio_int16 = np.clip(full_audio * 32767, -32768, 32767).astype(np.int16)

        # FIX 3: Write as proper 16-bit PCM WAV
        import soundfile as sf
        wav_path = out_path.replace('.mp3', '.wav')
        sf.write(wav_path, audio_int16, sample_rate, subtype='PCM_16')

        # FIX 4: Convert to MP3 with ffmpeg
        result = subprocess.run([
            "ffmpeg", "-y", "-i", wav_path,
            "-codec:a", "libmp3lame", "-qscale:a", "2",
            "-ar", str(sample_rate),
            out_path
        ], capture_output=True, timeout=30)

        if os.path.exists(wav_path):
            os.remove(wav_path)

        success = result.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 500
        if success:
            log.info(f"  Kokoro [{lang_code}/{voice}]: clean audio ({os.path.getsize(out_path)//1024}KB)")
        return success

    except ImportError:
        log.warning("Kokoro TTS not available, falling back to other methods")
    except Exception as e:
        log.warning(f"Kokoro generation failed: {e}")
    return False

# ═══════════════════════════════════════════════════════════
#  STAGE 4 — MUSIC
# ═══════════════════════════════════════════════════════════
def stage_4_music(cfg):
    mood = cfg.get("music_mood","cinematic dramatic")
    log.info(f"Stage 4: Music ({mood})...")

    def is_valid_audio(path):
        try:
            r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                "-of","default=noprint_wrappers=1:nokey=1", path],
                capture_output=True, text=True, timeout=15)
            if r.returncode != 0 or r.stdout.strip() == "":
                return False
            r2 = subprocess.run(["ffprobe","-v","error","-select_streams","a",
                "-show_entries","stream=codec_type","-of","default=noprint_wrappers=1:nokey=1", path],
                capture_output=True, text=True, timeout=15)
            if r2.returncode != 0 or "audio" not in r2.stdout.lower():
                return False
            dur = float(r.stdout.strip())
            return dur > 0.5
        except Exception:
            return False

    music_folder = ASSETS_DIR / "music"
    if music_folder.exists():
        mood_files = list(music_folder.glob("*.mp3")) + list(music_folder.glob("*.m4a")) + list(music_folder.glob("*.wav"))
        keyword_matches = [f for f in mood_files if any(w in f.stem.lower() for w in mood.split())]
        pool = keyword_matches if keyword_matches else mood_files
        if pool:
            chosen = random.choice(pool)
            if is_valid_audio(str(chosen)):
                log.info(f"Stage 4: Using your uploaded track — {chosen.name}")
                return str(chosen)

    freesound_key = os.environ.get("FREESOUND_KEY", "")
    if freesound_key:
        try:
            music = get_freesound_music(mood, freesound_key)
            if music and is_valid_audio(music):
                log.info("Stage 4: Music from Freesound")
                return music
        except Exception as e:
            log.warning(f"Stage 4: Freesound failed: {e}")

    pixabay_key = os.environ.get("PIXABAY_KEY", "")
    if pixabay_key:
        try:
            music = get_pixabay_music(mood, pixabay_key)
            if music and is_valid_audio(music):
                log.info("Stage 4: Music from Pixabay")
                return music
        except Exception as e:
            log.warning(f"Stage 4: Pixabay failed: {e}")

    music_map = {
        "serious corporate dramatic":  "https://freepd.com/music/Sci-Fi%20Intelligence.mp3",
        "dark suspense thriller":      "https://freepd.com/music/Dark%20Mystery.mp3",
        "calm lo-fi focus":            "https://freepd.com/music/Acoustic%20Meditation.mp3",
        "cinematic dramatic":          "https://freepd.com/music/Inspiring%20Cinematic.mp3",
        "energetic trap beat":         "https://freepd.com/music/Heavy%20Interlude.mp3",
        "playful upbeat cartoon":      "https://freepd.com/music/Fun%20Day.mp3",
        "dark noir":                   "https://freepd.com/music/Dark%20Mystery.mp3",
        "cool blue":                   "https://freepd.com/music/Blue%20Skies.mp3",
    }
    url = None
    for key in music_map:
        if any(w in mood for w in key.split()):
            url = music_map[key]; break
    url = url or music_map["cinematic dramatic"]

    music_path = str(WORKSPACE/"music.mp3")
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(music_path,"wb") as f: f.write(r.content)
            if is_valid_audio(music_path):
                log.info(f"Stage 4: Music from freepd.com")
                return music_path
    except Exception as e:
        log.warning(f"Stage 4: FreePD failed: {e}")

    music_path = str(WORKSPACE/"music.m4a")
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
        "-t","300","-c:a","aac",music_path], capture_output=True, timeout=30)
    log.warning("Stage 4: Using silent track")
    return music_path

def get_freesound_music(mood, api_key):
    search_terms = {
        "serious corporate dramatic": ["corporate", "dramatic", "cinematic"],
        "dark suspense thriller": ["suspense", "thriller", "dark"],
        "calm lo-fi focus": ["lo-fi", "calm", "focus"],
        "cinematic dramatic": ["cinematic", "dramatic"],
        "energetic trap beat": ["energetic", "trap", "beat"],
        "playful upbeat cartoon": ["cartoon", "playful", "upbeat"],
        "dark noir": ["noir", "dark", "mysterious"],
        "cool blue": ["chill", "lo-fi", "calm"]
    }
    search_query = random.choice(search_terms.get(mood, ["cinematic"]))
    try:
        resp = requests.get(
            "https://freesound.org/apiv2/search/text/",
            params={"query": search_query, "filter": "duration:[30 TO 180] type:wav",
                "sort": "rating_desc", "page_size": 20},
            headers={"Authorization": f"Token {api_key}"}, timeout=30)
        if resp.status_code != 200: return None
        results = resp.json().get("results", [])
        if not results: return None
        sound = random.choice(results)
        sound_id = sound["id"]
        detail_resp = requests.get(f"https://freesound.org/apiv2/sounds/{sound_id}/",
            headers={"Authorization": f"Token {api_key}"}, timeout=30)
        if detail_resp.status_code != 200: return None
        download_url = detail_resp.json().get("previews", {}).get("preview-hq-mp3")
        if not download_url: return None
        music_path = str(WORKSPACE / "freesound_music.mp3")
        r = requests.get(download_url, timeout=60)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(music_path, "wb") as f: f.write(r.content)
            return music_path
    except Exception as e:
        log.warning(f"Freesound music failed: {e}")
    return None

def get_pixabay_music(mood, api_key):
    genre_map = {
        "serious corporate dramatic": "cinematic",
        "dark suspense thriller": "dark",
        "calm lo-fi focus": "chill",
        "cinematic dramatic": "cinematic",
        "energetic trap beat": "electro",
        "playful upbeat cartoon": "pop",
        "dark noir": "dark",
        "cool blue": "chill"
    }
    genre = genre_map.get(mood, "cinematic")
    try:
        resp = requests.get("https://pixabay.com/api/videos/",
            params={"key": api_key, "q": genre, "page_size": 20, "video_type": "music"}, timeout=30)
        if resp.status_code != 200: return None
        results = resp.json().get("hits", [])
        if not results: return None
        music = random.choice(results)
        download_url = music["videos"]["medium"]["url"]
        music_path = str(WORKSPACE / "pixabay_music.mp4")
        r = requests.get(download_url, timeout=60)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(music_path, "wb") as f: f.write(r.content)
            audio_path = str(WORKSPACE / "pixabay_music.mp3")
            subprocess.run(["ffmpeg", "-y", "-i", music_path,
                "-vn", "-codec:a", "libmp3lame", "-qscale:a", "2", audio_path],
                capture_output=True, timeout=60)
            return audio_path
    except Exception as e:
        log.warning(f"Pixabay music failed: {e}")
    return None

# ═══════════════════════════════════════════════════════════
#  STAGE 5 — SFX
# ═══════════════════════════════════════════════════════════
_sfx_cache = {}

def fetch_sfx(sfx_type):
    if sfx_type == "none" or not sfx_type: return None
    if sfx_type in _sfx_cache: return _sfx_cache[sfx_type]

    folder_map = {
        "deep_impact": "sfx/Impacts",
        "whoosh":      "sfx/Whooshes",
        "riser":       "sfx/Risers",
    }
    if sfx_type in folder_map:
        real = pick_asset(folder_map[sfx_type])
        if real:
            _sfx_cache[sfx_type] = real
            return real

    sfx_dir = WORKSPACE/"sfx"; sfx_dir.mkdir(exist_ok=True)
    out = str(sfx_dir/f"{sfx_type}.mp3")

    presets = {
        "deep_impact": ("sine=frequency=80:duration=0.35:sample_rate=44100", "volume=0.3,lowpass=f=300,afade=t=out:st=0.15:d=0.2"),
        "whoosh":      ("sine=frequency=800:duration=0.25:sample_rate=44100", "volume=0.15,afade=t=in:d=0.02,afade=t=out:st=0.15:d=0.1,tremolo=f=12:d=0.3"),
        "click":       ("sine=frequency=1400:duration=0.06:sample_rate=44100", "volume=0.12"),
        "riser":       ("sine=frequency=200:duration=0.5:sample_rate=44100", "volume=0.2,afade=t=in:d=0.4"),
    }
    src, af = presets.get(sfx_type, presets["click"])
    r = subprocess.run(["ffmpeg","-y","-f","lavfi","-i",src,"-af",af,out],
        capture_output=True, timeout=10)
    if r.returncode == 0 and os.path.exists(out):
        _sfx_cache[sfx_type] = out
        return out
    return None

# ═══════════════════════════════════════════════════════════
#  STAGE 6 — VISUALS
# ═══════════════════════════════════════════════════════════
HALLUCINATION_WORDS = ["flag","flags","taj mahal","monument","text on","sign ","banner",
    "face ","portrait","person standing","scientist","sage ","wizard","emperor",
    "soldiers marching","map of ","chart ","graph ","logo ","chakra","written "]

def skip_ai(prompt):
    p = prompt.lower()
    return any(w in p for w in HALLUCINATION_WORDS)

def get_dur(path):
    try:
        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=noprint_wrappers=1:nokey=1",path],
            capture_output=True, text=True, timeout=20)
        return float(r.stdout.strip())
    except: return 4.0

ANIMS = ["zoom_in","pan_right","zoom_out","pan_left","pan_up"]

def ken_burns(anim, dur, w=1920, h=1080):
    fr = int(dur*25)
    opts = {
        "zoom_in":   f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps=25",
        "zoom_out":  f"zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps=25",
        "pan_right": f"zoompan=z='1.3':x='min(iw*0.3,on*1.5)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps=25",
        "pan_left":  f"zoompan=z='1.3':x='max(0,iw*0.3-on*1.5)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps=25",
        "pan_up":    f"zoompan=z='1.3':x='iw/2-(iw/zoom/2)':y='max(0,ih*0.3-on*1.0)':d={fr}:s={w}x{h}:fps=25",
    }
    return opts.get(anim,opts["zoom_in"])

def img_to_vid(img, out, dur, anim="zoom_in", grain=True):
    vf = ken_burns(anim, dur)
    if grain: vf += ",noise=alls=2:allf=t+u"
    r = subprocess.run(["ffmpeg","-y","-loop","1","-i",img,"-vf",vf,
        "-t",str(dur),"-c:v","libx264","-pix_fmt","yuv420p","-preset","fast",out],
        capture_output=True, timeout=180)
    return r.returncode==0

def make_text_stat(text, out, dur, lang="hindi"):
    safe = re.sub(r'''[':"\\%]''',"",text)[:60]
    words = safe.split()
    lines,cur=[],[]
    for w in words:
        cur.append(w)
        if len(" ".join(cur))>18: lines.append(" ".join(cur)); cur=[]
    if cur: lines.append(" ".join(cur))
    font = get_caption_font(bold=True)
    dt=[]
    for i,line in enumerate(lines[:3]):
        y=f"(h/2)-{(len(lines)//2-i)*90}"
        dt.append(
            f"drawtext=text='{line}':fontsize=76:fontcolor=#FFD700:"
            f"x=(w-text_w)/2:y={y}:fontfile={font}:"
            f"shadowcolor=black:shadowx=4:shadowy=4:alpha='if(lt(t,0.35),t/0.35,1)'"
        )
    vf=",".join(dt) if dt else f"drawtext=text='{safe[:20]}':fontsize=76:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:fontfile={font}"
    r=subprocess.run(["ffmpeg","-y","-f","lavfi",
        "-i",f"color=c=0x080808:size=1920x1080:duration={dur}:rate=25",
        "-vf",vf+",noise=alls=2:allf=t+u","-c:v","libx264","-pix_fmt","yuv420p",out],
        capture_output=True,timeout=60)
    if r.returncode != 0:
        log.warning(f"  text_stat animated version failed, retrying static")
        vf_static = ",".join(
            f"drawtext=text='{line}':fontsize=76:fontcolor=#FFD700:x=(w-text_w)/2:y=(h/2)-{(len(lines)//2-i)*90}:fontfile={font}:shadowcolor=black:shadowx=4:shadowy=4"
            for i, line in enumerate(lines[:3])
        ) if lines else f"drawtext=text='{safe[:20]}':fontsize=76:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:fontfile={font}"
        r2=subprocess.run(["ffmpeg","-y","-f","lavfi",
            "-i",f"color=c=0x080808:size=1920x1080:duration={dur}:rate=25",
            "-vf",vf_static+",noise=alls=2:allf=t+u","-c:v","libx264","-pix_fmt","yuv420p",out],
            capture_output=True,timeout=60)
        return r2.returncode==0
    return True

def fetch_pollinations(prompt, out, seed=None):
    try:
        s = seed or random.randint(1,99999)
        neg="text watermark faces flags modern buildings cars phones computers deformed"
        url=(f"https://image.pollinations.ai/prompt/{quote(prompt)}"
             f"?width=1920&height=1080&nologo=true&seed={s}&negative={quote(neg)}&model=flux")
        r=requests.get(url,timeout=90)
        if r.status_code==200 and len(r.content)>8000:
            with open(out,"wb") as f: f.write(r.content)
            return True
    except Exception as e: log.warning(f"Pollinations: {e}")
    return False

def fetch_duckduckgo_image(search, out):
    try:
        from duckduckgo_search import DDGS
        import requests
        with DDGS() as ddgs:
            results = list(ddgs.images(
                keywords=search,
                region="wt-wt",
                safesearch="moderate",
                size="Large",
                max_results=5
            ))
            if not results:
                return False
                
            for res in results:
                url = res.get("image")
                if not url:
                    continue
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        with open(out, "wb") as f:
                            f.write(r.content)
                        return True
                except:
                    continue
        return False
    except Exception as e:
        log.warning(f"DDG fetch failed for {search}: {e}")
        return False

def fetch_pexels_video(search, out, dur):
    try:
        h={"Authorization":PEXELS_KEY}
        r=requests.get("https://api.pexels.com/videos/search",headers=h,
            params={"query":search,"per_page":10,"orientation":"landscape"},timeout=15)
        vids=r.json().get("videos",[])
        if not vids: return False
        vid=random.choice(vids[:5])
        files=sorted(vid.get("video_files",[]),key=lambda x:x.get("width",0),reverse=True)
        if not files: return False
        raw=out.replace(".mp4","_raw.mp4")
        v=requests.get(files[0]["link"],stream=True,timeout=60)
        with open(raw,"wb") as f:
            for chunk in v.iter_content(8192): f.write(chunk)
        r2=subprocess.run(["ffmpeg","-y","-i",raw,"-t",str(dur),
            "-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=25",
            "-r","25","-vsync","cfr","-c:v","libx264","-an","-preset","fast",out],capture_output=True,timeout=60)
        return r2.returncode==0
    except Exception as e: log.warning(f"Pexels video: {e}"); return False

def fetch_pexels_image(search, out):
    try:
        h={"Authorization":PEXELS_KEY}
        r=requests.get("https://api.pexels.com/v1/search",headers=h,
            params={"query":search,"per_page":10,"orientation":"landscape"},timeout=15)
        photos=r.json().get("photos",[])
        if not photos: return False
        url=random.choice(photos[:5])["src"]["original"]
        img=requests.get(url,timeout=30)
        with open(out,"wb") as f: f.write(img.content)
        return True
    except Exception as e: log.warning(f"Pexels image: {e}"); return False

def fetch_pixabay(search, out, dur=None):
    try:
        if dur:
            r=requests.get("https://pixabay.com/api/videos/",
                params={"key":PIXABAY_KEY,"q":search,"video_type":"film","per_page":10},timeout=15)
            hits=r.json().get("hits",[])
            if not hits: return False
            url=random.choice(hits[:5])["videos"]["large"]["url"]
            raw=out.replace(".mp4","_raw2.mp4")
            v=requests.get(url,stream=True,timeout=60)
            with open(raw,"wb") as f:
                for chunk in v.iter_content(8192): f.write(chunk)
            r2=subprocess.run(["ffmpeg","-y","-i",raw,"-t",str(dur),
                "-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=25",
                "-r","25","-vsync","cfr","-c:v","libx264","-an","-preset","fast",out],capture_output=True,timeout=60)
            return r2.returncode==0
        else:
            r=requests.get("https://pixabay.com/api/",
                params={"key":PIXABAY_KEY,"q":search,"image_type":"photo","orientation":"horizontal","per_page":10,"safesearch":"true"},timeout=15)
            hits=r.json().get("hits",[])
            if not hits: return False
            url=random.choice(hits[:5])["largeImageURL"]
            img=requests.get(url,timeout=30)
            with open(out,"wb") as f: f.write(img.content); return True
    except Exception as e: log.warning(f"Pixabay: {e}"); return False

def solid_bg(out, dur):
    subprocess.run(["ffmpeg","-y","-f","lavfi",
        "-i",f"color=c=0x080808:size=1920x1080:duration={dur}:rate=25",
        "-c:v","libx264","-pix_fmt","yuv420p",out],capture_output=True,timeout=30)

def stage_6_visuals(script, cfg):
    topic   = cfg["topic"]
    vprefix = cfg.get("visual_prefix", topic)
    log.info(f"Stage 6: Visuals for {len(script)} scenes...")
    tg(f"🎨 Creating visuals...")
    vis=WORKSPACE/"visuals"; vis.mkdir(exist_ok=True)

    for i,scene in enumerate(script):
        n     = scene["scene"]
        vtype = scene.get("visual_type","ai_image")
        prompt= scene.get("ai_prompt",f"cinematic dramatic {topic} scene no faces no text")
        search= scene.get("visual_search",f"{vprefix} cinematic")
        out   = str(vis/f"scene_{n:03d}.mp4")
        img   = str(vis/f"scene_{n:03d}.jpg")
        anim  = ANIMS[i%len(ANIMS)]

        dur = get_dur(scene["audio_file"]) if scene.get("audio_file") else float(scene.get("duration_hint",4))
        scene["actual_duration"]=dur
        success=False

        if vtype=="text_stat":
            # Use caption (Hinglish) for text_stat cards
            display_text = scene.get("caption", scene.get("voiceover", ""))
            if make_text_stat(display_text,out,dur,cfg["lang"]):
                scene["video_file"]=out; log.info(f"  {n}: text_stat ✓"); continue

        elif vtype=="stock_video":
            log.info(f"  {n}: stock '{search}'")
            if fetch_pexels_video(search,out,dur): scene["video_file"]=out; success=True
            if not success and fetch_pixabay(search,out,dur): scene["video_file"]=out; success=True

        else:
            if skip_ai(prompt):
                log.info(f"  {n}: skip AI (hallucination risk)")
            else:
                if fetch_pollinations(prompt,img,seed=n*17+i):
                    if img_to_vid(img,out,dur,anim): scene["video_file"]=out; success=True; log.info(f"  {n}: Pollinations+{anim} ✓")

        if not success:
            if fetch_pexels_video(search,out,dur): scene["video_file"]=out; success=True
        if not success:
            if fetch_duckduckgo_image(search, img):
                if img_to_vid(img, out, dur, anim): scene["video_file"]=out; success=True
        if not success:
            if fetch_pexels_image(search,img):
                if img_to_vid(img,out,dur,anim): scene["video_file"]=out; success=True
        if not success:
            if fetch_pixabay(search,img):
                if img_to_vid(img,out,dur,anim): scene["video_file"]=out; success=True
        if not success:
            solid_bg(out,dur); scene["video_file"]=out; log.warning(f"  {n}: fallback solid bg")

    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 7 — ASSEMBLY
# ═══════════════════════════════════════════════════════════
def _srt(s):
    h,m=int(s//3600),int((s%3600)//60)
    return f"{h:02d}:{m:02d}:{int(s%60):02d},{int((s%1)*1000):03d}"

def get_caption_fonts():
    font_dir = ASSETS_DIR / "fonts" / "caption"
    if font_dir.exists():
        fonts = list(font_dir.glob("*.ttf")) + list(font_dir.glob("*.otf"))
        if fonts:
            return [str(f) for f in fonts]
    return [get_caption_font()]

def build_caption_drawtext(script):
    """Build FFmpeg drawtext filter using HINGLISH caption field."""
    filters = []
    font_list = get_caption_fonts()

    for scene in script:
        # FIXED: Use caption (Hinglish) for on-screen text, not voiceover (Devanagari)
        text = scene.get("caption", scene.get("voiceover", "")).strip()
        dur = scene.get("actual_duration", 4.0)
        start = scene.get("start_time", 0.0)
        if not text:
            continue

        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            word = words[i]
            is_key = bool(re.search(r'\d', word)) or (len(word) > 2 and word[0].isupper())
            if is_key:
                chunks.append((word, True))
                i += 1
            else:
                chunk_size = random.randint(1, 3)
                chunk_words = words[i:i+chunk_size]
                chunks.append((" ".join(chunk_words), False))
                i += chunk_size

        tpc = dur / max(len(chunks), 1)

        for j, (chunk_text, is_key) in enumerate(chunks):
            cs = start + j * tpc
            ce = cs + tpc - 0.05
            fade_in_end = cs + 0.2

            font = random.choice(font_list)

            if is_key:
                fontsize = random.randint(48, 64)
                color = "#FFD700"
            else:
                fontsize = random.randint(28, 36)
                color = "white"

            y_positions = ["h*0.65", "h*0.7", "h*0.75", "h*0.8"]
            y = random.choice(y_positions)

            safe_text = re.sub(r'''[':"\\%\[\]{}|]''', "", chunk_text)

            dt = (
                f"drawtext=text='{safe_text}':"
                f"fontsize={fontsize}:fontcolor={color}:"
                f"x=(w-text_w)/2:y={y}:"
                f"fontfile={font}:"
                f"borderw=4:bordercolor=black:"
                f"alpha='if(lt(t,{cs}),0,if(lt(t,{fade_in_end}),(t-{cs})/0.2,1))':"
                f"enable='between(t,{cs:.3f},{ce:.3f})'"
            )
            filters.append(dt)

    return ",".join(filters) if filters else "null"

def create_intro(cfg, out_path):
    topic = cfg.get("topic", "")
    safe_topic = re.sub(r'''[':"\\%\[\]{}|]''', "", topic[:60])
    font = get_caption_font(bold=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x080808:size=1920x1080:duration=2.0:rate=25",
        "-vf",
        f"drawtext=text='{safe_topic}':fontsize=72:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:fontfile={font}:borderw=6:bordercolor=black:alpha='if(lt(t,0.5),t/0.5,if(lt(t,1.5),1,if(lt(t,2.0),(2.0-t)/0.5,0)))',noise=alls=2:allf=t+u",
        "-c:v", "libx264", "-preset", "ultrafast", "-an", out_path
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)
    return out_path if os.path.exists(out_path) else None

def create_outro(cfg, out_path):
    cta_text = "Like, Share & Subscribe!"
    font = get_caption_font(bold=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x080808:size=1920x1080:duration=2.0:rate=25",
        "-vf",
        f"drawtext=text='{cta_text}':fontsize=64:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:fontfile={font}:borderw=6:bordercolor=black:alpha='if(lt(t,0.5),t/0.5,if(lt(t,1.5),1,if(lt(t,2.0),(2.0-t)/0.5,0)))',noise=alls=2:allf=t+u",
        "-c:v", "libx264", "-preset", "ultrafast", "-an", out_path
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)
    return out_path if os.path.exists(out_path) else None

def concat_with_transitions(clips, out_path):
    if len(clips) == 1:
        if os.path.exists(clips[0]):
            import shutil
            shutil.copy(clips[0], out_path)
        return

    transition_types = ["fade", "wipeleft", "wiperight", "circlecrop", "pixelize"]
    transition_duration = 0.5
    asm_dir = WORKSPACE / "assembly"
    asm_dir.mkdir(exist_ok=True)

    audio_list = str(asm_dir / "audio_concat.txt")
    audio_clips = []
    for i, clip in enumerate(clips):
        audio_tmp = str(asm_dir / f"audio_{i:03d}.m4a")
        subprocess.run([
            "ffmpeg", "-y", "-i", clip,
            "-vn", "-ac", "2", "-ar", "48000", "-c:a", "aac", "-b:a", "128k",
            audio_tmp
        ], capture_output=True, timeout=30)
        if os.path.exists(audio_tmp) and os.path.getsize(audio_tmp) > 500:
            audio_clips.append(audio_tmp)
        else:
            dur = get_dur(clip)
            silent = str(asm_dir / f"silent_{i:03d}.m4a")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
                "-t", str(dur), "-c:a", "aac", silent
            ], capture_output=True, timeout=15)
            audio_clips.append(silent)

    with open(audio_list, "w") as f:
        for ac in audio_clips:
            f.write(f"file '{os.path.abspath(ac)}'\n")

    concat_audio = str(asm_dir / "concat_audio.m4a")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", audio_list,
        "-c", "copy", concat_audio
    ], capture_output=True, timeout=120)

    if len(clips) > 40:
        log.warning("Too many clips for xfade chain, using simple video concat")
        video_list = str(asm_dir / "video_concat.txt")
        with open(video_list, "w") as f:
            for c in clips:
                f.write(f"file '{os.path.abspath(c)}'\n")
        concat_video = str(asm_dir / "concat_video.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", video_list,
            "-c", "copy", "-an", concat_video
        ], capture_output=True, timeout=300)
    else:
        filter_parts = []
        input_args = []
        for i, clip in enumerate(clips):
            input_args.extend(["-i", clip])

        current_v = "[0:v]"
        cum_dur = get_dur(clips[0])

        for i in range(1, len(clips)):
            trans_type = random.choice(transition_types)
            offset = cum_dur - transition_duration
            if offset < 0:
                offset = 0
            filter_parts.append(f"{current_v}[{i}:v]xfade=transition={trans_type}:duration={transition_duration}:offset={offset}[v{i}]")
            current_v = f"[v{i}]"
            cum_dur = offset + get_dur(clips[i])

        concat_video = str(asm_dir / "concat_video.mp4")
        filter_complex = ";".join(filter_parts)
        cmd = [
            "ffmpeg", "-y", *input_args,
            "-filter_complex", filter_complex,
            "-map", current_v, "-an",
            "-c:v", "libx264", "-preset", "ultrafast",
            concat_video
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=900)
        if result.returncode != 0 or not os.path.exists(concat_video):
            log.warning("xfade failed, falling back to simple video concat")
            video_list = str(asm_dir / "video_concat.txt")
            with open(video_list, "w") as f:
                for c in clips:
                    f.write(f"file '{os.path.abspath(c)}'\n")
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", video_list,
                "-c", "copy", "-an", concat_video
            ], capture_output=True, timeout=300)

    if os.path.exists(concat_video) and os.path.exists(concat_audio):
        subprocess.run([
            "ffmpeg", "-y", "-i", concat_video, "-i", concat_audio,
            "-c", "copy", "-shortest", out_path
        ], capture_output=True, timeout=120)
    else:
        log.error("Concat failed completely")
        raise RuntimeError("Could not concatenate clips")

def apply_overlay_to_scene(scene_video, overlay_video, dur, out_path):
    cmd = ["ffmpeg","-y",
        "-i", scene_video,
        "-stream_loop","-1","-i", overlay_video,
        "-filter_complex",
        f"[1:v]scale=1920:1080,fps=25,setpts=PTS-STARTPTS[ov];"
        f"[0:v]fps=25[base];"
        f"[base][ov]blend=all_mode=screen:shortest=1[v]",
        "-map","[v]","-t",str(dur),
        "-r","25","-vsync","cfr",
        "-c:v","libx264","-preset","ultrafast","-an",
        out_path]
    r = subprocess.run(cmd, capture_output=True, timeout=90)
    return r.returncode == 0 and os.path.exists(out_path)

def stage_7_assemble(script, cfg, music_path):
    log.info("Stage 7: Assembling...")
    tg("🎞️ Final assembly...")
    asm=WORKSPACE/"assembly"; asm.mkdir(exist_ok=True)

    scene_files=[]
    cur_time=0.0

    overlay_candidates = [s for s in script if s.get("sfx") in ("deep_impact","riser") and s.get("video_file")]
    overlay_scenes = random.sample(overlay_candidates, min(8, len(overlay_candidates))) if overlay_candidates else []
    if overlay_scenes:
        log.info(f"Applying overlay flash to {len(overlay_scenes)} high-impact scenes")
    for scene in overlay_scenes:
        overlay_video = get_overlay_video()
        if not overlay_video:
            break
        n = scene["scene"]
        dur = scene.get("actual_duration", float(scene.get("duration_hint",4)))
        composited = str(asm/f"overlay_{n:03d}.mp4")
        if apply_overlay_to_scene(scene["video_file"], overlay_video, dur, composited):
            scene["video_file"] = composited
            log.info(f"  Scene {n}: overlay flash applied")
        else:
            log.warning(f"  Scene {n}: overlay compositing failed")

    for scene in script:
        n     = scene["scene"]
        video = scene.get("video_file")
        audio = scene.get("audio_file")
        dur   = scene.get("actual_duration",4.0)
        sfx_t = scene.get("sfx","none")
        scene["start_time"]=cur_time

        if not video: continue

        out = str(asm/f"merged_{n:03d}.mp4")
        sfx_file = fetch_sfx(sfx_t) if sfx_t and sfx_t!="none" else None

        if audio and sfx_file:
            mixed_audio = str(asm/f"audio_{n:03d}.m4a")
            mix_r = subprocess.run(["ffmpeg","-y",
                "-i",os.path.abspath(audio),
                "-i",os.path.abspath(sfx_file),
                "-filter_complex","[0:a]adelay=180|180,volume=1.6[v];[1:a]volume=0.08[s];[v][s]amix=inputs=2:duration=first[a]",
                "-map","[a]","-c:a","aac",mixed_audio],capture_output=True,timeout=30)
            if mix_r.returncode != 0 or not os.path.exists(mixed_audio):
                log.warning(f"  SFX mix failed for scene {n}, using voice only")
                mixed_audio = audio
            cmd=["ffmpeg","-y","-i",os.path.abspath(video),"-i",mixed_audio,
                 "-c:v","copy","-c:a","aac",
                 "-map","0:v:0","-map","1:a:0","-shortest",out]
        elif audio:
            cmd=["ffmpeg","-y","-i",os.path.abspath(video),"-i",os.path.abspath(audio),
                 "-c:v","copy","-c:a","aac",
                 "-map","0:v:0","-map","1:a:0","-shortest",out]
        else:
            cmd=["ffmpeg","-y","-i",os.path.abspath(video),
                 "-c:v","copy","-an",out]

        r=subprocess.run(cmd,capture_output=True,timeout=60)
        if r.returncode==0 and os.path.exists(out):
            scene_files.append(out); cur_time+=dur
        else:
            log.warning(f"Scene {n} copy-merge failed, retrying with encode")
            cmd2=["ffmpeg","-y","-i",os.path.abspath(video)] + \
                 (["-i",os.path.abspath(audio if not (audio and sfx_file) else mixed_audio)] if audio else []) + \
                 (["-map","0:v:0","-map","1:a:0","-shortest"] if audio else ["-an"]) + \
                 ["-c:v","libx264","-preset","ultrafast","-c:a","aac",out]
            r2=subprocess.run(cmd2,capture_output=True,timeout=120)
            if r2.returncode==0 and os.path.exists(out):
                scene_files.append(out); cur_time+=dur
            else:
                log.warning(f"Scene {n} fully failed, skipping")

    if not scene_files: raise RuntimeError("No scenes assembled!")

    full_clips = []
    intro_path = str(asm / "intro.mp4")
    intro = create_intro(cfg, intro_path)
    if intro:
        full_clips.append(intro)
    full_clips.extend(scene_files)
    outro_path = str(asm / "outro.mp4")
    outro = create_outro(cfg, outro_path)
    if outro:
        full_clips.append(outro)

    raw = str(WORKSPACE / "raw.mp4")
    concat_with_transitions(full_clips, raw)
    if not os.path.exists(raw):
        raise RuntimeError("Concat failed: raw.mp4 was not created")
    final_dur = get_dur(raw)
    expected_dur = cur_time + (2.0 if intro else 0.0) + (2.0 if outro else 0.0)
    if final_dur < expected_dur * 0.8:
        log.warning(f"Concat output looks short ({final_dur:.0f}s actual vs {expected_dur:.0f}s expected)")

    total_dur = max(get_dur(raw), sum(s.get("actual_duration",4) for s in script))
    with_music=str(WORKSPACE/"with_music.mp4")
    if music_path and os.path.exists(music_path):
        r_mus = subprocess.run(["ffmpeg","-y","-i",raw,"-stream_loop","-1","-i",music_path,
            "-filter_complex",f"[1:a]volume=0.06,atrim=0:{total_dur}[m];[0:a][m]amix=inputs=2:duration=first[a]",
            "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-shortest",with_music],
            capture_output=True,timeout=300)
        if r_mus.returncode==0 and os.path.exists(with_music):
            raw = with_music
        else:
            log.warning(f"Music mix failed")

    grade = cfg.get("color_grade","cinematic")
    lut_file = get_lut_file(grade)
    if lut_file:
        gf = f"lut3d='{lut_file}'"
        log.info(f"  Using real LUT: {lut_file}")
    else:
        grade_filters = {
            "teal_orange": "curves=r='0/0 0.5/0.4 1/0.95':b='0/0.1 0.5/0.5 1/0.9',eq=saturation=1.15:contrast=1.1",
            "cool_blue":   "curves=b='0/0.1 0.5/0.6 1/1':eq=saturation=0.9:contrast=1.05",
            "dark_noir":   "eq=saturation=0.6:contrast=1.3:brightness=-0.05",
            "cinematic":   "eq=saturation=1.05:contrast=1.15:gamma=0.95",
        }
        gf = grade_filters.get(grade, grade_filters["cinematic"])
        log.info(f"  No LUT uploaded yet, using eq= approximation for '{grade}'")

    caption_filter = build_caption_drawtext(script)

    normalized = str(WORKSPACE/"normalized.mp4")
    subprocess.run(["ffmpeg","-y","-i",raw,
        "-af","loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v","copy","-c:a","aac",normalized],
        capture_output=True,timeout=300)
    raw_for_final = normalized if os.path.exists(normalized) else raw

    final=str(WORKSPACE/"final_video.mp4")
    combined_vf = gf if caption_filter=="null" else f"{gf},{caption_filter}"

    r=subprocess.run(["ffmpeg","-y","-i",raw_for_final,
        "-vf",combined_vf,
        "-c:v","libx264","-preset","ultrafast","-crf","23",
        "-c:a","aac",final],
        capture_output=True,timeout=1200)
    if r.returncode!=0:
        log.warning(f"Combined grade+caption failed. Trying captions only.")
        r2=subprocess.run(["ffmpeg","-y","-i",raw,
            "-vf",caption_filter if caption_filter!="null" else "null",
            "-c:v","libx264","-preset","ultrafast","-c:a","aac",final],
            capture_output=True,timeout=900)
        if r2.returncode!=0:
            log.warning("Captions also failed. Using uncolored/uncaptioned raw.")
            shutil.copy(raw,final)

    sz=os.path.getsize(final)/1024/1024
    log.info(f"Stage 7: {final} ({sz:.1f}MB, {total_dur:.0f}s)")
    return final

# ═══════════════════════════════════════════════════════════
#  STAGE 8 — QC
# ═══════════════════════════════════════════════════════════
def stage_8_qc(video_path, script, cfg):
    log.info("Stage 8: QC...")
    tg("🔍 QC check...")
    try:
        total=sum(s.get("actual_duration",4) for s in script)
        avg=total/max(len(script),1)
        hook=script[0].get("voiceover","") if script else ""
        text=gemini(f"""Rate this {cfg['genre']} YouTube video in {cfg['lang']} about "{cfg['topic']}":
Hook: "{hook}"
Scenes: {len(script)}, Duration: {total:.0f}s, Avg cut: {avg:.1f}s
Niche: {cfg.get('niche','general')}
Return ONLY JSON:
{{"score":8,"hook_score":9,"pacing_score":8,"verdict":"approved","reason":"brief","improvement":"one fix"}}
verdict: "approved"(>=7),"drafts"(5-6),"retry"(<5)""")
        text=text.strip().replace("```json","").replace("```","").strip()
        r=json.loads(text)
        log.info(f"Stage 8: {r['score']}/10 — {r['verdict']}")
        return r
    except Exception as e:
        log.warning(f"QC failed: {e}")
        return {"score":7,"verdict":"approved","reason":"QC unavailable"}

# ═══════════════════════════════════════════════════════════
#  STAGE 9 — PUBLISH
# ═══════════════════════════════════════════════════════════
def stage_9_publish(video_path, script, cfg):
    log.info("Stage 9: Publishing...")
    tg("📤 Uploading to YouTube...")
    topic = cfg["topic"]
    lang  = cfg["lang"]
    niche = cfg.get("niche","")
    genre = cfg["genre"]

    try:
        # v5.3 FIX: Build title from actual video content, not random hook
        scene_summaries = []
        for s in script[:8]:  # First 8 scenes = core content
            cap = s.get("caption", s.get("voiceover", ""))[:60]
            scene_summaries.append(cap)
        
        actual_content = "\n".join(f"- {s}" for s in scene_summaries)
        num_scenes = len(script)
        total_dur = sum(s.get('actual_duration',4) for s in script)
        
        lang_hint = "Write title and description in HINGLISH (Roman script, no Devanagari)." if lang == "hindi" else f"Write in {lang}."
        
        meta_text = groq(f"""YouTube metadata for a {genre} video about "{topic}".
        
ACTUAL VIDEO CONTENT:
{actual_content}

Total scenes: {num_scenes}
Duration: ~{total_dur:.0f} seconds

{lang_hint}

CRITICAL RULES:
- Title MUST honestly reflect the content. NO clickbait mismatch.
- If content is a biography → title as "The Untold Story of..." or "Inspiring Journey of..."
- If content exposes facts → title as "X Shocking Facts About..." and X must match actual scene count
- If content is a list → title must include the actual number of items
- NEVER promise "10 truths" if the video only has 6 facts
- NEVER use generic titles like "Poori Sacchai" or "Reality Exposed" unless the content actually exposes a scandal
- Description: 2 paragraphs summarizing actual content, not generic filler

Return ONLY JSON:
{{"title":"honest viral title under 60 chars",
  "description":"2 engaging paragraphs with actual content summary",
  "tags":["{topic}","{niche or 'viral'}","facts","hindi"],
  "hashtags":"#{topic.replace(' ','')} #{niche or 'viral'} #hindi"
}}""", max_tokens=800)
        
        meta = json.loads(extract_json_object(meta_text))
        log.info(f"Generated metadata: {meta}")
    except Exception as e:
        log.warning(f"Metadata generation failed: {e}")
        # v5.3: Honest fallback based on actual content type
        if num_scenes <= 12:
            meta = {
                "title": f"The Untold Story of {topic}",
                "description": f"A documentary exploring the journey and reality of {topic}.",
                "tags": [topic, "documentary", "hindi"],
                "hashtags": f"#{topic.replace(' ','')} #documentary #hindi"
            }
        else:
            meta = {
                "title": f"{num_scenes} Shocking Facts About {topic}",
                "description": f"Exploring {num_scenes} surprising truths about {topic} that you need to know.",
                "tags": [topic, "facts", "hindi"],
                "hashtags": f"#{topic.replace(' ','')} #facts #hindi"
            }

    meta.setdefault("title", f"The Reality of {topic}")
    meta.setdefault("description", f"Exploring {topic}.")
    meta.setdefault("tags", [topic, niche or "facts", "hindi"])
    meta.setdefault("hashtags", f"#{topic.replace(' ','')} #hindi")

    log.info(f"Title: {meta['title']}")
    now=datetime.now(timezone.utc)
    h,m=map(int,cfg["schedule"].split(":"))
    pub=now.replace(hour=h,minute=m,second=0,microsecond=0).isoformat().replace("+00:00","Z")

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        token_data=os.environ.get("YOUTUBE_TOKEN_JSON","")
        if not token_data: raise ValueError("YOUTUBE_TOKEN_JSON empty")
        with tempfile.NamedTemporaryFile(mode='w',suffix='.json',delete=False) as tmp:
            tmp.write(token_data); token_path=tmp.name
        creds=Credentials.from_authorized_user_file(token_path)
        yt=build("youtube","v3",credentials=creds)
        body={"snippet":{"title":meta["title"],
              "description":meta["description"]+"\n\n"+meta.get("hashtags",""),
              "tags":meta["tags"],
              "categoryId":"28"},
              "status":{"privacyStatus":"private","publishAt":pub,"selfDeclaredMadeForKids":False}}
        media=MediaFileUpload(video_path,mimetype="video/mp4",resumable=True,chunksize=5*1024*1024)
        req=yt.videos().insert(part="snippet,status",body=body,media_body=media)
        resp=None
        while resp is None:
            st,resp=req.next_chunk()
            if st: log.info(f"Upload {int(st.progress()*100)}%")
        url=f"https://youtube.com/watch?v={resp['id']}"
        log.info(f"Stage 9: {url}")
        return url
    except Exception as e:
        log.error(f"Upload failed: {e}")
        return f"Upload failed: {e}"
# ═══════════════════════════════════════════════════════════
#  STAGE 10 — GOOGLE DRIVE BACKUP
# ═══════════════════════════════════════════════════════════
_drive_service = None

def get_drive_service():
    global _drive_service
    if _drive_service:
        return _drive_service
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    token_data = os.environ.get("YOUTUBE_TOKEN_JSON", "")
    if not token_data:
        raise ValueError("YOUTUBE_TOKEN_JSON empty")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp.write(token_data); token_path = tmp.name
    creds = Credentials.from_authorized_user_file(token_path)
    _drive_service = build("drive", "v3", credentials=creds)
    return _drive_service

def find_or_create_drive_folder(service, name, parent_id=None):
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(q=query, fields="files(id,name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]

def stage_10_drive_backup(video_path, script, research, cfg, verdict, score):
    log.info("Stage 10: Backing up to Google Drive...")
    try:
        from googleapiclient.http import MediaFileUpload
        service = get_drive_service()

        root_id = find_or_create_drive_folder(service, "MediaAgency")
        bucket_name = {"approved": "Approved_Uploads", "drafts": "Drafts", "retry": "Rejects"}.get(verdict, "Drafts")
        bucket_id = find_or_create_drive_folder(service, bucket_name, root_id)

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        safe_topic = re.sub(r'[^a-zA-Z0-9]+', '-', cfg["topic"])[:40].strip('-')
        video_folder_name = f"{date_str}_{safe_topic}_score{score}"
        video_folder_id = find_or_create_drive_folder(service, video_folder_name, bucket_id)

        if video_path and os.path.exists(video_path):
            media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
            service.files().create(
                body={"name": "final_video.mp4", "parents": [video_folder_id]},
                media_body=media, fields="id"
            ).execute()
            log.info(f"  Drive: video uploaded to {bucket_name}/{video_folder_name}")

        for label, data in [("research.json", research), ("script_final.json", script)]:
            try:
                tmp_path = str(WORKSPACE / f"_drive_{label}")
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                media = MediaFileUpload(tmp_path, mimetype="application/json")
                service.files().create(
                    body={"name": label, "parents": [video_folder_id]},
                    media_body=media, fields="id"
                ).execute()
            except Exception as e:
                log.warning(f"  Drive: failed to upload {label}: {e}")

        folder_link = f"https://drive.google.com/drive/folders/{video_folder_id}"
        log.info(f"Stage 10: Backup complete → {folder_link}")
        return folder_link

    except Exception as e:
        log.warning(f"Stage 10: Drive backup failed (non-fatal): {e}")
        return None

# ═══════════════════════════════════════════════════════════
#  STAGE 7.5 — DOCUMENTARY AUDIO ASSEMBLY (PHASE 4)
# ═══════════════════════════════════════════════════════════
def stage_assemble_documentary(script, cfg, remotion_video, music_path):
    log.info("Stage 7.5: Assembling Documentary Audio & Muxing...")
    tg("🎞️ Assembling final documentary audio...")
    asm = WORKSPACE / "assembly"
    asm.mkdir(exist_ok=True)
    
    # 1. Concatenate all voiceover and SFX clips, inserting J-Cuts / silence gaps
    # For simplicity, we create an ffmpeg concat file for the audio tracks
    concat_file = asm / "audio_concat.txt"
    lines = []
    
    current_time = 0.0
    for scene in script:
        audio = scene.get("audio_file")
        dur = scene.get("actual_duration", 4.0)
        if audio and os.path.exists(audio):
            lines.append(f"file '{os.path.abspath(audio)}'")
        else:
            # Insert silence if no audio
            silence_path = asm / f"silence_{dur}.mp3"
            if not os.path.exists(silence_path):
                subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(dur), "-c:a", "libmp3lame", str(silence_path)], capture_output=True)
            lines.append(f"file '{os.path.abspath(silence_path)}'")
        current_time += dur
            
    with open(concat_file, "w") as f:
        f.write("\n".join(lines))
        
    voice_track = str(asm / "voice_track.mp3")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", voice_track], capture_output=True)
    
    # 2. Mix Voice + Music + (Optional ambient texture)
    final_video = str(WORKSPACE / "final_documentary_mixed.mp4")
    
    if music_path and os.path.exists(music_path):
        # 3-layer mix (video, voice, music)
        cmd = [
            "ffmpeg", "-y", 
            "-i", remotion_video, 
            "-i", voice_track, 
            "-i", os.path.abspath(music_path),
            "-filter_complex", "[1:a]volume=1.0[v];[2:a]volume=0.08[m];[v][m]amix=inputs=2:duration=first[a]",
            "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", final_video
        ]
    else:
        # Just Voice + Video
        cmd = [
            "ffmpeg", "-y", 
            "-i", remotion_video, 
            "-i", voice_track, 
            "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", final_video
        ]
        
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        log.error(f"Audio mix failed: {res.stderr}")
        return remotion_video # fallback
        
    log.info("✅ Documentary assembly complete!")
    return final_video

# ═══════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════
def run_pipeline():
    start=time.time()
    cfg=parse_input()

    log.info(f"🚀 v5.2 | {cfg['topic']} | niche={cfg.get('niche','')} | genre={cfg['genre']} | lang={cfg['lang']} | {cfg['duration_min']}min")
    tg(f"🚀 Starting v5.2\n📌 {cfg['topic']}\n🎬 {cfg['genre']} | {cfg['lang']} | {cfg['duration_min']}min\n⏰ Upload: {cfg['schedule']} UTC")

    try:
        research=stage_1_research(cfg)
        _save(research,"research.json")

        script=stage_2_script(research,cfg)
        _save(script,"script.json")
        tg(f"✍️ {len(script)} scenes written")

        script=stage_3_voice(script,cfg)

        music_path=stage_4_music(cfg)

        script=stage_6_visuals(script,cfg)
        _save(script,"script_final.json")

        final_video=stage_7_assemble(script,cfg,music_path)

        qc=stage_8_qc(final_video,script,cfg)
        _save(qc,"qc.json")

        verdict=qc.get("verdict","approved")
        score=qc.get("score",7)

        drive_link = stage_10_drive_backup(final_video, script, research, cfg, verdict, score)
        drive_note = f"\n📁 Drive: {drive_link}" if drive_link else ""

        if verdict=="retry":
            tg(f"❌ QC {score}/10 — Rejected\n{qc.get('reason','')}{drive_note}"); return
        if verdict=="drafts":
            tg(f"⚠️ QC {score}/10 — Drafts\n{qc.get('reason','')}{drive_note}"); return

        url=stage_9_publish(final_video,script,cfg)
        elapsed=int(time.time()-start)
        total=sum(s.get("actual_duration",4) for s in script)

        tg(f"✅ DONE!\n\n📺 {url}\n⏰ {cfg['schedule']} UTC\n🏆 QC: {score}/10\n🎬 {len(script)} scenes | {total:.0f}s\n✂️ Avg {total/max(len(script),1):.1f}s/cut\n⚡ {elapsed}s total{drive_note}")

    except Exception as e:
        import traceback
        log.error(f"CRASH: {e}\n{traceback.format_exc()}")
        tg(f"💥 Crashed: {str(e)[:250]}\nCheck GitHub Actions logs.")
        raise

# ═══════════════════════════════════════════════════════════
#  WAN2.1 COLAB INTEGRATION
# ═══════════════════════════════════════════════════════════
def stage_wan21_colab(scenes_needing_video, topic):
    if not scenes_needing_video:
        return {}

    session_file = os.path.expanduser("~/.config/colab-cli/sessions.json")
    if not os.path.exists(session_file):
        log.warning("Colab CLI session not found — skipping Wan2.1")
        return {}

    log.info(f"Wan2.1 via Colab CLI: {len(scenes_needing_video)} scenes")
    tg(f"🎨 Wan2.1 GPU generation: {len(scenes_needing_video)} animated clips...")

    prompts_file = str(WORKSPACE / "scene_prompts.json")
    with open(prompts_file, "w") as f:
        json.dump(scenes_needing_video, f, indent=2)

    clips_dir = WORKSPACE / "wan_clips"
    clips_dir.mkdir(exist_ok=True)

    try:
        result = subprocess.run([
            "colab", "run", "--gpu", "T4",
            "--upload", f"{prompts_file}:/content/scene_prompts.json",
            "--upload", "wan21_generator.py:/content/wan21_generator.py",
            "--download", "/content/clips/:./wan_clips/",
            "--download", "/content/wan21_results.json:./wan21_results.json",
            "wan21_generator.py"
        ], capture_output=True, text=True, timeout=1800)

        log.info(f"Colab exit code: {result.returncode}")
        if result.stdout: log.info(f"Colab output: {result.stdout[-500:]}")
        if result.stderr: log.warning(f"Colab stderr: {result.stderr[-300:]}")

        results_file = WORKSPACE / "wan21_results.json"
        if results_file.exists():
            with open(results_file) as f:
                results = json.load(f)
            clip_map = {}
            for r in results:
                if r.get("success"):
                    local_path = str(clips_dir / f"scene_{r['scene']:03d}.mp4")
                    if os.path.exists(local_path):
                        clip_map[r["scene"]] = local_path
                        log.info(f"  Scene {r['scene']}: Wan2.1 clip ✓")
            log.info(f"Wan2.1: {len(clip_map)}/{len(scenes_needing_video)} clips generated")
            tg(f"✅ Wan2.1: {len(clip_map)} animated clips ready")
            return clip_map
        else:
            log.error("wan21_results.json not found")
            return {}

    except subprocess.TimeoutExpired:
        log.error("Wan2.1 Colab run timed out")
        return {}
    except Exception as e:
        log.error(f"Wan2.1 Colab failed: {e}")
        return {}

# ═══════════════════════════════════════════════════════════
#  KLING API INTEGRATION
# ═══════════════════════════════════════════════════════════
def validate_kling_key(kling_key):
    if not kling_key:
        return False
    try:
        resp = requests.get("https://kling26ai.com/api/status?task_id=test",
            headers={"Authorization": f"Bearer {kling_key}"}, timeout=10)
        if resp.status_code == 401:
            log.error("KLING_API_KEY is invalid (401 Unauthorized)")
            return False
        return True
    except Exception:
        return True

def generate_kling_clip(prompt, duration=5, mode="std", scene_num=0):
    kling_key = os.environ.get("KLING_API_KEY", "")
    if not kling_key:
        return None

    out_path = str(WORKSPACE / "visuals" / f"kling_{scene_num:03d}.mp4")

    try:
        BASE = "https://kling26ai.com"
        resp = requests.post(f"{BASE}/api/generate",
            headers={"Authorization": f"Bearer {kling_key}", "Content-Type": "application/json"},
            json={"prompt": prompt, "aspect_ratio": "16:9", "duration": str(duration), "sound": False},
            timeout=30)

        if resp.status_code == 401:
            log.warning(f"Kling scene {scene_num}: 401 Unauthorized")
            return None
        if resp.status_code != 200:
            log.warning(f"Kling26 submit failed: {resp.status_code}")
            return None

        result = resp.json()
        if result.get("code") != 200:
            log.warning(f"Kling26 error: {result.get('message', '')}")
            return None

        task_id = result.get("data", {}).get("task_id")
        if not task_id:
            return None

        log.info(f"  Kling26 task {task_id} submitted, polling...")
        for attempt in range(60):
            time.sleep(5)
            poll = requests.get(f"{BASE}/api/status?task_id={task_id}",
                headers={"Authorization": f"Bearer {kling_key}"}, timeout=15)

            if poll.status_code == 401:
                return None
            if poll.status_code != 200:
                continue

            data = poll.json()
            if data.get("code") != 200:
                continue

            status = data.get("data", {}).get("status", "")
            if status == "SUCCESS":
                video_urls = data.get("data", {}).get("response", [])
                if video_urls:
                    r = requests.get(video_urls[0], stream=True, timeout=60)
                    with open(out_path, "wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    log.info(f"  Kling26 scene {scene_num}: ✓ ({os.path.getsize(out_path)//1024}KB)")
                    return out_path
                break
            elif status == "FAILED":
                log.warning(f"  Kling26 task failed")
                break
            else:
                log.info(f"  Kling26 {task_id}: {status} (attempt {attempt+1}/60)")

    except Exception as e:
        log.warning(f"  Kling26 scene {scene_num}: {e}")
    return None

def stage_kling_visuals(script, cfg, max_clips=2):
    kling_key = os.environ.get("KLING_API_KEY", "")
    if not kling_key:
        log.info("KLING_API_KEY not set — skipping Kling")
        return script

    if not validate_kling_key(kling_key):
        return script

    genre = cfg.get("genre","documentary")
    if genre not in ["documentary","shorts"]:
        log.info(f"Kling: skipping for genre={genre}")
        return script

    log.info(f"Kling: generating up to {max_clips} cinematic hero shots...")
    tg(f"🎬 Kling AI: generating {max_clips} cinematic clips...")

    candidates = [s for s in script
                  if s.get("visual_type") in ("stock_video","ai_image")
                  and not s.get("video_file")][:max_clips]

    for scene in candidates:
        n      = scene["scene"]
        prompt = scene.get("ai_prompt", scene.get("visual_search","cinematic scene"))
        kling_prompt = f"{prompt}, cinematic 4K, dramatic lighting, smooth motion, professional filmmaking"
        clip = generate_kling_clip(kling_prompt, duration=5, mode="std", scene_num=n)
        if clip:
            scene["video_file"] = clip
            scene["visual_source"] = "kling"
            log.info(f"  Scene {n}: Kling clip applied")

    return script

# ═══════════════════════════════════════════════════════════
#  v5.2 PIPELINE — DUAL-SCRIPT + KOKORO HINDI + ALL FEATURES
# ═══════════════════════════════════════════════════════════
def run_pipeline_v52():
    start = time.time()
    cfg   = parse_input()
    genre = cfg["genre"]

    log.info(f"🚀 v5.2 | {cfg['topic']} | {genre} | {cfg['lang']} | {cfg['duration_min']}min")
    tg(f"🚀 v5.2 DUAL-SCRIPT\n📌 {cfg['topic']}\n🎬 {genre} | {cfg['lang']} | {cfg['duration_min']}min\n⏰ {cfg['schedule']} UTC")

    try:
        research = None
        if genre == "documentary":
            log.info("🎯 Routing to new AI Studio Documentary Engine (Phase 2 Integration)...")
            from agents.engine import run_documentary_pipeline
            script = run_documentary_pipeline(cfg)
            _save(script, "script_ai_studio.json")
            tg(f"✍️ {len(script)} scenes generated via AI Studio")
        else:
            research = stage_1_research(cfg)
            _save(research, "research.json")

            script = stage_2_script(research, cfg)
            _save(script, "script.json")
            tg(f"✍️ {len(script)} scenes (Devanagari + Hinglish)")

        script = stage_3_voice(script, cfg)
        music_path = stage_4_music(cfg)

        # Wan2.1 for cartoon genres
        wan_scenes = []
        if genre in ("cartoon",) and os.path.exists(os.path.expanduser("~/.config/colab-cli/sessions.json")):
            wan_scenes = [s for s in script
                          if s.get("visual_type") == "ai_image"
                          and not skip_ai(s.get("ai_prompt",""))]
            log.info(f"Routing {len(wan_scenes)} scenes to Wan2.1")

        wan_clips = {}
        if wan_scenes:
            wan_clips = stage_wan21_colab(wan_scenes, cfg["topic"])

        for scene in script:
            if scene["scene"] in wan_clips:
                scene["video_file"] = wan_clips[scene["scene"]]
                scene["visual_source"] = "wan2.1"
                if scene.get("audio_file"):
                    scene["actual_duration"] = get_dur(scene["audio_file"])
                else:
                    scene["actual_duration"] = float(scene.get("duration_hint",4))

        # Kling removed per user request
        
        # We run stage_6_visuals for all genres to fetch DDG/Pexels/Pixabay assets
        script = stage_6_visuals(script, cfg)
        _save(script, "script_final.json")

        if genre == "documentary":
            log.info("🎯 Routing visual composition to Remotion (Phase 3 Integration)...")
            script_path = str(WORKSPACE / "script_final.json")
            final_video = str(WORKSPACE / "final_documentary.mp4")
            
            # Shell out to npx remotion render
            # We must pass the absolute paths to Remotion. The script json contains absolute paths.
            # We copy the assets to remotion/public to ensure Remotion can read them securely without file:// restrictions.
            public_dir = WORKSPACE.parent / "remotion" / "public" / "assets"
            public_dir.mkdir(parents=True, exist_ok=True)
            
            for scene in script:
                vid = scene.get("video_file")
                if vid and os.path.exists(vid):
                    import shutil
                    basename = os.path.basename(vid)
                    shutil.copy(vid, str(public_dir / basename))
                    # Remotion can access it via 'assets/basename'
                    scene["video_file"] = f"assets/{basename}"
            
            # Save updated script for Remotion
            _save({"scenes": script}, "script_remotion.json")
            script_path = str((WORKSPACE / "script_remotion.json").resolve())
            final_video_abs = str((WORKSPACE / "final_documentary.mp4").resolve())

            remotion_cmd = f"npx remotion render src/index.ts DocumentaryVideo {final_video_abs} --props={script_path}"
            log.info(f"Running Remotion: {remotion_cmd}")
            import subprocess
            res = subprocess.run(remotion_cmd, cwd="remotion", shell=True, capture_output=True, text=True)
            if res.returncode != 0:
                log.error(f"Remotion failed: {res.stderr}")
                raise Exception("Remotion render failed")
            log.info("✅ Remotion render complete!")
            
            # Phase 4: Mix the generated Remotion visuals with Audio/BGM
            final_video = stage_assemble_documentary(script, cfg, final_video, music_path)
        else:
            final_video = stage_7_assemble(script, cfg, music_path)

        qc = stage_8_qc(final_video, script, cfg)
        _save(qc, "qc.json")

        verdict = qc.get("verdict","approved")
        score   = qc.get("score",7)

        drive_link = stage_10_drive_backup(final_video, script, research, cfg, verdict, score)
        drive_note = f"\n📁 Drive: {drive_link}" if drive_link else ""

        if verdict == "retry":
            tg(f"❌ QC {score}/10 — Rejected\n{qc.get('reason','')}{drive_note}"); return
        if verdict == "drafts":
            tg(f"⚠️ QC {score}/10 — Drafts\n{qc.get('reason','')}{drive_note}"); return

        url     = stage_9_publish(final_video, script, cfg)
        elapsed = int(time.time()-start)
        total   = sum(s.get("actual_duration",4) for s in script)
        wan_ct  = sum(1 for s in script if s.get("visual_source")=="wan2.1")
        kling_ct= sum(1 for s in script if s.get("visual_source")=="kling")

        tg(
            f"✅ DONE!\n\n"
            f"📺 {url}\n"
            f"⏰ {cfg['schedule']} UTC\n"
            f"🏆 QC: {score}/10\n"
            f"🎬 {len(script)} scenes | {total:.0f}s\n"
            f"✂️ Avg {total/max(len(script),1):.1f}s/cut\n"
            f"🎥 Wan2.1: {wan_ct} clips | Kling: {kling_ct} clips\n"
            f"🌍 {cfg['lang']} | {cfg['genre']} | DUAL-SCRIPT\n"
            f"⚡ {elapsed}s total{drive_note}"
        )

    except Exception as e:
        import traceback
        log.error(f"CRASH: {e}\n{traceback.format_exc()}")
        tg(f"💥 Crashed: {str(e)[:250]}")
        raise


if __name__ == "__main__":
    run_pipeline_v52()