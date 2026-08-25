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

if not shutil.which("ffmpeg"):
    import glob
    winget_paths = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg*\bin"))
    for wp in winget_paths:
        if os.path.exists(os.path.join(wp, "ffmpeg.exe")):
            os.environ["PATH"] = wp + os.pathsep + os.environ.get("PATH", "")
            break
    if not shutil.which("ffmpeg"):
        try:
            import imageio_ffmpeg
            ff_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if ff_exe and os.path.exists(ff_exe):
                ff_dir = os.path.dirname(ff_exe)
                os.environ["PATH"] = ff_dir + os.pathsep + os.environ.get("PATH", "")
                alias = os.path.join(ff_dir, "ffmpeg.exe")
                if not os.path.exists(alias):
                    try:
                        shutil.copy2(ff_exe, alias)
                    except Exception:
                        pass
        except Exception:
            pass

if not shutil.which("npx"):
    node_dirs = [
        r"C:\Users\Asus\node-v20.18.0-win-x64",
        r"C:\Program Files\nodejs",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\node"),
    ]
    for nd in node_dirs:
        if os.path.exists(os.path.join(nd, "npx.cmd")) or os.path.exists(os.path.join(nd, "npx")):
            os.environ["PATH"] = nd + os.pathsep + os.environ.get("PATH", "")
            break

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
PEXELS_KEY      = os.environ.get("PEXELS_KEY", "3QjOv4tHN73fLie2daMFqgZDv9w2GRuBoTv5UBhyHYD5da26gVw8kqS4")
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
    "hindi":   ["hi-IN-SwaraNeural",        "hi-IN-MadhurNeural"],
    "english": ["en-GB-RyanNeural",         "en-US-ChristopherNeural"],
    "spanish": ["es-ES-ElviraNeural",       "es-MX-DaliaNeural"],
    "french":  ["fr-FR-DeniseNeural",       "fr-FR-HenriNeural"],
    "german":  ["de-DE-KatjaNeural",        "de-DE-ConradNeural"],
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
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}],
            temperature=0.8, max_tokens=max_tokens)
        return r.choices[0].message.content.strip()
    except Exception as e:
        log.warning(f"Groq llama-3.3-70b failed: {e}")
        raise RuntimeError("Groq failed")


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

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LUTS_DIR = ASSETS_DIR / "luts"
SFX_DIR = ASSETS_DIR / "sfx"
OVERLAYS_DIR = ASSETS_DIR / "overlays"
FONTS_DIR = ASSETS_DIR / "fonts" / "caption"

def pick_asset(subfolder, extension=None):
    """Returns a random file path from assets/<subfolder>/, or None if empty/missing."""
    folder = ASSETS_DIR / subfolder
    if not folder.exists():
        return None
    if extension:
        files = list(folder.glob(f"*.{extension}"))
    else:
        files = [f for f in folder.rglob("*") if f.is_file()]
    return str(random.choice(files)) if files else None

def get_caption_font(bold=False):
    """Real premium font if uploaded from assets/fonts/caption, otherwise safe system fallback."""
    folder = FONTS_DIR
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
    "teal_orange": ["teal and orange", "warm cinema", "kodak", "gold rush"],
    "cool_blue":   ["blue cold", "blue moon", "blue ice", "blue steel", "matrix green"],
    "dark_noir":   ["noir", "iron", "bleach"],
    "cinematic":   ["warm cinema", "teal and orange", "clean straight"],
    "cartoon":     ["vm thermal royalty", "vm thermal picasso", "vm thermal plastic", "gold rush"],
    "energetic":   ["vm thermal vice", "vm thermal crush", "vm thermal fahrenheit"],
}

def get_lut_file(color_grade):
    """Finds a real .cube LUT matching the genre mood from assets/luts."""
    folder = LUTS_DIR
    if not folder.exists():
        return None
    all_luts = list(folder.glob("*.cube"))
    if not all_luts:
        return None
    keywords = LUT_KEYWORD_MAP.get(color_grade, [])
    matches = [f for f in all_luts if any(kw in f.stem.lower() for kw in keywords)]
    if not matches:
        return str(random.choice(all_luts))
    return str(random.choice(matches))

def get_overlay_video():
    """Random VHS/glitch video overlay (.mp4) from assets/overlays."""
    if not OVERLAYS_DIR.exists():
        return None
    overlays = list(OVERLAYS_DIR.glob("*.mp4"))
    return str(random.choice(overlays)) if overlays else None

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
        wiki_headers = {"User-Agent": "MediaAgencyDocBot/1.0 (https://github.com/thenewbie343/media-agency; contact@mediaagency.ai)"}
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={quote(topic)}&utf8=&format=json"
        resp = requests.get(url, headers=wiki_headers, timeout=15)
        if resp.status_code == 200:
            import re
            snips = [re.sub(r'<[^>]+>', '', s["snippet"]) for s in resp.json().get("query", {}).get("search", [])][:8]
            if snips:
                return {"hook":snips[0],
                        "hook_question":f"What really happened with {topic}?",
                        "key_facts":snips,"statistics":[],"timeline":[],"visual_themes":[topic]}
    except:
        pass
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
    target = max(20, int(dur * 12))
    log.info(f"Stage 2: Duration {dur}m → {target} scenes target")

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
    max_stalled = 10

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
            f"NEVER repeat information already stated. If facts run out, explore the emotional impact, historical context, or broader consequences of the event."
        )

        vt_rule = "Use 'stock_video' or 'broll_video' mostly."
        if cfg.get("genre") == "documentary":
            vt_rule = (
                "PROGRESSIVE RHYTHM ARCHITECTURE (CRITICAL):\n"
                "1. 0-30s HOOK: Use fast visual changes every 2-3s (Scenes 1-5). Use 'text_stat', 'motion_graphics', and high-impact 'stock_video' ONLY. NO slow static images!\n"
                "2. NARRATIVE BUILD (Min 1-5): Widen spacing to 4-6s. Alternate 'ai_video' (AnimateDiff B-roll), 'stock_video' (real evidence), and 'ai_image' (Pollinations + Ken Burns).\n"
                "3. BURST SEQUENCES (Pattern Interrupt): Every 15-20 scenes (~2 mins), inject a 3-scene burst sequence with 1.5s rapid cuts (data popups, zooms, flash cuts).\n"
                "Ratios: 30% 'text_stat'/'motion_graphics', 25% 'ai_video', 20% 'stock_video', 15% 'ai_image', 10% 'broll_video'."
            )
        elif cfg.get("genre") in ("cartoon", "surreal", "anime"):
            vt_rule = "MUST use 'ai_video' or 'ai_image' for EVERY scene to generate visuals."

        prompt = f"""You are a world-class viral Hindi YouTube scriptwriter and documentary editor.
Style: {style}
{voice_note}
{caption_note}
{niche_note}

Topic: "{topic}"

{continuity}

STRICT RULES:
- voiceover: HINGLISH vocabulary in Devanagari — "स्टॉक" not "शेयर", "क्रैश" not "दुर्घटना"
- caption: Hinglish in Roman. MUST be actual dialogue/subtitles. NEVER write structural headers, tags, or metadata like "COLD WAR PEAK" in the caption. It is printed directly on screen for the viewer.
- ai_prompt: ENGLISH ONLY. MUST follow this 4-part structure: [Simple Subject] + [Environment] + [Camera Movement] + [Art Style]. Example: "a lone officer sitting at a radar desk, dimly lit bunker, slow camera zoom in, retro 80s aesthetic". GOLDEN RULE: MOVE THE CAMERA, NOT THE SUBJECT (e.g. slow pan left, dolly zoom, static shot). Max 1 action verb per prompt to prevent AI morphing.
- visual_search: ENGLISH ONLY. Keep it simple for stock footage searches (e.g. "military bunker").
- visual_type: {vt_rule}
- Each scene = ONE new fact or angle. NO repetition.
- Max 12 words voiceover, max 10 words caption.
- sfx: deep_impact|whoosh|click|riser|none

Return ONLY JSON array. No markdown.
[{{"scene":{start_num},"voiceover":"...","caption":"...","visual_type":"ai_video","visual_search":"...","ai_prompt":"...","emotion":"dramatic","sfx":"{sfx_def}","duration_hint":5}}]"""

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
                    if sim > 0.75:
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
#  STAGE 3 — VOICE (LOCKED AT DOCUMENTARY LEVEL)
# ═══════════════════════════════════════════════════════════

async def _edge_tts(text, path, voice, rate="+4%", pitch="+0Hz"):
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

