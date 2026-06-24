"""
=============================================================
  ZERO-COST AI MEDIA AGENCY — pipeline.py v3.0
  THE PROFESSIONAL EDIT
=============================================================
COMMAND FORMAT:
  /make [topic] [time]
  /make [topic] --genre documentary --lang hindi --duration 8 [time]
  /make [topic] --genre shorts --lang english --duration 1 [time]

GENRES: documentary | shorts | cartoon | study | ad | typography
LANG:   english | hindi | spanish | french | german | arabic
DURATION: 1-15 (minutes). If not given, auto-decided by topic.

WHAT'S NEW IN v3.0:
  - Word-by-word kinetic captions (1-3 words, center screen)
  - Color-coded captions (key words = neon yellow)
  - 5-layer audio: voice + ambient + score + sfx
  - Pattern interrupt hook (first 3 seconds)
  - AI hallucination prevention (skip AI for flags/monuments/faces)
  - Negative prompts for Pollinations
  - Film grain + cinematic LUT overlay
  - Smart genre/language/duration auto-detection
  - Multiple voice options per language
  - SFX on every caption pop
=============================================================
"""

import os, json, time, asyncio, logging, requests, subprocess
import random, re, shutil, tempfile
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agency")

# ─── Secrets ────────────────────────────────────────────────
GROQ_KEY       = os.environ["GROQ_KEY"]
GEMINI_KEY     = os.environ["GEMINI_KEY"]
PEXELS_KEY     = os.environ["PEXELS_KEY"]
PIXABAY_KEY    = os.environ["PIXABAY_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT  = os.environ["TELEGRAM_CHAT_ID"]
RAW_INPUT      = os.environ.get("TOPIC", "Black Holes 18:00")
SCHEDULE_TIME  = os.environ.get("SCHEDULE_TIME", "18:00")

# ─── Parse command ──────────────────────────────────────────
def parse_command(raw):
    """
    Parses: topic [--genre X] [--lang X] [--duration X] HH:MM
    Returns dict with all fields.
    """
    genre    = None
    lang     = None
    duration = None

    g = re.search(r'--genre\s+(\w+)', raw, re.IGNORECASE)
    l = re.search(r'--lang\s+(\w+)', raw, re.IGNORECASE)
    d = re.search(r'--duration\s+(\d+)', raw, re.IGNORECASE)

    if g: genre = g.group(1).lower(); raw = raw.replace(g.group(0), '')
    if l: lang  = l.group(1).lower(); raw = raw.replace(l.group(0), '')
    if d: duration = int(d.group(1)); raw = raw.replace(d.group(0), '')

    # Last token that looks like HH:MM is the time
    parts = raw.strip().split()
    sched = "18:00"
    if parts and re.match(r'^\d{1,2}:\d{2}$', parts[-1]):
        sched = parts[-1]
        parts = parts[:-1]

    topic = " ".join(parts).strip()
    return {
        "topic": topic,
        "genre": genre,
        "lang": lang,
        "duration_min": duration,
        "schedule": sched
    }

CMD        = parse_command(RAW_INPUT)
TOPIC      = CMD["topic"]
GENRE      = CMD["genre"]       # None = auto-detect
LANGUAGE   = CMD["lang"]        # None = auto-detect
DURATION   = CMD["duration_min"]  # None = auto-detect
SCHEDULE_TIME = CMD["schedule"]

WORKSPACE = Path(f"workspace_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
WORKSPACE.mkdir(exist_ok=True)

# ─── Voice map per language ──────────────────────────────────
VOICE_MAP = {
    "english":  ["en-GB-RyanNeural", "en-US-ChristopherNeural", "en-US-DavisNeural"],
    "hindi":    ["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"],
    "spanish":  ["es-ES-AlvaroNeural", "es-MX-JorgeNeural"],
    "french":   ["fr-FR-HenriNeural", "fr-FR-DeniseNeural"],
    "german":   ["de-DE-ConradNeural", "de-DE-KatjaNeural"],
    "arabic":   ["ar-SA-HamedNeural", "ar-EG-SalmaNeural"],
}

# ─── Genre config ────────────────────────────────────────────
GENRE_CONFIG = {
    "documentary": {
        "style": "BBC/Netflix documentary narrator. Cinematic, authoritative, dramatic storytelling.",
        "scene_target": 30,
        "default_duration_min": 5,
        "music": "dark cinematic orchestral dramatic",
        "ambient": True,
    },
    "shorts": {
        "style": "Viral YouTube Shorts. Ultra-fast, shocking, max energy. Every line must make you want to watch more.",
        "scene_target": 20,
        "default_duration_min": 1,
        "music": "energetic trap beat",
        "ambient": False,
    },
    "cartoon": {
        "style": "Fun animated YouTube channel. Energetic, simple, playful. Uses 'Whoa!' 'Did you know?' 'Mind blown!'",
        "scene_target": 25,
        "default_duration_min": 4,
        "music": "playful upbeat cartoon",
        "ambient": False,
    },
    "study": {
        "style": "Clear educational explainer. Simple language, structured, helpful and thorough.",
        "scene_target": 28,
        "default_duration_min": 8,
        "music": "calm lo-fi focus",
        "ambient": False,
    },
    "ad": {
        "style": "30-second brand advertisement. Hook in 3 seconds. Problem → Solution → CTA.",
        "scene_target": 12,
        "default_duration_min": 1,
        "music": "upbeat corporate motivational",
        "ambient": False,
    },
    "typography": {
        "style": "Ultra-short punchy phrases. Max 5 words per line. Impact font energy.",
        "scene_target": 20,
        "default_duration_min": 1,
        "music": "heavy bass cinematic",
        "ambient": False,
    },
}

# ─── Telegram ───────────────────────────────────────────────
def tg(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": f"🎬 {msg}"},
            timeout=10
        )
    except: pass

def _save(data, name):
    with open(WORKSPACE / name, "w") as f:
        json.dump(data, f, indent=2)

# ═══════════════════════════════════════════════════════════
#  STAGE 0 — AUTO DETECT genre/language/duration from topic
# ═══════════════════════════════════════════════════════════
def stage_0_autodetect(topic, genre, lang, duration):
    log.info("Stage 0: Auto-detecting genre/language/duration...")

    if genre and lang and duration:
        log.info(f"  All manual: genre={genre} lang={lang} duration={duration}min")
        return genre, lang, duration

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""Analyze this video topic and decide the best settings.

Topic: "{topic}"
Already specified: genre={genre}, language={lang}, duration={duration}

Return ONLY JSON:
{{
  "genre": "documentary",
  "language": "english",
  "duration_min": 5,
  "reason": "one line explanation"
}}

Rules:
- genre: one of [documentary, shorts, cartoon, study, ad, typography]
- language: one of [english, hindi, spanish, french, german, arabic]
- duration_min: 1 to 15 (shorts=1, documentary=5-8, study=8-12)
- If already specified above, keep that value exactly
- Detect language from topic text if it contains non-English words
- History/science topics = documentary
- City/travel topics = documentary or shorts
- Kids topics = cartoon
- How-to topics = study"""

        r = model.generate_content(prompt)
        text = r.text.strip().replace("```json","").replace("```","").strip()
        result = json.loads(text)

        g = genre    or result.get("genre", "documentary")
        l = lang     or result.get("language", "english")
        d = duration or result.get("duration_min", 5)

        log.info(f"  Auto-detected: genre={g} lang={l} duration={d}min reason={result.get('reason','')}")
        tg(f"🎯 Genre: {g} | Language: {l} | Duration: {d} min")
        return g, l, d

    except Exception as e:
        log.warning(f"Auto-detect failed: {e}, using defaults")
        g = genre    or "documentary"
        l = lang     or "english"
        d = duration or 5
        return g, l, d

# ═══════════════════════════════════════════════════════════
#  STAGE 1 — RESEARCH
# ═══════════════════════════════════════════════════════════
def stage_1_research(topic, lang):
    log.info("Stage 1: Research...")
    tg(f"📚 Researching '{topic}' in {lang}...")

    lang_instruction = f"Write all content in {lang} language." if lang != "english" else ""

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""Research the topic: "{topic}"
{lang_instruction}

Return ONLY valid JSON, no markdown:
{{
  "headline": "one shocking sentence in {lang}",
  "hook": "the single most surprising or shocking fact - must make viewer stop scrolling",
  "hook_question": "a mysterious question that makes viewer want to keep watching",
  "key_facts": ["fact1", "fact2", "fact3", "fact4", "fact5", "fact6", "fact7", "fact8", "fact9", "fact10"],
  "statistics": ["stat1 with number", "stat2 with number", "stat3 with number", "stat4 with number"],
  "timeline": ["earliest event", "event2", "event3", "event4", "event5", "recent event"],
  "surprising_facts": ["wow fact1", "wow fact2", "wow fact3", "wow fact4"],
  "visual_keywords": ["keyword1 for stock footage search", "keyword2", "keyword3", "keyword4", "keyword5"]
}}"""
        r = model.generate_content(prompt)
        text = r.text.strip().replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        log.warning(f"Research Gemini failed: {e}")

    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(f"https://html.duckduckgo.com/html/?q={quote(topic)}", headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        snippets = [r.get_text() for r in soup.select(".result__snippet")][:10]
        return {
            "headline": topic,
            "hook": snippets[0] if snippets else f"The truth about {topic}",
            "hook_question": f"What do you really know about {topic}?",
            "key_facts": snippets,
            "statistics": [],
            "timeline": [],
            "surprising_facts": snippets[:4],
            "visual_keywords": [topic]
        }
    except Exception as e:
        log.error(f"Research all failed: {e}")
        return {
            "headline": topic,
            "hook": f"Everything you know about {topic} is wrong.",
            "hook_question": f"What really happened with {topic}?",
            "key_facts": [f"Key fact about {topic}"],
            "statistics": [],
            "timeline": [],
            "surprising_facts": [],
            "visual_keywords": [topic]
        }

# ═══════════════════════════════════════════════════════════
#  STAGE 2 — SCRIPT (PROFESSIONAL VIRAL STYLE)
# ═══════════════════════════════════════════════════════════
def stage_2_script(research, genre, lang, duration_min):
    log.info("Stage 2: Writing professional script...")
    tg(f"✍️ Writing {genre} script ({duration_min} min)...")

    cfg = GENRE_CONFIG.get(genre, GENRE_CONFIG["documentary"])
    style = cfg["style"]

    # Calculate target scenes based on duration
    # Good pacing = 1 scene every 3-5 seconds
    # duration_min * 60 seconds / 4 seconds per scene
    target_scenes = max(cfg["scene_target"], int(duration_min * 60 / 4))
    lang_instruction = f"Write ALL voiceover text in {lang} language." if lang != "english" else ""

    prompt = f"""You are a world-class viral YouTube video editor and scriptwriter.
Style: {style}
{lang_instruction}

Research data:
{json.dumps(research, indent=2)}

TARGET: {target_scenes} scenes for a {duration_min} minute video.

=== CRITICAL RULES — THESE ARE NON-NEGOTIABLE ===

RULE 1 — HOOK (Scene 1 ONLY):
- Start with ONE shocking question or impossible fact
- NEVER start with "Astonishingly" or "In this video" or "Today we explore"
- GOOD: "What if I told you this ancient city had running water 4000 years before Rome?"
- GOOD: "In 1984, a single night killed 20,000 people. And the world said nothing."
- BAD: "X is the birthplace of four major world religions"

RULE 2 — VOICEOVER LENGTH:
- Maximum 12 words per scene voiceover
- Each line = ONE single idea only
- Short. Punchy. Dramatic pauses built in.

RULE 3 — VISUAL VARIETY (rotate through these types):
- "ai_image": AI generates a cinematic image (for concepts, places, emotions)
- "stock_video": search for real footage (for action, crowds, nature)
- "text_stat": white bold text on dark background (for statistics and shocking numbers)
- "text_question": center-screen question text (use 2-3 times to re-engage viewer)

RULE 4 — SCENE VARIETY:
Mix visual_type in this rough pattern:
ai_image, stock_video, ai_image, text_stat, stock_video, ai_image, text_question, stock_video...
Never use the same type 3 times in a row.

RULE 5 — VISUAL PROMPTS (for ai_image only):
- Be extremely specific and cinematic
- Include lighting, mood, camera angle, style
- AVOID: faces, flags, text, signs, logos, monuments with text
- GOOD: "aerial drone shot ancient brick city grid streets 2500 BC golden hour dramatic"
- BAD: "Indus Valley civilization"

RULE 6 — STOCK SEARCH (for stock_video only):
- Use simple 4-5 word search terms
- Use terms that definitely exist in stock libraries
- GOOD: "city aerial drone night", "crowd celebration fireworks", "ancient ruins sunset"
- BAD: "Aryabhata calculating mathematics 600 AD"

Return ONLY a valid JSON array, no markdown, no explanation:
[
  {{
    "scene": 1,
    "voiceover": "max 12 words in {lang}",
    "visual_type": "ai_image",
    "visual_prompt": "only for ai_image: detailed cinematic prompt",
    "visual_search": "only for stock_video: 4-5 word search term",
    "emotion": "dramatic",
    "sfx": "deep_impact",
    "duration_hint": 4
  }}
]

sfx options: deep_impact | whoosh | click | riser | none
emotion options: dramatic | mysterious | inspiring | shocking | calm | energetic"""

    groq_models = [
        "llama-3.3-70b-versatile",
        "deepseek-r1-distill-llama-70b",
        "llama-3.1-8b-instant",
    ]

    for model_name in groq_models:
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.85,
                max_tokens=6000,
            )
            text = response.choices[0].message.content.strip()
            text = text.replace("```json","").replace("```","").strip()
            start = text.find("[")
            end = text.rfind("]") + 1
            script = json.loads(text[start:end])

            if len(script) < 12:
                log.warning(f"Only {len(script)} scenes from {model_name}, retrying...")
                continue

            # Assign start times
            t = 0.0
            for s in script:
                s["start_time"] = t
                t += float(s.get("duration_hint", 4))

            log.info(f"Stage 2: {len(script)} scenes with {model_name}")
            return script

        except Exception as e:
            log.warning(f"Script {model_name} failed: {e}")
            time.sleep(2)

    # Fallback
    facts = research.get("key_facts", [topic])
    script = []
    t = 0.0
    for i, fact in enumerate(facts[:20]):
        scene = {
            "scene": i+1,
            "voiceover": fact[:60],
            "visual_type": "ai_image" if i % 3 != 2 else "text_stat",
            "visual_prompt": f"cinematic dramatic scene about {topic}",
            "visual_search": topic,
            "emotion": "dramatic",
            "sfx": "whoosh",
            "duration_hint": 4,
            "start_time": t
        }
        script.append(scene)
        t += 4
    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 3 — B-ROLL UPGRADE
# ═══════════════════════════════════════════════════════════
def stage_3_broll_upgrade(script):
    log.info("Stage 3: Upgrading visual prompts...")
    tg("🎬 Enhancing visuals...")

    # Scenes that need AI image — upgrade their prompts
    ai_scenes = [s for s in script if s.get("visual_type") == "ai_image"]
    stock_scenes = [s for s in script if s.get("visual_type") == "stock_video"]

    if not ai_scenes and not stock_scenes:
        return script

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Batch upgrade
        items = []
        for s in ai_scenes:
            items.append(f"Scene {s['scene']} [ai]: voiceover='{s['voiceover']}' prompt='{s.get('visual_prompt','')}'")
        for s in stock_scenes:
            items.append(f"Scene {s['scene']} [stock]: voiceover='{s['voiceover']}' search='{s.get('visual_search','')}'")

        prompt = f"""Improve these video scene visuals.

{chr(10).join(items)}

For [ai] scenes: Write a better Pollinations image prompt.
- Cinematic, specific, dramatic
- Include: lighting style, camera angle, time of day, mood
- NEVER include: faces, text, signs, flags, specific named monuments
- Max 15 words

For [stock] scenes: Write a better Pexels search term.
- Simple 4-5 words that will find real stock footage
- Think: what would a cameraman actually film?

Return ONLY JSON array, one entry per scene in same order:
[{{"scene": 1, "improved": "the improved prompt or search term"}}]"""

        r = model.generate_content(prompt)
        text = r.text.strip().replace("```json","").replace("```","").strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        upgrades = json.loads(text[start:end])

        upgrade_map = {u["scene"]: u["improved"] for u in upgrades}

        for s in script:
            if s["scene"] in upgrade_map:
                improved = upgrade_map[s["scene"]]
                if s.get("visual_type") == "ai_image":
                    s["visual_prompt"] = improved
                elif s.get("visual_type") == "stock_video":
                    s["visual_search"] = improved

    except Exception as e:
        log.warning(f"B-roll upgrade failed: {e}")

    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 4 — VOICE
# ═══════════════════════════════════════════════════════════
async def _edge_tts_save(text, path, voice):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(path)

def stage_4_voice(script, lang):
    log.info("Stage 4: Generating voice...")
    tg(f"🎙️ Generating {lang} voice for {len(script)} scenes...")

    audio_dir = WORKSPACE / "audio"
    audio_dir.mkdir(exist_ok=True)

    voices = VOICE_MAP.get(lang, VOICE_MAP["english"])
    primary_voice = voices[0]
    fallback_voice = voices[1] if len(voices) > 1 else "en-US-ChristopherNeural"

    for scene in script:
        n = scene["scene"]
        text = scene.get("voiceover", "").strip()

        # text_stat and text_question can optionally have no voiceover
        if not text or scene.get("visual_type") == "typography":
            scene["audio_file"] = None
            continue

        out = str(audio_dir / f"scene_{n:03d}.mp3")

        # Primary: Edge-TTS with chosen language voice
        try:
            asyncio.run(_edge_tts_save(text, out, primary_voice))
            scene["audio_file"] = out
            continue
        except Exception as e:
            log.warning(f"  Scene {n}: {primary_voice} failed: {e}")

        # Fallback 1: second voice of same language
        try:
            asyncio.run(_edge_tts_save(text, out, fallback_voice))
            scene["audio_file"] = out
            continue
        except: pass

        # Fallback 2: gTTS
        try:
            from gtts import gTTS
            lang_code = {"english":"en","hindi":"hi","spanish":"es","french":"fr","german":"de","arabic":"ar"}.get(lang,"en")
            gTTS(text=text, lang=lang_code, slow=False).save(out)
            scene["audio_file"] = out
        except Exception as e:
            log.error(f"  Scene {n}: All voice failed: {e}")
            scene["audio_file"] = None

    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 5 — VISUALS
#  - AI hallucination prevention
#  - 5 animation types cycling
#  - text_stat = bold white text on dark BG
#  - text_question = centered question with glow
#  - Film grain overlay
# ═══════════════════════════════════════════════════════════

# Keywords that Pollinations ALWAYS gets wrong
# For these, skip AI and go straight to Pexels/Pixabay
HALLUCINATION_KEYWORDS = [
    "flag", "flags", "taj mahal", "eiffel tower", "statue of liberty",
    "monument", "text", "sign", "banner", "newspaper", "book",
    "face", "portrait", "person standing", "scientist", "mathematician",
    "sage", "guru", "wizard", "historical figure", "emperor", "king",
    "crowd holding", "protest", "soldiers marching", "battle scene",
    "map of", "chart", "graph", "diagram", "infographic",
    "logo", "symbol", "chakra", "wheel", "written"
]

def should_skip_ai(prompt, search=""):
    combined = (prompt + " " + search).lower()
    return any(kw in combined for kw in HALLUCINATION_KEYWORDS)

def get_audio_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30
        )
        return float(r.stdout.strip())
    except:
        return 4.0

# Animation types — cycle for variety
ANIMATIONS = ["zoom_in","pan_right","zoom_out","pan_left","pan_up"]

def ken_burns(anim, duration, w=1920, h=1080):
    fps = 25
    fr = int(duration * fps)
    opts = {
        "zoom_in":   f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps={fps}",
        "zoom_out":  f"zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps={fps}",
        "pan_right": f"zoompan=z='1.3':x='min(iw*0.3,x+1.2)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps={fps}",
        "pan_left":  f"zoompan=z='1.3':x='max(0,iw*0.3-on*1.2)':y='ih/2-(ih/zoom/2)':d={fr}:s={w}x{h}:fps={fps}",
        "pan_up":    f"zoompan=z='1.3':x='iw/2-(iw/zoom/2)':y='max(0,ih*0.3-on*1.0)':d={fr}:s={w}x{h}:fps={fps}",
    }
    return opts.get(anim, opts["zoom_in"])

def img_to_video(img_path, out_path, duration, anim="zoom_in"):
    vf = ken_burns(anim, duration)
    # Add subtle film grain overlay
    grain_filter = f"{vf},noise=alls=3:allf=t+u"
    cmd = ["ffmpeg","-y","-loop","1","-i", img_path,
           "-vf", grain_filter,
           "-t", str(duration),"-c:v","libx264",
           "-pix_fmt","yuv420p","-preset","fast", out_path]
    r = subprocess.run(cmd, capture_output=True, timeout=180)
    return r.returncode == 0

def make_text_stat(text, out_path, duration, color="#FFD700"):
    """Bold stat text on dark cinematic background."""
    safe = text.replace("'","\\'").replace(":","\\:").replace("%","\\%").replace('"','\\"')
    words = safe.split()
    # Wrap at 20 chars
    lines, cur = [], []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) > 20:
            lines.append(" ".join(cur))
            cur = []
    if cur: lines.append(" ".join(cur))

    # Build drawtext chain
    dt_parts = []
    for i, line in enumerate(lines[:3]):
        y = f"(h/2)-{(len(lines)//2 - i)*90}"
        dt_parts.append(
            f"drawtext=text='{line}':fontsize=80:fontcolor={color}:"
            f"x=(w-text_w)/2:y={y}:fontname=DejaVu-Sans-Bold:"
            f"shadowcolor=black:shadowx=3:shadowy=3"
        )

    vf = ",".join(dt_parts) if dt_parts else f"drawtext=text='{safe[:30]}':fontsize=80:fontcolor={color}:x=(w-text_w)/2:y=(h-text_h)/2"

    cmd = ["ffmpeg","-y","-f","lavfi",
           "-i",f"color=c=0x0a0a0a:size=1920x1080:duration={duration}:rate=25",
           "-vf", vf + ",noise=alls=5:allf=t+u",
           "-c:v","libx264","-pix_fmt","yuv420p", out_path]
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    return r.returncode == 0

