"""
QC Editor Agent
Supervises script and manifest quality, enforcing the 17 Cinematic Validation Metrics,
directorial grammar, anti-literal visual arguments, and surgical repair isolation.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent
from .cinematic_qc import CinematicQCEngine

log = logging.getLogger("agency")


class QCEditorAgent(BaseAgent):
    """
    Supervising QC Editor Agent (R6).
    Evaluates hierarchical ScriptManifest against directorial quality,
    the 17 Cinematic Validation Metrics, and isolated surgical repair constraints.
    """

    def __init__(self):
        super().__init__()
        self.qc_engine = CinematicQCEngine()

    def _get_mock_fallback(self, prompt: str, system: str, force_json: bool) -> Dict[str, Any]:
        """Provides a context-aware mock fallback for QCEditor reflecting prompt metrics."""
        if "Verdict: REJECT" in prompt or "Failures:" in prompt:
            return {
                "status": "REJECTED",
                "score": 5,
                "feedback": "QC Editor rejected manifest due to directorial quality and 17 QC metric failures.",
                "failures": [
                    {
                        "shot_id": "detected_shots",
                        "beat_id": "b001",
                        "failure_type": "DIRECTORIAL_QC_FAIL",
                        "severity": "high",
                        "repair": {
                            "preserve_narration": True,
                            "preserve_timing": True,
                            "preserve_beat": True,
                            "preserve_ids": True,
                            "replace_visual_only": True,
                            "recommended_visual_job": "EXAMINE_EVIDENCE"
                        }
                    }
                ]
            }
        return {
            "status": "APPROVED",
            "score": 9,
            "feedback": "Directorial quality approved. 17 QC metrics validated.",
            "failures": []
        }

    def review_script(self, director_manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reviews the director's hierarchical script, evaluating editorial quality against 17 QC metrics.
        """
        log.info("[*] QCEditorAgent evaluating editorial quality via 17 cinematic QC metrics and supervising editor...")

        # Ensure we are dealing with a dict (v2 Schema)
        if not isinstance(director_manifest, dict) or "story_beats" not in director_manifest:
            log.warning("QC failed: manifest is not a valid v2 ScriptManifest dict.")
            return {
                "status": "REJECTED",
                "score": 1,
                "feedback": "Invalid manifest structure. Missing story_beats.",
                "failures": [
                    {
                        "shot_id": "global",
                        "beat_id": "global",
                        "failure_type": "INVALID_SCHEMA",
                        "severity": "critical",
                        "repair": {
                            "preserve_narration": True,
                            "preserve_timing": True,
                            "preserve_beat": True,
                            "preserve_ids": True,
                            "replace_visual_only": False,
                            "recommended_visual_job": "ESTABLISH_WORLD"
                        }
                    }
                ]
            }

        # Deterministic 17 Validation Metrics & Director Score Calculation
        director_eval = self.qc_engine.evaluate_manifest_director_score(director_manifest)
        overall_director_score = float(director_eval.get("overall_director_score", 0.0))
        verdict = director_eval.get("verdict", "REJECT")
        qc_failures = director_eval.get("failures", [])
        metrics = director_eval.get("validation_metrics", {})
        score_matrix = director_eval.get("director_score_matrix", {})

        has_api_keys = bool(os.environ.get("GEMINI_KEY") or os.environ.get("GROQ_KEY"))

        if not has_api_keys:
            # Deterministic Programmatic Evaluation when offline / test mode
            if overall_director_score >= 8.0 and verdict == "APPROVED" and len(qc_failures) == 0:
                return {
                    "status": "APPROVED",
                    "score": max(8, int(round(overall_director_score))),
                    "feedback": f"Directorial quality approved. 17 QC metrics validated with director score {overall_director_score}/10.0.",
                    "failures": [],
                    "validation_metrics": metrics,
                    "director_score_matrix": score_matrix,
                    "director_score": overall_director_score
                }
            else:
                failures = []
                for fail in (qc_failures or ["Director score below threshold 8.0"]):
                    failures.append({
                        "shot_id": "detected_shots",
                        "beat_id": "b001",
                        "failure_type": "DIRECTORIAL_QC_FAIL",
                        "severity": "high",
                        "description": fail,
                        "repair": {
                            "preserve_narration": True,
                            "preserve_timing": True,
                            "preserve_beat": True,
                            "preserve_ids": True,
                            "replace_visual_only": True,
                            "recommended_visual_job": "EXAMINE_EVIDENCE"
                        }
                    })

                status = "APPROVED" if (overall_director_score >= 8.0 and not qc_failures) else "REJECTED"
                return {
                    "status": status,
                    "score": max(1, int(round(overall_director_score))),
                    "feedback": (
                        f"Directorial quality approved with warnings ({overall_director_score}/10.0)"
                        if status == "APPROVED"
                        else f"QC Editor Rejected Script: {'; '.join(qc_failures) if qc_failures else 'Director score below 8.0'}"
                    ),
                    "failures": failures,
                    "validation_metrics": metrics,
                    "director_score_matrix": score_matrix,
                    "director_score": overall_director_score
                }

        system_prompt = """You are the Supervising Editor for an elite cinematic YouTube documentary.
Your job is to strictly evaluate the editorial quality of the generated ScriptManifest.

CRITICAL EDITORIAL RULES & 17 DIRECTORIAL QC METRICS:
1. 20 Visual Jobs Validation: Every shot MUST have a defined `visual_job` (e.g. ESTABLISH_WORLD, SHOW_EVIDENCE, EXAMINE_EVIDENCE, VISUALIZE_ABSTRACT_CONCEPT, HUMANIZE, REVEAL).
2. Anti-Literal Rule & Mute Test: Reject any shot that merely illustrates spoken words literally. The sequence must communicate a visual argument even when muted.
3. 12 Shot Relationships: Adjacent shots must follow relational grammar (e.g., DETAIL_TO_CONTEXT, NUMBER_TO_SCALE, EVIDENCE_TO_REVEAL, CONTRAST).
4. Camera Motion & Composition Diversity: Consecutive identical camera motions (>2) or compositions is a FAIL (Camera Fatigue). Static holds on evidence/reveals are rewarded.
5. Cinematography Completeness: Every non-graphic visual shot must define `lens`, `camera_angle`, and `composition`.
6. Editorial Cut Reason: Generic `cut_reason` (e.g. introduce_information, transition, show_fact) is a FAIL. Must be highly specific.
7. Dramatic Numbers & Motifs: Numbers must be punctuated with kinetic typography, and recurring visual motifs must escalate across acts.
8. Human Anchor Grounding: Abstract systems must be anchored in physical human consequence.
9. SFX Pacing Restraint: SFX must be restrained (1-4 per minute) with deliberate strategic silence on reveals.
10. REPAIR ISOLATION: When recommending a repair, you MUST instruct the Director to ONLY modify fields related to the failure. Under NO circumstances should narration, beat chronology, or unrelated IDs be modified to fix visual or camera issues.

You must return a JSON object in this exact format:
{
  "status": "APPROVED" | "REJECTED",
  "score": <1-10>,
  "feedback": "Detailed explanation of why it passed or failed.",
  "failures": [
    {
      "shot_id": "n001_s001",
      "beat_id": "b001",
      "failure_type": "VISUAL_REDUNDANCY",
      "severity": "high",
      "repair": {
        "preserve_narration": true,
        "preserve_timing": true,
        "preserve_beat": true,
        "preserve_ids": true,
        "replace_visual_only": true,
        "recommended_visual_job": "SHOW_EVIDENCE"
      }
    }
  ]
}
"""

        prompt = f"""ScriptManifest:
{json.dumps(director_manifest, indent=2)}

Computed 17 Directorial QC Metrics:
{json.dumps(metrics, indent=2)}

Computed Director Score Matrix:
{json.dumps(score_matrix, indent=2)}
Overall Director Score: {overall_director_score}/10.0 (Verdict: {verdict})
Failures: {json.dumps(qc_failures)}

Evaluate the editorial quality and return the JSON response."""

        try:
            output_dict = self.call_llm(prompt, system_prompt)
            if not isinstance(output_dict, dict) or "status" not in output_dict:
                raise ValueError("Invalid LLM response format for QC Editor")

            # Attach computed 17 metrics and director score matrix
            output_dict["validation_metrics"] = metrics
            output_dict["director_score_matrix"] = score_matrix
            output_dict["director_score"] = overall_director_score

            log.info(f"[*] QC Result: {output_dict.get('status')} (Score: {output_dict.get('score')})")
            if output_dict.get('status') == 'REJECTED':
                log.warning(f"QC Editor Rejected Script: {output_dict.get('feedback')}")
            return output_dict

        except Exception as e:
            log.warning(f"QC Editor Agent falling back to deterministic evaluation: {str(e)}")

            if overall_director_score >= 8.0 and verdict == "APPROVED" and len(qc_failures) == 0:
                return {
                    "status": "APPROVED",
                    "score": max(8, int(round(overall_director_score))),
                    "feedback": f"Directorial quality approved. 17 QC metrics validated with director score {overall_director_score}/10.0.",
                    "failures": [],
                    "validation_metrics": metrics,
                    "director_score_matrix": score_matrix,
                    "director_score": overall_director_score
                }
            else:
                failures = []
                for fail in qc_failures:
                    failures.append({
                        "shot_id": "detected_shots",
                        "beat_id": "b001",
                        "failure_type": "DIRECTORIAL_QC_FAIL",
                        "severity": "high",
                        "description": fail,
                        "repair": {
                            "preserve_narration": True,
                            "preserve_timing": True,
                            "preserve_beat": True,
                            "preserve_ids": True,
                            "replace_visual_only": True,
                            "recommended_visual_job": "EXAMINE_EVIDENCE"
                        }
                    })

                status = "APPROVED" if overall_director_score >= 8.0 and not failures else "REJECTED"
                return {
                    "status": status,
                    "score": max(1, int(round(overall_director_score))),
                    "feedback": (
                        f"Directorial quality approved with warnings ({overall_director_score}/10.0)"
                        if status == "APPROVED"
                        else f"QC Editor Rejected Script: {'; '.join(qc_failures) if qc_failures else 'Director score below 8.0'}"
                    ),
                    "failures": failures,
                    "validation_metrics": metrics,
                    "director_score_matrix": score_matrix,
                    "director_score": overall_director_score
                }