def stage_3_voice(manifest, cfg):
    lang = cfg["lang"]
    use_kokoro = os.environ.get("USE_KOKORO", "true").lower() in ("true", "1", "yes")
    log.info(f"Stage 3: Voice (Kokoro: {use_kokoro}, locked voice profile)...")
    tg(f"🎙️ Generating voice...")
    audio_dir = WORKSPACE / "audio"
    audio_dir.mkdir(exist_ok=True)
    failed_blocks = 0
    total_blocks = 0

    doc_fallback_voice = cfg.get("voice", VOICE_MAP.get(lang, VOICE_MAP["hindi"])[0])

    def _apply_studio_mastering(raw_path, target_path):
        """Applies highpass, vocal warmth, presence boost, and dynamic compression."""
        vocal_filter = (
            "highpass=f=80,"
            "equalizer=f=220:width_type=o:width=1.0:g=2.0,"
            "equalizer=f=3500:width_type=o:width=1.2:g=2.2,"
            "acompressor=threshold=0.12:ratio=3:attack=15:release=200,"
            "volume=1.50"
        )
        tmp_master = target_path + ".tmp.mp3"
        cmd = [
            "ffmpeg", "-y", "-i", raw_path,
            "-filter:a", vocal_filter,
            "-codec:a", "libmp3lame", "-qscale:a", "2",
            tmp_master
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        if r.returncode == 0 and os.path.exists(tmp_master) and os.path.getsize(tmp_master) > 500:
            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(tmp_master, target_path)
            if raw_path != target_path and os.path.exists(raw_path):
                try: os.remove(raw_path)
                except: pass
            return True
        if os.path.exists(tmp_master):
            try: os.remove(tmp_master)
            except: pass
        return False

    def _generate_voice(text, b_id, intent="EXPLANATION", attention=0.5):
        if not text:
            return None, 0.0
            
        out = str(audio_dir / f"block_{b_id}.mp3")
        done = False
        
        # Adaptive Pacing Calculation (Subtle & Cinematic: 0.92x to 1.08x)
        intent_upper = str(intent).upper()
        if intent_upper in ["HOOK", "MYSTERY"]:
            kokoro_speed = 0.95
            edge_rate = "-3%"
            edge_pitch = "-1Hz"
        elif intent_upper in ["CONFLICT", "CRISIS"]:
            kokoro_speed = 1.08
            edge_rate = "+8%"
            edge_pitch = "+1Hz"
        elif intent_upper in ["EVIDENCE", "ANOMALY", "REVEAL"]:
            kokoro_speed = 0.92
            edge_rate = "-5%"
            edge_pitch = "-2Hz"
        elif intent_upper in ["RESOLUTION", "AFTERMATH"]:
            kokoro_speed = 0.96
            edge_rate = "-2%"
            edge_pitch = "-1Hz"
        else: # EXPLANATION / DEFAULT
            kokoro_speed = 1.00
            edge_rate = "+2%"
            edge_pitch = "+0Hz"

        # 1. Try Kokoro first if enabled with adaptive pacing
        if use_kokoro:
            try:
                done = generate_kokoro_voice(text, out, lang, speed_override=kokoro_speed)
                if done:
                    log.info(f"  Block {b_id}: Kokoro TTS ✓ ({kokoro_speed}x, intent={intent_upper})")
            except Exception as e:
                log.warning(f"  Block {b_id}: Kokoro failed: {e}")

        # 2. Consistent Fallback to Edge-TTS with adaptive rate/pitch + studio mastering
        if not done:
            raw_edge = str(audio_dir / f"raw_{b_id}.mp3")
            for attempt in range(2):
                try:
                    asyncio.run(_edge_tts(text, raw_edge, doc_fallback_voice, rate=edge_rate, pitch=edge_pitch))
                    if os.path.exists(raw_edge) and os.path.getsize(raw_edge) > 500:
                        _apply_studio_mastering(raw_edge, out)
                        done = True
                        log.info(f"  Block {b_id}: Edge-TTS ({doc_fallback_voice}, rate={edge_rate}) + Studio Master ✓")
                    break
                except Exception as e:
                    log.warning(f"  Block {b_id} {doc_fallback_voice} attempt {attempt+1}: {e}")
                    time.sleep(1.5)

        # 3. Fallback to gTTS if Edge-TTS fails
        if not done:
            raw_gtts = str(audio_dir / f"raw_gtts_{b_id}.mp3")
            try:
                from gtts import gTTS
                lc = {"hindi":"hi","english":"en","spanish":"es","french":"fr","german":"de"}.get(lang,"hi")
                gTTS(text=text, lang=lc).save(raw_gtts)
                if os.path.exists(raw_gtts) and os.path.getsize(raw_gtts) > 500:
                    _apply_studio_mastering(raw_gtts, out)
                    done = True
                    log.info(f"  Block {b_id}: gTTS + Studio Master ✓")
            except Exception as e:
                log.error(f"  Block {b_id}: gTTS also failed: {e}")

        if not done:
            return None, 0.0
            
        # MEASURE ACTUAL DURATION AS SOURCE OF TRUTH
        try:
            r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                "-of","default=noprint_wrappers=1:nokey=1", out], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
            dur = float(r.stdout.strip())
            return out, dur
        except:
            return out, 4.0

    if isinstance(manifest, dict) and "story_beats" in manifest:
        from agents.visual_story_planner import VisualStoryPlanner
        planner = VisualStoryPlanner()
        planner.reset_timeline()
        
        for beat in manifest.get("story_beats", []):
            intent = beat.get("narrative_intent", "EXPLANATION")
            attention = float(beat.get("attention_intensity", 0.5))
            time_mode = beat.get("time_context", {}).get("mode", "modern")
            chapter_lut = planner.determine_chapter_color(intent, time_mode)
            beat["chapter_color_language"] = chapter_lut
            
            for block in beat.get("narration_blocks", []):
                total_blocks += 1
                b_id = block.get("block_id", f"b{total_blocks}")
                text = block.get("voiceover", "").strip()
                
                out_file, dur = _generate_voice(text, b_id, intent=intent, attention=attention)
                
                if not out_file:
                    failed_blocks += 1
                    block["audio_file"] = None
                    block["actual_voice_duration"] = float(block.get("duration_hint", 4.0))
                else:
                    block["audio_file"] = out_file
                    block["actual_voice_duration"] = dur
                    
                # Calculate authoritative total duration
                silence_dur = block.get("strategic_silence", {}).get("duration_seconds", 0.0)
                block["total_block_duration"] = block["actual_voice_duration"] + silence_dur

                # SEMANTIC VISUAL DECOMPOSITION UNDER CONTINUOUS NARRATION
                # Decomposes narration into purposeful visual units summing exactly to block duration
                block["shots"] = planner.decompose_narration_block(
                    block, 
                    block["total_block_duration"], 
                    beat_intent=intent, 
                    attention_intensity=attention,
                    time_mode=time_mode,
                    chapter_lut=chapter_lut
                )

                if total_blocks % 5 == 4:
                    time.sleep(1)
    else:
        # Legacy flat list support
        scenes = extract_scenes_list(manifest)
        for i, scene in enumerate(scenes):
            total_blocks += 1
            b_id = f"scene_{i}"
            text = scene.get("voiceover", "").strip()
            emotion = scene.get("emotion", "dramatic")
            
            out_file, dur = _generate_voice(text, b_id, emotion)
            
            if not out_file:
                failed_blocks += 1
                scene["audio_file"] = None
                scene["actual_duration"] = float(scene.get("duration_hint", 4.0))
            else:
                scene["audio_file"] = out_file
                scene["actual_duration"] = dur

            if total_blocks % 5 == 4:
                time.sleep(1)

    if failed_blocks:
        log.warning(f"Stage 3: {failed_blocks}/{total_blocks} blocks have NO audio")
    return manifest


def generate_kokoro_voice(text, out_path, lang="hindi", emotion="dramatic", speed_override=None):
    """Generate voice using Kokoro TTS with adaptive pacing and studio vocal mastering."""
    voice_map = {
        "hindi": "hf_alpha",     # Hindi Female — natural, clear
        "english": "af_heart",    # American Female
        "spanish": "af_heart",    # Fallback
        "french": "af_heart",     # Fallback
        "german": "af_heart"      # Fallback
    }

    lang_code_map = {
        "hindi": "h",      # 'h' triggers espeak-ng hi + Hindi G2P
        "english": "a",    # 'a' = American English
        "spanish": "a",    # Fallback
        "french": "a",     # Fallback  
        "german": "a"      # Fallback
    }

    voice = voice_map.get(lang, "hf_alpha" if lang == "hindi" else "af_heart")
    lang_code = lang_code_map.get(lang, "h" if lang == "hindi" else "a")

    if speed_override is not None:
        speed = float(speed_override)
    else:
        speed_map = {
            "dramatic": 1.0,
            "shocking": 1.08,
            "mysterious": 0.95,
            "inspiring": 1.05,
            "calm": 0.92,
            "energetic": 1.08
        }
        speed = speed_map.get(emotion, 1.0)

    try:
        from kokoro import KPipeline
        import numpy as np

        import sys, os, contextlib
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                pipeline = KPipeline(lang_code=lang_code)
                generator = pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+')

                audio_segments = []
                sample_rate = 24000

                for i, (gs, ps, audio) in enumerate(generator):
                    audio_segments.append(audio)

        if not audio_segments:
            return False

        full_audio = np.concatenate(audio_segments)

        # 1. Remove NaN/Inf that corrupt output
        full_audio = np.nan_to_num(full_audio, nan=0.0, posinf=0.0, neginf=0.0)

        # 2. Peak Normalization
        max_val = np.max(np.abs(full_audio))
        if max_val > 1e-5:
            full_audio = (full_audio / max_val) * 0.96

        # 3. float32 [-1.0, 1.0] → int16 [-32768, 32767]
        audio_int16 = np.clip(full_audio * 32767, -32768, 32767).astype(np.int16)

        # 4. Write as proper 16-bit PCM WAV
        import soundfile as sf
        wav_path = out_path.replace('.mp3', '.wav')
        sf.write(wav_path, audio_int16, sample_rate, subtype='PCM_16')

        # 5. Convert to MP3 with studio broadcast mastering filter
        vocal_filter = (
            "highpass=f=80,"
            "equalizer=f=220:width_type=o:width=1.0:g=2.0,"
            "equalizer=f=3500:width_type=o:width=1.2:g=2.2,"
            "acompressor=threshold=0.12:ratio=3:attack=15:release=200,"
            "volume=1.50"
        )
        result = subprocess.run([
            "ffmpeg", "-y", "-i", wav_path,
            "-filter:a", vocal_filter,
            "-codec:a", "libmp3lame", "-qscale:a", "2",
            "-ar", str(sample_rate),
            out_path
        ], capture_output=True, timeout=30)

        if os.path.exists(wav_path):
            os.remove(wav_path)

        success = result.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 500
        if success:
            log.info(f"  Kokoro [{lang_code}/{voice} @ {speed}x]: studio mastered audio ({os.path.getsize(out_path)//1024}KB)")
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

    # 1. Try Freesound if API key is provided
    freesound_key = os.environ.get("FREESOUND_KEY", "")
    if freesound_key:
        try:
            music = get_freesound_music(mood, freesound_key)
            if music and is_valid_audio(music):
                log.info("Stage 4: Music from Freesound ✓")
                return music
        except Exception as e:
            log.warning(f"Stage 4: Freesound failed: {e}")

    # 2. Try Pixabay if API key is provided
    pixabay_key = os.environ.get("PIXABAY_KEY", "")
    if pixabay_key:
        try:
            music = get_pixabay_music(mood, pixabay_key)
            if music and is_valid_audio(music):
                log.info("Stage 4: Music from Pixabay ✓")
                return music
        except Exception as e:
            log.warning(f"Stage 4: Pixabay failed: {e}")

    # 3. Use high-quality royalty-free thematic library from assets/music/
    music_folder = ASSETS_DIR / "music"
    if music_folder.exists():
        mood_files = list(music_folder.glob("*.mp3")) + list(music_folder.glob("*.m4a")) + list(music_folder.glob("*.wav"))
        keyword_matches = [f for f in mood_files if any(w in f.stem.lower() for w in mood.split())]
        pool = keyword_matches if keyword_matches else mood_files
        if pool:
            chosen = random.choice(pool)
            if is_valid_audio(str(chosen)):
                log.info(f"Stage 4: Using curated cinematic track — {chosen.name} ✓")
                return str(chosen)

    # 4. Fallback: synthesize dynamic cinematic ambient pad
    music_path = str(WORKSPACE / "music.mp3")
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "anoisesrc=d=300:c=pink:r=44100:a=0.015",
            "-f", "lavfi", "-i", "sine=f=55:d=300",
            "-f", "lavfi", "-i", "sine=f=110:d=300",
            "-f", "lavfi", "-i", "sine=f=164.81:d=300",
            "-filter_complex", "[1:a]volume=0.36[s1];[2:a]volume=0.30[s2];[3:a]volume=0.18[s3];[0:a][s1][s2][s3]amix=inputs=4[mix];[mix]lowpass=f=450,aecho=0.8:0.88:1000:0.4,volume=1.8[out]",
            "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", music_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        if is_valid_audio(music_path):
            log.info("Stage 4: Synthesized cinematic drone track ✓")
            return music_path
    except Exception as e:
        log.warning(f"Stage 4: Synthesis failed: {e}")

    return None

def get_freesound_music(mood, api_key):
    search_terms = {
        "serious corporate dramatic": ["corporate dramatic", "cinematic suspense"],
        "dark suspense thriller": ["suspense thriller", "dark cinematic"],
        "calm lo-fi focus": ["calm ambient", "cinematic ambient"],
        "cinematic dramatic": ["cinematic dramatic", "documentary score"],
        "energetic trap beat": ["cinematic beat", "action dramatic"],
        "playful upbeat cartoon": ["upbeat acoustic", "light documentary"],
        "dark noir": ["dark noir", "mystery cinematic"],
        "cool blue": ["ambient background", "documentary calm"]
    }
    search_query = random.choice(search_terms.get(mood, ["cinematic dramatic"]))
    try:
        resp = requests.get(
            "https://freesound.org/apiv2/search/text/",
            params={
                "query": search_query,
                "filter": "duration:[20.0 TO 300.0]",
                "fields": "id,name,previews,duration,tags",
                "sort": "rating_desc",
                "page_size": 15
            },
            headers={"Authorization": f"Token {api_key}", "User-Agent": "MediaAgencyBot/1.0"},
            timeout=20
        )
        if resp.status_code != 200:
            log.warning(f"Freesound returned status {resp.status_code}")
            return None
            
        results = resp.json().get("results", [])
        if not results:
            return None
            
        # Select best preview URL
        sound = random.choice(results)
        previews = sound.get("previews", {})
        download_url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")
        if not download_url:
            return None
            
        music_path = str(WORKSPACE / "freesound_music.mp3")
        r = requests.get(download_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code == 200 and len(r.content) > 2000:
            with open(music_path, "wb") as f:
                f.write(r.content)
            return music_path
    except Exception as e:
        log.warning(f"Freesound music search failed: {e}")
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
        "deep_impact": ("sine=frequency=80:duration=0.35:sample_rate=44100", "volume=0.36,lowpass=f=300,afade=t=out:st=0.15:d=0.2"),
        "whoosh":      ("sine=frequency=800:duration=0.25:sample_rate=44100", "volume=0.18,afade=t=in:d=0.02,afade=t=out:st=0.15:d=0.1,tremolo=f=12:d=0.3"),
        "click":       ("sine=frequency=1400:duration=0.06:sample_rate=44100", "volume=0.144"),
        "riser":       ("sine=frequency=200:duration=0.5:sample_rate=44100", "volume=0.24,afade=t=in:d=0.4"),
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
    fr = int((dur + 3.0) * 30)
    opts = {
        "zoom_in":   f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps=30",
        "zoom_out":  f"zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps=30",
        "pan_right": f"zoompan=z='1.3':x='min(iw*0.3,on*1.5)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps=30",
        "pan_left":  f"zoompan=z='1.3':x='max(0,iw*0.3-on*1.5)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps=30",
        "pan_up":    f"zoompan=z='1.3':x='iw/2-(ih/zoom/2)':y='max(0,ih*0.3-on*1.0)':d={fr}:s={w}x{h}:fps=30",
    }
    return opts.get(anim, opts["zoom_in"])

def img_to_vid(img, out, dur, anim="zoom_in", grain=True):
    vf = ken_burns(anim, dur)
    if grain: vf += ",noise=alls=2:allf=t+u"
    r = subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-vf", vf,
        "-t", str(dur + 3.0), "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-preset", "fast", out],
        capture_output=True, timeout=180)
    return r.returncode == 0

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

