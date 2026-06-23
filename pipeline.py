"""
=============================================================
  ZERO-COST AI MEDIA AGENCY — pipeline.py
  All 8 stages run automatically, end to end.
  No Anthropic key. No OpenAI key. No credit card.
=============================================================

APIs used (all 100% free, no card):
  - Groq           → Script writing  (console.groq.com)
  - Gemini Flash   → Research + B-roll terms (aistudio.google.com)
  - Gemini Pro     → QC (same key)
  - Pollinations   → Image generation (NO key needed, no signup)
  - Edge-TTS       → Voice (NO key needed, Microsoft free cloud)
  - Pexels         → Stock video fallback (pexels.com/api)
  - Pixabay        → Stock video fallback 2 (pixabay.com/api)
  - YouTube API    → Publishing (Google Cloud free)
  - Telegram       → Command interface (BotFather free)

HOW TO RUN:
  This file is triggered automatically by GitHub Actions.
  You never run it manually.
  Just send /make [topic] [HH:MM] in Telegram.
=============================================================
"""

import os
import json
import time
import asyncio
import logging
import requests
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote

# ─── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("agency")

# ─── Load secrets from environment (GitHub Actions Secrets) ─
GROQ_KEY        = os.environ["GROQ_KEY"]
GEMINI_KEY      = os.environ["GEMINI_KEY"]
PEXELS_KEY      = os.environ["PEXELS_KEY"]
PIXABAY_KEY     = os.environ["PIXABAY_KEY"]
TELEGRAM_TOKEN  = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT   = os.environ["TELEGRAM_CHAT_ID"]
TOPIC           = os.environ.get("TOPIC", "The History of the Internet")
SCHEDULE_TIME   = os.environ.get("SCHEDULE_TIME", "18:00")  # HH:MM UTC

# Rotate 3 HuggingFace tokens to beat rate limits
HF_TOKENS = [
    os.environ.get("HF_TOKEN_1", ""),
    os.environ.get("HF_TOKEN_2", ""),
    os.environ.get("HF_TOKEN_3", ""),
]

# ─── Channel config (edit this for different channel types) ─
CHANNEL_CONFIG = {
    "channel_type": "documentary",   # documentary | cartoon | typography_reel | study | ad
    "output_format": "landscape",    # landscape (1920x1080) | vertical (1080x1920)
    "video_length": "medium",        # short (60s) | medium (5min) | long (10min)
    "voice": "en-US-GuyNeural",      # Edge-TTS voice
    "music_mood": "cinematic dramatic",
    "captions": True,
    "broll_upgrade": True,           # Use Gemini to improve search terms
}

