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
        if text[i] == "[": depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    raise ValueError("Unbalanced JSON array")

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
#  PARSE INPUT — handles both daily auto and manual modes
# ═══════════════════════════════════════════════════════════
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
        # Strip any --genre/--lang/--duration flags that leaked in
        for pat in [r'--genre\s+\w+', r'--lang\s+\w+', r'--duration\s+\d+']:
            topic = re.sub(pat, '', topic, flags=re.IGNORECASE)
        topic = re.sub(r'\s+', ' ', topic).strip()
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
        "visual_prefix": topic,
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
    lang_note = f"Write ALL content in {lang} language." if lang != "english" else ""
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
[{{"scene":1,"voiceover":"exact words to say","visual_type":"stock_video","visual_search":"{vprefix} relevant keyword","ai_prompt":"cinematic image description","emotion":"dramatic","sfx":"{sfx_def}","duration_hint":4}}]

Rules:
- Split at natural pause/sentence boundaries
- Max 15 words per voiceover
- visual_type: "stock_video" or "ai_image" or "text_stat"
- visual_search MUST start with "{vprefix}"
- sfx: deep_impact|whoosh|click|riser|none""", max_tokens=3000)
scenes = json.loads(extract_json_array(text))
        t = 0.0
        for s in scenes:
            s["start_time"] = t; t += float(s.get("duration_hint",4))
            if vprefix.lower() not in s.get("visual_search","").lower():
                s["visual_search"] = f"{vprefix} {s.get('visual_search','')}"
        log.info(f"Stage 2: Parsed {len(scenes)} scenes from provided script")
        return scenes
    except Exception as e:
        log.warning(f"Script parse failed: {e}")
        # Fallback: split by sentences
        sentences = [s.strip() for s in re.split(r'[।\.\!\?]+', script_text) if len(s.strip()) > 10]
        t = 0.0
        scenes = []
        for i, sent in enumerate(sentences[:40]):
            vt = "text_stat" if i % 5 == 4 else "stock_video" if i % 3 == 1 else "ai_image"
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
    lang_note = f"ALL voiceover in {lang}." if lang != "english" else ""

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

    prompt = f"""You are a world-class viral Hindi YouTube scriptwriter.
Style: {style}
{lang_note}
{niche_note}

Topic: "{topic}"
Hook fact: {hook}
Hook question: {hook_q}
Key facts:
{facts_str}
Stats:
{stats_str}

Write {target} scenes. STRICT RULES:

RULE 1 — HOOK: Scene 1 = shocking opening. NEVER start with "आज हम", "नमस्ते", "दोस्तों", "In this video". Start MID-ACTION.
GOOD: "2008 में एक रात में 20,000 लोगों की नौकरी चली गई।"
BAD: "आज हम बात करेंगे..."

RULE 2 — SHORT: Max 12 words per scene voiceover.

RULE 3 — VISUAL MIX (rotate, never 3 same in row):
"stock_video" — real footage from Pexels
"ai_image" — AI generates cinematic image
"text_stat" — bold yellow text on dark background (for numbers/statistics)

RULE 4 — SEARCH TERMS: visual_search MUST start with "{vprefix}"
GOOD: "{vprefix} money crash India" or "{vprefix} dramatic night city"
BAD: "money crash" or "dramatic city"

RULE 5 — AI PROMPTS: No faces, no text, no flags, no specific monuments.
GOOD: "dark cinematic office building night dramatic lighting aerial"
BAD: "Harshad Mehta sitting in office"

RULE 6 — SFX: deep_impact=dramatic reveal | whoosh=transition | click=fact | riser=build tension | none=calm