def is_valid_image_file(path):
    """Verifies that an image file exists, is non-empty, and can be fully decoded by PIL."""
    if not path or not os.path.exists(path):
        return False
    try:
        if os.path.getsize(path) < 1000:
            return False
        from PIL import Image
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            im.load()
        return True
    except Exception:
        return False

def save_and_verify_image(content, out_path):
    """
    Saves binary image content, converts RGBA/WebP/AVIF to standard RGB JPEG/PNG,
    and guarantees it can be decoded without error by Chromium/Remotion.
    """
    if not content or len(content) < 1000:
        return False
    try:
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(content))
        img.load()
        
        # Normalize color channels
        if out_path.endswith(".png"):
            if img.mode not in ("RGBA", "RGB"):
                img = img.convert("RGBA")
            img.save(out_path, format="PNG")
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(out_path, format="JPEG", quality=95)
            
        return is_valid_image_file(out_path)
    except Exception as e:
        log.warning(f"Image validation/conversion failed for {out_path}: {e}")
        if os.path.exists(out_path):
            try: os.remove(out_path)
            except: pass
        return False

def fetch_pollinations(prompt, out, seed=None):
    try:
        s = seed or random.randint(1, 99999)
        neg = "text watermark logos cartoon 3d render deformed blur bad anatomy saturated oversaturated plastic skin CGI"
        url = (f"https://image.pollinations.ai/prompt/{quote(prompt)}"
               f"?width=1920&height=1080&nologo=true&seed={s}&negative={quote(neg)}&model=flux")
        r = requests.get(url, timeout=90)
        if r.status_code == 200 and len(r.content) > 1000:
            return save_and_verify_image(r.content, out)
    except Exception as e: log.warning(f"Pollinations: {e}")
    return False

WIKI_HEADERS = {
    "User-Agent": "MediaAgencyDocBot/1.0 (https://github.com/thenewbie343/media-agency; contact@mediaagency.ai)"
}

_DDG_RATE_LIMITED = False

def fetch_duckduckgo_image(search, out):
    global _DDG_RATE_LIMITED
    import requests, random
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # 1. Try DDG first (if not previously rate limited)
    if not _DDG_RATE_LIMITED:
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    from ddgs import DDGS
                except ImportError:
                    from duckduckgo_search import DDGS
            
            clean_search = " ".join([w for w in search.split() if len(w)>2][:4])
            with DDGS() as ddgs:
                results = list(ddgs.images(clean_search, max_results=10))
                if results:
                    urls = [r.get("image") for r in results if r.get("image")]
                    if urls:
                        img_r = requests.get(random.choice(urls), headers=headers, timeout=15)
                        if img_r.status_code == 200 and len(img_r.content) > 1000:
                            if save_and_verify_image(img_r.content, out):
                                log.info(f"DDG fetched & verified: {clean_search}")
                                return True
        except Exception as e:
            if "403" in str(e) or "Ratelimit" in str(e):
                _DDG_RATE_LIMITED = True
                log.warning(f"DDG rate-limited (403). Tripping circuit breaker to use Wikimedia directly.")
            else:
                log.warning(f"DDG failed for '{search}': {e}. Falling back to Wikimedia.")

    # 2. Try the smart Wikipedia article-first fetcher
    try:
        wiki_url = fetch_wikimedia_image(search)
        if not wiki_url:
            simple = " ".join(search.split()[:2])
            wiki_url = fetch_wikimedia_image(simple)
            
        if wiki_url:
            img_r = requests.get(wiki_url, headers=WIKI_HEADERS, timeout=15)
            if img_r.status_code == 200 and len(img_r.content) > 1000:
                if save_and_verify_image(img_r.content, out):
                    log.info(f"Wikimedia fetched & verified: {wiki_url}")
                    return True
    except Exception as e:
        log.warning(f"Wikimedia fallback failed: {e}")

    # 3. Last resort Wikimedia Commons raw search
    try:
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query", "generator": "search", "gsrsearch": f"{search} filetype:bitmap",
            "gsrnamespace": 6, "gsrlimit": 10, "prop": "imageinfo", "iiprop": "url", "format": "json"
        }
        r = requests.get(url, params=params, headers=WIKI_HEADERS, timeout=15)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            urls = [p["imageinfo"][0]["url"] for p in pages.values() if "imageinfo" in p and p["imageinfo"]]
            if urls:
                img_r = requests.get(random.choice(urls), headers=WIKI_HEADERS, timeout=15)
                if img_r.status_code == 200 and len(img_r.content) > 1000:
                    if save_and_verify_image(img_r.content, out):
                        log.info(f"Wikimedia raw commons fetched & verified: {search}")
                        return True
    except Exception as e:
        log.warning(f"Wikimedia raw commons failed: {e}")
        
    return False

def fetch_wikimedia_image(query):
    """Fetches full-resolution historical images from Wikipedia / Wikimedia Commons with compliant headers."""
    import requests
    import urllib.parse
    import random
    
    if not query:
        return None
    
    # Tier 1: Direct Wikipedia pageimage (lead image)
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles={urllib.parse.quote(query)}"
        r = requests.get(url, headers=WIKI_HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1" and "original" in page_info:
                    return page_info["original"]["source"]
    except Exception as e:
        log.debug(f"Direct Wikipedia pageimage failed: {e}")
        
    # Tier 2: Wikipedia full-text article search to resolve title
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
        r = requests.get(search_url, headers=WIKI_HEADERS, timeout=10)
        if r.status_code == 200:
            search_data = r.json()
            results = search_data.get("query", {}).get("search", [])
            if results:
                first_title = results[0]["title"]
                url2 = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles={urllib.parse.quote(first_title)}"
                r2 = requests.get(url2, headers=WIKI_HEADERS, timeout=10)
                if r2.status_code == 200:
                    pages2 = r2.json().get("query", {}).get("pages", {})
                    for page_id, page_info in pages2.items():
                        if page_id != "-1" and "original" in page_info:
                            return page_info["original"]["source"]
    except Exception as e:
        log.debug(f"Wikipedia search fallback failed: {e}")

    # Tier 3: Wikimedia Commons raw bitmap search
    try:
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query", "generator": "search", "gsrsearch": f"{query} filetype:bitmap",
            "gsrnamespace": 6, "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url", "format": "json"
        }
        r = requests.get(url, params=params, headers=WIKI_HEADERS, timeout=10)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            urls = [p["imageinfo"][0]["url"] for p in pages.values() if "imageinfo" in p and p["imageinfo"]]
            if urls:
                return random.choice(urls)
    except Exception as e:
        log.debug(f"Wikimedia Commons API failed: {e}")
        
    return None

def _clean_pexels_query(search: str) -> str:
    """Cleans search strings into high-converting visual stock queries."""
    noise = {"official", "case", "file", "document", "cinematic", "dramatic", "scene", "4k", "hd", "footage", "photo", "evidence", "record"}
    words = [w for w in re.sub(r'[^\w\s]', '', search).split() if len(w) > 2 and w.lower() not in noise]
    if len(words) >= 2:
        return " ".join(words[:4])
    return search.strip() if search.strip() else "cinematic documentary"

def fetch_pexels_video(search, out, dur):
    try:
        if not PEXELS_KEY: return False
        clean_search = _clean_pexels_query(search)
        h = {"Authorization": PEXELS_KEY}
        
        # Primary search
        r = requests.get("https://api.pexels.com/videos/search", headers=h,
                         params={"query": clean_search, "per_page": 10, "orientation": "landscape"}, timeout=15)
        vids = r.json().get("videos", []) if r.status_code == 200 else []
        
        # Fallback cascade if specific search returned zero
        if not vids and len(clean_search.split()) > 2:
            shorter_query = " ".join(clean_search.split()[:2])
            r = requests.get("https://api.pexels.com/videos/search", headers=h,
                             params={"query": shorter_query, "per_page": 10, "orientation": "landscape"}, timeout=15)
            vids = r.json().get("videos", []) if r.status_code == 200 else []
            
        if not vids:
            return False
            
        # Select best video with highest resolution (4K or 1080p)
        vid = vids[0]
        files = vid.get("video_files", [])
        hd_files = [f for f in files if f.get("width", 0) >= 1920 or f.get("quality") == "hd"]
        chosen_file = max(hd_files, key=lambda x: x.get("width", 0)) if hd_files else files[0]
        
        raw = out.replace(".mp4", "_raw.mp4")
        v = requests.get(chosen_file["link"], stream=True, timeout=60)
        with open(raw, "wb") as f:
            for chunk in v.iter_content(8192):
                f.write(chunk)
                
        r2 = subprocess.run([
            "ffmpeg", "-y", "-i", raw, "-t", str(dur),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=25",
            "-r", "25", "-vsync", "cfr", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", "-preset", "fast", out
        ], capture_output=True, timeout=60)
        return r2.returncode == 0
    except Exception as e:
        log.warning(f"Pexels video: {e}")
        return False

def fetch_pexels_image(search, out):
    try:
        if not PEXELS_KEY: return False
        clean_search = _clean_pexels_query(search)
        h = {"Authorization": PEXELS_KEY}
        
        r = requests.get("https://api.pexels.com/v1/search", headers=h,
                         params={"query": clean_search, "per_page": 10, "orientation": "landscape"}, timeout=15)
        photos = r.json().get("photos", []) if r.status_code == 200 else []
        
        if not photos and len(clean_search.split()) > 2:
            shorter_query = " ".join(clean_search.split()[:2])
            r = requests.get("https://api.pexels.com/v1/search", headers=h,
                             params={"query": shorter_query, "per_page": 10, "orientation": "landscape"}, timeout=15)
            photos = r.json().get("photos", []) if r.status_code == 200 else []
            
        if not photos:
            return False
            
        best_photo = max(photos, key=lambda p: p.get("width", 0) * p.get("height", 0))
        url = best_photo["src"].get("large2x") or best_photo["src"].get("original") or best_photo["src"].get("large")
        img = requests.get(url, timeout=30)
        if img.status_code == 200 and len(img.content) > 1000:
            return save_and_verify_image(img.content, out)
        return False
    except Exception as e:
        log.warning(f"Pexels image: {e}")
        return False

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
                "-r","25","-vsync","cfr","-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart","-an","-preset","fast",out],capture_output=True,timeout=60)
            return r2.returncode==0
        else:
            r=requests.get("https://pixabay.com/api/",
                params={"key":PIXABAY_KEY,"q":search,"image_type":"photo","orientation":"horizontal","per_page":10,"safesearch":"true"},timeout=15)
            hits=r.json().get("hits",[])
            if not hits: return False
            url=random.choice(hits[:5])["largeImageURL"]
            img=requests.get(url,timeout=30)
            if img.status_code == 200 and len(img.content) > 1000:
                return save_and_verify_image(img.content, out)
            return False
    except Exception as e: log.warning(f"Pixabay: {e}"); return False

def solid_bg(out, dur):
    subprocess.run(["ffmpeg","-y","-f","lavfi",
        "-i",f"color=c=0x080808:size=1920x1080:duration={dur}:rate=25",
        "-c:v","libx264","-pix_fmt","yuv420p",out],capture_output=True,timeout=30)

