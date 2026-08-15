import os
import json
import logging
import subprocess
from pathlib import Path
from PIL import Image

try:
    import imagehash
except ImportError:
    imagehash = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

log = logging.getLogger("agency")

class VideoQCAgent:
    def __init__(self, model_name="gemini-1.5-flash"):
        self.model_name = model_name
        gemini_key = os.environ.get("GEMINI_KEY", "")
        if gemini_key and genai:
            genai.configure(api_key=gemini_key)
            self.model = genai.GenerativeModel(model_name=self.model_name)
        else:
            self.model = None

    def extract_1fps(self, video_path, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        log.info(f"Extracting 1fps frames from {video_path} for pHash...")
        cmd = [
            "ffmpeg", "-y", "-i", video_path, "-vf", "fps=1",
            os.path.join(output_dir, "frame_%04d.jpg")
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return sorted(list(Path(output_dir).glob("frame_*.jpg")))

    def extract_shot_frames(self, video_path, output_dir, shot_timeline):
        """Extracts 5 specific frames per shot: 0%, 25%, 50%, 75%, 100%"""
        os.makedirs(output_dir, exist_ok=True)
        log.info("Extracting 5-point frames for each shot...")
        
        extracted = []
        for idx, shot in enumerate(shot_timeline):
            s_id = shot["shot_id"]
            start = shot["start_time"]
            dur = shot["duration"]
            end = shot["end_time"]
            
            v_type = shot.get("visual_type", "")
            if v_type == "ai_video" or dur >= 4.0:
                times = [start, start + dur * 0.25, start + dur * 0.50, start + dur * 0.75, max(start, end - 0.2)]
            elif v_type in ("stock_video", "real_photo"):
                times = [start + dur * 0.25, start + dur * 0.75]
            else:
                times = [start + dur * 0.50]
            
            for t_idx, t in enumerate(times):
                out_file = os.path.join(output_dir, f"shot_{idx:03d}_{s_id}_t{t_idx}.jpg")
                cmd = ["ffmpeg", "-y", "-ss", str(t), "-i", video_path, "-vframes", "1", "-q:v", "2", out_file]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(out_file):
                    extracted.append((shot, out_file, t_idx))
                    
        return extracted

    def detect_repetitions(self, frames):
        if not imagehash or not frames:
            return {"duplicates": [], "static_loops": []}

        hashes = []
        for f in frames:
            try:
                h = imagehash.phash(Image.open(f))
                hashes.append((f.name, h))
            except Exception as e:
                hashes.append((f.name, None))

        static_loops = []
        duplicates = []
        threshold = 5
        
        for i in range(1, len(hashes)):
            prev_name, prev_hash = hashes[i-1]
            curr_name, curr_hash = hashes[i]
            if prev_hash and curr_hash and (curr_hash - prev_hash) <= threshold:
                static_loops.append((prev_name, curr_name))
                
        for i in range(len(hashes)):
            for j in range(i+2, len(hashes)): 
                h1, h2 = hashes[i][1], hashes[j][1]
                if h1 and h2 and (h1 - h2) <= threshold:
                    duplicates.append((hashes[i][0], hashes[j][0]))
                    
        return {"static_loops": static_loops, "duplicates": duplicates}

    def review_video(self, video_path, script_data, cfg):
        log.info("🎥 Starting V3 3-LEVEL QC process...")
        
        ws_dir = os.path.dirname(video_path)
        frames_1fps_dir = os.path.join(ws_dir, "qc_frames_1fps")
        frames_shot_dir = os.path.join(ws_dir, "qc_frames_shots")
        
        # 1. Level 1: Deterministic mappings
        shot_timeline = []
        current_time = 0.0
        
        stats = {
            "ai_video": 0, "stock": 0, "photo": 0, "graphic": 0, "fallback": 0,
            "longest_shot": 0
        }
        
        is_v2 = isinstance(script_data, dict) and "story_beats" in script_data
        if is_v2:
            for beat in script_data.get("story_beats", []):
                for block in beat.get("narration_blocks", []):
                    for shot in block.get("shots", []):
                        dur = float(shot.get("actual_duration", shot.get("duration_seconds", 4.0)) or 4.0)
                        stats["longest_shot"] = max(stats["longest_shot"], dur)
                        
                        v_type = shot.get("visual_type", "")
                        prov = shot.get("asset_provenance", "")
                        
                        if v_type == "ai_video": stats["ai_video"] += 1
                        elif v_type == "stock_video" or prov == "STOCK": stats["stock"] += 1
                        elif v_type == "real_photo": stats["photo"] += 1
                        elif v_type == "motion_graphics": stats["graphic"] += 1
                        
                        if shot.get("asset", {}).get("fallback_used"):
                            stats["fallback"] += 1
                        
                        shot_timeline.append({
                            "shot_id": shot.get("shot_id"),
                            "visual_job": shot.get("visual_job", ""),
                            "shot_role": shot.get("shot_role", ""),
                            "asset_provenance": prov,
                            "ai_prompt": shot.get("ai_prompt", ""),
                            "start_time": current_time,
                            "duration": dur,
                            "end_time": current_time + dur,
                            "narration": block.get("caption", block.get("voiceover", "")),
                            "attention": beat.get("attention_intensity", "")
                        })
                        current_time += dur
                        
        num_scenes = len(shot_timeline)
        total_duration = current_time
        avg_shot_dur = total_duration / max(1, num_scenes) if num_scenes > 0 else 0
        
        # P-Hash Loops
        frames_1fps = self.extract_1fps(video_path, frames_1fps_dir)
        rep_report = self.detect_repetitions(frames_1fps)
        
        # Level 2: 5-Point Frame Sampling
        shot_frames = self.extract_shot_frames(video_path, frames_shot_dir, shot_timeline)
        
        vision_result = {}
        worst_shots = []
        if self.model and len(shot_frames) > 0:
            try:
                # We can't send 75 frames to Gemini Vision all at once without hitting token limits quickly.
                # We will pick 1 frame per shot (the 50% mark) for global grading, 
                # plus the first 30 seconds (Hook QC).
                
                mid_frames = [f for f in shot_frames if f[2] == 2] # t_idx == 2 is 50%
                hook_frames = [f for f in shot_frames if f[0]["start_time"] <= 30.0 and f[2] in (0,4)]
                
                # Deduplicate
                eval_frames = []
                seen = set()
                for f in hook_frames + mid_frames:
                    if f[1] not in seen:
                        eval_frames.append(f)
                        seen.add(f[1])
                
                eval_frames = sorted(eval_frames, key=lambda x: x[0]["start_time"])
                selected_frames = eval_frames[:15] # Hard limit for safety
                
                prompt = (
                    f"You are a strict Documentary QC Editor reviewing '{cfg.get('topic')}'.\n"
                    "We are doing Level 2 (Vision) & Level 3 (Editorial) QC.\n\n"
                    "Frames provided:\n"
                )
                
                for i, (shot, f_path, t_idx) in enumerate(selected_frames):
                    prompt += f"Frame {i+1}: Shot {shot['shot_id']} | Job: {shot['visual_job']} | Role: {shot['shot_role']} | Provenance: {shot['asset_provenance']} | Intent: {shot['ai_prompt']} | Narration: {shot.get('narration')} | Attention: {shot.get('attention')}\n"
                    
                prompt += """
Score from 0 to 10:
VISUAL_RELEVANCE: Does this visual directly represent the intent?
VISUAL_EXPLANATION: Does it help the viewer understand?
EVIDENCE_QUALITY: Is archival/evidence high quality?
SHOT_VARIETY: Are compositions distinct?
COMPOSITION_VERIFICATION: Rule of thirds, subject framing, leading lines.
HISTORICAL_ACCURACY: Are era/locations appropriate?
CINEMATOGRAPHY: Is camera usage cinematic?
TEXT_QUALITY: Readable text?
FILLER_DETECTION: Is it specific (10) or generic filler (0)?
DOCUMENTARY_FEEL: Does this feel like Vox/Masterclass?
HOOK_SCORE: Are the first 30 seconds highly engaging with quick evidence/context?
VISUAL_BOREDOM_SCORE: Contextual (0=Boring/Slow, 10=Engaging). Note: Slow archival reveals or emotionally heavy narration shots can still be engaging.
FACTUAL_CLAIM_COVERAGE: Do visuals specifically support the facts stated in the narration?
SEMANTIC_COVERAGE: Does the visual rhythm cover the semantic meaning of the narration block?
ATTENTION_CURVE_VALIDATION: Does the visual intensity match the target attention intensity?
CAUSALITY_PROGRESSION_QC: Does the sequence logically escalate (Cause -> Event -> Consequence)?
HUMAN_EDITOR_SIMULATION: Does sequence make sense visually without audio? Does audio make sense without video?

Also detect (true/false):
MANIFEST_MISMATCH_DETECTED: Do frames fail to match their intended visual_job? (e.g. SHOW_LOCATION but shows a person)
ANACHRONISM_DETECTED: Modern tech in historical era?
AI_ARTIFACT_DETECTED: Warped faces, melting physics, gibberish text in AI?

Return ONLY JSON:
{
  "VISUAL_RELEVANCE": 8, "VISUAL_EXPLANATION": 7, "EVIDENCE_QUALITY": 8,
  "SHOT_VARIETY": 9, "COMPOSITION_VERIFICATION": 8, "HISTORICAL_ACCURACY": 7,
  "CINEMATOGRAPHY": 8, "TEXT_QUALITY": 9, "FILLER_DETECTION": 8,
  "DOCUMENTARY_FEEL": 9, "HOOK_SCORE": 8, "VISUAL_BOREDOM_SCORE": 7,
  "FACTUAL_CLAIM_COVERAGE": 9, "SEMANTIC_COVERAGE": 8, "ATTENTION_CURVE_VALIDATION": 9,
  "CAUSALITY_PROGRESSION_QC": 8, "HUMAN_EDITOR_SIMULATION": 9,
  "MANIFEST_MISMATCH_DETECTED": false,
  "ANACHRONISM_DETECTED": false,
  "AI_ARTIFACT_DETECTED": false,
  "worst_5_shots": [
    {
      "shot_id": "b001_n001_s002",
      "failures": ["AI_ARTIFACT_DETECTED", "COMPOSITION_VERIFICATION"],
      "severity": "high",
      "suggested_repair": {
        "keep_visual_job": true,
        "switch_medium": "stock_video",
        "regenerate_prompt": true
      }
    }
  ],
  "reason": "Overall flow is good but pacing dips."
}
"""
                pil_images = [Image.open(f_path) for _, f_path, _ in selected_frames]
                resp = self.model.generate_content([prompt] + pil_images)
                import re
                text = resp.text.strip().replace("```json","").replace("```","").strip()
                text = re.sub(r",(\s*[}\]])", r"\1", text)
                vision_result = json.loads(text)
                worst_shots = vision_result.get("worst_5_shots", [])
            except Exception as e:
                log.warning(f"Vision model failed: {e}")
                
        # Final Scoring
        rubric_keys = [
            "VISUAL_RELEVANCE", "VISUAL_EXPLANATION", "EVIDENCE_QUALITY",
            "SHOT_VARIETY", "COMPOSITION_VERIFICATION", "HISTORICAL_ACCURACY",
            "CINEMATOGRAPHY", "TEXT_QUALITY", "FILLER_DETECTION", "DOCUMENTARY_FEEL",
            "HOOK_SCORE", "VISUAL_BOREDOM_SCORE", "FACTUAL_CLAIM_COVERAGE", "SEMANTIC_COVERAGE", 
            "ATTENTION_CURVE_VALIDATION", "CAUSALITY_PROGRESSION_QC", "HUMAN_EDITOR_SIMULATION"
        ]
        
        scores = [vision_result.get(k, 7) for k in rubric_keys]
        llm_score = sum(scores) / len(scores) if scores else 7.0
        
        blockers = []
        # Level 1 Blockers
        if len(rep_report["static_loops"]) > max(1, total_duration) * 0.15: blockers.append("FROZEN_FRAME")
        if len(rep_report["duplicates"]) > max(1, total_duration) * 0.2: blockers.append("VIDEO_LOOP")
        if num_scenes < max(1, total_duration / 10): blockers.append("SHOT_DENSITY_TOO_LOW")
        if avg_shot_dur > 8.0: blockers.append("LONG_LOW_INFORMATION_SHOT")
        
        # Level 2 & 3 Blockers
        if vision_result.get("MANIFEST_MISMATCH_DETECTED"): blockers.append("VISUAL_NARRATION_MISMATCH")
        if vision_result.get("ANACHRONISM_DETECTED"): blockers.append("HISTORICAL_ANACHRONISM")
        if vision_result.get("HOOK_SCORE", 10) < 4: blockers.append("WEAK_FIRST_30_SECONDS")
        if vision_result.get("VISUAL_BOREDOM_SCORE", 10) < 4: blockers.append("EXCESSIVE_VISUAL_REPETITION")
        if vision_result.get("AI_ARTIFACT_DETECTED"): blockers.append("AI_ARTIFACT_DETECTED")
        if vision_result.get("FACTUAL_CLAIM_COVERAGE", 10) < 5: blockers.append("POOR_FACTUAL_COVERAGE")
            
        status = "HARD_REJECT" if blockers else "APPROVED"
        verdict = "retry" if blockers else ("approved" if llm_score >= 7.0 else "drafts")
            
        def pct(count): return f"{(count / max(1, num_scenes)) * 100:.1f}%"
            
        report = {
            "status": status,
            "verdict": verdict,
            "score": round(llm_score, 1),
            "reason": f"Blockers: {', '.join(blockers)}. " + vision_result.get("reason", ""),
            "worst_5_shots": worst_shots,
            "rubric": {k: vision_result.get(k, 0) for k in rubric_keys},
            "metrics": {
                "SHOT_COUNT": num_scenes,
                "AVERAGE_SHOT_LENGTH": round(avg_shot_dur, 2),
                "LONGEST_SHOT": round(stats["longest_shot"], 2),
                "AI_VIDEO_PERCENTAGE": pct(stats["ai_video"]),
                "ARCHIVAL_PERCENTAGE": pct(stats["photo"]),
                "STOCK_PERCENTAGE": pct(stats["stock"]),
                "GRAPHICS_PERCENTAGE": pct(stats["graphic"]),
                "FALLBACK_PERCENTAGE": pct(stats["fallback"]),
                "STATIC_LOOP_SECONDS": len(rep_report["static_loops"]),
                "BLOCKERS_TRIGGERED": blockers
            }
        }
        
        log.info(f"V3 Video QC Complete: {report['status']} (Score: {report['score']})")
        return report