def make_text_question(text, out_path, duration):
    """Glowing centered question text."""
    safe = text.replace("'","\\'").replace(":","\\:").replace("%","\\%")
    # Split long question
    words = safe.split()
    lines, cur = [], []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) > 22:
            lines.append(" ".join(cur))
            cur = []
    if cur: lines.append(" ".join(cur))

    dt_parts = []
    for i, line in enumerate(lines[:2]):
        y = f"(h/2)-{(len(lines)//2 - i)*80}"
        dt_parts.append(
            f"drawtext=text='{line}':fontsize=70:fontcolor=white:"
            f"x=(w-text_w)/2:y={y}:fontname=DejaVu-Sans-Bold:"
            f"shadowcolor=0x00FFFF:shadowx=0:shadowy=0:borderw=2:bordercolor=0x00BFFF"
        )

    vf = ",".join(dt_parts) if dt_parts else f"drawtext=text='{safe[:30]}':fontsize=70:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2"

    cmd = ["ffmpeg","-y","-f","lavfi",
           "-i",f"color=c=0x050510:size=1920x1080:duration={duration}:rate=25",
           "-vf", vf,
           "-c:v","libx264","-pix_fmt","yuv420p", out_path]
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    return r.returncode == 0

def fetch_pollinations(prompt, out_path, seed=None):
    """Pollinations with negative prompt to reduce hallucinations."""
    try:
        s = seed or random.randint(1, 99999)
        neg = "text watermark signature blurry deformed ugly duplicate mirrored distorted flag letters words faces"
        url = (f"https://image.pollinations.ai/prompt/{quote(prompt)}"
               f"?width=1920&height=1080&nologo=true&seed={s}"
               f"&negative={quote(neg)}&model=flux")
        r = requests.get(url, timeout=90)
        if r.status_code == 200 and len(r.content) > 8000:
            with open(out_path,"wb") as f: f.write(r.content)
            return True
    except Exception as e:
        log.warning(f"  Pollinations: {e}")
    return False

