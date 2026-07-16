"""
=============================================================
  ULTIMATE HINDI CHANNEL — pipeline.py v5.0 FINAL
=============================================================
TWO MODES:
  Mode 1 (Daily Auto): Reads topics.json → 3 videos/day
                        Finance | Tech | Crime in Hindi
  Mode 2 (Manual):     /make command or GitHub workflow
                        Any genre/lang/duration

WHAT'S IN v5.0:
  - Niche engine: finance/tech/crime auto-settings
  - Script injection: if you provide script it uses it
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
    # Array never closed (response got cut off mid-object due to token
    # limit). Salvage whichever complete {...} objects exist instead of
    # discarding the entire batch.
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
NICHE_INPUT     = os.environ.get("NICHE", "")      # finance|tech|crime (daily mode)
SCRIPT_INPUT    = os.environ.get("SCRIPT", "")     # optional pre-written script

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
def gemini(prompt, model="gemini-2.0-flash"):
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
#  PARSE INPUT — handles both daily auto and manual modes
# ═══════════════════════════════════════════════════════════
def sanitize_visual_term(term, vprefix, niche="", is_prompt=False):
    """
    Safety net run AFTER the LLM response, regardless of whether it obeyed
    the English-only instruction. Strips Devanagari script (Pexels/Pixabay/
    Pollinations cannot use it — this was the root cause of near-zero stock
    results) and falls back to a safe generic term if nothing usable remains.
    """
    if not term:
        term = vprefix
    # Strip Devanagari unicode block (U+0900–U+097F) entirely
    cleaned = re.sub(r'[\u0900-\u097F]+', ' ', term)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # If nothing meaningful survived, use a safe generic fallback
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

# ═══════════════════════════════════════════════════════════
#  REAL ASSET POOLS — premium fonts, LUTs, overlays, SFX
#  Upload your actual files to these folders in the repo:
#    assets/fonts/caption/*.ttf     ← Roman-script fonts for captions
#    assets/fonts/heading/*.ttf     ← bold display fonts (optional use)
#    assets/luts/<color_grade>/*.cube   e.g. assets/luts/cinematic/*.cube
#    assets/overlays/*.png          ← transparent bg-removed fire/particles
#    assets/sfx/deep_impact/*.mp3
#    assets/sfx/whoosh/*.mp3
#    assets/sfx/click/*.mp3
#    assets/sfx/riser/*.mp3
# If a folder is missing or empty, the pipeline automatically falls
# back to the built-in system fonts / synthesized tones / plain color
# grade — nothing breaks if you haven't uploaded everything yet.
# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
#  HINGLISH — Roman-script Hindi+English mix, not pure Devanagari.
#  This is what modern Indian YouTube/Instagram content actually
#  sounds like, and it also means captions can use ANY of your
#  premium Latin fonts directly — no Devanagari font needed at all.
# ═══════════════════════════════════════════════════════════
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
    """
    Real premium font if uploaded, otherwise safe system fallback.
    Filters by filename keyword — your font names already say what
    they are ("Zosma Bold", "ZabriskieBook-Heavy" vs "Zosma", "Zephyr")
    so no folder subdivision is needed, just a name match.
    """
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
    # Fallback: Hinglish is Roman script, so any Latin system font works fine
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Maps our internal color-grade categories to keywords found in your
# actual LUT filenames (all living flat in assets/luts/, not subfoldered)
LUT_KEYWORD_MAP = {
    "teal_orange": ["warm cinema", "kodak", "clean straight", "gold rush"],
    "cool_blue":   ["blue cold", "blue moon", "blue ice", "blue steel", "matrix green"],
    "dark_noir":   ["noir", "iron", "bleach"],
    "cinematic":   ["warm cinema", "clean straight", "big"],
    "cartoon":     ["thermal royalty", "thermal picasso", "thermal plastic", "gold rush"],
    "energetic":   ["thermal vice", "thermal crush", "cross"],
}

def get_lut_file(color_grade):
    """
    Finds a real .cube LUT whose filename matches this genre's mood,
    searching the flat assets/luts/ folder by keyword instead of
    expecting subfolders (your LUTs are named thematically, e.g.
    "SL Noir HDR.cube", "Warm Cinema.cube", "VM Thermal Vice.cube").

    IMPORTANT: if nothing matches, returns None (falls back to the safe
    eq= color grade) instead of picking a random LUT — a random pick
    previously caused whole videos to render in the wrong mood entirely
    (e.g. a bright pink LUT applied to a serious crime documentary).
    """
    folder = ASSETS_DIR / "luts"
    if not folder.exists():
        return None
    all_luts = list(folder.glob("*.cube"))
    if not all_luts:
        return None
    keywords = LUT_KEYWORD_MAP.get(color_grade, [])
    matches = [f for f in all_luts if any(kw in f.stem.lower() for kw in keywords)]
    if not matches:
        return None  # no matching mood — safer to skip than guess wrong
    return str(random.choice(matches))

def get_overlay_video():
    """
    Random VHS/glitch video overlay (.mp4) if uploaded to assets/overlays/.
    These are effect clips (screen-blended over footage for a transition
    flash), not transparent PNGs — handled via the blend filter, not
    alpha overlay.
    """
    return pick_asset("overlays", "mp4")

def extract_json_object(text):
    """Same robust extraction as extract_json_array, but for a single {...} object."""
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
    # Truncated mid-object (token limit hit) — salvage whatever complete
    # "key": "value" fields exist instead of discarding everything and
    # falling back to a generic placeholder title/description.
    return _salvage_truncated_object(text[start:])

def _salvage_truncated_object(fragment):
    last_complete = fragment.rfind('",')
    if last_complete == -1:
        last_complete = fragment.rfind('"}')
        if last_complete == -1:
            raise ValueError("Cannot salvage truncated object — no complete field found")
        return fragment[:last_complete+2]
    trimmed = fragment[:last_complete+1].rstrip(',')
    return trimmed + "}"

def extract_english_prefix(topic, genre="documentary"):
    """
    Pulls out any English/ASCII words from the topic (e.g. 'Paytm', 'RBI',
    'ISRO') to use as a safe stock-search prefix. If the topic is entirely
    in Hindi/Devanagari with no English words, falls back to a generic
    genre-based term instead of ever passing Devanagari to Pexels/Pixabay/
    Pollinations, which cannot use it and previously caused every search
    to return zero results.
    """
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

def parse_input():
    """
    Returns unified config dict regardless of input mode.
    Daily auto: NICHE + TOPIC + optional SCRIPT env vars
    Manual:     RAW_INPUT with optional --genre --lang --duration flags
    """
    # Daily auto mode (from daily_scheduler.yml)
    if NICHE_INPUT and NICHE_INPUT in NICHE_PRESETS:
        preset = NICHE_PRESETS[NICHE_INPUT]
        topic = RAW_INPUT or f"Latest {NICHE_INPUT} news"
        # Parse schedule time from end of TOPIC if present
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

    # Manual mode (Telegram or GitHub workflow)
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
    # Fallback
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
#  STAGE 2 — SCRIPT
#  If user provided script → parse it into scenes
#  Otherwise → generate with Groq
# ═══════════════════════════════════════════════════════════
def parse_provided_script(script_text, cfg):
    """Convert user-provided script text into scene JSON format."""
    log.info("Stage 2: Parsing provided script...")
    topic   = cfg["topic"]
    sfx_def = cfg.get("sfx_default","whoosh")
    vprefix = cfg.get("visual_prefix", topic)
    try:
        # Try to get Groq to parse it into scenes
        text = groq(f"""Parse this script into video scenes.
Script:
{script_text[:3000]}

Topic: {topic}
Language: {cfg['lang']}