HF_TOKENS = [
    os.environ.get("HF_TOKEN_1", ""),
    os.environ.get("HF_TOKEN_2", ""),
    os.environ.get("HF_TOKEN_3", "")
]
HF_TOKENS = [t for t in HF_TOKENS if t.strip()]

def fetch_hf_image(prompt, out_path):
    if HF_TOKENS:
        urls = [
            "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        ]
        token = random.choice(HF_TOKENS)
        headers = {"Authorization": f"Bearer {token}"}
        for url in urls:
            try:
                r = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=20)
                if r.status_code == 200 and len(r.content) > 1000:
                    if save_and_verify_image(r.content, out_path):
                        return True
            except Exception:
                pass
    # If HF returns 410 Deprecated or fails, seamlessly use Pollinations FLUX.1 Engine!
    return fetch_pollinations(prompt, out_path)

def fetch_hf_video(prompt, out_path):
    if not HF_TOKENS: return False
    urls = [
        "https://router.huggingface.co/hf-inference/models/damo-vilab/text-to-video-ms-1.7b",
        "https://api-inference.huggingface.co/models/damo-vilab/text-to-video-ms-1.7b"
    ]
    token = random.choice(HF_TOKENS)
    headers = {"Authorization": f"Bearer {token}"}
    for url in urls:
        try:
            r = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=55)
            if r.status_code == 200:
                with open(out_path, "wb") as f: f.write(r.content)
                return True
        except Exception as e:
            pass
    return False

# ═══════════════════════════════════════════════════════════
#  YOUTUBE DISCOVERY + AUTHORIZED MEDIA LAYER
# ═══════════════════════════════════════════════════════════

def fetch_youtube_authorized_clip(discovery_dict, out, target_duration=5.0):
    """
    Downloads a short clip from an AUTHORIZED YouTube source using yt-dlp.
    
    SAFETY: Rejects any discovery where source_role != YOUTUBE_AUTHORIZED.
    yt-dlp is NOT a rights mechanism — authorization is checked BEFORE download.
    """
    # Hard rights check — REJECT non-authorized sources
    asset_state = discovery_dict.get("source_role", "")
    if asset_state != "YOUTUBE_AUTHORIZED":
        log.warning(f"YouTube clip REJECTED: {discovery_dict.get('title', '')[:50]} — state={asset_state}, not AUTHORIZED.")
        return False
    
    video_id = discovery_dict.get("youtube_video_id", "")
    if not video_id:
        return False
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Check if yt-dlp is available
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, timeout=5, 
                               encoding="utf-8", errors="replace")
        if result.returncode != 0:
            log.warning("yt-dlp not available. Cannot download YouTube authorized clips.")
            return False
    except (FileNotFoundError, Exception):
        log.warning("yt-dlp not installed. Skipping YouTube authorized clip download.")
        return False
    
    try:
        raw = out.replace(".mp4", "_yt_raw.mp4")
        
        # Build yt-dlp command with duration limiting
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", raw,
            "--no-check-certificates",
        ]
        
        # If candidate timestamps exist, use them for segment extraction
        timestamps = discovery_dict.get("candidate_timestamps") or []
        if timestamps and len(timestamps) > 0:
            ts = timestamps[0]
            if "-" in ts:
                start, end = ts.split("-", 1)
                cmd.extend(["--download-sections", f"*{start}-{end}"])
            else:
                cmd.extend(["--download-sections", f"*{ts}-{ts}+{int(target_duration)}"])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, timeout=120,
                               encoding="utf-8", errors="replace")
        
        if result.returncode != 0 or not os.path.exists(raw):
            log.warning(f"yt-dlp download failed for {video_id}: {result.stderr[:200]}")
            return False
        
        # Trim and normalize with FFmpeg
        r2 = subprocess.run([
            "ffmpeg", "-y", "-i", raw, "-t", str(target_duration),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=25",
            "-r", "25", "-vsync", "cfr", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-an", "-preset", "fast", out
        ], capture_output=True, timeout=60, encoding="utf-8", errors="replace")
        
        if r2.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 1000:
            log.info(f"✅ YouTube AUTHORIZED clip downloaded: {discovery_dict.get('title', '')[:50]}")
            # Clean up raw
            try: os.remove(raw)
            except: pass
            return True
        
        log.warning(f"FFmpeg post-processing failed for YouTube clip {video_id}")
        return False
        
    except Exception as e:
        log.warning(f"YouTube authorized clip fetch failed: {e}")
        return False


def resolve_youtube_to_archive(discovery_dict, out, dur=5.0):
    """
    Takes a YOUTUBE_REFERENCE discovery and attempts to find the same 
    underlying material from rights-cleared archive sources.
    
    Search order:
    1. Wikimedia Commons (by extracted event/date/location)
    2. Internet Archive thumbnails
    3. Library of Congress
    """
    # Only process REFERENCE videos (not AUTHORIZED — those can be used directly)
    state = discovery_dict.get("source_role", "")
    if state == "YOUTUBE_AUTHORIZED":
        return False  # Not needed, use fetch_youtube_authorized_clip instead
    
    alt_query = discovery_dict.get("alternative_archive_query", "")
    if not alt_query:
        # Build from title
        title = discovery_dict.get("title", "")
        alt_query = re.sub(r'[^\w\s]', '', title)[:60]
    
    if not alt_query:
        return False
    
    log.info(f"🔄 YouTube→Archive resolution: \"{alt_query[:50]}\"")
    
    # Tier 1: Wikimedia Commons
    try:
        wiki_url = fetch_wikimedia_image(alt_query)
        if wiki_url:
            img_out = out.replace(".mp4", "_archive.jpg")
            img_r = requests.get(wiki_url, headers=WIKI_HEADERS, timeout=15)
            if img_r.status_code == 200 and len(img_r.content) > 1000:
                with open(img_out, "wb") as f:
                    f.write(img_r.content)
                if img_to_vid(img_out, out, dur, "zoom_in"):
                    log.info(f"✅ YouTube→Archive resolved via Wikimedia: {alt_query[:40]}")
                    return True
    except Exception as e:
        log.debug(f"Wikimedia archive resolution failed: {e}")
    
    # Tier 2: Internet Archive
    try:
        ia_url = "https://archive.org/advancedsearch.php"
        ia_params = {
            "q": alt_query,
            "fl[]": "identifier,title,mediatype",
            "rows": 5,
            "output": "json",
            "mediatype": "image"
        }
        r = requests.get(ia_url, params=ia_params, headers=WIKI_HEADERS, timeout=15)
        if r.status_code == 200:
            docs = r.json().get("response", {}).get("docs", [])
            for doc in docs:
                identifier = doc.get("identifier", "")
                if identifier:
                    thumb_url = f"https://archive.org/services/img/{identifier}"
                    img_out = out.replace(".mp4", "_ia.jpg")
                    img_r = requests.get(thumb_url, headers=WIKI_HEADERS, timeout=15)
                    if img_r.status_code == 200 and len(img_r.content) > 1000:
                        with open(img_out, "wb") as f:
                            f.write(img_r.content)
                        if img_to_vid(img_out, out, dur, "zoom_in"):
                            log.info(f"✅ YouTube→Archive resolved via Internet Archive: {identifier}")
                            return True
    except Exception as e:
        log.debug(f"Internet Archive resolution failed: {e}")
    
    # Tier 3: Library of Congress (loc.gov)
    try:
        loc_url = "https://www.loc.gov/search/"
        loc_params = {
            "q": alt_query,
            "fo": "json",
            "fa": "original-format:photo,print,drawing",
            "c": 5
        }
        r = requests.get(loc_url, params=loc_params, headers=WIKI_HEADERS, timeout=15)
        if r.status_code == 200:
            results = r.json().get("results", [])
            for result in results:
                image_url = result.get("image_url")
                if image_url and isinstance(image_url, list):
                    image_url = image_url[0]
                if image_url and isinstance(image_url, str):
                    if not image_url.startswith("http"):
                        image_url = f"https:{image_url}"
                    img_out = out.replace(".mp4", "_loc.jpg")
                    img_r = requests.get(image_url, headers=WIKI_HEADERS, timeout=15)
                    if img_r.status_code == 200 and len(img_r.content) > 1000:
                        with open(img_out, "wb") as f:
                            f.write(img_r.content)
                        if img_to_vid(img_out, out, dur, "zoom_in"):
                            log.info(f"✅ YouTube→Archive resolved via LOC: {result.get('title', '')[:40]}")
                            return True
    except Exception as e:
        log.debug(f"Library of Congress resolution failed: {e}")
    
    log.info(f"YouTube→Archive resolution found no rights-cleared alternative for: {alt_query[:50]}")
    return False