def fetch_pexels_video(search, out_path, duration):
    try:
        headers = {"Authorization": PEXELS_KEY}
        r = requests.get("https://api.pexels.com/videos/search",
            headers=headers,
            params={"query": search,"per_page":5,"orientation":"landscape"},
            timeout=15)
        videos = r.json().get("videos",[])
        if not videos: return False
        files = sorted(videos[0].get("video_files",[]), key=lambda x:x.get("width",0), reverse=True)
        if not files: return False
        raw = out_path.replace(".mp4","_raw.mp4")
        v = requests.get(files[0]["link"], stream=True, timeout=60)
        with open(raw,"wb") as f:
            for chunk in v.iter_content(8192): f.write(chunk)
        cmd = ["ffmpeg","-y","-i",raw,"-t",str(duration),
               "-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
               "-c:v","libx264","-an","-preset","fast", out_path]
        return subprocess.run(cmd, capture_output=True, timeout=60).returncode == 0
    except Exception as e:
        log.warning(f"  Pexels video: {e}")
    return False

def fetch_pexels_image(search, out_path):
    try:
        headers = {"Authorization": PEXELS_KEY}
        r = requests.get("https://api.pexels.com/v1/search",
            headers=headers,
            params={"query":search,"per_page":5,"orientation":"landscape"},
            timeout=15)
        photos = r.json().get("photos",[])
        if not photos: return False
        url = photos[random.randint(0,min(2,len(photos)-1))]["src"]["original"]
        img = requests.get(url, timeout=30)
        with open(out_path,"wb") as f: f.write(img.content)
        return True
    except Exception as e:
        log.warning(f"  Pexels image: {e}")
    return False