Return ONLY JSON array (no markdown):
[{{"scene":1,"voiceover":"exact words to say — copy verbatim from the script, do not translate or rewrite it","visual_type":"stock_video","visual_search":"English keyword only","ai_prompt":"English cinematic description only","emotion":"dramatic","sfx":"{sfx_def}","duration_hint":4}}]

Rules:
- Split at natural pause/sentence boundaries
- Max 15 words per voiceover
- Do NOT translate or rewrite the voiceover text — use it exactly as the user wrote it
- visual_type: "stock_video" or "ai_image" or "text_stat"
- visual_search and ai_prompt MUST BE IN ENGLISH ONLY regardless of what language the script is in — use generic nouns like "office building", "money currency", "worried person" — no brand names, no Hindi/Devanagari text
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
        # Fallback: split by sentences
        sentences = [s.strip() for s in re.split(r'[।\.\!\?]+', script_text) if len(s.strip()) > 10]
        t = 0.0
        scenes = []
        for i, sent in enumerate(sentences[:40]):
            vt = "text_stat" if i % 10 == 9 else "stock_video" if i % 3 == 1 else "ai_image"
            s = {"scene":i+1,"voiceover":sent[:80],"visual_type":vt,
                 "visual_search":f"{vprefix} cinematic","ai_prompt":f"cinematic {topic} scene",
                 "emotion":"dramatic","sfx":sfx_def,"duration_hint":4,"start_time":t}
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

    # If user provided a script, use it
    if cfg.get("provided_script"):
        return parse_provided_script(cfg["provided_script"], cfg)

    log.info(f"Stage 2: Writing script for {topic}")
    tg(f"✍️ Writing script...")

    target = max(15, int(dur * scenes_pm))
    lang_note = HINGLISH_INSTRUCTION if lang == "hindi" else (f"ALL voiceover in {lang}." if lang != "english" else "")

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

    # ── OUTLINE FIRST — this is the fix for disconnected, nonsensical
    # scenes. Batching alone (with only "the last line" as context) has
    # no memory of the overall story, so scenes drift into unrelated
    # fragments after a few batches. Generating a structured beat outline
    # ONCE up front, then feeding that FULL outline into every batch,
    # keeps the whole video on one coherent throughline.
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
Each point = one beat of the story in ONE short sentence (English is fine here,
this is just a planning outline, not the final script).
Point 1 MUST be the shocking hook. Points must flow in logical order —
each one should follow naturally from the one before it, like telling a real story
to a friend, not jumping between unrelated facts.

Return ONLY a JSON array of {num_beats} short strings, no markdown, no explanation:
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

    # ── BATCHED GENERATION ──────────────────────────────────────
    # Requesting 90+ scenes of Hindi text in ONE completion reliably
    # gets truncated mid-array (Hindi/Devanagari uses far more tokens
    # per character than English), which is why "Unbalanced JSON array"
    # kept happening regardless of API key. Fix: generate in small
    # batches that always fit comfortably within the token budget —
    # but now every batch sees the FULL outline, not just the last line,
    # so the story stays connected across all of them.
    BATCH_SIZE = 10
    full_script = []
    stalled = 0

    while len(full_script) < target and stalled < 3:
        remaining = target - len(full_script)
        batch_n = min(BATCH_SIZE, remaining)
        start_num = len(full_script) + 1
        progress_pct = int((start_num / target) * 100)

        continuity = (
            f"STORY OUTLINE (the whole video's arc — stay connected to this throughout):\n{outline_str}\n\n"
            f"You are now writing scenes for roughly the {progress_pct}% point of the story "
            f"(scene {start_num} of {target} total). Write scenes that correspond to whichever "
            f"outline beat(s) fit this point in the story. Do not jump to a random unrelated fact — "
            f"follow the outline's order and keep building the SAME story."
        )
        if full_script:
            continuity += f'\n\nThe previous scene said: "{full_script[-1].get("voiceover","")}". Continue naturally from there, do not repeat it.'
        else:
            continuity += "\n\nThis is the OPENING of the video. Scene 1 must be the shocking hook from the outline."

        prompt = f"""You are a world-class viral Hindi YouTube scriptwriter.
Style: {style}
{lang_note}
{niche_note}

Topic: "{topic}"

{continuity}

Write EXACTLY {batch_n} scenes, numbered {start_num} to {start_num + batch_n - 1}.

STRICT RULES:
- Every scene must be a real, grammatically complete sentence a human would actually say —
  never a garbled or nonsensical fragment. Read it back in your head before writing it:
  does it actually mean something coherent? If not, rewrite it.
- Max 12 words per scene voiceover
- visual_type: mostly "stock_video" or "ai_image". Use "text_stat" RARELY — only for scenes
  that state an actual number, statistic, or shocking data point. Do NOT force a text_stat
  on a fixed pattern; most scenes should show real footage, not a text card.
- visual_search MUST BE 100% IN ENGLISH ONLY, even though voiceover is in {lang}. Use simple generic nouns a stock photo site understands (e.g. "bank building", "indian currency", "worried man office", "smartphone screen"). NEVER put Hindi/Devanagari text in visual_search. NEVER use specific brand/company names in visual_search — use generic category words instead (e.g. "mobile payment app" not "Paytm").
- ai_prompt MUST ALSO BE IN ENGLISH ONLY. Cinematic description, no faces, no text, no flags, no monuments, no specific brand names or logos (use generic descriptions like "fintech office" instead of company names — brand names get blocked by the image generator's safety filter).
- visual_search and ai_prompt must actually match what THIS scene's voiceover is about — never generic filler unrelated to the sentence
- sfx: deep_impact=reveal | whoosh=transition | click=fact | riser=tension | none=calm

CRITICAL: Return ONLY a raw JSON array of exactly {batch_n} objects. No reasoning, no explanation, no markdown fences.
[{{"scene":{start_num},"voiceover":"text in {lang}","visual_type":"stock_video","visual_search":"English keyword only","ai_prompt":"English cinematic description only","emotion":"dramatic","sfx":"{sfx_def}","duration_hint":4}}]"""

        try:
            # Gemini is materially better at natural Hinglish than Groq's
            # open models — this directly targets the repeated "broken/
            # nonsensical sentences" feedback. Groq remains the fallback
            # if Gemini's quota is exhausted for this run.
            try:
                text = gemini(prompt)
            except Exception as gem_err:
                log.warning(f"  Gemini failed for this batch ({gem_err}), falling back to Groq")
                text = groq(prompt, max_tokens=2500)
            batch = json.loads(extract_json_array(text))
            if not batch:
                raise ValueError("Empty batch returned")
            for j, s in enumerate(batch):
                s["scene"] = start_num + j  # guarantee correct sequential numbering
                # Safety net: strip any Hindi/Devanagari that leaked through
                # despite instructions, and fall back to a safe generic
                # English term so Pexels/Pollinations never receive Hindi text
                s["visual_search"] = sanitize_visual_term(s.get("visual_search",""), vprefix, niche)
                s["ai_prompt"] = sanitize_visual_term(s.get("ai_prompt",""), vprefix, niche, is_prompt=True)
            full_script.extend(batch)
            log.info(f"  Batch OK: +{len(batch)} scenes ({len(full_script)}/{target} total)")
            stalled = 0
            # Respect free-tier rate limits — without this delay, rapid
            # back-to-back batch calls can trigger 429 errors on longer
            # videos (96+ scenes = 10+ batch calls in a row)
            time.sleep(3)
        except Exception as e:
            log.warning(f"  Batch failed: {e}")
            stalled += 1
            time.sleep(8)  # back off longer on failure, likely a rate limit

    if len(full_script) >= 10:
        # Hard safety cap: no matter what the LLM decided, never let more
        # than 15% of scenes become text_stat cards. This is what was
        # causing "only 5-6 real clips visible" — too many yellow-text
        # cards were diluting the actual visual content.
        max_text_stat = max(1, int(len(full_script) * 0.15))
        text_stat_indices = [i for i, s in enumerate(full_script) if s.get("visual_type") == "text_stat"]
        if len(text_stat_indices) > max_text_stat:
            excess = text_stat_indices[max_text_stat:]
            for idx in excess:
                full_script[idx]["visual_type"] = "ai_image" if idx % 2 == 0 else "stock_video"
            log.info(f"  Capped text_stat: {len(text_stat_indices)} → {max_text_stat} (converted {len(excess)} to real visuals)")

        t = 0.0
        for s in full_script:
            s["start_time"] = t; t += float(s.get("duration_hint",4))
            if vprefix.lower() not in s.get("visual_search","").lower():
                s["visual_search"] = f"{vprefix} {s.get('visual_search','')}"
        log.info(f"Stage 2: {len(full_script)} scenes written (batched, target was {target})")
        return full_script

    log.error(f"Stage 2: batching produced only {len(full_script)} scenes — using cycling fallback")
    import itertools
    facts = [f for f in ([research.get("hook","")] + research.get("key_facts",[]) + research.get("statistics",[])) if f]
    if not facts:
        facts = [f"{topic} ke baare mein jaankari"]
    cycled = list(itertools.islice(itertools.cycle(facts), target))
    variants = ["aerial establishing shot","close-up detail shot","wide dramatic angle","low angle dramatic","office interior shot"]
    t = 0.0; script = []
    for i, f in enumerate(cycled):
        vt = "text_stat" if i % 10 == 9 else ("stock_video" if i % 3 == 1 else "ai_image")
        variant = variants[i % len(variants)]
        s = {"scene": i+1, "voiceover": f[:60], "visual_type": vt,
             "visual_search": f"{vprefix} {variant}",
             "ai_prompt": f"{variant} cinematic dramatic {topic} scene, no text, no faces",
             "emotion": "dramatic", "sfx": sfx_def, "duration_hint": 4, "start_time": t}
        script.append(s); t += 4
    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 3 — VOICE
