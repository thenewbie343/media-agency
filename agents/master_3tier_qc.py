"""
Master 3-Tier QC Engine (Part 3: Cinematic Execution + Final QC)
Unifies the 3 Core Decision Layers:
- TIER 1: IS IT TRUE? (Asset correctness, provenance, rights, anti-anachronism)
- TIER 2: DOES IT TELL THE STORY? (Micro-beat progression, knowledge delta, info gain >= 0.2, zero redundancy)
- TIER 3: DOES IT FEEL CINEMATIC? (Pacing contrast, SFX restraint, camera language, chapter color, typography)
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

from agents.asset_verifier import AssetVerifier
from agents.sequence_verifier import SequenceVerifier
from agents.cinematic_qc import CinematicQCEngine
from agents.schema import HistoricalFidelity

log = logging.getLogger(__name__)


def _get_val(obj: Union[Dict[str, Any], Any], key: str, default: Any = None) -> Any:
    """Helper to get value from either dict or Pydantic model."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class Master3TierQC:
    """
    Unified 3-Tier Quality Control Gate.
    Evaluates master documentary manifests before final Remotion rendering.
    """

    def __init__(self):
        self.tier1_verifier = AssetVerifier()
        self.tier2_verifier = SequenceVerifier()
        self.tier3_engine = CinematicQCEngine()

    def evaluate_documentary_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes complete 3-Tier QC evaluation across Truth, Story, and Cinematics.
        Returns a comprehensive scorecard and pre-render verdict.
        """
        if not isinstance(manifest, dict) or "story_beats" not in manifest:
            return {
                "overall_score": 0.0,
                "broadcast_approved": False,
                "tier1_truth": {"score": 0.0, "status": "FAIL", "issues": ["Invalid manifest structure"]},
                "tier2_story": {"score": 0.0, "status": "FAIL", "issues": ["Missing story_beats"]},
                "tier3_cinematic": {"score": 0.0, "status": "FAIL", "issues": ["No scenes to evaluate"]},
                "remediation_actions": ["Regenerate manifest using VisualStoryPlanner"]
            }

        story_beats = manifest.get("story_beats", [])

        # ═══════════════════════════════════════════════════════════
        # TIER 1: IS IT TRUE? (Truth & Asset Intelligence)
        # ═══════════════════════════════════════════════════════════
        t1_issues = []
        t1_total_shots = 0
        t1_verified_shots = 0
        anachronism_violations = 0

        for beat in story_beats:
            for block in beat.get("narration_blocks", []):
                for shot in block.get("shots", []):
                    t1_total_shots += 1
                    req = _get_val(shot, "visual_requirement")
                    v_res = _get_val(shot, "verification_result")
                    asset = _get_val(shot, "asset") or {}

                    fidelity = str(_get_val(req, "historical_fidelity", "OPTIONAL"))
                    if "STRICT_ARCHIVAL" in fidelity or "ERA_ACCURATE" in fidelity:
                        # Ensure no stock b-roll was assigned
                        prov = _get_val(shot, "asset_provenance")
                        vtype = _get_val(shot, "visual_type")
                        if prov == "STOCK" and vtype == "broll_video":
                            t1_issues.append(f"Shot {_get_val(shot, 'shot_id')} violates fidelity: generic stock assigned to {fidelity} requirement.")

                    anachronism = float(_get_val(v_res, "anachronism_risk", 0.0))
                    if anachronism > 0.4:
                        anachronism_violations += 1
                        t1_issues.append(f"Shot {_get_val(shot, 'shot_id')} flagged for high anachronism risk ({anachronism:.2f}).")

                    if _get_val(asset, "status") == "success" or _get_val(asset, "path") or _get_val(asset, "fallback_used"):
                        t1_verified_shots += 1

        t1_score = 10.0
        if t1_total_shots > 0:
            t1_score -= (len(t1_issues) * 1.5)
            t1_score = max(1.0, min(10.0, t1_score))

        t1_status = "PASS" if t1_score >= 8.0 and anachronism_violations == 0 else "FAIL"

        # ═══════════════════════════════════════════════════════════
        # TIER 2: DOES IT TELL THE STORY? (Story & Scene Authoring)
        # ═══════════════════════════════════════════════════════════
        t2_issues = []
        t2_scene_pass_count = 0
        total_scenes = 0
        total_info_gain = 0.0
        total_shots_t2 = 0

        for beat in story_beats:
            for block in beat.get("narration_blocks", []):
                total_scenes += 1
                shots = block.get("shots", [])
                
                # Mock editorial scene from block metadata if not standalone
                from agents.schema import EditorialScene
                scene = EditorialScene(
                    scene_id=block.get("block_id", f"scene_{total_scenes}"),
                    scene_intent=block.get("description", "Direct scene"),
                    narrative_function=str(block.get("narrative_intent", beat.get("narrative_intent", "EXPLANATION"))),
                    viewer_emotion="Focus and tension",
                    viewer_question=_get_val(shots[0], "viewer_question", "What does the evidence prove?") if shots else "What happens next?",
                    knowledge_before="Audience perceives initial conditions.",
                    knowledge_after="Audience understands systemic turning point.",
                    visual_argument=_get_val(beat.get("visual_sequence_plan"), "visual_argument", "process vs consequence"),
                    scene_world=_get_val(beat.get("time_context"), "location", "Investigation Setting")
                )

                seq_res = self.tier2_verifier.verify_visual_sequence(scene, shots)
                if seq_res.passed:
                    t2_scene_pass_count += 1
                else:
                    t2_issues.extend(seq_res.issues)

                for s in shots:
                    total_shots_t2 += 1
                    total_info_gain += float(_get_val(s, "information_gain", 0.6))

        avg_ig = (total_info_gain / max(1, total_shots_t2))
        t2_score = 10.0
        if total_scenes > 0:
            scene_pass_rate = t2_scene_pass_count / total_scenes
            t2_score = (scene_pass_rate * 7.0) + (min(1.0, avg_ig / 0.75) * 3.0)
            t2_score = max(1.0, min(10.0, t2_score))

        t2_status = "PASS" if t2_score >= 8.0 else "FAIL"

        # ═══════════════════════════════════════════════════════════
        # TIER 3: DOES IT FEEL CINEMATIC? (Cinematic Execution & Restraint)
        # ═══════════════════════════════════════════════════════════
        t3_eval = self.tier3_engine.evaluate_manifest_director_score(manifest)
        t3_score = float(t3_eval.get("overall_director_score", 8.5))
        t3_issues = t3_eval.get("failures", [])
        t3_status = "PASS" if t3_score >= 8.0 else "FAIL"

        # ═══════════════════════════════════════════════════════════
        # MASTER BROADCAST SCORECARD & VERDICT
        # ═══════════════════════════════════════════════════════════
        overall_score = round((t1_score * 0.35) + (t2_score * 0.35) + (t3_score * 0.30), 2)
        broadcast_approved = (t1_status == "PASS" and t2_status == "PASS" and t3_status == "PASS" and overall_score >= 8.0)

        remediation_actions = []
        if t1_status == "FAIL":
            remediation_actions.append("Re-verify pixel assets against historical fidelity requirements; eliminate anachronisms.")
        if t2_status == "FAIL":
            remediation_actions.append("Re-author low information gain scenes; eliminate consecutive repetitive visual subjects.")
        if t3_status == "FAIL":
            remediation_actions.append("Enforce SFX cooldown restraint (>= 18s) and ensure diverse camera motion vectors.")

        report = {
            "overall_score": overall_score,
            "broadcast_approved": broadcast_approved,
            "verdict": "APPROVED" if broadcast_approved else "REJECTED_NEEDS_REMEDIATION",
            "tier1_truth": {
                "score": round(t1_score, 2),
                "status": t1_status,
                "verified_shots": f"{t1_verified_shots}/{t1_total_shots}",
                "anachronism_violations": anachronism_violations,
                "issues": t1_issues[:5]
            },
            "tier2_story": {
                "score": round(t2_score, 2),
                "status": t2_status,
                "scenes_passed": f"{t2_scene_pass_count}/{total_scenes}",
                "avg_information_gain": round(avg_ig, 3),
                "issues": t2_issues[:5]
            },
            "tier3_cinematic": {
                "score": round(t3_score, 2),
                "status": t3_status,
                "director_metrics": t3_eval.get("validation_metrics", {}),
                "issues": t3_issues[:5]
            },
            "remediation_actions": remediation_actions
        }

        # Save machine-readable scorecard
        try:
            with open("three_tier_qc_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            log.info(f"📊 Master 3-Tier QC Report saved: Overall Score = {overall_score}/10.0 ({report['verdict']})")
        except Exception as e:
            log.warning(f"Could not write three_tier_qc_report.json: {e}")

        return report