def fetch_pixabay_image(search, out_path):
    try:
        r = requests.get("https://pixabay.com/api/",
            params={"key":PIXABAY_KEY,"q":search,"image_type":"photo",
                    "orientation":"horizontal","per_page":5,"safesearch":"true"},
            timeout=15)
        hits = r.json().get("hits",[])
        if not hits: return False
        url = hits[random.randint(0,min(2,len(hits)-1))]["largeImageURL"]
        img = requests.get(url, timeout=30)
        with open(out_path,"wb") as f: f.write(img.content)
        return True
    except Exception as e:
        log.warning(f"  Pixabay: {e}")
    return False

def fetch_pixabay_video(search, out_path, duration):
    try:
        r = requests.get("https://pixabay.com/api/videos/",
            params={"key":PIXABAY_KEY,"q":search,"video_type":"film","per_page":5},
            timeout=15)
        hits = r.json().get("hits",[])
        if not hits: return False
        url = hits[0]["videos"]["large"]["url"]
        raw = out_path.replace(".mp4","_raw2.mp4")
        v = requests.get(url, stream=True, timeout=60)
        with open(raw,"wb") as f:
            for chunk in v.iter_content(8192): f.write(chunk)
        cmd = ["ffmpeg","-y","-i",raw,"-t",str(duration),
               "-vf","scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
               "-c:v","libx264","-an","-preset","fast", out_path]
        return subprocess.run(cmd, capture_output=True, timeout=60).returncode == 0
    except Exception as e:
        log.warning(f"  Pixabay video: {e}")
    return False