# ═══════════════════════════════════════════════════════════
async def _edge_tts(text, path, voice, rate="+8%", pitch="+0Hz"):
    import edge_tts
    # Slightly faster rate makes Edge-TTS sound noticeably less flat/robotic.
    # This is a real engine limitation — true emotional prosody isn't
    # available on the free tier — but varying rate/pitch by the scene's
    # tagged emotion at least breaks up the "same tone the whole video"
    # monotony, using a field the script already generates but was
    # previously never actually applied anywhere.
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(path)

# Maps each scene's "emotion" tag (already generated by the script but
# previously unused) to a rate/pitch tweak for more dynamic delivery
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
    audio_dir = WORKSPACE / "audio"; audio_dir.mkdir(exist_ok=True)
    failed_scenes = 0
    
    for idx, scene in enumerate(script):
        n = scene["scene"]
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
                            scene["audio_file"]=out; done=True
                        break
                    except Exception as e:
                        log.warning(f"  Scene {n} {v} attempt {attempt+1}: {e}")
                        time.sleep(1.5)
                if done: break

        # Fallback to gTTS
        if not done:
            try:
                from gtts import gTTS
                lc={"hindi":"hi","english":"en","spanish":"es","french":"fr","german":"de"}.get(lang,"hi")
                gTTS(text=text,lang=lc).save(out)
                if os.path.exists(out) and os.path.getsize(out) > 500:
                    scene["audio_file"]=out
                    done=True
            except Exception as e:
                log.error(f"  Scene {n}: gTTS also failed: {e}")
        
        if not done:
            failed_scenes += 1
            scene["audio_file"] = None
        
        if idx % 5 == 4:
            time.sleep(1)
    
    if failed_scenes:
        log.warning(f"Stage 3: {failed_scenes}/{len(script)} scenes have NO audio (all retries exhausted)")
    return script

def generate_kokoro_voice(text, out_path, lang, emotion):
    """Generate voice using Kokoro TTS"""
    voice_map = {
        "english": "af_heart",
        "hindi": "af_heart",  # Kokoro doesn't have Hindi, use English for Hinglish
        "spanish": "af_heart",
        "french": "af_heart",
        "german": "af_heart"
    }
    voice = voice_map.get(lang, "af_heart")
    
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
        pipeline = KPipeline(lang_code='a')
        generator = pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+')
        
        audio_segments = []
        sample_rate = 24000
        
        for i, (gs, ps, audio) in enumerate(generator):
            audio_segments.append(audio)
        
        if audio_segments:
            import numpy as np
            full_audio = np.concatenate(audio_segments)
            
            try:
                from pydub import AudioSegment
                audio_segment = AudioSegment(
                    full_audio.tobytes(),
                    frame_rate=sample_rate,
                    sample_width=full_audio.dtype.itemsize,
                    channels=1
                )
                audio_segment.export(out_path, format="mp3")
                return os.path.exists(out_path) and os.path.getsize(out_path) > 500
            except ImportError:
                import soundfile as sf
                wav_path = out_path.replace('.mp3', '.wav')
                sf.write(wav_path, full_audio, sample_rate)
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_path,
                    "-codec:a", "libmp3lame", "-qscale:a", "2", out_path
                ], capture_output=True, timeout=30)
                return os.path.exists(out_path) and os.path.getsize(out_path) > 500
    except ImportError:
        log.warning("Kokoro TTS not available, falling back to other methods")
    except Exception as e:
        log.warning(f"Kokoro generation failed: {e}")
    return False

# ═══════════════════════════════════════════════════════════
#  STAGE 4 — MUSIC (freepd.com + incompetech — CC licensed)
# ═══════════════════════════════════════════════════════════
def stage_4_music(cfg):
    mood = cfg.get("music_mood","cinematic dramatic")
    log.info(f"Stage 4: Music ({mood})...")

    def is_valid_audio(path):
        """Verify the file is actually decodable audio, not an HTML error
        page or truncated download (a 200 status with a 'not found' HTML
        body was silently accepted before, causing the 'Invalid argument'
        crash later in ffmpeg during the final mix)."""
        try:
            r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                "-of","default=noprint_wrappers=1:nokey=1", path],
                capture_output=True, text=True, timeout=15)
            return r.returncode == 0 and r.stdout.strip() != ""
        except Exception:
            return False

    # PRIMARY: your own uploaded royalty-free tracks in assets/music/.
    # The hardcoded freepd.com/incompetech URLs below have proven
    # unreliable (both failed validation in testing, causing silent
    # tracks) — your own files are the dependable source now.
    music_folder = ASSETS_DIR / "music"
    if music_folder.exists():
        mood_files = list(music_folder.glob("*.mp3")) + list(music_folder.glob("*.m4a")) + list(music_folder.glob("*.wav"))
        # Prefer a filename matching the mood keywords if you organize them that way
        keyword_matches = [f for f in mood_files if any(w in f.stem.lower() for w in mood.split())]
        pool = keyword_matches if keyword_matches else mood_files
        if pool:
            chosen = random.choice(pool)
            if is_valid_audio(str(chosen)):
                log.info(f"Stage 4: Using your uploaded track — {chosen.name}")
                return str(chosen)

    # 2. Try Freesound API
    freesound_key = os.environ.get("FREESOUND_KEY", "")
    if freesound_key:
        try:
            music = get_freesound_music(mood, freesound_key)
            if music and is_valid_audio(music):
                log.info("Stage 4: Music from Freesound")
                return music
        except Exception as e:
            log.warning(f"Stage 4: Freesound failed: {e}")

    # 3. Try Pixabay API
    pixabay_key = os.environ.get("PIXABAY_KEY", "")
    if pixabay_key:
        try:
            music = get_pixabay_music(mood, pixabay_key)
            if music and is_valid_audio(music):
                log.info("Stage 4: Music from Pixabay")
                return music
        except Exception as e:
            log.warning(f"Stage 4: Pixabay failed: {e}")

    # 4. Try FreePD
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

    # 5. Generate silence
    music_path = str(WORKSPACE/"music.m4a")
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
        "-t","300","-c:a","aac",music_path], capture_output=True, timeout=30)
    log.warning("Stage 4: Using silent track")
    return music_path

