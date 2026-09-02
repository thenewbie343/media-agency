"""
V3 Authored Vertical Slice Benchmark Runner
Executes the full real pipeline: Claim -> EvidenceAsset -> EditorialScene -> VisualSequence -> Shot -> ShotRenderer -> Remotion
Topic: The 1983 Soviet Nuclear False Alarm (Stanislav Petrov)
Target Duration: 60.0 Seconds
"""

import os
import sys
import json
import shutil
import logging
import subprocess
from pathlib import Path

# Setup paths
MEDIA_AGENCY_DIR = Path(r"c:\Users\Asus\Downloads\assets\media-agency")
sys.path.append(str(MEDIA_AGENCY_DIR))

import pipeline
from scratch.v3_fixture_data import get_v3_petrov_fixture

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("v3_authored_benchmark")

def main():
    log.info("🎬 ====================================================================")
    log.info("🎬 ANTIGRAVITY V3 — AUTHORED VERTICAL SLICE BENCHMARK")
    log.info("🎬 Topic: The Computer Error That Almost Started World War 3 (1983)")
    log.info("🎬 Target: 60-Second Full Editorial Sequence (Evidence + Reconstruction + Graphics)")
    log.info("🎬 ====================================================================")

    # 1. Load Fixture (Claims, Evidence Assets, 10-Shot Sequence)
    manifest, claims, evidence_items = get_v3_petrov_fixture()
    log.info(f"Loaded {len(claims)} Claims and {len(evidence_items)} Primary Evidence Assets.")
    
    cfg = {
        "topic": "The Computer Error That Almost Started World War 3",
        "genre": "investigative_documentary",
        "lang": "english",
        "voice": "en-US-ChristopherNeural",
        "fps": 30
    }

    workspace = MEDIA_AGENCY_DIR / "workspace_v3_authored"
    workspace.mkdir(parents=True, exist_ok=True)
    pipeline.WORKSPACE = workspace

    manifest_dict = manifest.model_dump()
    with open(workspace / "script_raw.json", "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)

    # 2. Stage 3: Voice Generation (Edge-TTS / Kokoro)
    log.info("🎙️ Generating Voiceover Audio via Stage 3...")
    manifest_dict = pipeline.stage_3_voice(manifest_dict, cfg)

    # 3. Stage 6: Visual Retrieval / Generation for Reconstruction Shots
    log.info("🎨 Generating Visuals & Reconstructions via Stage 6...")
    manifest_dict = pipeline.stage_6_visuals(manifest_dict, cfg)

    # 4. Copy Assets into Remotion Public Assets Folder
    remotion_public = MEDIA_AGENCY_DIR / "remotion" / "public" / "assets"
    remotion_public.mkdir(parents=True, exist_ok=True)

    log.info("📦 Synchronizing assets into Remotion public catalog...")
    for beat in manifest_dict.get("story_beats", []):
        for block in beat.get("narration_blocks", []):
            if block.get("audio_file"):
                src = Path(block["audio_file"])
                if src.exists():
                    dest = remotion_public / src.name
                    shutil.copy2(src, dest)
                    block["audio_file"] = src.name

            for shot in block.get("shots", []):
                asset = shot.get("asset", {})
                for key in ["path", "bg_file", "fg_file"]:
                    if asset.get(key):
                        src = Path(asset[key])
                        if src.exists():
                            dest = remotion_public / src.name
                            shutil.copy2(src, dest)
                            asset[key] = src.name

    # 5. Save Remotion Props
    script_props_path = workspace / "script_remotion.json"
    with open(script_props_path, "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)

    # 6. Audit Assets
    audit_passed, missing_assets = pipeline.audit_assets(str(script_props_path))
    if not audit_passed:
        log.warning(f"Audit reported missing non-critical assets: {missing_assets}")
    else:
        log.info("✅ Pre-Render Asset Audit PASSED!")

    # 7. Render via Remotion
    final_video_raw = str((workspace / "final_documentary_raw.mp4").resolve())
    remotion_cmd = (
        f"npx remotion render src/index.ts DocumentaryVideo \"{final_video_raw}\" "
        f"--props=\"{script_props_path}\" --concurrency=2 "
        f"--delay-render-timeout-in-milliseconds=60000 --log=verbose --crf=22"
    )

    log.info(f"🚀 Executing Remotion Render: {remotion_cmd}")
    res = subprocess.run(
        remotion_cmd,
        cwd=str(MEDIA_AGENCY_DIR / "remotion"),
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if res.returncode != 0:
        log.error(f"❌ Remotion render failed:\n{res.stderr}")
        raise RuntimeError("Remotion render failed")

    log.info("✅ Remotion render complete!")

    # 8. Audio Mix (BGM Ducking + Room Tone)
    final_video_mastered = pipeline.stage_assemble_documentary(manifest_dict, cfg, final_video_raw, "")
    log.info(f"🏆 Final Mastered Video: {final_video_mastered}")

    # 9. Copy to Brain Artifacts
    artifact_dir = Path(r"c:\Users\Asus\.gemini\antigravity\brain\cb637683-2dde-4a49-aa58-16dbdda693df")
    artifact_video = artifact_dir / "test_v3_authored_benchmark.mp4"
    shutil.copy2(final_video_mastered, artifact_video)
    log.info(f"📁 Copied to Artifacts: {artifact_video}")
    log.info("🎯 BENCHMARK RUN COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