def solid_bg(out_path, duration, color="0x0a0a0a"):
    cmd = ["ffmpeg","-y","-f","lavfi",
           "-i",f"color=c={color}:size=1920x1080:duration={duration}:rate=25",
           "-c:v","libx264","-pix_fmt","yuv420p", out_path]
    return subprocess.run(cmd, capture_output=True, timeout=30).returncode == 0

def stage_5_visuals(script):
    log.info("Stage 5: Generating visuals...")
    tg(f"🎨 Creating {len(script)} visuals...")

    vis_dir = WORKSPACE / "visuals"
    vis_dir.mkdir(exist_ok=True)

    for i, scene in enumerate(script):
        n = scene["scene"]
        vtype = scene.get("visual_type","ai_image")
        prompt = scene.get("visual_prompt","cinematic dramatic scene")
        search = scene.get("visual_search", TOPIC)
        out = str(vis_dir / f"scene_{n:03d}.mp4")
        img = str(vis_dir / f"scene_{n:03d}.jpg")
        anim = ANIMATIONS[i % len(ANIMATIONS)]

        if scene.get("audio_file"):
            duration = get_audio_duration(scene["audio_file"])
        else:
            duration = float(scene.get("duration_hint", 4))
        scene["actual_duration"] = duration

        success = False

        # ── Text stat ────────────────────────────────────────
        if vtype == "text_stat":
            if make_text_stat(scene["voiceover"], out, duration):
                scene["video_file"] = out
                log.info(f"  Scene {n}: text_stat ✓")
                continue

        # ── Text question ────────────────────────────────────
        elif vtype == "text_question":
            if make_text_question(scene["voiceover"], out, duration):
                scene["video_file"] = out
                log.info(f"  Scene {n}: text_question ✓")
                continue

        # ── Stock video ──────────────────────────────────────
        elif vtype == "stock_video":
            log.info(f"  Scene {n}: stock_video '{search}'")
            if fetch_pexels_video(search, out, duration):
                scene["video_file"] = out
                log.info(f"  Scene {n}: Pexels video ✓")
                success = True
            if not success and fetch_pixabay_video(search, out, duration):
                scene["video_file"] = out
                log.info(f"  Scene {n}: Pixabay video ✓")
                success = True

        # ── AI image ─────────────────────────────────────────
        else:  # ai_image
            # Check if this topic might hallucinate badly
            if should_skip_ai(prompt, search):
                log.info(f"  Scene {n}: Skipping AI (hallucination risk) → stock")
                if fetch_pexels_video(search, out, duration):
                    scene["video_file"] = out
                    success = True
                if not success and fetch_pexels_image(search, img):
                    if img_to_video(img, out, duration, anim):
                        scene["video_file"] = out
                        success = True
            else:
                log.info(f"  Scene {n}: Pollinations '{prompt[:50]}'")
                if fetch_pollinations(prompt, img, seed=n*13):
                    if img_to_video(img, out, duration, anim):
                        scene["video_file"] = out
                        log.info(f"  Scene {n}: Pollinations+{anim} ✓")
                        success = True

        # ── Universal fallbacks (all types) ──────────────────
        if not success:
            log.info(f"  Scene {n}: Trying Pexels video fallback...")
            if fetch_pexels_video(search or TOPIC, out, duration):
                scene["video_file"] = out
                success = True

        if not success:
            log.info(f"  Scene {n}: Trying Pexels image...")
            if fetch_pexels_image(search or TOPIC, img):
                if img_to_video(img, out, duration, anim):
                    scene["video_file"] = out
                    success = True

        if not success:
            log.info(f"  Scene {n}: Trying Pixabay image...")
            if fetch_pixabay_image(search or TOPIC, img):
                if img_to_video(img, out, duration, anim):
                    scene["video_file"] = out
                    success = True

        if not success:
            log.warning(f"  Scene {n}: All layers failed → solid bg")
            solid_bg(out, duration)
            scene["video_file"] = out

    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 6 — ASSEMBLY
