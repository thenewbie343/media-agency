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

        # ── EMOTIONAL STORYTELLING QC GATE ──
        emotional_verdict = "ALIVE"
        all_blocks = []
        for beat in director_manifest.get("story_beats", []):
            for block in beat.get("narration_blocks", []):
                all_blocks.append(block)

        if all_blocks:
            # Check for flat dramatic tension (all same value)
            tensions = [b.get("dramatic_tension", 0.5) for b in all_blocks if "dramatic_tension" in b]
            if tensions and len(set(tensions)) <= 1:
                emotional_verdict = "FLAT"
                qc_failures.append("FLAT_EMOTIONAL_CURVE: All scenes have identical dramatic_tension. Script lacks emotional dynamics.")
                overall_director_score = min(overall_director_score, 5.0)

            # Check for AI cliche phrases in voiceovers
            banned_phrases = [
                "in the world of", "little did they know", "let's delve",
                "it's worth noting", "buckle up", "strap in",
                "in a shocking turn", "this begs the question",
                "at the end of the day", "the landscape of", "nestled in"
            ]
            all_text = " ".join(b.get("voiceover", "").lower() + " " + b.get("caption", "").lower() for b in all_blocks)
            found_cliches = [p for p in banned_phrases if p in all_text]
            if found_cliches:
                emotional_verdict = "MONOTONE"
                qc_failures.append(f"AI_CLICHE_DETECTED: Found banned phrases: {', '.join(found_cliches)}")
                overall_director_score -= 1.5

            # Check for strategic silence (breathing room)
            has_silence = any(
                (b.get("strategic_silence") or {}).get("duration_seconds", 0) > 0
                for b in all_blocks
            ) or float(metrics.get("number_of_silence_moments", 0)) > 0
            if not has_silence:
                qc_failures.append("NO_BREATHING_ROOM: Zero strategic silences. Script will sound rushed.")
                overall_director_score -= 0.5

        metrics["emotional_verdict"] = emotional_verdict

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
1. 20 Visual Jobs Validation: Every shot MUST have a defined `visual_job`.
2. Anti-Literal Rule & Mute Test: Reject any shot that merely illustrates spoken words literally.
3. 12 Shot Relationships: Adjacent shots must follow relational grammar.
4. Camera Motion & Composition Diversity: Consecutive identical motions (>2) = FAIL.
5. Cinematography Completeness: Every non-graphic shot must define `lens`, `camera_angle`, `composition`. (`lighting` and `depth` are OPTIONAL and should NOT cause rejection if missing).
6. Editorial Cut Reason: Generic `cut_reason` = FAIL.
7. Dramatic Numbers & Motifs: Numbers punctuated with typography, motifs escalate.
8. Human Anchor Grounding: Abstract systems anchored in physical human consequence.
9. SFX Pacing Restraint: 1-4 SFX per minute with strategic silence on reveals.
10. REPAIR ISOLATION: Repairs must ONLY modify failure-related fields.

EMOTIONAL STORYTELLING QC (NEW — MANDATORY):
11. FLAT SCRIPT DETECTION: If ALL scenes have the same `dramatic_tension` value OR lack `viewer_emotion`, REJECT immediately. Score = 3.
12. PACING MONOTONY: If ALL blocks have similar word counts (variance < 10%), the script lacks rhythmic variety. Flag as WARNING.
13. VISCERAL LANGUAGE CHECK: If zero scenes contain sensory details (physical sensations, environmental sounds, human internal states), score penalty of -2.0.
14. AI CLICHE DETECTION: If the script contains banned AI phrases ("In the world of", "Little did they know", "Let's delve deeper", "It's worth noting", "Buckle up"), REJECT with score = 4.
15. EMOTIONAL CURVE: The `dramatic_tension` values across scenes should form a CURVE (rising to climax, brief dip, final peak) — NOT a flat line.
16. BREATHING ROOM: At least 1 scene must have `strategic_silence` > 0. Dead air is a storytelling tool.
17. HUMAN STAKES: At least 1 scene must reference a specific named person or human consequence.

You must return a JSON object in this exact format:
{
  "status": "APPROVED" | "REJECTED",
  "score": <1-10>,
  "feedback": "Detailed explanation of why it passed or failed.",
  "emotional_verdict": "ALIVE" | "FLAT" | "MONOTONE",
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