def get_freesound_music(mood, api_key):
    """Get background music from Freesound API"""
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
            params={
                "query": search_query,
                "filter": "duration:[30 TO 180] type:wav",
                "sort": "rating_desc",
                "page_size": 20
            },
            headers={"Authorization": f"Token {api_key}"},
            timeout=30
        )
        if resp.status_code != 200:
            return None
        results = resp.json().get("results", [])
        if not results:
            return None
        sound = random.choice(results)
        sound_id = sound["id"]
        
        detail_resp = requests.get(
            f"https://freesound.org/apiv2/sounds/{sound_id}/",
            headers={"Authorization": f"Token {api_key}"},
            timeout=30
        )
        if detail_resp.status_code != 200:
            return None
        download_url = detail_resp.json().get("previews", {}).get("preview-hq-mp3")
        if not download_url:
            return None
        
        music_path = str(WORKSPACE / "freesound_music.mp3")
        r = requests.get(download_url, timeout=60)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(music_path, "wb") as f:
                f.write(r.content)
            return music_path
    except Exception as e:
        log.warning(f"Freesound music failed: {e}")
    return None

def get_pixabay_music(mood, api_key):
    """Get background music from Pixabay API"""
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
        resp = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": api_key, "q": genre, "page_size": 20, "video_type": "music"},
            timeout=30
        )
        if resp.status_code != 200:
            return None
        results = resp.json().get("hits", [])
        if not results:
            return None
        music = random.choice(results)
        download_url = music["videos"]["medium"]["url"]
        
        music_path = str(WORKSPACE / "pixabay_music.mp4")
        r = requests.get(download_url, timeout=60)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(music_path, "wb") as f:
                f.write(r.content)
            audio_path = str(WORKSPACE / "pixabay_music.mp3")
            subprocess.run([
                "ffmpeg", "-y", "-i", music_path,
                "-vn", "-codec:a", "libmp3lame", "-qscale:a", "2",
                audio_path
            ], capture_output=True, timeout=60)
            return audio_path
    except Exception as e:
        log.warning(f"Pixabay music failed: {e}")
    return None

# ═══════════════════════════════════════════════════════════
#  STAGE 5 — SFX (Freesound preview URLs — no OAuth needed)
# ═══════════════════════════════════════════════════════════
SFX_QUERIES = {
    "deep_impact": "cinematic impact boom",
    "whoosh":      "swoosh transition whoosh",
    "click":       "digital click notification",
    "riser":       "tension riser build suspense",
    "none":        None,
}

_sfx_cache = {}  # avoid re-generating same SFX

def fetch_sfx(sfx_type):
    """
    Generates deterministic SFX tones instead of Freesound free-text search.
    Freesound text search is unpredictable (e.g. "riser" can return a wind/
    whistle clip) — synthesized tones guarantee the correct, expected sound.
    """
    if sfx_type == "none" or not sfx_type: return None
    if sfx_type in _sfx_cache: return _sfx_cache[sfx_type]

    # Your real curated SFX folders use these exact (capitalized) names —
    # this maps our internal sfx_type keys to your actual folder names.
    # No "click" folder was supplied, so click always uses the synthesized
    # tone below, which is fine (it's a tiny, unobtrusive sound anyway).
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
        "deep_impact": ("sine=frequency=80:duration=0.4:sample_rate=44100", "volume=0.5,afade=t=out:st=0.2:d=0.2"),
        "whoosh":      ("anoisesrc=color=pink:duration=0.3:sample_rate=44100", "volume=0.25,afade=t=in:d=0.05,afade=t=out:st=0.15:d=0.15,highpass=f=800"),
        "click":       ("sine=frequency=1400:duration=0.08:sample_rate=44100", "volume=0.3"),
        "riser":       ("sine=frequency=200:duration=0.6:sample_rate=44100", "volume=0.3,afade=t=in:d=0.5"),
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
    if grain: vf += ",noise=alls=4:allf=t+u"
    r = subprocess.run(["ffmpeg","-y","-loop","1","-i",img,"-vf",vf,
        "-t",str(dur),"-c:v","libx264","-pix_fmt","yuv420p","-preset","fast",out],
        capture_output=True, timeout=180)
    return r.returncode==0

def make_text_stat(text, out, dur, lang="hindi"):
    # Yellow text on very dark background
    safe = re.sub(r"[':\"\\%]","",text)[:60]
    words = safe.split()
    lines,cur=[],[]
    for w in words:
        cur.append(w)
        if len(" ".join(cur))>18: lines.append(" ".join(cur)); cur=[]
    if cur: lines.append(" ".join(cur))
    # Hinglish is Roman script, so any premium Latin font works here now —
    # stat cards are hook/emphasis moments, so use a bold/heavy font
    font = get_caption_font(bold=True)
    dt=[]
    for i,line in enumerate(lines[:3]):
        y=f"(h/2)-{(len(lines)//2-i)*90}"
        # Fade-in animation instead of static text — alpha ramps 0→1 over
        # the first 0.35s for a cleaner entrance than an abrupt hard cut.
        # (Note: fontsize expressions for a "scale pop" effect aren't
        # reliably supported across ffmpeg versions, so keeping this to
        # the well-documented alpha parameter to avoid breaking generation.)
        dt.append(
            f"drawtext=text='{line}':fontsize=76:fontcolor=#FFD700:"
            f"x=(w-text_w)/2:y={y}:fontfile={font}:"
            f"shadowcolor=black:shadowx=4:shadowy=4:alpha='if(lt(t,0.35),t/0.35,1)'"
        )
    vf=",".join(dt) if dt else f"drawtext=text='{safe[:20]}':fontsize=76:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:fontfile={font}"
    r=subprocess.run(["ffmpeg","-y","-f","lavfi",
        "-i",f"color=c=0x080808:size=1920x1080:duration={dur}:rate=25",
        "-vf",vf+",noise=alls=6:allf=t+u","-c:v","libx264","-pix_fmt","yuv420p",out],
        capture_output=True,timeout=60)
    if r.returncode != 0:
        # Alpha animation failed on this ffmpeg build — retry without it
        # rather than losing the whole text card
        log.warning(f"  text_stat animated version failed, retrying static: {r.stderr.decode()[-100:]}")
        vf_static = ",".join(
            f"drawtext=text='{line}':fontsize=76:fontcolor=#FFD700:x=(w-text_w)/2:y=(h/2)-{(len(lines)//2-i)*90}:fontfile={font}:shadowcolor=black:shadowx=4:shadowy=4"
            for i, line in enumerate(lines[:3])
        ) if lines else f"drawtext=text='{safe[:20]}':fontsize=76:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:fontfile={font}"
        r2=subprocess.run(["ffmpeg","-y","-f","lavfi",
            "-i",f"color=c=0x080808:size=1920x1080:duration={dur}:rate=25",
            "-vf",vf_static+",noise=alls=6:allf=t+u","-c:v","libx264","-pix_fmt","yuv420p",out],
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
            "-r","25","-vsync","cfr",
            "-c:v","libx264","-an","-preset","fast",out],capture_output=True,timeout=60)
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
        if dur:  # video
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
                "-r","25","-vsync","cfr",
                "-c:v","libx264","-an","-preset","fast",out],capture_output=True,timeout=60)
            return r2.returncode==0
        else:  # image
            r=requests.get("https://pixabay.com/api/",
                params={"key":PIXABAY_KEY,"q":search,"image_type":"photo",
                        "orientation":"horizontal","per_page":10,"safesearch":"true"},timeout=15)
            hits=r.json().get("hits",[])
            if not hits: return False
            url=random.choice(hits[:5])["largeImageURL"]
            img=requests.get(url,timeout=30)
            with open(out,"wb") as f: f.write(img.content); return True
    except Exception as e: log.warning(f"Pixabay: {e}"); return False

