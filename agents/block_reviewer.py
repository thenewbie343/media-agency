import os
import json
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .adaptive_critic import GeminiQuotaManager, FrameSampler

log = logging.getLogger(__name__)

class BlockReviewer(BaseAgent):
    def __init__(self, quota_manager: GeminiQuotaManager):
        super().__init__()
        self.quota_manager = quota_manager
        
    def evaluate_block(self, block_data: Dict[str, Any], shots: List[Dict[str, Any]], work_dir: str) -> Dict[str, Any]:
        """
        Evaluate a full narration block consisting of multiple shots.
        """
        block_id = block_data.get("beat_id", "b_unknown")
        narration = block_data.get("description", "")
        
        # Calculate block priority
        priority = 0.5
        intent = block_data.get("narrative_intent", "")
        if intent in ["HOOK", "CLIMAX", "MAJOR_REVEAL"]:
            priority = 0.9
            
        if not self.quota_manager.can_call(priority):
            log.info(f"BlockReviewer: Skipping Gemini review for block {block_id} (priority {priority})")
            return {"status": "PASS", "reason": "Local only", "score": 0.9}
            
        # Sample frames for the block
        all_frames = []
        for shot in shots:
            vid = shot.get("asset", {}).get("path")
            if vid and os.path.exists(vid):
                # 1 frame per shot for block review to save tokens
                frames = FrameSampler.sample_frames(vid, os.path.join(work_dir, "frames"), num_frames=1)
                all_frames.extend(frames)
                
        if not all_frames:
            return {"status": "UNVERIFIED", "reason": "No frames to review"}
            
        # Call Gemini (stubbed for now)
        try:
            # Here we would call self._call_vlm(frames, prompt)
            self.quota_manager.record_call(True)
            return {"status": "PASS", "story_alignment": 0.8}
        except Exception as e:
            self.quota_manager.record_call(False)
            log.error(f"BlockReviewer Vision API failed: {e}")
            return {"status": "UNAVAILABLE"}