def stage_6_visuals(manifest, cfg):
    if not isinstance(manifest, dict) or "project_meta" not in manifest:
        log.error("Invalid ScriptManifest in stage_6_visuals")
        return manifest
        
    topic = manifest.get("project_meta", {}).get("topic", cfg.get("topic", ""))
    vprefix = cfg.get("visual_prefix", topic)
    
    # Flatten shots for processing
    all_shots = []
    for beat in manifest.get("story_beats", []):
        for block in beat.get("narration_blocks", []):
            block_dur = block.get("total_block_duration", 4.0)
            for shot in block.get("shots", []):
                # Compute absolute duration
                mode = shot.get("duration_mode", "ratio")
                if mode == "fixed" and shot.get("duration_seconds"):
                    shot["computed_duration"] = float(shot.get("duration_seconds"))
                else:
                    ratio = float(shot.get("duration_ratio", 1.0))
                    shot["computed_duration"] = block_dur * ratio
                    
                all_shots.append(shot)
                
    log.info(f"Stage 6: Visuals for {len(all_shots)} shots...")
    tg(f"🎨 Creating visuals...")
    vis = WORKSPACE / "visuals"
    vis.mkdir(exist_ok=True)

    for i, shot in enumerate(all_shots):
        n_id = shot.get("shot_id", f"s{i}")
        vtype = shot.get("visual_type", "ai_image")
        prompt = shot.get("ai_prompt", f"cinematic dramatic {topic} scene no faces no text")
        search = shot.get("visual_query", f"{vprefix} cinematic")
        out = str(vis / f"shot_{n_id}.mp4")
        img = str(vis / f"shot_{n_id}.jpg")
        
        # Determine camera motion for Ken Burns fallback
        motion_map = {
            "zoom_in": "zoom_in",
            "slow_push_in": "zoom_in",
            "pan_right": "pan_right",
            "slow_lateral": "pan_right",
            "zoom_out": "zoom_out",
            "top_down": "pan_up",
            "pan_left": "pan_left"
        }
        anim = motion_map.get(shot.get("camera_motion", "zoom_in"), "zoom_in")

        dur = shot.get("computed_duration", 4.0)
        shot["actual_duration"] = dur

        # If a video clip was already generated (e.g. by Colab / Wan2.1 / AnimateDiff), preserve it!
        if shot.get("asset", {}).get("path") and os.path.exists(shot["asset"]["path"]) and os.path.getsize(shot["asset"]["path"]) > 1000:
            log.info(f"  {n_id}: Using pre-generated clip ({shot.get('asset', {}).get('source', 'Colab')}) ✓")
            continue
            
        if "asset" not in shot:
            shot["asset"] = {}

        success = False

        if vtype in ["text_stat", "motion_graphics"]:
            # Remotion handles native Motion Graphics UI overlays, maps, timelines, and typography!
            # We fetch a dramatic visual background (Pollinations 4K or Pexels) for Remotion to layer over
            if not skip_ai(prompt) and fetch_pollinations(prompt, img, seed=i*17):
                if img_to_vid(img, out, dur, anim):
                    shot["asset"]["path"] = out
                    shot["asset"]["source"] = "pollinations"
                    log.info(f"  {n_id}: motion_graphics 4K background ✓")
                    continue
            if fetch_pexels_video(search, out, dur):
                shot["asset"]["path"] = out
                shot["asset"]["source"] = "pexels"
                log.info(f"  {n_id}: motion_graphics video background ✓")
                continue

        if vtype in ["intro_video", "ai_video"]:
            if not skip_ai(prompt):
                if fetch_hf_video(prompt, out):
                    shot["asset"]["path"] = out; shot["asset"]["source"] = "hf_video"; success = True; log.info(f"  {n_id}: HF_Video ✓")
            if not success and fetch_hf_image(prompt, img):
                if img_to_vid(img, out, dur, anim):
                    shot["asset"]["path"] = out; shot["asset"]["source"] = "hf_image"; success = True; log.info(f"  {n_id}: HF_Image+KenBurns fallback ✓")
            if not success and fetch_pollinations(prompt, img, seed=i*17):
                if img_to_vid(img, out, dur, anim):
                    shot["asset"]["path"] = out; shot["asset"]["source"] = "pollinations"; success = True; log.info(f"  {n_id}: Pollinations fallback ✓")
            if not success and fetch_pexels_video(search, out, dur):
                shot["asset"]["path"] = out; shot["asset"]["source"] = "pexels"; success = True; log.info(f"  {n_id}: Pexels fallback ✓")

        elif vtype == "real_photo":
            # Prioritize authentic YouTube discovery (if authorized or resolvable archive)
            try:
                from agents.youtube_discovery import youtube_search_by_claim
                yt_discs = youtube_search_by_claim(search, max_results=2)
                for disc in yt_discs:
                    if disc.get("source_role") == "YOUTUBE_AUTHORIZED":
                        if fetch_youtube_authorized_clip(disc, out, dur):
                            shot["asset"]["path"] = out
                            shot["asset"]["source"] = "youtube_authorized"
                            shot["asset"]["youtube_asset_state"] = "YOUTUBE_AUTHORIZED"
                            shot["asset"]["youtube_video_id"] = disc.get("youtube_video_id")
                            shot["asset_provenance"] = "YOUTUBE_AUTHORIZED"
                            success = True
                            log.info(f"  {n_id}: YouTube AUTHORIZED Clip ✓")
                            break
                    elif disc.get("source_role") == "YOUTUBE_REFERENCE":
                        # Attempt to resolve reference video to rights-cleared archive
                        if resolve_youtube_to_archive(disc, out, dur):
                            shot["asset"]["path"] = out
                            shot["asset"]["source"] = "archive"
                            shot["asset_provenance"] = "AUTHENTIC_ARCHIVE"
                            success = True
                            log.info(f"  {n_id}: YouTube→Archive Resolved ✓")
                            break
            except Exception as e:
                log.debug(f"YouTube discovery attempt skipped: {e}")

            # Fallback to authentic web images for real photos
            if not success and fetch_duckduckgo_image(search, img):
                if img_to_vid(img, out, dur, anim):
                    shot["asset"]["path"] = out; shot["asset"]["source"] = "ddg"; success = True; log.info(f"  {n_id}: DDG Real Photo ✓")
            if not success and fetch_pexels_image(search, img):
                if img_to_vid(img, out, dur, anim):
                    shot["asset"]["path"] = out; shot["asset"]["source"] = "pexels"; success = True; log.info(f"  {n_id}: Pexels image ✓")
            if not success and not skip_ai(prompt):
                if fetch_hf_image(prompt, img):
                    if img_to_vid(img, out, dur, anim):
                        shot["asset"]["path"] = out; shot["asset"]["source"] = "hf_image"; success = True; log.info(f"  {n_id}: HF_Image fallback ✓")
                if not success and fetch_pollinations(prompt, img, seed=i*17):
                    if img_to_vid(img, out, dur, anim):
                        shot["asset"]["path"] = out; shot["asset"]["source"] = "pollinations"; success = True; log.info(f"  {n_id}: Pollinations fallback ✓")

        elif vtype in ["ai_image", "motion_graphics"]:
            if not skip_ai(prompt):
                if fetch_hf_image(prompt, img):
                    if img_to_vid(img, out, dur, anim):
                        shot["asset"]["path"] = out; shot["asset"]["source"] = "hf_image"; success = True; log.info(f"  {n_id}: HF_Image ✓")
                if not success and fetch_pollinations(prompt, img, seed=i*17):
                    if img_to_vid(img, out, dur, anim):
                        shot["asset"]["path"] = out; shot["asset"]["source"] = "pollinations"; success = True; log.info(f"  {n_id}: Pollinations fallback ✓")
            if not success and fetch_pexels_image(search, img):
                if img_to_vid(img, out, dur, anim):
                    shot["asset"]["path"] = out; shot["asset"]["source"] = "pexels"; success = True; log.info(f"  {n_id}: Pexels image fallback ✓")

        elif vtype in ["stock_video", "broll_video"]:
            if fetch_pexels_video(search, out, dur):
                shot["asset"]["path"] = out; shot["asset"]["source"] = "pexels"; success = True; log.info(f"  {n_id}: Pexels video ✓")
            if not success and fetch_pixabay(search, out, dur):
                shot["asset"]["path"] = out; shot["asset"]["source"] = "pixabay"; success = True; log.info(f"  {n_id}: Pixabay video fallback ✓")

        # Global Fallbacks if everything above failed
        if not success and fetch_duckduckgo_image(search, img):
            if img_to_vid(img, out, dur, anim): shot["asset"]["path"] = out; shot["asset"]["source"] = "ddg"; success = True
        
        if not success:
            log.warning(f"  {n_id}: ALL standard visuals failed. Falling back to generic cinematic Pexels video.")
            if fetch_pexels_video("cinematic documentary abstract", out, dur):
                shot["asset"]["path"] = out; shot["asset"]["source"] = "pexels_fallback"; success = True
            elif fetch_pixabay("cinematic documentary abstract", out, dur):
                shot["asset"]["path"] = out; shot["asset"]["source"] = "pixabay_fallback"; success = True
            else:
                log.warning(f"  {n_id}: Generic stock fallback failed. Falling back to dynamic text-stat as LAST resort.")
                # We do not use make_text_stat anymore, Remotion will use fallback_type (e.g. MapFallback, ClassifiedFile)
                shot["asset"]["path"] = None
                shot["asset"]["source"] = "react_fallback_only"
                shot["asset"]["fallback_used"] = True
                
        if success:
            shot["asset"]["status"] = "success"
        else:
            shot["asset"]["status"] = "failed"
            shot["asset"]["fallback_used"] = True

    return manifest

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
    scenes = extract_scenes_list(script)

    for scene in scenes:
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
    scenes = extract_scenes_list(script)

    overlay_candidates = [s for s in scenes if s.get("sfx") in ("deep_impact","riser") and s.get("video_file")]
    overlay_scenes = random.sample(overlay_candidates, min(8, len(overlay_candidates))) if overlay_candidates else []
    if overlay_scenes:
        log.info(f"Applying overlay flash to {len(overlay_scenes)} high-impact scenes")
    for scene in overlay_scenes:
        overlay_video = get_overlay_video()
        if not overlay_video:
            break
        n = scene.get("scene", 0)
        dur = scene.get("actual_duration", float(scene.get("duration_hint",4)))
        composited = str(asm/f"overlay_{n:03d}.mp4")
        if apply_overlay_to_scene(scene["video_file"], overlay_video, dur, composited):
            scene["video_file"] = composited
            log.info(f"  Scene {n}: overlay flash applied")
        else:
            log.warning(f"  Scene {n}: overlay compositing failed")

    for scene in scenes:
        n     = scene.get("scene", 0)
        video = scene.get("video_file")
        audio = scene.get("audio_file")
        dur   = scene.get("actual_duration",4.0)
        sfx_t = scene.get("sfx","none")
        scene["start_time"]=cur_time

        if not video: continue

        out = str(asm/f"merged_{n:03d}.mp4")
        sfx_file = fetch_sfx(sfx_t) if sfx_t and sfx_t!="none" else None

        mixed_audio = None
        if audio and sfx_file:
            mixed_audio = str(asm/f"audio_{n:03d}.m4a")
            mix_r = subprocess.run(["ffmpeg","-y",
                "-i",os.path.abspath(audio),
                "-i",os.path.abspath(sfx_file),
                "-filter_complex","[0:a]adelay=180|180,volume=1.92[v];[1:a]volume=0.096[s];[v][s]amix=inputs=2:duration=first[a]",
                "-map","[a]","-c:a","aac",mixed_audio],capture_output=True,timeout=30)
            if mix_r.returncode != 0 or not os.path.exists(mixed_audio):
                log.warning(f"  SFX mix failed for scene {n}, using voice only")
                mixed_audio = audio

        aud_track = mixed_audio if (audio and sfx_file) else os.path.abspath(audio) if audio else None
        video_dur = get_dur(video)
        audio_dur = get_dur(aud_track) if aud_track else dur

        if aud_track and video_dur < audio_dur - 0.5:
            # Video is shorter than audio, loop video to match audio length
            cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", os.path.abspath(video), "-i", aud_track,
                   "-c:v", "libx264", "-c:a", "aac",
                   "-map", "0:v:0", "-map", "1:a:0", "-shortest", out]
        elif aud_track:
            cmd = ["ffmpeg", "-y", "-i", os.path.abspath(video), "-i", aud_track,
                   "-c:v", "copy", "-c:a", "aac",
                   "-map", "0:v:0", "-map", "1:a:0", "-shortest", out]
        else:
            cmd = ["ffmpeg", "-y", "-i", os.path.abspath(video),
                   "-c:v", "copy", "-an", out]

        r=subprocess.run(cmd,capture_output=True,timeout=60)
        if r.returncode==0 and os.path.exists(out):
            scene_files.append(out); cur_time+=dur
        else:
            log.warning(f"Scene {n} copy-merge failed, retrying with encode")
            cmd2=["ffmpeg","-y","-stream_loop","-1","-i",os.path.abspath(video)] + \
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

    total_dur = max(get_dur(raw), sum(s.get("actual_duration",4) for s in scenes) if scenes else 0.0)
    with_music=str(WORKSPACE/"with_music.mp4")
    if music_path and os.path.exists(music_path):
        r_mus = subprocess.run(["ffmpeg","-y","-i",raw,"-stream_loop","-1","-i",music_path,
            "-filter_complex",f"[1:a]volume=0.072,atrim=0:{total_dur}[m];[0:a][m]amix=inputs=2:duration=first[a]",
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

def extract_scenes_list(script):
    """Safely convert any script representation (list, dict with 'scenes', or dict with 'story_beats') into a flat list of scene dicts."""
    raw_scenes = []
    if isinstance(script, list):
        raw_scenes = script
    elif isinstance(script, str):
        if script.strip():
            raw_scenes = [script]
    elif isinstance(script, dict):
        if "scenes" in script and isinstance(script["scenes"], list):
            raw_scenes = script["scenes"]
        elif "story_beats" in script and isinstance(script["story_beats"], list):
            flat_scenes = []
            for beat in script.get("story_beats", []):
                if isinstance(beat, dict):
                    blocks = beat.get("narration_blocks", [])
                    if isinstance(blocks, list):
                        for block in blocks:
                            if isinstance(block, dict):
                                d = dict(block)
                                if "actual_duration" not in d:
                                    d["actual_duration"] = block.get("actual_voice_duration") or block.get("duration_hint", 4.0)
                                flat_scenes.append(d)
                            elif isinstance(block, str):
                                flat_scenes.append(block)
                    elif isinstance(blocks, str):
                        flat_scenes.append(blocks)
                elif isinstance(beat, (dict, str)):
                    flat_scenes.append(beat)
            raw_scenes = flat_scenes
        else:
            raw_scenes = []
    else:
        raw_scenes = []

    normalized = []
    for s in raw_scenes:
        if isinstance(s, dict):
            normalized.append(s)
        elif isinstance(s, str):
            if s.strip():
                normalized.append({
                    "caption": s,
                    "voiceover": s,
                    "actual_duration": 4.0,
                    "duration_hint": 4.0,
                })
    return normalized

# ═══════════════════════════════════════════════════════════
#  STAGE 8 — QC
# ═══════════════════════════════════════════════════════════
def stage_8_qc(video_path, script, cfg):
    log.info("Stage 8: QC...")
    tg("🔍 QC check...")
    try:
        from agents.video_qc import VideoQCAgent
        agent = VideoQCAgent()
        report = agent.review_video(video_path, script, cfg)
        log.info(f"Stage 8: {report['score']}/10 — {report['verdict']}")
        return report
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

    is_v2 = isinstance(script, dict) and "story_beats" in script
    scene_summaries = []
    num_scenes = 0
    total_dur = 0.0
    
    if is_v2:
        for beat in script.get("story_beats", []):
            for block in beat.get("narration_blocks", []):
                for shot in block.get("shots", []):
                    num_scenes += 1
                    total_dur += float(shot.get("actual_duration", shot.get("duration_seconds", 4.0)))
                    if len(scene_summaries) < 8:
                        cap = shot.get("caption", block.get("caption", ""))[:60]
                        if cap:
                            scene_summaries.append(cap)
    else:
        scenes = extract_scenes_list(script)
        num_scenes = len(scenes)
        total_dur = sum(s.get('actual_duration', 4.0) for s in scenes) if scenes else 0.0
        for s in scenes[:8]:
            cap = s.get("caption", s.get("voiceover", ""))[:60]
            if cap:
                scene_summaries.append(cap)
                
    actual_content = "\n".join(f"- {s}" for s in scene_summaries)
    
    lang_hint = "Write title and description in HINGLISH (Roman script, no Devanagari)." if lang == "hindi" else f"Write in {lang}."
    
    try:
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
        
        raw_json_str = extract_json_object(meta_text)
        clean_json = re.sub(r'[\x00-\x1F\x7F]', ' ', raw_json_str)
        meta = json.loads(clean_json, strict=False)
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
    token_data = os.environ.get("DRIVE_TOKEN_JSON", "")
    if not token_data:
        raise ValueError("DRIVE_TOKEN_JSON empty")
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

# ═══════════════════════════════════════════════════════════
#  STAGE 7.5 — DOCUMENTARY AUDIO ASSEMBLY (PHASE 4)
# ═══════════════════════════════════════════════════════════
def stage_assemble_documentary(script, cfg, remotion_video, music_path):
    log.info("Stage 7.5: Mixing Background Music into Remotion Render...")
    tg("🎞️ Mixing background music...")
    asm = WORKSPACE / "assembly"
    asm.mkdir(exist_ok=True)
    
    if not os.path.exists(remotion_video):
        raise RuntimeError(f"Remotion video missing at {remotion_video}!")
        
    final_output = str(asm / "final_documentary.mp4")
    total_dur = get_dur(remotion_video)

    if music_path and os.path.exists(music_path):
        # Mix the Remotion audio (TTS, Foley) with the background music using intelligent sidechain ducking
        cmd = [
            "ffmpeg", "-y", "-i", remotion_video, "-stream_loop", "-1", "-i", music_path,
            "-filter_complex", f"[1:a]volume=0.24,atrim=0:{total_dur}[bgm];[bgm][0:a]sidechaincompress=threshold=0.12:ratio=4:attack=200:release=1000[ducked];[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", final_output
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=300)
        if r.returncode == 0 and os.path.exists(final_output) and os.path.getsize(final_output) > 1000:
            log.info("✅ Documentary audio assembly complete with dynamic BGM sidechain ducking!")
            return final_output
        else:
            # Fallback simple amix
            log.warning("Sidechain mix failed, attempting simple amix fallback...")
            cmd_fb = [
                "ffmpeg", "-y", "-i", remotion_video, "-stream_loop", "-1", "-i", music_path,
                "-filter_complex", f"[1:a]volume=0.216,atrim=0:{total_dur}[m];[0:a][m]amix=inputs=2:duration=first[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", final_output
            ]
            r_fb = subprocess.run(cmd_fb, capture_output=True, timeout=300)
            if r_fb.returncode == 0 and os.path.exists(final_output):
                return final_output
            log.warning("Music mix failed, using raw Remotion output")
            return remotion_video
    else:
        log.info("No music track provided, using raw Remotion output")
        return remotion_video

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
        scenes=extract_scenes_list(script)
        total=sum(s.get("actual_duration",4) for s in scenes) if scenes else 0.0

        tg(f"✅ DONE!\n\n📺 {url}\n⏰ {cfg['schedule']} UTC\n🏆 QC: {score}/10\n🎬 {len(scenes)} scenes | {total:.0f}s\n✂️ Avg {total/max(len(scenes),1):.1f}s/cut\n⚡ {elapsed}s total{drive_note}")

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

    session_file = os.path.expanduser("~/.config/colab-cli/token.json")
    if not os.path.exists(session_file):
        log.warning("Colab CLI token not found — skipping Wan2.1")
        return {}

    # Enforce pinned compatible versions of colab-cli and jupyter-kernel-client
    try:
        import sys
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-colab-cli==0.6.0", "jupyter-kernel-client==0.15.0"], capture_output=True, timeout=40)
    except Exception as sync_err:
        log.warning(f"colab_cli version sync notice: {sync_err}")

    log.info(f"Wan2.1 via Colab CLI: {len(scenes_needing_video)} scenes")
    tg(f"🎨 Wan2.1 GPU generation: {len(scenes_needing_video)} animated clips...")

    prompts_file = str(WORKSPACE / "scene_prompts.json")
    with open(prompts_file, "w") as f:
        json.dump(scenes_needing_video, f, indent=2)

    clips_dir = WORKSPACE / "wan_clips"
    clips_dir.mkdir(exist_ok=True)

    try:
        # Pass prompts as a JSON string argument to the script
        import shlex
        prompts_json_str = json.dumps(scenes_needing_video)
        hf_token = os.environ.get("HF_TOKEN_1", "")
        
        cmd = [
            "colab", "run", "--gpu", "T4", "--timeout", "21600",
            "wan21_generator.py",
            prompts_json_str,
            hf_token
        ]
        
        log.info(f"Executing: colab run --gpu T4 --timeout 21600 wan21_generator.py '[json...]' '[token]'")
        import base64
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        current_file = None
        b64_buffer = []
        
        for line in process.stdout:
            # Check if we are starting a file download
            if line.startswith("<<FILE:"):
                current_file = line.strip().replace("<<FILE:", "").replace(">>", "")
                b64_buffer = []
                log.info(f"Colab returning file: {current_file} (downloading base64...)")
                continue
            
            # Check if file download is finished
            if line.startswith("<<EOF>>") and current_file:
                b64_data = "".join(b64_buffer).strip()
                try:
                    raw_data = base64.b64decode(b64_data)
                    dest_path = WORKSPACE / current_file if current_file == "wan21_results.json" else clips_dir / current_file
                    with open(dest_path, "wb") as f:
                        f.write(raw_data)
                    log.info(f"Saved {current_file} from Colab ({len(raw_data)//1024}KB)")
                except Exception as e:
                    log.error(f"Failed to decode base64 for {current_file}: {e}")
                
                current_file = None
                b64_buffer = []
                continue
                
            # If we are inside a file block, buffer the base64 chunks
            if current_file:
                b64_buffer.append(line)
            else:
                # Normal log line from Colab - print it in real-time!
                print(f"[Colab] {line.strip()}", flush=True)

        process.wait()
        log.info(f"Colab exit code: {process.returncode}")

        results_file = WORKSPACE / "wan21_results.json"
        if results_file.exists():
            with open(results_file) as f:
                results = json.load(f)
            clip_map = {}
            for r in results:
                if r.get("success"):
                    scene_id = r["scene"]
                    is_num = False
                    try:
                        int(scene_id)
                        is_num = True
                    except:
                        pass
                    filename = f"scene_{int(scene_id):03d}.mp4" if is_num else f"scene_{scene_id}.mp4"
                    local_path = str(clips_dir / filename)
                    if os.path.exists(local_path):
                        clip_map[scene_id] = local_path
                        log.info(f"  Scene {scene_id}: Wan2.1 clip ✓")
            log.info(f"Wan2.1: {len(clip_map)}/{len(scenes_needing_video)} clips generated")
            tg(f"✅ Wan2.1: {len(clip_map)} animated clips ready")
            return clip_map
        else:
            log.warning("⚠️ Colab GPU temporarily unavailable or in daily cooldown. Seamlessly routing visual generation to Pollinations Engine...")
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

    scenes = extract_scenes_list(script)
    candidates = [s for s in scenes
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

def audit_assets(script_path):
    import json
    import os
    from pathlib import Path
    log.info("🔍 Pre-Render Asset Audit starting...")
    
    with open(script_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    required_files = []
    missing_files = []
    
    public_assets_dir = BASE_DIR / "remotion" / "public" / "assets"
    
    def check_asset_exists(file_ref):
        if not file_ref:
            return True
        # Check direct path
        p1 = public_assets_dir / file_ref
        if p1.exists(): return True
        # Check sfx path
        p2 = public_assets_dir / "sfx" / file_ref
        if p2.exists(): return True
        # Check without sfx/ prefix if present
        if file_ref.startswith("sfx/"):
            sub = file_ref[4:]
            if (public_assets_dir / sub).exists() or (public_assets_dir / "sfx" / sub).exists():
                return True
        # Check with .mp3 or .wav
        for ext in [".mp3", ".wav"]:
            if (public_assets_dir / f"{file_ref}{ext}").exists(): return True
            if (public_assets_dir / "sfx" / f"{file_ref}{ext}").exists(): return True
            if (public_assets_dir / "sfx" / "Impacts" / f"{file_ref}{ext}").exists(): return True
            if (public_assets_dir / "sfx" / "Whooshes" / f"{file_ref}{ext}").exists(): return True
            if (public_assets_dir / "sfx" / "Risers" / f"{file_ref}{ext}").exists(): return True
        return False

    is_v2 = isinstance(manifest, dict) and "story_beats" in manifest
    if is_v2:
        for beat in manifest.get("story_beats", []):
            for block in beat.get("narration_blocks", []):
                if block.get("audio_file"):
                    required_files.append(block["audio_file"])
                for shot in block.get("shots", []):
                    if shot.get("video_file"):
                        required_files.append(shot["video_file"])
                    if shot.get("fg_file"):
                        required_files.append(shot["fg_file"])
                    if shot.get("sound_design"):
                        required_files.append(f"sfx/{shot['sound_design']}.mp3")
                    if shot.get("editorial_events"):
                        valid_events = []
                        for evt in shot.get("editorial_events", []):
                            if evt.get("type") in ["SFX", "IMPACT"]:
                                cue = evt.get("cue")
                                if cue and not check_asset_exists(cue):
                                    log.warning(f"Editorial event audio {cue} missing in {public_assets_dir}. Stripping event.")
                                    continue
                            valid_events.append(evt)
                        shot["editorial_events"] = valid_events
    else:
        log.warning("Audit skipped for non-V2 manifest")
        return True, []
        
    for file_path in required_files:
        basename = os.path.basename(file_path)
        if file_path.startswith("sfx/"):
            if not check_asset_exists(file_path):
                log.warning(f"SFX file {file_path} missing. Safely stripping from render manifest.")
                if is_v2:
                    for beat in manifest.get("story_beats", []):
                        for block in beat.get("narration_blocks", []):
                            for shot in block.get("shots", []):
                                if shot.get("sound_design") and file_path.endswith(f"{shot['sound_design']}.mp3"):
                                    shot["sound_design"] = None
                continue # Do not fail the audit for optional SFX
        elif file_path.startswith("/"):
            check_path = file_path # Absolute path
            if not os.path.exists(check_path):
                missing_files.append(check_path)
        else:
            check_path = f"remotion/public/assets/{basename}"
            if not (public_assets_dir / basename).exists() and not check_asset_exists(file_path):
                missing_files.append(check_path)
            
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
            
    with open("render_asset_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"required": required_files, "missing": missing_files}, f, indent=2)
        
    if missing_files:
        log.error(f"❌ Asset Audit FAILED! Missing {len(missing_files)} files: {missing_files[:5]}")
        return False, missing_files

    # ── YOUTUBE RIGHTS SAFETY GATE ──────────────────────────────
    try:
        from agents.youtube_discovery import audit_youtube_rights
        yt_passed, yt_violations = audit_youtube_rights(manifest)
        if not yt_passed:
            log.error(f"❌ YouTube Rights Safety Gate FAILED: {yt_violations}")
            return False, yt_violations
    except Exception as e:
        log.warning(f"YouTube rights audit check warning: {e}")

    log.info("✅ Asset Audit PASSED! All files present and rights cleared.")
    return True, []

def run_pipeline_v52():
    start = time.time()
    cfg   = parse_input()
    genre = cfg["genre"]

    log.info(f"🚀 v5.2 | {cfg['topic']} | {genre} | {cfg['lang']} | {cfg['duration_min']}min")
    tg(f"🚀 v5.2 DUAL-SCRIPT\n📌 {cfg['topic']}\n🎬 {genre} | {cfg['lang']} | {cfg['duration_min']}min\n⏰ {cfg['schedule']} UTC")

    try:
        research = None
        stats = {}
        if genre == "documentary":
            log.info("🎯 Routing to new AI Studio Documentary Engine (Phase 2 Integration)...")
            from agents.engine import run_documentary_pipeline
            script, research, stats = run_documentary_pipeline(cfg)
            
            # V3 VISUAL INTELLIGENCE: Manifest Reviewer
            log.info("🔍 V3: Running Manifest Review before asset generation...")
            from agents.manifest_reviewer import ManifestReviewerAgent
            reviewer = ManifestReviewerAgent()
            review_result = reviewer.review_manifest(script)
            
            if review_result.get("status") == "FAILED":
                log.error("MANIFEST REVIEW FAILED. Aborting generation.")
                raise RuntimeError(f"Manifest failed validation: {review_result.get('errors')}")
                
            _save(script, "script_ai_studio.json")
            tg(f"✍️ {len(script)} scenes generated via AI Studio. AI Video: {review_result['metrics']['ai_video_percentage']:.1f}%")
            
            
            # 24. TEST BEFORE FULL RENDER
            test_mode = os.environ.get("TEST_MODE", "").lower()
            is_hero_test = (test_mode == "hero")
            if test_mode in ("true", "1", "yes", "grammar", "hero"):
                log.info(f"🧪 TEST_MODE enabled (mode={test_mode}). Truncating script.")
                log.info("🧪 TEST_MODE enabled. Enforcing specific mixed-asset coverage (30-45s).")
                
                import shutil
                if not shutil.which("ffmpeg"):
                    raise RuntimeError("FFmpeg not found. Install FFmpeg or run inside the GitHub Actions environment.")
                    
                if isinstance(script, dict) and "story_beats" in script:
                    truncated_beats = []
                    shot_count = 0
                    
                    for beat in script.get("story_beats", []):
                        if shot_count >= 15:
                            break
                        new_blocks = []
                        for block in beat.get("narration_blocks", []):
                            if shot_count >= 15:
                                break
                            
                            for i, shot in enumerate(block.get("shots", [])):
                                if is_hero_test and shot_count < 2:
                                    shot["visual_type"] = "ai_video"
                                    shot["generation_priority"] = 1.0
                                shot_count += 1
                                
                            new_blocks.append(block)
                        
                        if new_blocks:
                            beat["narration_blocks"] = new_blocks
                            truncated_beats.append(beat)
                    
                    script["story_beats"] = truncated_beats
                    _save(script, "test_manifest.json")
                    log.info(f"Truncated to {shot_count} shots for natural TEST_MODE.")

        else:
            research = stage_1_research(cfg)
            _save(research, "research.json")

            script = stage_2_script(research, cfg)
            _save(script, "script.json")
            tg(f"✍️ {len(script)} scenes (Devanagari + Hinglish)")
            
            if genre == "documentary":
                log.info("Upgrading legacy flat script to v2.0 hierarchy using DirectorAgent...")
                from agents.director import DirectorAgent
                director = DirectorAgent()
                script = director.add_metadata(script)

        script = stage_3_voice(script, cfg)
        music_path = stage_4_music(cfg)

        # V3 Automated Repair Loop
        max_repairs = 2
        for repair_attempt in range(max_repairs + 1):
            if repair_attempt > 0:
                log.info(f'🔧 REPAIR LOOP: Attempt {repair_attempt} for worst shots.')
                # V3.2 Diagnostic Repair
                worst_shots_data = qc.get('worst_5_shots', [])
                repair_map = {}
                if isinstance(worst_shots_data, list) and len(worst_shots_data) > 0 and isinstance(worst_shots_data[0], dict):
                    repair_map = {ws.get('shot_id'): ws for ws in worst_shots_data if 'shot_id' in ws}
                else:
                    # Legacy fallback
                    repair_map = {ws.split(':')[0]: {} for ws in worst_shots_data if isinstance(ws, str)}

                if isinstance(script, dict) and 'story_beats' in script:
                    for beat in script.get('story_beats', []):
                        for block in beat.get('narration_blocks', []):
                            for shot in block.get('shots', []):
                                s_id = shot.get('shot_id')
                                if s_id in repair_map:
                                    ws = repair_map[s_id]
                                    s_rep = ws.get('suggested_repair', {})
                                    
                                    if s_rep.get('regenerate_prompt'):
                                        shot['ai_prompt'] = f"{shot.get('ai_prompt')} [REPAIR: Avoid {', '.join(ws.get('failures', []))}]"
                                    elif s_rep.get('switch_medium'):
                                        new_med = s_rep.get('switch_medium')
                                        shot['visual_type'] = new_med
                                        if new_med == "stock_video": shot["asset_provenance"] = "STOCK"
                                        elif new_med == "motion_graphics": shot["asset_provenance"] = "DATA_VISUALIZATION"
                                        elif new_med == "real_photo": shot["asset_provenance"] = "ARCHIVAL_FOOTAGE"
                                    else:
                                        shot['visual_type'] = 'stock_video'
                                        shot['asset_provenance'] = 'STOCK'
                                        
                                    if 'asset' in shot:
                                        shot['asset'].pop('path', None)
                                        shot['asset'].pop('status', None)
                                        shot['asset'].pop('source', None)
            # Route ONLY ai_video (25%) scenes to Colab AnimateDiff
            wan_scenes = []
            if os.path.exists(os.path.expanduser("~/.config/colab-cli/token.json")):
                is_v2 = isinstance(script, dict) and "story_beats" in script
                flat_shots = []
                if is_v2:
                    for beat in script.get("story_beats", []):
                        for block in beat.get("narration_blocks", []):
                            for shot in block.get("shots", []):
                                flat_shots.append({
                                    "scene": shot.get("shot_id"),
                                    "visual_type": shot.get("visual_type"),
                                    "ai_prompt": shot.get("ai_prompt"),
                                    "duration_hint": shot.get("duration_seconds") or 4.0,
                                })
                else:
                    scenes = extract_scenes_list(script)
                    for i, scene in enumerate(scenes):
                        flat_shots.append({
                            "scene": i,
                            "visual_type": scene.get("visual_type"),
                            "ai_prompt": scene.get("ai_prompt"),
                            "duration_hint": scene.get("duration_hint", 4.0),
                        })
                wan_scenes = [s for s in flat_shots
                              if s.get("visual_type") == "ai_video"
                              and not skip_ai(s.get("ai_prompt",""))]
                log.info(f"Routing {len(wan_scenes)} ai_video shots to Wan2.1 (Colab GPU generator)")

            wan_clips = {}
            if wan_scenes:
                wan_clips = stage_wan21_colab(wan_scenes, cfg["topic"])

            is_v2 = isinstance(script, dict) and "story_beats" in script
            if is_v2:
                for beat in script.get("story_beats", []):
                    for block in beat.get("narration_blocks", []):
                        for shot in block.get("shots", []):
                            s_id = shot.get("shot_id")
                            if s_id in wan_clips:
                                shot.setdefault("asset", {})["path"] = wan_clips[s_id]
                                shot["asset"]["source"] = "wan2.1"
                                shot["asset"]["status"] = "success"

                                v_dur = shot.get("duration_seconds")
                                if not v_dur:
                                    ratio = shot.get("duration_ratio", 1.0)
                                    v_dur = float(block.get("actual_voice_duration") or block.get("duration_hint", 4.0)) * ratio

                                source_dur = 5.0 # Wan2.1 produces 5s clips
                                if v_dur > source_dur * 1.5:
                                    diff = v_dur / source_dur
                                    shot["asset"]["coverage_strategy"] = "slow_mo" if diff <= 2.0 else "coverage_composition"
                                    log.warning(f"V3 LOOP PREVENTION: Shot {s_id} assigned {v_dur}s but AI clip is {source_dur}s. Strategy: {shot['asset']['coverage_strategy']}")
                                    shot["actual_duration"] = v_dur
                                    continue
                                    
                                shot["actual_duration"] = v_dur
            else:
                scenes = extract_scenes_list(script)
                for scene in scenes:
                    if scene.get("scene") in wan_clips:
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
                public_dir = WORKSPACE.parent / "remotion" / "public" / "assets"
                public_dir.mkdir(parents=True, exist_ok=True)

                import shutil
                import re

                # Sync exact repository assets (SFX, Overlays, LUTs, Fonts) to Remotion public assets directory
                if SFX_DIR.exists():
                    shutil.copytree(SFX_DIR, public_dir / "sfx", dirs_exist_ok=True)
                if OVERLAYS_DIR.exists():
                    shutil.copytree(OVERLAYS_DIR, public_dir / "overlays", dirs_exist_ok=True)
                if LUTS_DIR.exists():
                    shutil.copytree(LUTS_DIR, public_dir / "luts", dirs_exist_ok=True)
                if FONTS_DIR.exists():
                    shutil.copytree(FONTS_DIR, public_dir / "fonts" / "caption", dirs_exist_ok=True)

                # Seed standard cues with real high-quality audio files from assets/sfx
                sfx_dest = public_dir / "sfx"
                sfx_dest.mkdir(parents=True, exist_ok=True)
                sfx_cue_mappings = {
                    "deep_impact": SFX_DIR / "Impacts" / "Impact_1.wav",
                    "impact": SFX_DIR / "Impacts" / "Impact_1.wav",
                    "whoosh": SFX_DIR / "Whooshes" / "Cinematic Whoosh.mp3",
                    "subtle_whoosh": SFX_DIR / "Whooshes" / "Whoosh Fly By 1 1.mp3",
                    "riser": SFX_DIR / "Risers" / "Riser 1.wav",
                    "cinematic_whoosh": SFX_DIR / "Whooshes" / "Cinematic Whoosh.mp3",
                    "paper_rustle": SFX_DIR / "Whooshes" / "Whoosh Fly By 1 2.mp3",
                    "wind_howl": SFX_DIR / "Risers" / "Riser 2.wav",
                }
                for cue_name, src_path in sfx_cue_mappings.items():
                    if src_path.exists():
                        ext = src_path.suffix
                        shutil.copy2(src_path, sfx_dest / f"{cue_name}{ext}")
                        shutil.copy2(src_path, public_dir / f"{cue_name}{ext}")
                        if ext == ".wav":
                            shutil.copy2(src_path, sfx_dest / f"{cue_name}.mp3")
                            shutil.copy2(src_path, public_dir / f"{cue_name}.mp3")

                try:
                    from rembg import remove
                    from PIL import Image, ImageFilter
                except ImportError:
                    remove = None

                def clean_caption_text(text):
                    if not text: return ""
                    # Remove anything in brackets or parentheses
                    t = re.sub(r'\[.*?\]', '', text)
                    t = re.sub(r'\(.*?\)', '', text)
                    # Remove speaker tags like "Narrator:" or "Voiceover:"
                    t = re.sub(r'^[A-Za-z\s]+:', '', t)
                    # Clean up multiple spaces and strip
                    t = re.sub(r'\s+', ' ', t).strip()
                    return t

                def is_sfx_present(sfx_name):
                    if not sfx_name: return False
                    candidates = [
                        public_dir / sfx_name,
                        public_dir / "sfx" / sfx_name,
                        public_dir / f"{sfx_name}.mp3",
                        public_dir / f"{sfx_name}.wav",
                        public_dir / "sfx" / f"{sfx_name}.mp3",
                        public_dir / "sfx" / f"{sfx_name}.wav",
                        public_dir / "sfx" / "Impacts" / f"{sfx_name}.wav",
                        public_dir / "sfx" / "Whooshes" / f"{sfx_name}.mp3",
                        public_dir / "sfx" / "Risers" / f"{sfx_name}.wav",
                    ]
                    return any(c.exists() for c in candidates)

                # Clean Narration Captions
                if isinstance(script, dict) and "story_beats" in script:
                    for beat in script.get("story_beats", []):
                        for block in beat.get("narration_blocks", []):
                            raw_cap = block.get("caption", block.get("voiceover", ""))
                            block["caption"] = clean_caption_text(raw_cap)

                            # Copy audio file to public_dir for Remotion
                            aud = block.get("audio_file")
                            if aud and os.path.exists(aud):
                                dest_aud = public_dir / os.path.basename(aud)
                                shutil.copy2(aud, dest_aud)
                                block["audio_file"] = os.path.basename(aud)

                            for shot in block.get("shots", []):
                                vid = shot.get("asset", {}).get("path")
                                img_candidate = shot.get("asset", {}).get("image_path") or (str(vis / f"shot_{shot.get('shot_id')}.jpg") if 'vis' in locals() else None)
                                if not img_candidate and vid and vid.endswith('.mp4'):
                                    possible_jpg = vid.replace('.mp4', '.jpg')
                                    if os.path.exists(possible_jpg) and is_valid_image_file(possible_jpg):
                                        img_candidate = possible_jpg

                                # For still images, real photos, and motion graphics, prefer image asset for Remotion CameraSystem & 2.5D cutouts
                                if shot.get("visual_type") in ("ai_image", "real_photo", "motion_graphics") and img_candidate and is_valid_image_file(img_candidate):
                                    dest = public_dir / os.path.basename(img_candidate)
                                    shutil.copy2(img_candidate, dest)
                                    shot["asset"]["path"] = os.path.basename(img_candidate)
                                    vid = img_candidate
                                elif vid and os.path.exists(vid) and (vid.endswith(".mp4") or is_valid_image_file(vid)):
                                    dest = public_dir / os.path.basename(vid)
                                    shutil.copy2(vid, dest)
                                    shot["asset"]["path"] = os.path.basename(vid)
                                else:
                                    # Asset is missing or invalid — fallback gracefully so Remotion renders fallback UI
                                    shot["asset"]["path"] = None
                                    shot["asset"]["fallback_used"] = True
                                    shot["asset"]["status"] = "failed"
                                    vid = None

                                # 2.5D Parallax Foreground Extraction
                                if remove and shot.get("visual_type") in ("ai_image", "real_photo") and vid and not vid.endswith('.mp4') and is_valid_image_file(vid):
                                    try:
                                        shot["asset"]["bg_file"] = os.path.basename(vid)
                                        fg_name = os.path.splitext(os.path.basename(vid))[0] + "_fg.png"
                                        fg_path = public_dir / fg_name

                                        if not os.path.exists(fg_path):
                                            log.info(f"Generating 2.5D Foreground for {vid}...")
                                            input_img = Image.open(vid)
                                            output_img = remove(input_img).convert("RGBA")
                                            r, g, b, alpha = output_img.split()
                                            blurred_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=1))
                                            output_img = Image.merge("RGBA", (r, g, b, blurred_alpha))
                                            output_img.save(fg_path)

                                        shot["asset"]["fg_file"] = fg_name
                                    except Exception as e:
                                        log.error(f"Failed to generate foreground for {vid}: {e}")
                else:
                    scenes = extract_scenes_list(script)
                    for s in scenes:
                        if isinstance(s, dict):
                            raw_cap = s.get("caption", s.get("voiceover", ""))
                            s["caption"] = clean_caption_text(raw_cap)

                            aud = s.get("audio_file")
                            if aud and os.path.exists(aud):
                                dest_aud = public_dir / os.path.basename(aud)
                                shutil.copy2(aud, dest_aud)
                                s["audio_file"] = os.path.basename(aud)

                            vid = s.get("video_file") or s.get("image_file")
                            if vid and os.path.exists(vid) and (vid.endswith(".mp4") or is_valid_image_file(vid)):
                                dest = public_dir / os.path.basename(vid)
                                shutil.copy2(vid, dest)
                                s["video_file"] = os.path.basename(vid)

                                if remove and s.get("visual_type") in ("ai_image", "real_photo") and not vid.endswith('.mp4') and is_valid_image_file(vid):
                                    try:
                                        s["bg_file"] = os.path.basename(vid)
                                        fg_name = os.path.splitext(os.path.basename(vid))[0] + "_fg.png"
                                        fg_path = public_dir / fg_name

                                        if not os.path.exists(fg_path):
                                            log.info(f"Generating 2.5D Foreground for {vid}...")
                                            input_img = Image.open(vid)
                                            output_img = remove(input_img).convert("RGBA")
                                            r, g, b, alpha = output_img.split()
                                            blurred_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=1))
                                            output_img = Image.merge("RGBA", (r, g, b, blurred_alpha))
                                            output_img.save(fg_path)

                                        s["fg_file"] = fg_name
                                    except Exception as e:
                                        log.error(f"Failed to generate foreground for {vid}: {e}")

                # SFX Safety Check: strip missing sound_design and editorial_events audio files to prevent Remotion 404 crash
                is_v2 = isinstance(script, dict) and "story_beats" in script
                if is_v2:
                    for beat in script.get("story_beats", []):
                        for block in beat.get("narration_blocks", []):
                            for s in block.get("shots", []):
                                if s.get("sound_design"):
                                    sfx_name = s["sound_design"]
                                    if not is_sfx_present(sfx_name):
                                        log.warning(f"SFX file {sfx_name} not found in public assets. Stripping to prevent crash.")
                                        s["sound_design"] = None
                                if s.get("editorial_events"):
                                    valid_events = []
                                    for evt in s.get("editorial_events", []):
                                        if evt.get("type") in ["SFX", "IMPACT"]:
                                            cue = evt.get("cue")
                                            if cue and not is_sfx_present(cue):
                                                log.warning(f"SFX cue {cue} not found in public assets. Stripping event to prevent crash.")
                                                continue
                                        valid_events.append(evt)
                                    s["editorial_events"] = valid_events
                else:
                    for s in extract_scenes_list(script):
                        if s.get("sound_design"):
                            sfx_name = s["sound_design"]
                            if not is_sfx_present(sfx_name):
                                log.warning(f"SFX file {sfx_name} not found in public assets. Stripping to prevent crash.")
                                s["sound_design"] = None

                # Authoritative Pre-Render Cinematic Timeline Compilation
                if is_v2:
                    from agents.cinematic_timeline import CinematicTimelineCompiler
                    from agents.cinematic_qc import CinematicQCEngine
                    timeline_compiler = CinematicTimelineCompiler()
                    compiled_timeline = timeline_compiler.compile_timeline(script, fps=30)
                    script["cinematic_timeline"] = compiled_timeline
                    
                    qc_engine = CinematicQCEngine()
                    director_score_res = qc_engine.evaluate_manifest_director_score(script)
                    log.info(f"🎬 Pre-Render Director Score: {director_score_res.get('overall_director_score', 8.0)}/10.0 ({director_score_res.get('verdict')})")
                    _save(compiled_timeline, "cinematic_timeline.json")

                _save(script, "script_remotion.json")
                script_path = str((WORKSPACE / "script_remotion.json").resolve())
                final_video_abs = str((WORKSPACE / "final_documentary.mp4").resolve())

                # Pre-Render Asset Audit
                audit_passed, missing_assets = audit_assets(script_path)
                if not audit_passed:
                    log.error("Asset audit failed. Aborting Remotion render to prevent 404 crash.")
                    raise RuntimeError(f"Missing required assets before render: {missing_assets}")

                # Prevent headless deadlock by lowering concurrency and providing ample delay-render timeout
                remotion_cmd = f"npx remotion render src/index.ts DocumentaryVideo {final_video_abs} --props={script_path} --concurrency=2 --delay-render-timeout-in-milliseconds=60000 --log=verbose --crf=22"
                log.info(f"Running Remotion: {remotion_cmd}")
                import subprocess
                res = subprocess.run(remotion_cmd, cwd="remotion", shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
                if res.returncode != 0:
                    log.error(f"Remotion failed: {res.stderr}")
                    raise Exception("Remotion render failed")
                log.info("✅ Remotion render complete!")

                # Phase 4: Mix the generated Remotion visuals with Audio/BGM
                final_video = stage_assemble_documentary(script, cfg, final_video_abs, music_path)
            else:
                final_video = stage_7_assemble(script, cfg, music_path)

            qc = stage_8_qc(final_video, script, cfg)

            is_test_mode = os.environ.get("TEST_MODE", "").lower() in ("true", "1", "yes")

            if is_test_mode:
                import shutil
                test_video_path = str(WORKSPACE / "test_video.mp4")
                shutil.copy2(final_video, test_video_path)
                _save(qc, "test_visual_report.json")
                log.info(f"🧪 TEST_MODE: Saved {test_video_path} and test_visual_report.json")
            else:
                _save(qc, "qc.json")

            verdict = qc.get("verdict","approved")
            score   = qc.get("score",7)

            drive_link = stage_10_drive_backup(final_video, script, research, cfg, verdict, score)
            drive_note = f"\n📁 Drive: {drive_link}" if drive_link else ""

            if verdict == "retry" or qc.get("status") == "HARD_REJECT":
                tg(f"❌ QC {score}/10 — Rejected\n{qc.get('reason','')}{drive_note}"); return
            if verdict == "drafts":
                tg(f"⚠️ QC {score}/10 — Drafts\n{qc.get('reason','')}{drive_note}"); return
            if verdict not in ('retry', 'HARD_REJECT'):
                break
            if repair_attempt == max_repairs:
                log.error('Max repair attempts reached. Failing.')
                break




        # Calculate stats
        is_v2 = isinstance(script, dict) and "story_beats" in script
        num_scenes = 0
        total_dur = 0.0
        if is_v2:
            for beat in script.get("story_beats", []):
                for block in beat.get("narration_blocks", []):
                    for shot in block.get("shots", []):
                        num_scenes += 1
                        total_dur += float(shot.get("actual_duration", shot.get("duration_seconds", 4.0)))
        else:
            scenes = extract_scenes_list(script)
            num_scenes = len(scenes)
            total_dur = sum(s.get('actual_duration', 4.0) for s in scenes) if scenes else 0.0
            
        wan_ct = len(wan_scenes) if 'wan_scenes' in locals() else 0
        
        if is_test_mode:
            log.info("🧪 TEST_MODE: Halting before publish. Test successful.")
            url = "TEST_MODE_NO_URL"
            elapsed = int(time.time()-start)
            
            report = {
                "initial_manifest_status": stats.get("initial_status", "UNKNOWN"),
                "qc_failures_count": stats.get("qc_failures_count", 0),
                "repair_count": stats.get("repair_count", 0),
                "repaired_shot_ids": stats.get("repaired_shot_ids", []),
                "schema_repair_count": stats.get("schema_repair_count", 0),
                "final_manifest_status": stats.get("final_status", "UNKNOWN"),
                "generic_fallback_count": sum(1 for b in script.get("story_beats", []) for n in b.get("narration_blocks", []) for s in n.get("shots", []) if s.get("visual_type") == "fallback"),
                "asset_audit_passed": audit_passed if "audit_passed" in locals() else "N/A",
                "final_shot_count": num_scenes,
                "average_shot_duration": total_dur / max(num_scenes, 1)
            }
            
            import shutil
            import json
            
            with open("test_visual_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            
            if os.path.exists("remotion/test_out.mp4"):
                shutil.copy("remotion/test_out.mp4", "test_video.mp4")
                
            print("\n=== TEST_MODE REPORT ===")
            print(json.dumps(report, indent=2))
            print("========================\n")
            
        else:
            url     = stage_9_publish(final_video, script, cfg)
            elapsed = int(time.time()-start)

        tg(
            f"✅ DONE!\n\n"
            f"📺 {url}\n"
            f"⏰ {cfg['schedule']} UTC\n"
            f"🏆 QC: {score}/10\n"
            f"🎬 {num_scenes} scenes | {total_dur:.0f}s\n"
            f"✂️ Avg {total_dur/max(num_scenes,1):.1f}s/cut\n"
            f"🎥 Wan2.1: {wan_ct} clips\n"
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