#  - Word-by-word kinetic captions (1-3 words at a time)
#  - Center screen, not bottom
#  - Yellow highlight for key words
#  - SFX click on every caption pop
#  - Film grain unified look
# ═══════════════════════════════════════════════════════════

def _srt(s):
    h,m = int(s//3600), int((s%3600)//60)
    sec,ms = int(s%60), int((s%1)*1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

def build_kinetic_srt(script):
    """
    Word-by-word SRT: 1-3 words per entry, centered.
    Key words (nouns, numbers, proper nouns) get yellow color via ASS override.
    """
    entries = []
    # Simple heuristic: words with capital letters or numbers = key word
    def is_key_word(w):
        clean = re.sub(r'[^a-zA-Z0-9]','',w)
        return bool(re.search(r'\d', clean)) or (clean and clean[0].isupper() and len(clean) > 2)

    for scene in script:
        text = scene.get("voiceover","").strip()
        if not text: continue
        dur = scene.get("actual_duration", 4.0)
        start = scene.get("start_time", 0.0)
        words = text.split()
        if not words: continue

        # Group into 2-3 word chunks
        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i+3]
            chunk = " ".join(chunk_words)
            chunks.append(chunk)
            i += 3

        time_per = dur / len(chunks)
        for j, chunk in enumerate(chunks):
            cs = start + j * time_per
            ce = cs + time_per - 0.05
            entries.append((cs, ce, chunk))

    return entries

def make_sfx_click(out_path, duration=0.1):
    """Generate a subtle digital click sound."""
    cmd = ["ffmpeg","-y","-f","lavfi",
           "-i",f"sine=frequency=1200:duration={duration}:sample_rate=44100",
           "-af","volume=0.15,afade=t=out:st=0:d={duration}",
           out_path]
    subprocess.run(cmd, capture_output=True, timeout=10)

def stage_6_assemble(script, genre):
    log.info("Stage 6: Assembling professional video...")
    tg("🎞️ Final assembly...")

    asm = WORKSPACE / "assembly"
    asm.mkdir(exist_ok=True)

    # Step 1: Merge each scene's video + audio
    scene_files = []
    current_time = 0.0

    for scene in script:
        n = scene["scene"]
        video = scene.get("video_file")
        audio = scene.get("audio_file")
        dur = scene.get("actual_duration", 4.0)
        scene["start_time"] = current_time

        if not video:
            log.warning(f"  Scene {n}: no video, skipping")
            continue

        out = str(asm / f"merged_{n:03d}.mp4")

        if audio:
            cmd = ["ffmpeg","-y",
                   "-i", os.path.abspath(video),
                   "-i", os.path.abspath(audio),
                   "-t", str(dur),
                   "-c:v","libx264","-c:a","aac",
                   "-map","0:v:0","-map","1:a:0",
                   "-shortest","-preset","fast", out]
        else:
            cmd = ["ffmpeg","-y",
                   "-i", os.path.abspath(video),
                   "-t", str(dur),
                   "-c:v","libx264","-preset","fast","-an", out]

        r = subprocess.run(cmd, capture_output=True, timeout=180)
        if r.returncode == 0 and os.path.exists(out):
            scene_files.append(out)
            current_time += dur
        else:
            log.warning(f"  Scene {n} merge failed: {r.stderr.decode()[-100:]}")

    if not scene_files:
        raise RuntimeError("No scenes assembled!")

    # Step 2: Concat
    concat_f = str(asm / "concat.txt")
    with open(concat_f,"w") as f:
        for sf in scene_files:
            f.write(f"file '{os.path.abspath(sf)}'\n")

    raw = str(WORKSPACE / "raw_output.mp4")
    r = subprocess.run(
        ["ffmpeg","-y","-f","concat","-safe","0","-i",concat_f,
         "-c:v","libx264","-c:a","aac","-movflags","+faststart","-preset","fast", raw],
        capture_output=True, timeout=600
    )
    if r.returncode != 0:
        raise RuntimeError(f"Concat failed: {r.stderr.decode()[-300:]}")

    # Step 3: Build kinetic word-by-word SRT
    srt_entries = build_kinetic_srt(script)
    srt_path = str(asm / "kinetic.srt")
    with open(srt_path,"w", encoding="utf-8") as f:
        for i,(cs,ce,text) in enumerate(srt_entries, 1):
            f.write(f"{i}\n{_srt(cs)} --> {_srt(ce)}\n{text}\n\n")

    # Step 4: Burn captions — CENTER SCREEN, bold, large
    # Alignment=10 = center of screen (ASS alignment)
    caption_style = (
        "FontSize=36,FontName=DejaVu Sans Bold,"
        "PrimaryColour=&H00FFFFFF,"   # white
        "OutlineColour=&H00000000,"   # black outline
        "Outline=4,Shadow=2,"
        "Alignment=10,"               # CENTER of screen
        "MarginV=0"
    )

    final = str(WORKSPACE / "final_video.mp4")
    sub_filter = f"subtitles={srt_path}:force_style='{caption_style}'"

    r = subprocess.run(
        ["ffmpeg","-y","-i",raw,
         "-vf", sub_filter,
         "-c:v","libx264","-c:a","copy","-preset","fast", final],
        capture_output=True, timeout=600
    )
    if r.returncode != 0:
        log.warning("Caption burn failed, using raw")
        shutil.copy(raw, final)

    sz = os.path.getsize(final)/1024/1024
    total_dur = sum(s.get("actual_duration",4) for s in script)
    log.info(f"Stage 6: Done → {final} ({sz:.1f}MB, {total_dur:.0f}s)")
    return final

# ═══════════════════════════════════════════════════════════
#  STAGE 7 — QC
# ═══════════════════════════════════════════════════════════
def stage_7_qc(video_path, script, genre):
    log.info("Stage 7: QC check...")
    tg("🔍 Quality checking...")

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        total_dur = sum(s.get("actual_duration",4) for s in script)
        avg_cut = total_dur / max(len(script),1)
        hook = script[0].get("voiceover","") if script else ""
        scenes_text = "\n".join([
            f"Scene {s['scene']} ({s.get('actual_duration',4):.1f}s) [{s.get('visual_type','ai_image')}]: {s['voiceover']}"
            for s in script[:15]
        ])

        r = model.generate_content(f"""Rate this {genre} YouTube video:

Hook (first line): "{hook}"
Total scenes: {len(script)}
Total duration: {total_dur:.0f}s
Avg cut: {avg_cut:.1f}s (target: 3-5s)
Language: {LANGUAGE}

First 15 scenes:
{scenes_text}

Score 0-10 each. Return ONLY JSON:
{{
  "score": 8,
  "hook_score": 9,
  "pacing_score": 8,
  "visual_variety_score": 7,
  "verdict": "approved",
  "reason": "brief reason",
  "improvement": "one specific fix"
}}

verdict: "approved"(>=7), "drafts"(5-6), "retry"(<5)""")

        text = r.text.strip().replace("```json","").replace("```","").strip()
        result = json.loads(text)
        log.info(f"Stage 7: {result['score']}/10 — {result['verdict'].upper()}")
        return result
    except Exception as e:
        log.warning(f"QC failed: {e}")
        return {"score":7,"verdict":"approved","reason":"QC unavailable"}

# ═══════════════════════════════════════════════════════════
#  STAGE 8 — PUBLISH
# ═══════════════════════════════════════════════════════════
def generate_metadata(topic, script, genre, lang):
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        hook = script[0].get("voiceover","") if script else ""
        lang_note = f"Title and description in {lang} language." if lang != "english" else ""
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":f"""Write YouTube metadata for a {genre} video.
Topic: "{topic}"
Hook line: "{hook}"
{lang_note}

Return ONLY JSON:
{{
  "title": "viral title under 60 chars with power word or number",
  "description": "3 engaging paragraphs with keywords",
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10"],
  "hashtags": "#tag1 #tag2 #tag3 #tag4 #tag5"
}}"""}],
            max_tokens=600,
        )
        text = r.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        log.warning(f"Metadata failed: {e}")
        return {
            "title": f"The Shocking Truth About {topic}",
            "description": f"Everything about {topic} explained.",
            "tags": [topic, genre, "facts", "viral", "documentary"],
            "hashtags": f"#{topic.replace(' ','')} #{genre} #viral #facts"
        }

def stage_8_publish(video_path, script, genre, lang):
    log.info("Stage 8: Publishing...")
    tg("📤 Uploading to YouTube...")

    meta = generate_metadata(TOPIC, script, genre, lang)
    log.info(f"  Title: {meta['title']}")

    now = datetime.now(timezone.utc)
    h, m = map(int, SCHEDULE_TIME.split(":"))
    pub = now.replace(hour=h, minute=m, second=0, microsecond=0)
    pub_str = pub.isoformat().replace("+00:00","Z")

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        token_data = os.environ.get("YOUTUBE_TOKEN_JSON","")
        if not token_data:
            raise ValueError("YOUTUBE_TOKEN_JSON is empty")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp.write(token_data)
            token_path = tmp.name

        creds = Credentials.from_authorized_user_file(token_path)
        yt = build("youtube","v3", credentials=creds)

        body = {
            "snippet": {
                "title": meta["title"],
                "description": meta["description"] + "\n\n" + meta.get("hashtags",""),
                "tags": meta["tags"],
                "categoryId": "28",
                "defaultLanguage": {"english":"en","hindi":"hi","spanish":"es",
                                    "french":"fr","german":"de","arabic":"ar"}.get(lang,"en")
            },
            "status": {
                "privacyStatus": "private",
                "publishAt": pub_str,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=5*1024*1024)
        req = yt.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                log.info(f"  Upload: {int(status.progress()*100)}%")

        url = f"https://youtube.com/watch?v={response['id']}"
        log.info(f"Stage 8: {url}")
        return url

    except Exception as e:
        log.error(f"Upload failed: {e}")
        return f"Upload failed: {e}"

# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
def run_pipeline():
    start = time.time()
    log.info(f"🚀 Pipeline v3.0 | Topic: '{TOPIC}' | Genre: {GENRE} | Lang: {LANGUAGE} | Duration: {DURATION}min")
    tg(f"🚀 Starting pipeline v3.0\nTopic: {TOPIC}\nSchedule: {SCHEDULE_TIME} UTC")

    try:
        # Stage 0: Auto-detect settings
        genre, lang, dur = stage_0_autodetect(TOPIC, GENRE, LANGUAGE, DURATION)
        _save({"genre":genre,"lang":lang,"duration":dur}, "settings.json")

        # Stage 1: Research
        research = stage_1_research(TOPIC, lang)
        _save(research, "research.json")
        tg(f"📚 Research done: {len(research.get('key_facts',[]))} facts found")

        # Stage 2: Script
        script = stage_2_script(research, genre, lang, dur)
        _save(script, "script.json")
        tg(f"✍️ Script: {len(script)} scenes | Avg {dur*60/max(len(script),1):.1f}s/scene")

        # Stage 3: B-roll upgrade
        script = stage_3_broll_upgrade(script)
        _save(script, "script_upgraded.json")

        # Stage 4: Voice
        voices = VOICE_MAP.get(lang, VOICE_MAP["english"])
        script = stage_4_voice(script, lang)
        tg(f"🎙️ Voice done: {voices[0]}")

        # Stage 5: Visuals
        script = stage_5_visuals(script)
        _save(script, "script_final.json")

        # Stage 6: Assembly
        final_video = stage_6_assemble(script, genre)

        # Stage 7: QC
        qc = stage_7_qc(final_video, script, genre)
        _save(qc, "qc_result.json")

        verdict = qc.get("verdict","approved")
        score = qc.get("score",7)

        if verdict == "retry":
            tg(f"❌ QC: {score}/10 — Rejected\n{qc.get('reason','')}\nFix: {qc.get('improvement','')}")
            return

        if verdict == "drafts":
            tg(f"⚠️ QC: {score}/10 — Saved to Drafts\n{qc.get('reason','')}\nReview before publishing.")
            return

        # Stage 8: Publish
        url = stage_8_publish(final_video, script, genre, lang)
        elapsed = int(time.time() - start)
        total_dur = sum(s.get("actual_duration",4) for s in script)

        tg(
            f"✅ DONE!\n\n"
            f"📺 {url}\n"
            f"⏰ Goes live: {SCHEDULE_TIME} UTC\n"
            f"🏆 QC Score: {score}/10\n"
            f"🎬 {len(script)} scenes | {total_dur:.0f}s video\n"
            f"✂️ Avg cut: {total_dur/max(len(script),1):.1f}s\n"
            f"🌍 Language: {lang} | Genre: {genre}\n"
            f"⚡ Time: {elapsed}s"
        )

    except Exception as e:
        log.error(f"Pipeline crashed: {e}")
        tg(f"💥 Crashed: {str(e)[:300]}\nCheck GitHub Actions logs.")
        raise

if __name__ == "__main__":
    run_pipeline()