CRITICAL: Return ONLY the raw JSON array. No reasoning, no explanation, no <think> tags, no markdown fences. Your entire response must be parseable by json.loads() directly.[{{"scene":1,"voiceover":"text in {lang}","visual_type":"stock_video","visual_search":"{vprefix} keyword","ai_prompt":"cinematic description","emotion":"dramatic","sfx":"{sfx_def}","duration_hint":4}}]"""

    try:
        text = groq(prompt, max_tokens=4000)
        script = json.loads(extract_json_array(text))
        if len(script) < 10:
            raise ValueError(f"Only {len(script)} scenes")
        t = 0.0
        for s in script:
            s["start_time"] = t; t += float(s.get("duration_hint",4))
            # Enforce topic prefix in search
            if vprefix.lower() not in s.get("visual_search","").lower():
                s["visual_search"] = f"{vprefix} {s.get('visual_search','')}"
        log.info(f"Stage 2: {len(script)} scenes written")
        return script
   except Exception as e:
        log.error(f"Stage 2 failed: {e}")
        import itertools
        facts = [f for f in ([research.get("hook","")] + research.get("key_facts",[]) + research.get("statistics",[])) if f]
        if not facts: facts = [f"{topic} के बारे में जानकारी"]
        cycled = list(itertools.islice(itertools.cycle(facts), target))
        t = 0.0; script = []
        for i,f in enumerate(cycled):
            if not f: continue
            vt = "text_stat" if i%5==4 else ("stock_video" if i%3==1 else "ai_image")
variants = ["aerial establishing shot","close-up detail shot","wide dramatic angle","low angle dramatic","office interior shot"]
            variant = variants[i % len(variants)]
            s = {"scene":i+1,"voiceover":f[:60],"visual_type":vt,
                 "visual_search":f"{vprefix} {variant}","ai_prompt":f"{variant} cinematic dramatic {topic} scene, no text, no faces",
                 "emotion":"dramatic","sfx":sfx_def,"duration_hint":4,"start_time":t}            script.append(s); t+=4
        return script

# ═══════════════════════════════════════════════════════════
#  STAGE 3 — VOICE
# ═══════════════════════════════════════════════════════════
async def _edge_tts(text, path, voice):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(path)

def stage_3_voice(script, cfg):
    lang  = cfg["lang"]
    voice = cfg.get("voice", VOICE_MAP.get(lang, VOICE_MAP["hindi"])[0])
    fallback = VOICE_MAP.get(lang, VOICE_MAP["hindi"])
    log.info(f"Stage 3: Voice ({voice})...")
    tg(f"🎙️ Generating voice...")
    audio_dir = WORKSPACE/"audio"; audio_dir.mkdir(exist_ok=True)
    for scene in script:
        n    = scene["scene"]
        text = scene.get("voiceover","").strip()
        if not text or scene.get("visual_type")=="text_stat":
            scene["audio_file"]=None; continue
        out = str(audio_dir/f"scene_{n:03d}.mp3")
        done = False
        for v in fallback:
            try:
                asyncio.run(_edge_tts(text, out, v))
                scene["audio_file"]=out; done=True; break
            except: pass
        if not done:
            try:
                from gtts import gTTS
                lc={"hindi":"hi","english":"en","spanish":"es","french":"fr","german":"de"}.get(lang,"hi")
                gTTS(text=text,lang=lc).save(out)
                scene["audio_file"]=out
            except:
                log.error(f"Scene {n}: all voice failed")
                scene["audio_file"]=None
    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 4 — MUSIC (freepd.com + incompetech — CC licensed)
# ═══════════════════════════════════════════════════════════
def stage_4_music(cfg):
    mood = cfg.get("music_mood","cinematic dramatic")
    log.info(f"Stage 4: Music ({mood})...")

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
    # Find best match
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
            log.info(f"Stage 4: Music downloaded from freepd.com")
            return music_path
    except Exception as e:
        log.warning(f"Stage 4 freepd failed: {e}")

    # Fallback: incompetech
    try:
        # Use a known working CC track
        r = requests.get("https://incompetech.filmmusic.io/song/3989-impact-prelude/download?type=mp3", timeout=30)
        if r.status_code == 200:
            with open(music_path,"wb") as f: f.write(r.content)
            log.info("Stage 4: Music from incompetech")
            return music_path
    except Exception as e:
        log.warning(f"Stage 4 incompetech failed: {e}")

    # Last resort: generate silence
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
        "-t","300","-c:a","aac",music_path], capture_output=True, timeout=30)
    return music_path

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

_sfx_cache = {}  # avoid re-downloading same SFX

def fetch_sfx(sfx_type):
    """Generate deterministic SFX tones instead of unpredictable Freesound search results."""
    if sfx_type == "none" or not sfx_type: return None
    if sfx_type in _sfx_cache: return _sfx_cache[sfx_type]

    sfx_dir = WORKSPACE/"sfx"; sfx_dir.mkdir(exist_ok=True)
    out = str(sfx_dir/f"{sfx_type}.mp3")

    presets = {
        "deep_impact": ("sine=frequency=80:duration=0.4", "volume=0.5,afade=t=out:st=0.2:d=0.2"),
        "whoosh":      ("anoisesrc=color=pink:duration=0.3", "volume=0.25,afade=t=in:d=0.05,afade=t=out:st=0.15:d=0.15,highpass=f=800"),
        "click":       ("sine=frequency=1400:duration=0.08", "volume=0.3"),
        "riser":       ("sine=frequency=200:duration=0.6", "volume=0.3,afade=t=in:d=0.5"),
    }
    src, af = presets.get(sfx_type, presets["click"])
    r = subprocess.run(["ffmpeg","-y","-f","lavfi","-i",src,"-af",af,out],
        capture_output=True, timeout=10)
    if r.returncode == 0 and os.path.exists(out):
        _sfx_cache[sfx_type] = out
        return out
    return None

    # Fallback: generate tone
    freq = {"deep_impact":"100","whoosh":"400","click":"1200","riser":"300"}.get(sfx_type,"440")
    subprocess.run(["ffmpeg","-y","-f","lavfi",
        "-i",f"sine=frequency={freq}:duration=0.5:sample_rate=44100",
        "-af","volume=0.3",out], capture_output=True, timeout=10)
    _sfx_cache[sfx_type] = out
    return out

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
    dt=[]
    for i,line in enumerate(lines[:3]):
        y=f"(h/2)-{(len(lines)//2-i)*90}"
        dt.append(f"drawtext=text='{line}':fontsize=76:fontcolor=#FFD700:x=(w-text_w)/2:y={y}:fontname=DejaVu-Sans-Bold:shadowcolor=black:shadowx=4:shadowy=4")
    vf=",".join(dt) if dt else f"drawtext=text='{safe[:20]}':fontsize=76:fontcolor=#FFD700:x=(w-text_w)/2:y=(h-text_h)/2"
    r=subprocess.run(["ffmpeg","-y","-f","lavfi",
        "-i",f"color=c=0x080808:size=1920x1080:duration={dur}:rate=25",
        "-vf",vf+",noise=alls=6:allf=t+u","-c:v","libx264","-pix_fmt","yuv420p",out],
        capture_output=True,timeout=60)
    return r.returncode==0

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
            "-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
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
                "-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
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

def build_caption_drawtext(script):
    """
    Build FFmpeg drawtext filter string.
    2-3 words at a time, lower-third position, word-by-word timing.
    Key words (numbers, capitalized) in yellow. Rest in white.
    """
    filters = []
    
    for scene in script:
        text  = scene.get("voiceover","").strip()
        dur   = scene.get("actual_duration",4.0)
        start = scene.get("start_time",0.0)
        if not text: continue
        
        words = text.split()
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur)>=3: chunks.append(" ".join(cur)); cur=[]
        if cur: chunks.append(" ".join(cur))
        
        tpc = dur/max(len(chunks),1)
        
        for j,chunk in enumerate(chunks):
            cs = start + j*tpc
            ce = cs + tpc - 0.05
            
            # Detect key words (numbers, caps) for yellow
            has_key = bool(re.search(r'\d', chunk)) or any(
                w[0].isupper() and len(w)>2 for w in chunk.split() if w
            )
            color = "#FFD700" if has_key else "white"
            
            safe = re.sub(r"[':\"\\%\[\]{}|]","",chunk)
            
            # Lower third: 75% down the screen
            # Size 28, bold, black outline
            dt = (f"drawtext=text='{safe}':"
                  f"fontsize=28:fontcolor={color}:"
                  f"x=(w-text_w)/2:y=h*0.75:"
                  f"fontfile=/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf:" 
                  f"borderw=4:bordercolor=black:"
                  f"enable='between(t,{cs:.3f},{ce:.3f})'")
            filters.append(dt)
    
    return ",".join(filters) if filters else "null"

def stage_7_assemble(script, cfg, music_path):
    log.info("Stage 7: Assembling...")
    tg("🎞️ Final assembly...")
    asm=WORKSPACE/"assembly"; asm.mkdir(exist_ok=True)

    # Step 1: Merge video+voice per scene, add SFX
    scene_files=[]
    cur_time=0.0

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
            # Mix voice + SFX — use .m4a container to match aac codec
            mixed_audio = str(asm/f"audio_{n:03d}.m4a")
            mix_result = subprocess.run(["ffmpeg","-y",
                "-i",os.path.abspath(audio),
                "-i",os.path.abspath(sfx_file),
                "-filter_complex","[0:a]volume=1.0[v];[1:a]volume=0.4[s];[v][s]amix=inputs=2:duration=first",
                "-c:a","aac",mixed_audio],capture_output=True,timeout=30)
            if mix_result.returncode != 0 or not os.path.exists(mixed_audio):
                log.warning(f"  SFX mix failed for scene {n}, using voice only")
                mixed_audio = audio  # fallback to plain voice
            cmd=["ffmpeg","-y","-i",os.path.abspath(video),"-i",mixed_audio,
                 "-t",str(dur),"-c:v","libx264","-c:a","aac",
                 "-map","0:v:0","-map","1:a:0","-shortest","-preset","fast",out]
        elif audio:
            cmd=["ffmpeg","-y","-i",os.path.abspath(video),"-i",os.path.abspath(audio),
                 "-t",str(dur),"-c:v","libx264","-c:a","aac",
                 "-map","0:v:0","-map","1:a:0","-shortest","-preset","fast",out]
        else:
            cmd=["ffmpeg","-y","-i",os.path.abspath(video),
                 "-t",str(dur),"-c:v","libx264","-preset","fast","-an",out]

        r=subprocess.run(cmd,capture_output=True,timeout=180)
        if r.returncode==0 and os.path.exists(out):
            scene_files.append(out); cur_time+=dur
        else:
            log.warning(f"Scene {n} merge failed: {r.stderr.decode()[-80:]}")

    if not scene_files: raise RuntimeError("No scenes assembled!")

    # Step 2: Concat all scenes
    cfile=str(asm/"concat.txt")
    with open(cfile,"w") as f:
        for sf in scene_files: f.write(f"file '{os.path.abspath(sf)}'\n")

    raw=str(WORKSPACE/"raw.mp4")
    r=subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",cfile,
        "-c:v","libx264","-c:a","aac","-movflags","+faststart","-preset","fast",raw],
        capture_output=True,timeout=600)
    if r.returncode!=0: raise RuntimeError(f"Concat failed: {r.stderr.decode()[-200:]}")

    # Apply genre-specific color grade
    grade = cfg.get("color_grade","cinematic")
    grade_filters = {
        "teal_orange": "curves=r='0/0 0.5/0.4 1/0.95':b='0/0.1 0.5/0.5 1/0.9',eq=saturation=1.15:contrast=1.1",
        "cool_blue":   "curves=b='0/0.1 0.5/0.6 1/1':eq=saturation=0.9:contrast=1.05",
        "dark_noir":   "eq=saturation=0.6:contrast=1.3:brightness=-0.05",
        "cinematic":   "eq=saturation=1.05:contrast=1.15:gamma=0.95",
    }
    gf = grade_filters.get(grade, grade_filters["cinematic"])
    graded = str(WORKSPACE/"graded.mp4")
    r = subprocess.run(["ffmpeg","-y","-i",raw,"-vf",gf,"-c:v","libx264","-c:a","copy","-preset","fast",graded],
        capture_output=True, timeout=300)
    if r.returncode == 0 and os.path.exists(graded):
        raw = graded
    # Step 3: Mix background music at -18dB
    with_music=str(WORKSPACE/"with_music.mp4")
    total_dur = sum(s.get("actual_duration",4) for s in script)
    if music_path and os.path.exists(music_path):
        subprocess.run(["ffmpeg","-y","-i",raw,"-stream_loop","-1","-i",music_path,
            "-filter_complex",f"[1:a]volume=0.12,atrim=0:{total_dur}[m];[0:a][m]amix=inputs=2:duration=first[a]",
            "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-shortest",with_music],
            capture_output=True,timeout=600)
        if os.path.exists(with_music): shutil.copy(with_music, raw)

    # Step 4: Add captions (drawtext — lower third, 2-3 words, synced)
    final=str(WORKSPACE/"final_video.mp4")
    caption_filter = build_caption_drawtext(script)

    if caption_filter != "null":
        r=subprocess.run(["ffmpeg","-y","-i",raw,
            "-vf",caption_filter,
            "-c:v","libx264","-c:a","copy","-preset","fast",final],
            capture_output=True,timeout=600)
        if r.returncode!=0:
            log.warning(f"Caption failed: {r.stderr.decode()[-200:]}. Using raw.")
            shutil.copy(raw,final)
    else:
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

    # Generate metadata
    try:
        hook = script[0].get("voiceover","") if script else ""
        niche_tag = f"#{niche}Hindi #Hindi{niche.capitalize()}" if niche else ""
        meta_text = groq(f"""YouTube metadata for {lang} {genre} video.
