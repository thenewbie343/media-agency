import os
import time
import logging
import subprocess
from typing import Dict, Any, List, Tuple
from enum import Enum

log = logging.getLogger(__name__)

class ReviewMode(Enum):
    FULL_REVIEW = "FULL_REVIEW"
    BALANCED_REVIEW = "BALANCED_REVIEW"
    LOW_QUOTA_REVIEW = "LOW_QUOTA_REVIEW"
    OFFLINE_REVIEW = "OFFLINE_REVIEW"

class GeminiQuotaManager:
    def __init__(self, mode: ReviewMode = ReviewMode.BALANCED_REVIEW):
        self.mode = mode
        self.calls_used = 0
        self.calls_avoided = 0
        self.failures = 0
        self.status = "READY"
        
    def can_call(self, priority: float) -> bool:
        if self.mode == ReviewMode.OFFLINE_REVIEW or self.status == "UNAVAILABLE":
            return False
            
        if self.mode == ReviewMode.LOW_QUOTA_REVIEW and priority < 0.8:
            return False
            
        if self.mode == ReviewMode.BALANCED_REVIEW and priority < 0.5:
            # Low priority shots get filtered.
            pass
            
        return True
        
    def record_call(self, success: bool):
        if success:
            self.calls_used += 1
            self.failures = 0 # reset on success
        else:
            self.failures += 1
            if self.failures >= 3:
                log.error("GeminiQuotaManager: Multiple failures detected. Downgrading to OFFLINE_REVIEW.")
                self.mode = ReviewMode.OFFLINE_REVIEW
                self.status = "UNAVAILABLE"

    def record_avoided(self):
        self.calls_avoided += 1

class FrameSampler:
    @staticmethod
    def sample_frames(video_path: str, output_dir: str, num_frames: int = 3) -> List[str]:
        if not os.path.exists(video_path):
            return []
        
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.basename(video_path).split('.')[0]
        
        frames = []
        try:
            cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            duration = float(res.stdout.strip()) if res.stdout.strip() else 4.0
            
            timestamps = [duration * 0.1, duration * 0.5, duration * 0.9]
            if num_frames == 1:
                timestamps = [duration * 0.5]
                
            for i, ts in enumerate(timestamps[:num_frames]):
                out_img = os.path.join(output_dir, f"{base}_frame_{i}.jpg")
                ff_cmd = f'ffmpeg -y -ss {ts:.2f} -i "{video_path}" -frames:v 1 -q:v 2 "{out_img}" -v error'
                subprocess.run(ff_cmd, shell=True)
                if os.path.exists(out_img):
                    frames.append(out_img)
                    
        except Exception as e:
            log.warning(f"FrameSampler failed on {video_path}: {e}")
            
        return frames

class Level0_TechnicalCritic:
    @staticmethod
    def evaluate(file_path: str) -> bool:
        if not file_path or not os.path.exists(file_path):
            return False
            
        if os.path.getsize(file_path) < 1024:
            log.warning(f"Level0 Fail: {file_path} is suspiciously small.")
            return False
            
        return True

class Level1_SemanticCritic:
    @staticmethod
    def evaluate(obs: Dict[str, Any], mode: str) -> Tuple[float, str]:
        # Extract confidence
        entity_score = float(obs.get("entity_confidence", 0.5))
        event_score = float(obs.get("event_confidence", 0.5))
        date_score = float(obs.get("date_confidence", 0.5))
        anachronism = float(obs.get("anachronism_score", 0.0))
        
        if anachronism >= 0.8:
            return 0.1, "FAIL"
            
        confidence = (entity_score * 0.4) + (date_score * 0.4) + (event_score * 0.2)
        
        if confidence >= 0.90:
            return confidence, "PASS"
        elif confidence >= 0.50:
            return confidence, "SUSPECT"
        else:
            return confidence, "FAIL"

class Level2_SelectiveGemini:
    @staticmethod
    def evaluate(quota_manager: GeminiQuotaManager, semantic_confidence: float, editorial_priority: float) -> bool:
        # Determine if we should trigger Gemini
        if semantic_confidence >= 0.90 and editorial_priority < 0.8:
            return False # Avoid Gemini, local is highly confident
            
        if quota_manager.can_call(editorial_priority):
            return True
            
        return False