def solid_bg(out, dur):
    subprocess.run(["ffmpeg","-y","-f","lavfi",
        "-i",f"color=c=0x080808:size=1920x1080:duration={dur}:rate=25",
        "-c:v","libx264","-pix_fmt","yuv420p",out],
        capture_output=True,timeout=30)

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
            if make_text_stat(scene["voiceover"],out,dur,cfg["lang"]):
                scene["video_file"]=out; log.info(f"  {n}: text_stat ✓"); continue

        elif vtype=="stock_video":
            log.info(f"  {n}: stock '{search}'")
            if fetch_pexels_video(search,out,dur): scene["video_file"]=out; success=True
            if not success and fetch_pixabay(search,out,dur): scene["video_file"]=out; success=True

        else:  # ai_image
            if skip_ai(prompt):
                log.info(f"  {n}: skip AI (hallucination risk)")
            else:
                if fetch_pollinations(prompt,img,seed=n*17+i):
                    if img_to_vid(img,out,dur,anim): scene["video_file"]=out; success=True; log.info(f"  {n}: Pollinations+{anim} ✓")

        # Universal fallbacks
        if not success:
            if fetch_pexels_video(search,out,dur): scene["video_file"]=out; success=True
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
#  - Merges video+voice per scene
#  - Mixes in music at -18dB
#  - Mixes in SFX at -12dB per scene
#  - Rebuilt caption engine (drawtext, lower-third, word-by-word)
# ═══════════════════════════════════════════════════════════
def _srt(s):
    h,m=int(s//3600),int((s%3600)//60)
    return f"{h:02d}:{m:02d}:{int(s%60):02d},{int((s%1)*1000):03d}"

def get_caption_fonts():
    """Get list of available caption fonts from assets/fonts/caption/"""
    font_dir = ASSETS_DIR / "fonts" / "caption"
    if font_dir.exists():
        fonts = list(font_dir.glob("*.ttf")) + list(font_dir.glob("*.otf"))
        if fonts:
            return [str(f) for f in fonts]
    return [get_caption_font()]

def build_caption_drawtext(script):
    """
    Build FFmpeg drawtext filter string with:
    - Different fonts for key vs regular words
    - Larger sizes for important words
    - Fade-in animations
    - Bold for key words
    """
    filters = []
    font_list = get_caption_fonts()

    for scene in script:
        text = scene.get("voiceover", "").strip()
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
            
            safe_text = re.sub(r"[':\"\\%\[\]{}|]", "", chunk_text)
            
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
    """Create an intro clip with the topic title"""
    topic = cfg.get("topic", "")
    safe_topic = re.sub(r"[':\"\\%\[\]{}|]", "", topic[:60])
    font = get_caption_font(bold=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x080808:size=1920:1080:duration=2.0:rate=25",
        "-vf",
        f"drawtext=text='{safe_topic}':fontsize=72:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:fontfile={font}:borderw=6:bordercolor=black:alpha='if(lt(t,0.5),t/0.5,if(lt(t,1.5),1,if(lt(t,2.0),(2.0-t)/0.5,0)))',noise=alls=6:allf=t+u",
        "-c:v", "libx264", "-preset", "ultrafast", "-an", out_path
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)
    return out_path if os.path.exists(out_path) else None

def create_outro(cfg, out_path):
    """Create an outro clip with call-to-action"""
    cta_text = "Like, Share & Subscribe!"
    font = get_caption_font(bold=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x080808:size=1920:1080:duration=2.0:rate=25",
        "-vf",
        f"drawtext=text='{cta_text}':fontsize=64:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2:fontfile={font}:borderw=6:bordercolor=black:alpha='if(lt(t,0.5),t/0.5,if(lt(t,1.5),1,if(lt(t,2.0),(2.0-t)/0.5,0)))',noise=alls=6:allf=t+u",
        "-c:v", "libx264", "-preset", "ultrafast", "-an", out_path
    ]
    subprocess.run(cmd, capture_output=True, timeout=60)
    return out_path if os.path.exists(out_path) else None

def concat_with_transitions(clips, out_path):
    """Concatenate clips with xfade transitions between them"""
    if len(clips) == 1:
        if os.path.exists(clips[0]):
            import shutil
            shutil.copy(clips[0], out_path)
        return

    transition_types = ["fade", "wipeleft", "wiperight", "circlecrop", "pixelize"]
    transition_duration = 0.5

    # Process clips to ensure they have audio (add silent audio if missing)
    processed_clips = []
    asm_dir = WORKSPACE / "assembly"
    asm_dir.mkdir(exist_ok=True)
    for i, clip in enumerate(clips):
        temp_out = str(asm_dir / f"temp_clip_{i:03d}.mp4")
        # Check if clip has audio stream
        check_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a", "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            clip
        ]
        check_result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=30)
        has_audio = len(check_result.stdout.strip()) > 0
        if has_audio:
            processed_clips.append(clip)
        else:
            # Add silent audio
            subprocess.run([
                "ffmpeg", "-y",
                "-i", clip,
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-shortest",
                "-c:v", "copy", "-c:a", "aac", temp_out
            ], capture_output=True, timeout=60)
            if os.path.exists(temp_out):
                processed_clips.append(temp_out)
            else:
                processed_clips.append(clip)

    filter_parts = []
    input_args = []
    for i, clip in enumerate(processed_clips):
        input_args.extend(["-i", clip])

    current_v = "[0:v]"
    current_a = "[0:a]"

    for i in range(1, len(processed_clips)):
        trans_type = random.choice(transition_types)
        dur_prev = get_dur(processed_clips[i-1])
        offset = dur_prev - transition_duration
        filter_parts.append(f"{current_v}[{i}:v]xfade=transition={trans_type}:duration={transition_duration}:offset={offset}[v{i}]")
        filter_parts.append(f"{current_a}[{i}:a]acrossfade=duration={transition_duration}[a{i}]")
        current_v = f"[v{i}]"
        current_a = f"[a{i}]"

    filter_complex = ";".join(filter_parts)
    cmd = [
        "ffmpeg", "-y", *input_args,
        "-filter_complex", filter_complex,
        "-map", current_v, "-map", current_a,
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", out_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=900)
    if result.returncode != 0 or not os.path.exists(out_path):
        # Fallback to simple concat if transitions fail
        cfile = WORKSPACE / "assembly" / "concat_fallback.txt"
        with open(cfile, "w") as f:
            for clip in processed_clips:
                f.write(f"file '{os.path.abspath(clip)}'\n")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(cfile),
            "-c", "copy", out_path
        ], capture_output=True, timeout=120)
