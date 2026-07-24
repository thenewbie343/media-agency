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
from diffusers import AnimateDiffPipeline, MotionAdapter, DDIMScheduler

# ── Load AnimateDiff (SD1.5 - T4 compatible, ~3.5GB RAM) ──
print("Loading AnimateDiff (SD1.5)...")
adapter_id = "guoyww/animatediff-motion-adapter-v1-5-2"
model_id   = "emilianJR/epiCRealism"

adapter = MotionAdapter.from_pretrained(adapter_id, torch_dtype=torch.float16)
pipe    = AnimateDiffPipeline.from_pretrained(model_id, motion_adapter=adapter, torch_dtype=torch.float16)
pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config, clip_sample=False, timestep_spacing="linspace", steps_offset=1)

pipe.enable_vae_slicing()
pipe.enable_model_cpu_offload()

print("AnimateDiff loaded with CPU offloading and VAE slicing")

# ── Generate each scene ───────────────────────────────────
results = []
for scene in scenes:
    n      = scene["scene"]
    prompt = scene.get("ai_prompt", "cinematic dramatic scene")
    dur    = float(scene.get("duration_hint", 4))
    out    = str(output_dir / f"scene_{n:03d}.mp4")

    num_frames = 16

    print(f"  Scene {n}: '{prompt[:60]}' → {num_frames} frames")
    try:
        output = pipe(
            prompt=f"cinematic 4k, detailed, anime studio ghibli style, {prompt}",
            negative_prompt="blurry, low quality, text, watermark, ugly, deformed, extra limbs",
            height=512,
            width=896,
            num_frames=num_frames,
            guidance_scale=7.5,
            num_inference_steps=20,
            generator=torch.Generator("cpu").manual_seed(n * 17)
        ).frames[0]

        import imageio
        imageio.mimwrite(out, output, fps=8, quality=8)

        if os.path.exists(out) and os.path.getsize(out) > 1000:
            print(f"  Scene {n}: ✓ ({os.path.getsize(out)//1024}KB)")
            with open(out, "rb") as vf:
                b64_data = base64.b64encode(vf.read()).decode('utf-8')
            print(f"<<FILE:scene_{n:03d}.mp4>>\n{b64_data}\n<<EOF>>")
            
            results.append({"scene": n, "file": f"./wan_clips/scene_{n:03d}.mp4", "success": True})
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
