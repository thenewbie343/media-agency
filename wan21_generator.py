"""
wan21_generator.py
==================
This script runs ON Google Colab T4 GPU (NOT on GitHub Actions).
GitHub Actions installs Colab CLI and calls:
  colab run --gpu T4 wan21_generator.py

It receives scene prompts via a JSON file,
generates video clips using Wan2.1-T2V-1.3B,
saves them to /content/clips/,
and Colab CLI downloads them back.

Usage by pipeline.py:
  - pipeline.py writes scene_prompts.json
  - GitHub Actions uploads it to Colab via colab upload
  - colab run --gpu T4 wan21_generator.py
  - colab download /content/clips/ ./wan_clips/
  - pipeline.py picks up clips from ./wan_clips/
"""

import json, os, subprocess, sys
import base64
import threading
import time
from pathlib import Path

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

def keep_alive():
    while True:
        print("... [keepalive] ...", file=sys.stderr, flush=True)
        time.sleep(15)

threading.Thread(target=keep_alive, daemon=True).start()

# ── Read scene prompts from sys.argv[1] ───────────────────
if len(sys.argv) < 2:
    print("Error: No prompts provided. Pass JSON string as argument.")
    sys.exit(1)

scenes = json.loads(sys.argv[1])
output_dir = Path("/content/clips")
output_dir.mkdir(exist_ok=True)

print(f"Wan2.1 generator: {len(scenes)} scenes to generate")

if len(sys.argv) > 2 and sys.argv[2]:
    hf_token = sys.argv[2]
    # Set HF_TOKEN environment variable so diffusers can pick it up automatically
    os.environ["HF_TOKEN"] = hf_token

# ── Install AnimateDiff dependencies ───────────────────────────
print("Installing dependencies...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q",
    "diffusers", "transformers", "accelerate",
    "torch", "torchvision", "imageio[ffmpeg]",
    "safetensors"], check=True)

import torch
from diffusers import AnimateDiffPipeline, MotionAdapter, DPMSolverMultistepScheduler

# ── Load AnimateDiff (SD1.5 Realistic/Artistic Model - T4 compatible) ──
print("Loading AnimateDiff (DreamShaper v8)...")
adapter_id = "guoyww/animatediff-motion-adapter-v1-5-2"
model_id   = "stablediffusionapi/dreamshaper-v8"
fallback_model_id = "runwayml/stable-diffusion-v1-5"

try:
    adapter = MotionAdapter.from_pretrained(adapter_id, torch_dtype=torch.float16)
except Exception as e:
    print(f"MotionAdapter load notice ({e}). Retrying without HF_TOKEN...")
    if "HF_TOKEN" in os.environ:
        del os.environ["HF_TOKEN"]
    adapter = MotionAdapter.from_pretrained(adapter_id, torch_dtype=torch.float16)

try:
    pipe = AnimateDiffPipeline.from_pretrained(model_id, motion_adapter=adapter, torch_dtype=torch.float16)
except Exception as e:
    print(f"Primary model ({model_id}) load notice ({e}). Falling back to {fallback_model_id}...")
    if "HF_TOKEN" in os.environ:
        del os.environ["HF_TOKEN"]
    pipe = AnimateDiffPipeline.from_pretrained(fallback_model_id, motion_adapter=adapter, torch_dtype=torch.float16)

# CRITICAL: Force linear beta schedule for AnimateDiff compatibility to prevent noise
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config,
    beta_schedule="linear",
    algorithm_type="dpmsolver++",
    use_karras_sigmas=True
)

# Disable safety checker to prevent false positives (black frames) on historical content
pipe.safety_checker = None
pipe.requires_safety_checker = False

if hasattr(pipe, "enable_vae_slicing"):
    pipe.enable_vae_slicing()
if hasattr(pipe, "enable_model_cpu_offload"):
    pipe.enable_model_cpu_offload()

print("AnimateDiff Engine loaded successfully with DreamShaper v8 & DPM++ 2M Karras")

ANTI_MUTATION_NEGATIVE = (
    "flickering, frame boiling, morphing, shape shifting, unstable background, "
    "sudden jitter, warp, temporal incoherence, deformed, distorted, disfigured, "
    "extra limbs, missing limbs, bad anatomy, floating objects, mutation, "
    "over-saturated, hyper-detailed noise, text, watermark, signature"
)

# ── Generate each scene ───────────────────────────────────
results = []
for scene in scenes:
    n      = scene["scene"]
    prompt = scene.get("ai_prompt", "cinematic dramatic scene")
    dur    = float(scene.get("duration_hint", 4))
    
    # Reconcile numeric/string scene ID
    is_num = False
    try:
        int(n)
        is_num = True
    except:
        pass
        
    filename = f"scene_{int(n):03d}.mp4" if is_num else f"scene_{n}.mp4"
    out    = str(output_dir / filename)

    # Dynamically calculate frames based on audio duration (8 fps)
    # Cap at 48 frames (6 seconds) to prevent Colab T4 OutOfMemory errors
    num_frames = min(max(16, int(dur * 8)), 48)

    # Calculate a stable numeric seed
    if is_num:
        seed_val = int(n) * 17
    else:
        import zlib
        seed_val = zlib.adler32(str(n).encode('utf-8'))

    print(f"  Scene {n}: '{prompt[:60]}' → {num_frames} frames (seed: {seed_val})")
    try:
        output = pipe(
            prompt=f"masterpiece, best quality, ultra-detailed, {prompt}",
            negative_prompt=ANTI_MUTATION_NEGATIVE,
            height=448,
            width=768,
            num_frames=num_frames,
            guidance_scale=6.5,
            num_inference_steps=25,
            generator=torch.Generator().manual_seed(seed_val)
        ).frames[0]

        import numpy as np
        import imageio
        frames_np = [np.array(f) for f in output]
        # CRITICAL: Remotion uses Chrome which requires yuv420p pixel format for H264 MP4 videos.
        # Default imageio RGB export uses yuv444p which causes delayRender() timeout failures!
        imageio.mimwrite(out, frames_np, fps=8, quality=9, output_params=["-pix_fmt", "yuv420p"])

        if os.path.exists(out) and os.path.getsize(out) > 1000:
            print(f"  Scene {n}: ✓ ({os.path.getsize(out)//1024}KB)")
            with open(out, "rb") as vf:
                b64_data = base64.b64encode(vf.read()).decode('utf-8')
            print(f"<<FILE:{filename}>>\n{b64_data}\n<<EOF>>")
            
            results.append({"scene": n, "file": f"./wan_clips/{filename}", "success": True})
        else:
            print(f"  Scene {n}: ✗ empty file")
            results.append({"scene": n, "file": None, "success": False})

    except Exception as e:
        print(f"  Scene {n}: ✗ {e}")
        results.append({"scene": n, "file": None, "success": False})

# Output the results manifest via base64 as well
manifest = json.dumps(results)
print(f"<<FILE:wan21_results.json>>\n{base64.b64encode(manifest.encode('utf-8')).decode('utf-8')}\n<<EOF>>")
print(f"\nDone. Generated {sum(1 for r in results if r['success'])}/{len(scenes)} clips")