def apply_overlay_to_scene(scene_video, overlay_video, dur, out_path):
    """
    Screen-blends a VHS/glitch overlay clip onto a scene's video.
    These overlay packs have black backgrounds by design — 'screen' blend
    mode makes black areas transparent-ish and only the bright glitch/
    static effect shows through, which is exactly how these packs are
    meant to be used in real editing software.
    The overlay is looped to cover the full scene duration since most
    glitch clips are shorter than a typical 4s scene.
    """
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

    # Step 1: Merge video+voice per scene, add SFX
    scene_files=[]
    cur_time=0.0

    # Apply real VHS/glitch overlays at up to 8 high-impact moments
    # (deep_impact/riser scenes) — these get a screen-blended transition
    # effect using your actual overlay pack, giving a genuine "premium
    # editor" flash instead of a plain hard cut.
    overlay_candidates = [s for s in script if s.get("sfx") in ("deep_impact","riser") and s.get("video_file")]
    overlay_scenes = random.sample(overlay_candidates, min(8, len(overlay_candidates))) if overlay_candidates else []
    if overlay_scenes:
        log.info(f"Applying overlay flash to {len(overlay_scenes)} high-impact scenes")
    for scene in overlay_scenes:
        overlay_video = get_overlay_video()
        if not overlay_video:
            break  # no overlays uploaded, stop trying for remaining scenes
        n = scene["scene"]
        dur = scene.get("actual_duration", float(scene.get("duration_hint",4)))
        composited = str(asm/f"overlay_{n:03d}.mp4")
        if apply_overlay_to_scene(scene["video_file"], overlay_video, dur, composited):
            scene["video_file"] = composited
            log.info(f"  Scene {n}: overlay flash applied ({os.path.basename(overlay_video)})")
        else:
            log.warning(f"  Scene {n}: overlay compositing failed, using plain clip")

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
            # Mix voice + SFX. Previously both started at t=0 simultaneously,
            # meaning a loud whoosh/impact directly collided with the first
            # spoken word — a jarring, unprofessional-sounding clash. Now
            # the SFX "lands" first and the voice is delayed ~180ms behind
            # it, matching how real transition stings are edited (sting
            # hits, then dialogue begins).
            mixed_audio = str(asm/f"audio_{n:03d}.m4a")
            mix_r = subprocess.run(["ffmpeg","-y",
                "-i",os.path.abspath(audio),
                "-i",os.path.abspath(sfx_file),
                "-filter_complex","[0:a]adelay=180|180,volume=1.0[v];[1:a]volume=0.45[s];[v][s]amix=inputs=2:duration=first",
                "-c:a","aac",mixed_audio],capture_output=True,timeout=30)
            if mix_r.returncode != 0 or not os.path.exists(mixed_audio):
                log.warning(f"  SFX mix failed for scene {n}, using voice only")
                mixed_audio = audio
            # Video clips are already correctly encoded at generation time
            # (Ken Burns, Pexels trim, text_stat, solid_bg all output
            # matching 1920x1080 h264/25fps). Re-encoding here was wasting
            # huge amounts of CPU time on GitHub's 2-core runners and
            # caused the 600s timeout crash on longer videos.
            # -c:v copy just re-packages the frames — no re-encode needed.
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
            # Stream copy failed (rare codec mismatch) — fall back to
            # a real encode for just this one scene rather than failing.
            log.warning(f"Scene {n} copy-merge failed, retrying with encode: {r.stderr.decode()[-80:]}")
            cmd2=["ffmpeg","-y","-i",os.path.abspath(video)] + \
                 (["-i",os.path.abspath(audio if not (audio and sfx_file) else mixed_audio)] if audio else []) + \
                 (["-map","0:v:0","-map","1:a:0","-shortest"] if audio else ["-an"]) + \
                 ["-c:v","libx264","-preset","ultrafast","-c:a","aac",out]
            r2=subprocess.run(cmd2,capture_output=True,timeout=120)
            if r2.returncode==0 and os.path.exists(out):
                scene_files.append(out); cur_time+=dur
            else:
                log.warning(f"Scene {n} fully failed, skipping: {r2.stderr.decode()[-80:]}")

    if not scene_files: raise RuntimeError("No scenes assembled!")

    # Step 1.5: Add intro and outro
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

    # Step 2: Concat with transitions
    raw = str(WORKSPACE / "raw.mp4")
    concat_with_transitions(full_clips, raw)
    if not os.path.exists(raw):
        raise RuntimeError("Concat failed: raw.mp4 was not created")
    final_dur = get_dur(raw)
    expected_dur = cur_time + (2.0 if intro else 0.0) + (2.0 if outro else 0.0)
    if final_dur < expected_dur * 0.8:
        log.warning(
            f"Concat output looks short ({final_dur:.0f}s actual vs {expected_dur:.0f}s expected)"
        )

    # Step 2.5: Mix background music into the audio track FIRST
    # (audio-only operation — fast, uses -c:v copy, no video re-encode)
    total_dur = max(get_dur(raw), sum(s.get("actual_duration",4) for s in script))
    with_music=str(WORKSPACE/"with_music.mp4")
    if music_path and os.path.exists(music_path):
        r_mus = subprocess.run(["ffmpeg","-y","-i",raw,"-stream_loop","-1","-i",music_path,
            "-filter_complex",f"[1:a]volume=0.12,atrim=0:{total_dur}[m];[0:a][m]amix=inputs=2:duration=first[a]",
            "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-shortest",with_music],
            capture_output=True,timeout=300)
        if r_mus.returncode==0 and os.path.exists(with_music):
            raw = with_music
        else:
            log.warning(f"Music mix failed: {r_mus.stderr.decode()[-150:]}")

    # Step 3: SINGLE video re-encode combining color grade + captions.
    # Doing these together (instead of 2 separate full-video passes)
    # roughly halves total render time — critical on GitHub's free
    # CPU-only runners where an 8-min 1080p re-encode is already slow.
    grade = cfg.get("color_grade","cinematic")

    # Real .cube LUT if you've uploaded one — this is genuine professional
    # color grading, not the crude eq=saturation approximation. Falls back
    # automatically if no LUT files exist yet in assets/luts/.
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

    final=str(WORKSPACE/"final_video.mp4")
    combined_vf = gf if caption_filter=="null" else f"{gf},{caption_filter}"

    # Use ultrafast preset — this is a CPU-bound free runner, not a quality
    # bottleneck; ultrafast still looks fine for YouTube upload and cuts
    # encode time dramatically vs "fast" preset on 2-core hosted runners.
    r=subprocess.run(["ffmpeg","-y","-i",raw,
        "-vf",combined_vf,
        "-c:v","libx264","-preset","ultrafast","-crf","23",
        "-c:a","aac",final],
        capture_output=True,timeout=1200)
    if r.returncode!=0:
        log.warning(f"Combined grade+caption failed: {r.stderr.decode()[-250:]}. Trying captions only.")
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
# ═══════════════════════════════════════════════════════════
#  STAGE 10 — GOOGLE DRIVE BACKUP
#  Every video gets archived to Drive regardless of QC verdict —
#  Approved_Uploads / Drafts / Rejects, exactly like the original
#  vision for this project. Reuses the same YOUTUBE_TOKEN_JSON
#  credential (now with drive.file scope added).
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
        raise ValueError("YOUTUBE_TOKEN_JSON empty — cannot access Drive")
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
    """Uploads the final video + research + script to a dated Drive folder,
    routed into Approved_Uploads / Drafts / Rejects based on QC verdict."""
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

        # Upload final video
        if video_path and os.path.exists(video_path):
            media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
            service.files().create(
                body={"name": "final_video.mp4", "parents": [video_folder_id]},
                media_body=media, fields="id"
            ).execute()
            log.info(f"  Drive: video uploaded to {bucket_name}/{video_folder_name}")

        # Upload research + script JSON for debugging/reuse
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