Topic: "{topic}"
Niche: {niche}
Hook: "{hook}"
Return ONLY JSON:
{{"title":"viral {lang} title under 60 chars with power word",
  "description":"3 engaging paragraphs in {lang} with keywords. Add income disclaimer if finance.",
  "tags":["{topic}","hindi","{niche}","viral","facts"],
  "hashtags":"#{topic.replace(' ','')} #hindi #{niche} #viral"
}}""", max_tokens=400)
        meta_text=meta_text.replace("```json","").replace("```","").strip()
        meta=json.loads(meta_text)
    except:
        meta={"title":f"{topic} — पूरी सच्चाई",
              "description":f"{topic} के बारे में पूरी जानकारी।",
              "tags":[topic,"hindi",niche or "facts"],"hashtags":f"#{topic.replace(' ','')} #hindi"}

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
              "tags":meta.get("tags",[topic]),"categoryId":"28"},
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
    Returns dict: {scene_number: local_video_path}
    """
    if not scenes_needing_video:
        return {}

    colab_token = os.environ.get("COLAB_TOKEN", "")
    if not colab_token:
        log.warning("COLAB_TOKEN not set — skipping Wan2.1, using Pollinations instead")
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
        # Install Colab CLI (if not already installed)
        subprocess.run(["pip", "install", "-q", "google-colab-cli"],
            capture_output=True, timeout=60)

        # Authenticate
        env = os.environ.copy()
        env["COLAB_TOKEN"] = colab_token

        # Provision T4 GPU, run generator, download clips, stop
        # Using colab run which handles full lifecycle automatically
        result = subprocess.run([
            "colab", "run", "--gpu", "T4",
            "--upload", f"{prompts_file}:/content/scene_prompts.json",
            "--upload", "wan21_generator.py:/content/wan21_generator.py",
            "--download", "/content/clips/:./wan_clips/",
            "--download", "/content/wan21_results.json:./wan21_results.json",
            "wan21_generator.py"
        ], capture_output=True, text=True, timeout=1800, env=env)  # 30 min max

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
    Generate one video clip via Kling API.
    Returns local file path or None.
    Uses klingapi.com (official Kling developer API).
    """
    kling_key = os.environ.get("KLING_API_KEY", "")
    if not kling_key:
        return None

    out_path = str(WORKSPACE / "visuals" / f"kling_{scene_num:03d}.mp4")

    try:
        BASE = "https://api.klingapi.com"

        # Submit generation task
        resp = requests.post(f"{BASE}/v1/videos/text2video",
            headers={"Authorization": f"Bearer {kling_key}",
                     "Content-Type": "application/json"},
            json={"model": "kling-v2.6-pro" if mode=="pro" else "kling-v2.6",
                  "prompt": prompt,
                  "negative_prompt": "blurry, ugly, text, watermark, faces, deformed",
                  "duration": duration,
                  "aspect_ratio": "16:9",
                  "mode": mode},
            timeout=30)

        if resp.status_code != 200:
            log.warning(f"Kling submit failed: {resp.status_code} {resp.text[:200]}")
            return None

        task_id = resp.json().get("task_id")
        if not task_id:
            log.warning(f"Kling: no task_id in response")
            return None

        log.info(f"  Kling task {task_id} submitted, polling...")

        # Poll for result (max 5 minutes)
        for attempt in range(60):
            time.sleep(5)
            poll = requests.get(f"{BASE}/v1/videos/text2video/{task_id}",
                headers={"Authorization": f"Bearer {kling_key}"},
                timeout=15)

            if poll.status_code != 200:
                continue

            data   = poll.json()
            status = data.get("status", "")

            if status == "completed":
                video_url = data.get("video_url", "") or data.get("url","")
                if video_url:
                    r = requests.get(video_url, stream=True, timeout=60)
                    with open(out_path, "wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    log.info(f"  Kling scene {scene_num}: ✓ ({os.path.getsize(out_path)//1024}KB)")
                    return out_path
                break
            elif status in ("failed", "error"):
                log.warning(f"  Kling task failed: {data.get('error','')}")
                break
            else:
                log.info(f"  Kling {task_id}: {status} (attempt {attempt+1}/60)")

    except Exception as e:
        log.warning(f"  Kling scene {scene_num}: {e}")

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
        if genre in ("cartoon",) and os.environ.get("COLAB_TOKEN"):
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

        if verdict == "retry":
            tg(f"❌ QC {score}/10 — Rejected\n{qc.get('reason','')}"); return
        if verdict == "drafts":
            tg(f"⚠️ QC {score}/10 — Drafts\n{qc.get('reason','')}"); return

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
            f"⚡ {elapsed}s total"
        )

    except Exception as e:
        import traceback
        log.error(f"CRASH: {e}\n{traceback.format_exc()}")
        tg(f"💥 Crashed: {str(e)[:250]}")
        raise


# Override main entry point to use v5.1
if __name__ == "__main__":
    run_pipeline_v51()