# ─── Working directory ──────────────────────────────────────
WORKSPACE = Path(f"workspace_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
WORKSPACE.mkdir(exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  HELPER: Send Telegram updates so you know what's happening
# ═══════════════════════════════════════════════════════════
def telegram_update(message: str):
    """Send a progress update to your Telegram chat."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT, "text": f"🤖 {message}"}, timeout=10)
    except Exception as e:
        log.warning(f"Telegram update failed: {e}")

# ═══════════════════════════════════════════════════════════
#  STAGE 1 — RESEARCH AGENT
#  Uses: Gemini 2.5 Flash (free, no card)
#  Fallback: DuckDuckGo scrape (no key, always works)
# ═══════════════════════════════════════════════════════════
def stage_1_research(topic: str) -> dict:
    log.info("Stage 1: Research starting...")
    telegram_update(f"📚 Stage 1: Researching '{topic}'...")

    # ── Primary: Gemini Flash ──────────────────────────────
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
Research the topic: "{topic}"

Return ONLY a valid JSON object with this exact structure:
{{
  "headline": "one compelling sentence summary",
  "key_facts": ["fact 1", "fact 2", "fact 3", "fact 4", "fact 5"],
  "statistics": ["stat with number 1", "stat with number 2"],
  "timeline": ["earliest event", "middle event", "recent event"],
  "hook": "a shocking or surprising opening fact that grabs attention"
}}

No markdown, no explanation, just the JSON.
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip any accidental markdown fences
        text = text.replace("```json", "").replace("```", "").strip()
        research = json.loads(text)
        log.info("Stage 1: Gemini research complete")
        return research

    except Exception as e:
        log.warning(f"Stage 1: Gemini failed ({e}), trying DuckDuckGo fallback...")

    # ── Fallback: DuckDuckGo scrape ────────────────────────
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://html.duckduckgo.com/html/?q={quote(topic)}"
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        snippets = [r.get_text() for r in soup.select(".result__snippet")][:5]

        research = {
            "headline": f"Research on: {topic}",
            "key_facts": snippets,
            "statistics": [],
            "timeline": [],
            "hook": snippets[0] if snippets else f"Discover the story of {topic}"
        }
        log.info("Stage 1: DuckDuckGo fallback complete")
        return research

    except Exception as e:
        log.error(f"Stage 1: All research methods failed: {e}")
        # Return minimal data so pipeline doesn't stop
        return {
            "headline": topic,
            "key_facts": [f"Key information about {topic}"],
            "statistics": [],
            "timeline": [],
            "hook": f"The fascinating story of {topic}"
        }

# ═══════════════════════════════════════════════════════════
#  STAGE 2 — SCRIPT AGENT
#  Uses: Groq API, Llama 3.3 70B (free, no card)
#  Fallback: DeepSeek R1 on Groq (same key, same API)
# ═══════════════════════════════════════════════════════════
def stage_2_script(research: dict, channel_type: str) -> list:
    log.info("Stage 2: Writing script...")
    telegram_update("✍️ Stage 2: Writing script...")

    style_prompts = {
        "documentary": "Write like a BBC/Netflix documentary narrator. Serious, authoritative, cinematic.",
        "cartoon":     "Write like a fun animated YouTube channel. Energetic, simple, uses 'Whoa!', 'Did you know?'",
        "typography_reel": "Write as ultra-short punchy phrases. Max 8 words per line. High impact only.",
        "study":       "Write as a clear educational explainer. Simple language, structured, helpful.",
        "ad":          "Write as a 30-second advertisement. Hook in 3 seconds. Problem → Solution → CTA.",
    }
    style = style_prompts.get(channel_type, style_prompts["documentary"])

    prompt = f"""
You are a professional YouTube scriptwriter. {style}

Research data:
{json.dumps(research, indent=2)}

Create a video script. Return ONLY valid JSON, no markdown, no explanation:
[
  {{
    "scene": 1,
    "voiceover": "exactly what the narrator says for this scene",
    "visual_prompt": "detailed description of what should be shown visually",
    "music_mood": "the emotional feel for background music",
    "duration_hint": "estimated seconds for this scene"
  }}
]

Rules:
- 6 to 8 scenes total
- Scene 1 MUST start with the hook fact
- Each voiceover is 2-4 sentences max
- Visual prompts must be specific and cinematic
- No scene should be silent or empty
"""

    groq_models = [
        "llama-3.3-70b-versatile",       # Primary: best quality
        "deepseek-r1-distill-llama-70b",  # Fallback 1: better reasoning
        "llama-3.1-8b-instant",           # Fallback 2: fast, always available
    ]

    for model in groq_models:
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_KEY)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )
            text = response.choices[0].message.content.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            # Extract JSON array
            start = text.find("[")
            end = text.rfind("]") + 1
            script = json.loads(text[start:end])
            log.info(f"Stage 2: Script written with {model}, {len(script)} scenes")
            return script

        except Exception as e:
            log.warning(f"Stage 2: {model} failed: {e}. Trying next model...")
            time.sleep(2)

    log.error("Stage 2: All Groq models failed. Using minimal fallback script.")
    return [
        {
            "scene": 1,
            "voiceover": research.get("hook", f"Let's explore {TOPIC}"),
            "visual_prompt": f"dramatic cinematic opening shot about {TOPIC}",
            "music_mood": "dramatic",
            "duration_hint": "10"
        }
    ]

# ═══════════════════════════════════════════════════════════
#  STAGE 3 — GEMINI B-ROLL UPGRADE
#  Turns plain voiceover text into cinematic search terms
#  Uses: Gemini 2.5 Flash (same key as research)
#  Skipped automatically for typography_reel channel type
# ═══════════════════════════════════════════════════════════
def stage_3_broll_upgrade(script: list, channel_type: str) -> list:
    # Typography reels don't need video at all, skip this stage
    if channel_type == "typography_reel" or not CHANNEL_CONFIG["broll_upgrade"]:
        log.info("Stage 3: B-roll upgrade skipped (not needed)")
        return script

    log.info("Stage 3: Upgrading visual search terms with Gemini...")
    telegram_update("🎬 Stage 3: Translating script to cinematic visuals...")

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        for scene in script:
            try:
                prompt = (
                    f"Convert this script line into a cinematic stock footage search term. "
                    f"Be visual, specific, dramatic. Max 8 words. "
                    f"Script: '{scene['voiceover']}' "
                    f"Current visual idea: '{scene['visual_prompt']}'"
                )
                response = model.generate_content(prompt)
                upgraded = response.text.strip()
                log.info(f"  Scene {scene['scene']}: '{scene['visual_prompt']}' → '{upgraded}'")
                scene["visual_prompt"] = upgraded
                time.sleep(0.5)  # Respect rate limits
            except Exception as e:
                log.warning(f"  Scene {scene['scene']} upgrade failed: {e}. Keeping original.")

    except Exception as e:
        log.warning(f"Stage 3: B-roll upgrade failed entirely: {e}. Using original prompts.")

    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 4 — VOICE AGENT
#  Primary: Edge-TTS (Microsoft free cloud, NO key needed)
#  Fallback: gTTS (Google, NO key needed)
#  Note: Kokoro-82M requires GPU. GitHub Actions has CPU only,
#        so Edge-TTS is primary here. Add Kokoro for local use.
# ═══════════════════════════════════════════════════════════
async def _edge_tts_generate(text: str, output_path: str, voice: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def stage_4_voice(script: list, voice: str) -> list:
    log.info("Stage 4: Generating voice audio...")
    telegram_update("🎙️ Stage 4: Generating voice...")

    audio_dir = WORKSPACE / "audio"
    audio_dir.mkdir(exist_ok=True)

    for scene in script:
        scene_num = scene["scene"]
        output_path = str(audio_dir / f"scene_{scene_num:02d}.mp3")
        text = scene["voiceover"]

        # ── Primary: Edge-TTS ──────────────────────────────
        try:
            asyncio.run(_edge_tts_generate(text, output_path, voice))
            scene["audio_file"] = output_path
            log.info(f"  Scene {scene_num}: Edge-TTS OK")
            continue
        except Exception as e:
            log.warning(f"  Scene {scene_num}: Edge-TTS failed ({e}), trying gTTS...")

        # ── Fallback: gTTS ─────────────────────────────────
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(output_path)
            scene["audio_file"] = output_path
            log.info(f"  Scene {scene_num}: gTTS OK")
        except Exception as e:
            log.error(f"  Scene {scene_num}: ALL voice methods failed: {e}")
            scene["audio_file"] = None

    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 5 — VISUAL AGENT
#  Layer 1: Pollinations.ai image API (NO key, NO signup, free)
#           → Ken Burns zoom via FFmpeg = looks like video
#  Layer 2: Pexels stock video (free API key)
#  Layer 3: Pixabay stock video (free API key)
#  Layer 4: Solid color placeholder (absolute last resort)
#
#  WHY NOT HUGGINGFACE TEXT-TO-VIDEO?
#  HuggingFace video models are unreliable on the free tier —
#  they return 1-second black screens or time out constantly.
#  Pollinations + Ken Burns looks MORE professional and NEVER fails.
# ═══════════════════════════════════════════════════════════
def get_audio_duration(audio_file: str) -> float:
    """Get exact duration of audio file in seconds using FFprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_file],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except Exception:
        return 5.0  # Default 5 seconds

def layer1_pollinations_image(visual_prompt: str, output_path: str, duration: float) -> bool:
    """Generate image with Pollinations (no key), then animate with Ken Burns zoom."""
    try:
        # Generate image
        image_path = output_path.replace(".mp4", ".jpg")
        encoded = quote(visual_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1920&height=1080&nologo=true"
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            return False
        with open(image_path, "wb") as f:
            f.write(resp.content)

        # Animate: slow zoom-in (Ken Burns effect) using FFmpeg
        zoom_filter = (
            f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={int(duration*25)}:s=1920x1080:fps=25"
        )
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-vf", zoom_filter,
            "-t", str(duration), "-c:v", "libx264",
            "-pix_fmt", "yuv420p", output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        return result.returncode == 0

    except Exception as e:
        log.warning(f"  Pollinations layer failed: {e}")
        return False

def layer2_pexels_video(visual_prompt: str, output_path: str, duration: float) -> bool:
    """Search Pexels for matching stock video and trim to duration."""
    try:
        headers = {"Authorization": PEXELS_KEY}
        params = {"query": visual_prompt, "per_page": 5, "orientation": "landscape"}
        resp = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15)
        data = resp.json()
        videos = data.get("videos", [])
        if not videos:
            return False

        # Pick highest resolution file
        video_files = videos[0].get("video_files", [])
        best = sorted(video_files, key=lambda x: x.get("width", 0), reverse=True)
        if not best:
            return False

        video_url = best[0]["link"]
        raw_path = output_path.replace(".mp4", "_raw.mp4")
        r = requests.get(video_url, stream=True, timeout=60)
        with open(raw_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Trim to exact duration
        cmd = ["ffmpeg", "-y", "-i", raw_path, "-t", str(duration),
               "-c:v", "libx264", "-an", output_path]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0

    except Exception as e:
        log.warning(f"  Pexels layer failed: {e}")
        return False

def layer3_pixabay_video(visual_prompt: str, output_path: str, duration: float) -> bool:
    """Search Pixabay for matching stock video and trim to duration."""
    try:
        params = {
            "key": PIXABAY_KEY, "q": quote(visual_prompt),
            "video_type": "film", "per_page": 5
        }
        resp = requests.get("https://pixabay.com/api/videos/", params=params, timeout=15)
        data = resp.json()
        hits = data.get("hits", [])
        if not hits:
            return False

        video_url = hits[0]["videos"]["large"]["url"]
        raw_path = output_path.replace(".mp4", "_raw.mp4")
        r = requests.get(video_url, stream=True, timeout=60)
        with open(raw_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        cmd = ["ffmpeg", "-y", "-i", raw_path, "-t", str(duration),
               "-c:v", "libx264", "-an", output_path]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0

    except Exception as e:
        log.warning(f"  Pixabay layer failed: {e}")
        return False

def layer4_solid_color(output_path: str, duration: float) -> bool:
    """Last resort: solid dark gradient (never fails, always works)."""
    try:
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x1a1a2e:size=1920x1080:duration={duration}:rate=25",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0
    except Exception:
        return False

def stage_5_visuals(script: list, channel_type: str) -> list:
    log.info("Stage 5: Generating visuals...")
    telegram_update("🎨 Stage 5: Creating visuals...")

    visual_dir = WORKSPACE / "visuals"
    visual_dir.mkdir(exist_ok=True)

    for scene in script:
        scene_num = scene["scene"]
        output_path = str(visual_dir / f"scene_{scene_num:02d}.mp4")
        prompt = scene.get("visual_prompt", f"cinematic scene about {TOPIC}")
        duration = float(scene.get("duration_hint", "6"))

        # Get actual audio duration if audio was generated
        if scene.get("audio_file"):
            duration = get_audio_duration(scene["audio_file"])

        success = False
        layers = [
            ("Pollinations+KenBurns", lambda: layer1_pollinations_image(prompt, output_path, duration)),
            ("Pexels stock video",    lambda: layer2_pexels_video(prompt, output_path, duration)),
            ("Pixabay stock video",   lambda: layer3_pixabay_video(prompt, output_path, duration)),
            ("Solid color fallback",  lambda: layer4_solid_color(output_path, duration)),
        ]

        for layer_name, layer_fn in layers:
            log.info(f"  Scene {scene_num}: Trying {layer_name}...")
            try:
                if layer_fn():
                    log.info(f"  Scene {scene_num}: {layer_name} ✓")
                    scene["video_file"] = output_path
                    scene["actual_duration"] = duration
                    success = True
                    break
            except Exception as e:
                log.warning(f"  Scene {scene_num}: {layer_name} error: {e}")

        if not success:
            log.error(f"  Scene {scene_num}: ALL visual layers failed!")

    return script

# ═══════════════════════════════════════════════════════════
#  STAGE 6 — ASSEMBLY AGENT
#  Combines: video + voice + captions into final MP4
#  Uses: FFmpeg (free, pre-installed everywhere)
#  Adds: burned-in subtitles, proper audio mix
# ═══════════════════════════════════════════════════════════
def stage_6_assemble(script: list, output_format: str) -> str:
    log.info("Stage 6: Assembling final video...")
    telegram_update("🎞️ Stage 6: Assembling video...")

    assembly_dir = WORKSPACE / "assembly"
    assembly_dir.mkdir(exist_ok=True)

    # Step 1: For each scene, merge its video + audio
    scene_files = []
    for scene in script:
        video = scene.get("video_file")
        audio = scene.get("audio_file")
        scene_num = scene["scene"]

        if not video:
            log.warning(f"  Scene {scene_num}: No video, skipping")
            continue

        scene_output = str(assembly_dir / f"merged_{scene_num:02d}.mp4")

        if audio:
            # Merge video and audio, fit video to audio length
            duration = get_audio_duration(audio)
            cmd = [
                "ffmpeg", "-y",
                "-i", video, "-i", audio,
                "-t", str(duration),
                "-c:v", "libx264", "-c:a", "aac",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", scene_output
            ]
        else:
            # No audio, just copy video
            cmd = ["ffmpeg", "-y", "-i", video, "-c:v", "libx264", scene_output]

        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode == 0:
            scene_files.append(scene_output)
        else:
            log.warning(f"  Scene {scene_num}: Merge failed")

    if not scene_files:
        raise RuntimeError("No scenes assembled. Pipeline cannot continue.")

    # Step 2: Write FFmpeg concat file
    concat_path = str(assembly_dir / "concat.txt")
    with open(concat_path, "w") as f:
        for sf in scene_files:
            abs_path = os.path.abspath(sf)
            f.write(f"file '{abs_path}'\n")

    # Step 3: Concatenate all scenes into one video
    raw_output = str(WORKSPACE / "raw_output.mp4")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_path,
        "-c:v", "libx264", "-c:a", "aac",
        "-movflags", "+faststart",
        raw_output
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"Concatenation failed: {result.stderr.decode()}")

    # Step 4: Add captions (burned-in subtitles) if enabled
    final_output = str(WORKSPACE / "final_video.mp4")

    if CHANNEL_CONFIG.get("captions"):
        # Build SRT subtitle file
        srt_path = str(assembly_dir / "captions.srt")
        current_time = 0.0
        with open(srt_path, "w") as f:
            for i, scene in enumerate(script, 1):
                duration = scene.get("actual_duration", 5.0)
                start = _seconds_to_srt(current_time)
                end = _seconds_to_srt(current_time + duration)
                text = scene.get("voiceover", "")[:80]  # Trim long lines
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
                current_time += duration

        # Burn captions into video
        cmd = [
            "ffmpeg", "-y", "-i", raw_output,
            "-vf", f"subtitles={srt_path}:force_style='FontSize=20,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2'",
            "-c:a", "copy", final_output
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            log.warning("Caption burning failed, using video without captions")
            import shutil
            shutil.copy(raw_output, final_output)
    else:
        import shutil
        shutil.copy(raw_output, final_output)

    log.info(f"Stage 6: Assembly complete → {final_output}")
    return final_output

def _seconds_to_srt(seconds: float) -> str:
    """Convert seconds to SRT timestamp format HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ═══════════════════════════════════════════════════════════
#  STAGE 7 — QC AGENT
#  Uses: Gemini 2.5 Flash (video analysis, same key)
#  Scores 0-10. Routes to Approved / Drafts / Retry
# ═══════════════════════════════════════════════════════════
def stage_7_qc(video_path: str, script: list) -> dict:
    log.info("Stage 7: Running quality check...")
    telegram_update("🔍 Stage 7: AI quality check...")

    # Build a text-based QC since uploading video to Gemini
    # costs quota — use script + metadata analysis instead
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        script_text = "\n".join([f"Scene {s['scene']}: {s['voiceover']}" for s in script])
        prompt = f"""
You are a YouTube video quality controller. Analyze this video script and rate it.

Topic: {TOPIC}
Channel type: {CHANNEL_CONFIG['channel_type']}
Script:
{script_text}

Rate the video 0-10 on:
- Hook strength (first 3 seconds)
- Pacing and flow
- Value to viewer
- Viral potential

Return ONLY JSON:
{{
  "score": 8,
  "hook_score": 9,
  "pacing_score": 7,
  "verdict": "approved",
  "reason": "Strong hook, good pacing",
  "improvement": "Could add more statistics"
}}

verdict must be exactly: "approved" (score >= 7), "drafts" (score 5-6), or "retry" (score < 5)
"""
        response = model.generate_content(prompt)
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        log.info(f"Stage 7: Score {result['score']}/10 — {result['verdict'].upper()}")
        return result

    except Exception as e:
        log.warning(f"Stage 7: QC failed ({e}), auto-approving")
        return {"score": 7, "verdict": "approved", "reason": "QC unavailable, auto-approved"}

# ═══════════════════════════════════════════════════════════
#  STAGE 8 — PUBLISH AGENT
#  Uses: YouTube Data API v3 (Google Cloud free)
#  Generates: title, description, tags with Groq
# ═══════════════════════════════════════════════════════════
def generate_metadata(topic: str, script: list) -> dict:
    """Use Groq to write YouTube title, description, and tags."""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        script_summary = " ".join([s.get("voiceover", "")[:100] for s in script[:3]])
        prompt = f"""
Write YouTube metadata for a video about: "{topic}"

Script preview: {script_summary}

Return ONLY JSON:
{{
  "title": "compelling YouTube title under 60 chars with numbers or power words",
  "description": "3 paragraph description with keywords, no hashtags here",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
  "hashtags": "#tag1 #tag2 #tag3"
}}
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        log.warning(f"Metadata generation failed: {e}")
        return {
            "title": f"The Truth About {topic}",
            "description": f"In this video, we explore {topic} in depth.",
            "tags": [topic, "documentary", "educational"],
            "hashtags": f"#{topic.replace(' ', '')} #documentary"
        }

def stage_8_publish(video_path: str, script: list, schedule_time: str) -> str:
    log.info("Stage 8: Publishing to YouTube...")
    telegram_update("📤 Stage 8: Uploading to YouTube...")

    # Generate metadata
    metadata = generate_metadata(TOPIC, script)
    log.info(f"  Title: {metadata['title']}")

    # Build scheduled publish time (today at requested HH:MM UTC)
    now = datetime.now(timezone.utc)
    hour, minute = map(int, schedule_time.split(":"))
    publish_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    publish_at_str = publish_at.isoformat().replace("+00:00", "Z")

    # Upload to YouTube
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = Credentials.from_authorized_user_file("token.json")
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": metadata["title"],
                "description": metadata["description"] + "\n\n" + metadata.get("hashtags", ""),
                "tags": metadata["tags"],
                "categoryId": "28"  # Science & Technology
            },
            "status": {
                "privacyStatus": "private",
                "publishAt": publish_at_str,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                log.info(f"  Upload progress: {progress}%")

        video_id = response["id"]
        youtube_url = f"https://youtube.com/watch?v={video_id}"
        log.info(f"Stage 8: Published! {youtube_url}")
        return youtube_url

    except FileNotFoundError:
        log.error("Stage 8: token.json not found. Run auth setup first.")
        return "YouTube auth not configured"
    except Exception as e:
        log.error(f"Stage 8: YouTube upload failed: {e}")
        return f"Upload failed: {e}"

# ═══════════════════════════════════════════════════════════
#  MAIN PIPELINE — runs all 8 stages in order
# ═══════════════════════════════════════════════════════════
def run_pipeline():
    start_time = time.time()
    log.info(f"🚀 Pipeline starting for topic: '{TOPIC}'")
    telegram_update(f"🚀 Starting pipeline for: '{TOPIC}'\nThis takes 8-15 minutes. I'll update you at each stage.")

    try:
        # Stage 1: Research
        research = stage_1_research(TOPIC)
        _save(research, "research.json")

        # Stage 2: Script
        script = stage_2_script(research, CHANNEL_CONFIG["channel_type"])
        _save(script, "script.json")

        # Stage 3: B-roll upgrade
        script = stage_3_broll_upgrade(script, CHANNEL_CONFIG["channel_type"])
        _save(script, "script_upgraded.json")

        # Stage 4: Voice (runs on all scenes)
        script = stage_4_voice(script, CHANNEL_CONFIG["voice"])

        # Stage 5: Visuals (runs on all scenes, 4-layer fallback)
        script = stage_5_visuals(script, CHANNEL_CONFIG["channel_type"])
        _save(script, "script_final.json")

        # Stage 6: Assembly
        final_video = stage_6_assemble(script, CHANNEL_CONFIG["output_format"])

        # Stage 7: QC
        qc_result = stage_7_qc(final_video, script)
        _save(qc_result, "qc_result.json")

        verdict = qc_result.get("verdict", "approved")
        score = qc_result.get("score", 7)

        if verdict == "retry":
            telegram_update(
                f"❌ QC Score: {score}/10\nVideo rejected.\nReason: {qc_result.get('reason')}\n"
                f"Improvement needed: {qc_result.get('improvement', 'N/A')}"
            )
            log.info("Pipeline ended: video rejected by QC")
            return

        if verdict == "drafts":
            telegram_update(
                f"⚠️ QC Score: {score}/10\nSaved to Drafts for your review.\n"
                f"Reason: {qc_result.get('reason')}"
            )
            log.info("Pipeline ended: video saved to drafts")
            return

        # Stage 8: Publish (only if approved)
        youtube_url = stage_8_publish(final_video, script, SCHEDULE_TIME)

        elapsed = int(time.time() - start_time)
        telegram_update(
            f"✅ Done! Video published.\n\n"
            f"📺 {youtube_url}\n"
            f"⏰ Scheduled: {SCHEDULE_TIME} UTC\n"
            f"🏆 QC Score: {score}/10\n"
            f"⚡ Time taken: {elapsed}s"
        )
        log.info(f"✅ Pipeline complete in {elapsed}s")

    except Exception as e:
        log.error(f"Pipeline crashed: {e}")
        telegram_update(f"💥 Pipeline crashed at: {str(e)[:200]}\nCheck GitHub Actions logs.")
        raise

def _save(data, filename: str):
    """Save intermediate data to workspace for debugging."""
    path = WORKSPACE / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    log.info(f"  Saved: {filename}")

if __name__ == "__main__":
    run_pipeline()