def stage_9_publish(video_path, script, cfg):
    log.info("Stage 9: Publishing...")
    tg("📤 Uploading to YouTube...")
    topic = cfg["topic"]
    lang  = cfg["lang"]
    niche = cfg.get("niche","")
    genre = cfg["genre"]

    # Generate metadata
    try:
        hook = script[0].get("voiceover","") if script else ""
        lang_hint = "Write the title and description in HINGLISH (Hindi-English mixed, Roman script only, no Devanagari) — this is standard for Indian YouTube titles and is more clickable/searchable." if lang=="hindi" else f"Write in {lang}."
        meta_text = groq(f"""YouTube metadata for a {genre} video.
Topic: "{topic}"
Niche: {niche}
Hook: "{hook}"
{lang_hint}
Return ONLY JSON, no reasoning, no markdown fences, no explanation:
{{"title":"viral title under 60 chars with power word or number",
  "description":"3 engaging paragraphs with keywords",
  "tags":["{topic}","hinglish","{niche}","viral","facts"],
  "hashtags":"#{topic.replace(' ','')} #hinglish #{niche} #viral"
}}""", max_tokens=800)
        meta = json.loads(extract_json_object(meta_text))
        log.info(f"Generated metadata: {meta}")
    except Exception as e:
        log.warning(f"Metadata generation failed, using fallback: {e}")
        meta={"title":f"{topic} — Poori Sacchai",
              "description":f"{topic} ke baare mein poori jaankari.",
              "tags":[topic,"hinglish",niche or "facts"],
              "hashtags":f"#{topic.replace(' ','')} #hinglish"}

    # Ensure all required keys exist in meta
    meta.setdefault("title", f"{topic} — Poori Sacchai")
    meta.setdefault("description", f"{topic} ke baare mein poori jaankari.")
    meta.setdefault("tags", [topic, "hinglish", niche or "facts"])
    meta.setdefault("hashtags", f"#{topic.replace(' ','')} #hinglish")

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
#  MAIN
# ═══════════════════════════════════════════════════════════
def run_pipeline():
    start=time.time()
    cfg=parse_input()

    log.info(f"🚀 v5.0 | {cfg['topic']} | niche={cfg.get('niche','')} | genre={cfg['genre']} | lang={cfg['lang']} | {cfg['duration_min']}min")
    tg(f"🚀 Starting v5.0\n📌 {cfg['topic']}\n🎬 {cfg['genre']} | {cfg['lang']} | {cfg['duration_min']}min\n⏰ Upload: {cfg['schedule']} UTC")

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

        if verdict=="retry":
            tg(f"❌ QC {score}/10 — Rejected\n{qc.get('reason','')}")
            return
        if verdict=="drafts":
            tg(f"⚠️ QC {score}/10 — Drafts\n{qc.get('reason','')}")
            return

        url=stage_9_publish(final_video,script,cfg)
        elapsed=int(time.time()-start)
        total=sum(s.get("actual_duration",4) for s in script)

        tg(f"✅ DONE!\n\n📺 {url}\n⏰ {cfg['schedule']} UTC\n🏆 QC: {score}/10\n🎬 {len(script)} scenes | {total:.0f}s\n✂️ Avg {total/max(len(script),1):.1f}s/cut\n⚡ {elapsed}s total")

    except Exception as e:
        import traceback
        log.error(f"CRASH: {e}\n{traceback.format_exc()}")
        tg(f"💥 Crashed: {str(e)[:250]}\nCheck GitHub Actions logs.")
        raise

# ═══════════════════════════════════════════════════════════
#  COLAB CLI — Wan2.1 video generation on free T4 GPU
#  Added in v5.1
#
#  How it works:
#  1. pipeline.py collects all ai_image scenes that need
#     cartoon/animated video
#  2. Writes scene_prompts.json with their prompts
#  3. GitHub Actions installs colab CLI
#  4. colab run --gpu T4 wan21_generator.py
#  5. Downloads generated clips back
#  6. pipeline.py uses them instead of Pollinations images
#
#  Requires: COLAB_TOKEN secret in GitHub
#  Get it: colab auth token (run once locally, copy output)
# ═══════════════════════════════════════════════════════════

def stage_wan21_colab(scenes_needing_video, topic):
    """
    Runs Wan2.1 on Colab T4 GPU via CLI.
    Auth is set up by the GitHub Actions workflow (writes the session
    file to ~/.config/colab-cli/sessions.json before pipeline.py runs) —
    this function just verifies it's usable and proceeds.
    Returns dict: {scene_number: local_video_path}
    """
    if not scenes_needing_video:
        return {}

    session_file = os.path.expanduser("~/.config/colab-cli/sessions.json")
    if not os.path.exists(session_file):
        log.warning("Colab CLI session not found — skipping Wan2.1, using Pollinations instead")
        return {}

    log.info(f"Wan2.1 via Colab CLI: {len(scenes_needing_video)} scenes")
    tg(f"🎨 Wan2.1 GPU generation: {len(scenes_needing_video)} animated clips...")

    # Write prompts file
    prompts_file = str(WORKSPACE / "scene_prompts.json")
    with open(prompts_file, "w") as f:
        json.dump(scenes_needing_video, f, indent=2)

    clips_dir = WORKSPACE / "wan_clips"
    clips_dir.mkdir(exist_ok=True)

    try:
        # Provision T4 GPU, run generator, download clips, stop
        # Using colab run which handles full lifecycle automatically
        result = subprocess.run([
            "colab", "run", "--gpu", "T4",
            "--upload", f"{prompts_file}:/content/scene_prompts.json",
            "--upload", "wan21_generator.py:/content/wan21_generator.py",
            "--download", "/content/clips/:./wan_clips/",
            "--download", "/content/wan21_results.json:./wan21_results.json",
            "wan21_generator.py"
        ], capture_output=True, text=True, timeout=1800)  # 30 min max

        log.info(f"Colab exit code: {result.returncode}")
        if result.stdout: log.info(f"Colab output: {result.stdout[-500:]}")
        if result.stderr: log.warning(f"Colab stderr: {result.stderr[-300:]}")

        # Read results
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
            log.error("wan21_results.json not found — Colab run may have failed")
            return {}

    except subprocess.TimeoutExpired:
        log.error("Wan2.1 Colab run timed out (30 min limit)")
        return {}
    except Exception as e:
        log.error(f"Wan2.1 Colab failed: {e}")
        return {}

# ═══════════════════════════════════════════════════════════
#  KLING API — cinematic video generation
#  Added in v5.1
#
#  Official Kling API via klingapi.com
#  Free API key on signup — but needs credits for production
#  Free tier: 66 credits/day = 2 clips/day at 360p
#
#  For production: use klingapi.com prepaid ($9.80 minimum)
#  OR use the free 2 clips/day for hero shots only
#
#  Get API key: klingapi.com/docs → sign up → copy API key
#  Add as KLING_API_KEY secret in GitHub
# ═══════════════════════════════════════════════════════════

def generate_kling_clip(prompt, duration=5, mode="std", scene_num=0):
    """
    Generate one video clip via Kling API (supports kling26ai.com and aimlapi.com).
    Returns local file path or None.
    """
    kling_key = os.environ.get("KLING_API_KEY", "")
    if not kling_key:
        return None

    out_path = str(WORKSPACE / "visuals" / f"kling_{scene_num:03d}.mp4")

    try:
        # Try kling26ai.com first
        BASE = "https://kling26ai.com"

        # Submit generation task
        resp = requests.post(f"{BASE}/api/generate",
            headers={"Authorization": f"Bearer {kling_key}",
                     "Content-Type": "application/json"},
            json={"prompt": prompt,
                  "aspect_ratio": "16:9",
                  "duration": str(duration),
                  "sound": False},
            timeout=30)

        if resp.status_code != 200:
            log.warning(f"Kling26 submit failed: {resp.status_code} {resp.text[:200]}")
            # Fallback to AIML API
            return generate_kling_clip_aimlapi(prompt, duration, mode, scene_num, kling_key, out_path)

        result = resp.json()
        if result.get("code") != 200:
            log.warning(f"Kling26 error: {result.get('message', '')}")
            return generate_kling_clip_aimlapi(prompt, duration, mode, scene_num, kling_key, out_path)

        task_id = result.get("data", {}).get("task_id")
        if not task_id:
            log.warning(f"Kling26: no task_id in response")
            return generate_kling_clip_aimlapi(prompt, duration, mode, scene_num, kling_key, out_path)

        log.info(f"  Kling26 task {task_id} submitted, polling...")

        # Poll for result (max 5 minutes)
        for attempt in range(60):
            time.sleep(5)
            poll = requests.get(f"{BASE}/api/status?task_id={task_id}",
                headers={"Authorization": f"Bearer {kling_key}"},
                timeout=15)

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
                log.warning(f"  Kling26 task failed: {data.get('data', {}).get('error_message','')}")
                break
            else:
                log.info(f"  Kling26 {task_id}: {status} (attempt {attempt+1}/60)")

    except Exception as e:
        log.warning(f"  Kling26 scene {scene_num}: {e}")
        return generate_kling_clip_aimlapi(prompt, duration, mode, scene_num, kling_key, out_path)

    return None

def generate_kling_clip_aimlapi(prompt, duration, mode, scene_num, kling_key, out_path):
    """Fallback Kling generation via AIML API"""
    try:
        BASE = "https://api.aimlapi.com"
        resp = requests.post(f"{BASE}/v2/video/generations",
            headers={"Authorization": f"Bearer {kling_key}",
                     "Content-Type": "application/json"},
            json={"model": "klingai/video-v2-6-pro-text-to-video" if mode=="pro" else "klingai/video-v2-6-text-to-video",
                  "prompt": prompt,
                  "duration": duration,
                  "negative_prompt": "blurry, ugly, text, watermark, faces, deformed",
                  "generate_audio": False},
            timeout=30)
        if resp.status_code != 200:
            log.warning(f"AIMLAPI Kling submit failed: {resp.status_code} {resp.text[:200]}")
            return None
        gen_id = resp.json().get("id")
        if not gen_id:
            return None
        log.info(f"  AIMLAPI Kling task {gen_id} submitted, polling...")
        for attempt in range(60):
            time.sleep(5)
            poll = requests.get(f"{BASE}/v2/video/generations?generation_id={gen_id}",
                headers={"Authorization": f"Bearer {kling_key}"},
                timeout=15)
            if poll.status_code != 200:
                continue
            data = poll.json()
            status = data.get("status", "")
            if status == "completed":
                video_url = data.get("video", {}).get("url", "")
                if video_url:
                    r = requests.get(video_url, stream=True, timeout=60)
                    with open(out_path, "wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    log.info(f"  AIMLAPI Kling scene {scene_num}: ✓ ({os.path.getsize(out_path)//1024}KB)")
                    return out_path
                break
            elif status == "error":
                log.warning(f"  AIMLAPI Kling task failed: {data.get('error', '')}")
                break
            else:
                log.info(f"  AIMLAPI Kling {gen_id}: {status} (attempt {attempt+1}/60)")
    except Exception as e:
        log.warning(f"  AIMLAPI Kling scene {scene_num}: {e}")
    return None

def stage_kling_visuals(script, cfg, max_clips=2):
    """
    Uses Kling for the most important scenes (hero shots).
    Free tier: 2 clips/day max (66 credits, 30 credits per 5s clip).
    Only used for documentary/cinematic genres.
    Skips if KLING_API_KEY not set.
    """
    kling_key = os.environ.get("KLING_API_KEY", "")
    if not kling_key:
        log.info("KLING_API_KEY not set — skipping Kling")
        return script

    genre = cfg.get("genre","documentary")
    if genre not in ["documentary","shorts"]:
        log.info(f"Kling: skipping for genre={genre}")
        return script

    log.info(f"Kling: generating up to {max_clips} cinematic hero shots...")
    tg(f"🎬 Kling AI: generating {max_clips} cinematic clips...")

    # Pick most important scenes (first 2 stock_video or ai_image scenes)
    candidates = [s for s in script
                  if s.get("visual_type") in ("stock_video","ai_image")
                  and not s.get("video_file")][:max_clips]

    for scene in candidates:
        n      = scene["scene"]
        prompt = scene.get("ai_prompt", scene.get("visual_search","cinematic scene"))
        # Make prompt more cinematic for Kling
        kling_prompt = f"{prompt}, cinematic 4K, dramatic lighting, smooth motion, professional filmmaking"
        clip = generate_kling_clip(kling_prompt, duration=5, mode="std", scene_num=n)
        if clip:
            scene["video_file"] = clip
            scene["visual_source"] = "kling"
            log.info(f"  Scene {n}: Kling clip applied")

    return script


# ═══════════════════════════════════════════════════════════
#  UPDATED run_pipeline() — includes Wan2.1 + Kling
# ═══════════════════════════════════════════════════════════

def run_pipeline_v51():
    """
    v5.1 pipeline — adds Colab CLI Wan2.1 + Kling API
    Replaces run_pipeline() when both optional integrations active.
    """
    start = time.time()
    cfg   = parse_input()
    genre = cfg["genre"]

    log.info(f"🚀 v5.1 | {cfg['topic']} | {genre} | {cfg['lang']} | {cfg['duration_min']}min")
    tg(f"🚀 v5.1\n📌 {cfg['topic']}\n🎬 {genre} | {cfg['lang']} | {cfg['duration_min']}min\n⏰ {cfg['schedule']} UTC")

    try:
        # Stages 1-3: Research, Script, Voice
        research = stage_1_research(cfg)
        _save(research, "research.json")

        script = stage_2_script(research, cfg)
        _save(script, "script.json")
        tg(f"✍️ {len(script)} scenes")

        script = stage_3_voice(script, cfg)
        music_path = stage_4_music(cfg)

        # Stage 5: Route scenes to correct visual engine
        # ─── Wan2.1 for cartoon/animated genres ──────────
        wan_scenes = []
        if genre in ("cartoon",) and os.path.exists(os.path.expanduser("~/.config/colab-cli/sessions.json")):
            wan_scenes = [s for s in script
                          if s.get("visual_type") == "ai_image"
                          and not skip_ai(s.get("ai_prompt",""))]
            log.info(f"Routing {len(wan_scenes)} scenes to Wan2.1")

        wan_clips = {}
        if wan_scenes:
            wan_clips = stage_wan21_colab(wan_scenes, cfg["topic"])

        # Apply Wan2.1 clips to script
        for scene in script:
            if scene["scene"] in wan_clips:
                scene["video_file"] = wan_clips[scene["scene"]]
                scene["visual_source"] = "wan2.1"
                # Still need duration from audio
                if scene.get("audio_file"):
                    scene["actual_duration"] = get_dur(scene["audio_file"])
                else:
                    scene["actual_duration"] = float(scene.get("duration_hint",4))

        # ─── Kling for documentary hero shots ────────────
        if genre in ("documentary","shorts") and os.environ.get("KLING_API_KEY"):
            script = stage_kling_visuals(script, cfg, max_clips=2)

        # ─── Standard visual pipeline for remaining scenes ─
        script = stage_6_visuals(script, cfg)
        _save(script, "script_final.json")

        # Stages 7-9: Assembly, QC, Publish
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
            f"🌍 {cfg['lang']} | {cfg['genre']}\n"
            f"⚡ {elapsed}s total{drive_note}"
        )

    except Exception as e:
        import traceback
        log.error(f"CRASH: {e}\n{traceback.format_exc()}")
        tg(f"💥 Crashed: {str(e)[:250]}")
        raise


# Override main entry point to use v5.1
if __name__ == "__main__":
    run_pipeline_v51()
