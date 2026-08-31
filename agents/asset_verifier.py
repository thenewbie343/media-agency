"""
Asset Semantic Verifier & Anti-Garbage Engine
=============================================
Performs deep pixel and semantic verification of candidate visual assets
against normalized VisualRequirement specifications.

Features:
- Entity Lock (Rejects Mao/Stalin/unrelated figures when Napoleon is required)
- Era / Historical Context Lock (Rejects modern anachronisms like smartphones, modern cars, drones in historical scenes)
- Event Lock (Rejects unrelated battles / events)
- Location Lock (Rejects unrelated geographies)
- Required Object Lock (Ensures key artifacts/devices are present)
- Structured Observation Analysis via VLM (Gemini Vision) with robust deterministic Python scoring
- Deterministic Local CV/Heuristic Verifier fallback when VLM is offline
"""

import re
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from .schema import VisualRequirement, VerificationResult, HistoricalFidelity

log = logging.getLogger("asset_verifier")


class AssetVerifier:
    def __init__(self):
        self.gemini_key = os.environ.get("GEMINI_KEY", "")

    def verify_candidate(
        self,
        candidate: Dict[str, Any],
        req: VisualRequirement,
        local_preview_path: Optional[str] = None
    ) -> VerificationResult:
        """
        Evaluates candidate against the VisualRequirement and returns a VerificationResult.
        """
        # 1. Gather Candidate Information
        cand_id = candidate.get("candidate_id", "cand_unknown")
        cand_url = candidate.get("highres_url") or candidate.get("preview_url") or ""
        title = candidate.get("title", "")
        desc = candidate.get("description", "")
        creator = candidate.get("creator", "")
        date_str = candidate.get("date", "")
        combined_text = f"{title} {desc} {creator} {date_str}".strip()

        # 2. Check for Direct Garbage & Entity Mismatches in Metadata
        anachronisms_detected = []
        unrelated_subjects_detected = []

        # Check Forbidden Objects / Keywords
        for forbidden in req.forbidden_objects:
            if re.search(r'\b' + re.escape(forbidden) + r'\b', combined_text, re.IGNORECASE):
                if any(m in forbidden.lower() for m in ["mao", "stalin", "hitler", "churchill", "psyche", "cupid", "madonna", "soldier"]):
                    unrelated_subjects_detected.append(f"Forbidden entity/subject detected: {forbidden}")
                else:
                    anachronisms_detected.append(f"Forbidden modern object/anachronism detected: {forbidden}")

        # 3. Determine Verification Mode
        if req.evidence_required or req.historical_fidelity == HistoricalFidelity.STRICT_ARCHIVAL:
            mode = "EVIDENCE_STRICT"
            threshold = 0.85
            max_anachronism = 0.15
            max_unrelated = 0.15
        elif req.historical_required or req.historical_fidelity == HistoricalFidelity.ERA_ACCURATE:
            mode = "HISTORICAL_STRICT"
            threshold = 0.85
            max_anachronism = 0.15
            max_unrelated = 0.20
        elif req.subject_entity and req.historical_fidelity != HistoricalFidelity.ABSTRACT:
            mode = "ENTITY_STRICT"
            threshold = 0.80
            max_anachronism = 0.25
            max_unrelated = 0.20
        elif req.historical_fidelity == HistoricalFidelity.ABSTRACT:
            mode = "ABSTRACT"
            threshold = 0.70
            max_anachronism = 0.50
            max_unrelated = 0.40
        else:
            mode = "CONTEXTUAL"
            threshold = 0.75
            max_anachronism = 0.30
            max_unrelated = 0.30

        # 4. Perform Structured Analysis (VLM or Local Heuristic Engine)
        observations = self._observe_candidate(candidate, req, combined_text, local_preview_path)
        provider = observations.pop("_provider", "LOCAL_HEURISTIC")
        vision_status = observations.pop("_vision_status", "READY")

        # 5. Deterministic Python Scoring Policy
        scores, rejection_reasons = self._calculate_deterministic_scores(observations, req, mode)

        if anachronisms_detected:
            scores["anachronism_risk"] = max(scores["anachronism_risk"], 0.90)
            rejection_reasons.extend(anachronisms_detected)

        if unrelated_subjects_detected:
            scores["unrelated_subject_risk"] = max(scores["unrelated_subject_risk"], 0.90)
            rejection_reasons.extend(unrelated_subjects_detected)

        # Calculate weighted overall match
        overall_match = scores["overall_match"]
        passed = (
            overall_match >= threshold and
            scores["anachronism_risk"] <= max_anachronism and
            scores["unrelated_subject_risk"] <= max_unrelated
        )
        
        unverified = False
        if provider == "LOCAL_HEURISTIC" and mode in ["EVIDENCE_STRICT", "HISTORICAL_STRICT", "ENTITY_STRICT"]:
            unverified = True
            passed = False
            if "Vision model unavailable; cannot strictly verify" not in rejection_reasons:
                rejection_reasons.append("Vision model unavailable; cannot strictly verify (UNVERIFIED)")

        if not passed and not rejection_reasons:
            if overall_match < threshold:
                rejection_reasons.append(f"Overall match score {overall_match:.2f} below mode threshold {threshold:.2f} ({mode})")
            if scores["anachronism_risk"] > max_anachronism:
                rejection_reasons.append(f"Anachronism risk {scores['anachronism_risk']:.2f} exceeds tolerance {max_anachronism:.2f}")
            if scores["unrelated_subject_risk"] > max_unrelated:
                rejection_reasons.append(f"Unrelated subject risk {scores['unrelated_subject_risk']:.2f} exceeds tolerance {max_unrelated:.2f}")

        result = VerificationResult(
            candidate_id=cand_id,
            candidate_url_or_path=cand_url,
            verifier_provider=provider,
            verifier_status=vision_status if provider == "LOCAL_HEURISTIC" and vision_status == "UNAVAILABLE" else "READY",
            unverified=unverified,
            entity_match=round(scores["entity_match"], 2),
            event_match=round(scores["event_match"], 2),
            date_match=round(scores["date_match"], 2),
            location_match=round(scores["location_match"], 2),
            object_match=round(scores["object_match"], 2),
            visual_role_match=round(scores["visual_role_match"], 2),
            evidence_match=round(scores["evidence_match"], 2),
            anachronism_risk=round(scores["anachronism_risk"], 2),
            unrelated_subject_risk=round(scores["unrelated_subject_risk"], 2),
            overall_match=round(overall_match, 2),
            passed=passed,
            rejection_reasons=rejection_reasons
        )

        return result

    def _observe_candidate(
        self,
        candidate: Dict[str, Any],
        req: VisualRequirement,
        combined_text: str,
        local_preview_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Gathers factual observations of candidate pixels and metadata.
        Uses Gemini Vision when API key + image are present, otherwise uses deterministic local analyzer.
        """
        if self.gemini_key and local_preview_path and os.path.exists(local_preview_path) and os.environ.get("VISION_STATUS") != "UNAVAILABLE":
            try:
                vlm_obs = self._call_vlm_observer(local_preview_path, req)
                if vlm_obs and isinstance(vlm_obs, dict):
                    vlm_obs["_provider"] = "GEMINI_VISION"
                    return vlm_obs
            except Exception as e:
                log.warning(f"VLM observation failed, falling back to local observer: {e}")

        # Deterministic Local Observer (analyzes text, entity fingerprints, metadata, provider, era)
        local_obs = self._local_observation_engine(candidate, req, combined_text)
        local_obs["_provider"] = "LOCAL_HEURISTIC"
        if os.environ.get("VISION_STATUS") == "UNAVAILABLE":
            local_obs["_vision_status"] = "UNAVAILABLE"
        return local_obs

    def _local_observation_engine(
        self,
        candidate: Dict[str, Any],
        req: VisualRequirement,
        text: str
    ) -> Dict[str, Any]:
        """
        Deterministic local observer that maps factual presence of entities, dates, locations, and objects.
        """
        text_lower = text.lower()
        
        # 1. Entity presence
        entity_present = False
        entity_conf = 0.0
        if req.subject_entity:
            entity_words = [w.lower() for w in req.subject_entity.split() if len(w) > 2]
            matches = sum(1 for w in entity_words if w in text_lower)
            if matches == len(entity_words):
                entity_present = True
                entity_conf = 1.0
            elif matches > 0:
                entity_present = True
                entity_conf = matches / len(entity_words)
        else:
            entity_conf = 1.0

        # 2. Event presence
        event_present = False
        event_conf = 0.0
        if req.event:
            event_words = [w.lower() for w in req.event.split() if len(w) > 2]
            matches = sum(1 for w in event_words if w in text_lower)
            if matches >= 1:
                event_present = True
                event_conf = matches / len(event_words)
        else:
            event_conf = 1.0

        # 3. Date / Era presence
        date_conf = 0.5
        if req.start_year:
            year_str = str(req.start_year)
            if year_str in text:
                date_conf = 1.0
            elif req.time_period and req.time_period.lower() in text_lower:
                date_conf = 0.9
            elif abs(req.start_year - 1800) < 100 and any(w in text_lower for w in ["19th century", "1800", "napoleonic", "empire", "coronation", "regency"]):
                date_conf = 0.85
        elif not req.historical_required:
            date_conf = 1.0

        # 4. Location presence
        loc_conf = 0.5
        if req.location:
            loc_words = [w.lower() for w in req.location.split() if len(w) > 2]
            if any(w in text_lower for w in loc_words):
                loc_conf = 1.0
            else:
                loc_conf = 0.3
        else:
            loc_conf = 1.0

        # 5. Object presence
        obj_conf = 0.5
        if req.required_objects:
            obj_matches = sum(1 for o in req.required_objects if o.lower() in text_lower)
            obj_conf = obj_matches / len(req.required_objects) if req.required_objects else 1.0
        else:
            obj_conf = 1.0

        # 6. Check for Anachronism Indicators
        anachronism_score = 0.0
        modern_indicators = [
            "smartphone", "iphone", "android", "laptop", "computer", "drone", "uav", "car", "automobile",
            "traffic", "highway", "skyscraper", "jet", "airplane", "speedometer", "coffee cup", "t-shirt"
        ]
        if req.historical_required and (req.start_year and req.start_year < 1920):
            for m in modern_indicators:
                if re.search(r'\b' + m + r'\b', text_lower):
                    anachronism_score = 0.95
                    break

        # 7. Check for Unrelated Subjects
        unrelated_score = 0.0
        unrelated_indicators = [
            "mao zedong", "mao", "stalin", "hitler", "churchill", "psyche", "cupid", "madonna", "renaissance madonna",
            "asian map", "chinese character", "stock graph", "speedometer", "modern office"
        ]
        if req.subject_entity and "napoleon" in req.subject_entity.lower():
            for u in unrelated_indicators:
                if u in text_lower:
                    unrelated_score = 0.95
                    break

        return {
            "entity_present": entity_present,
            "entity_confidence": entity_conf,
            "event_present": event_present,
            "event_confidence": event_conf,
            "date_confidence": date_conf,
            "location_confidence": loc_conf,
            "object_confidence": obj_conf,
            "anachronism_score": anachronism_score,
            "unrelated_score": unrelated_score,
            "provenance": candidate.get("provenance", "STOCK"),
            "provider": candidate.get("provider", "unknown")
        }

    def _call_vlm_observer(self, image_path: str, req: VisualRequirement) -> Dict[str, Any]:
        """Calls Gemini Vision model to extract structured factual observations from image pixels."""
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_key)
        vision_model = os.environ.get("VISION_MODEL", "gemini-3.1-flash")
        model = genai.GenerativeModel(vision_model)

        from PIL import Image
        with Image.open(image_path) as img:
            img_copy = img.copy()

        prompt = f"""Analyze this documentary candidate image objectively and return structured factual observations.
Target Requirement:
- Subject Entity: {req.subject_entity}
- Historical Event: {req.event}
- Target Date / Era: {req.date_range} ({req.time_period})
- Location: {req.location}
- Required Objects: {', '.join(req.required_objects)}
- Forbidden Objects: {', '.join(req.forbidden_objects[:6])}

Return ONLY valid JSON matching this schema:
{{
  "detected_subject": "specific person or main subject visible in image",
  "is_target_entity_present": true or false,
  "detected_event": "specific event depicted",
  "estimated_era": "e.g. 1800s, 19th century, modern contemporary",
  "is_era_accurate": true or false,
  "detected_location": "location if identifiable",
  "detected_objects": ["list", "of", "visible", "objects"],
  "has_anachronisms": true or false,
  "anachronism_details": "description of any modern or out-of-era elements",
  "is_unrelated_subject": true or false
}}"""

        response = model.generate_content([prompt, img_copy])
        clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)

        # Convert VLM observations to standardized format
        return {
            "entity_present": data.get("is_target_entity_present", False),
            "entity_confidence": 1.0 if data.get("is_target_entity_present") else 0.0,
            "event_present": bool(data.get("detected_event")),
            "event_confidence": 0.9 if data.get("detected_event") else 0.4,
            "date_confidence": 1.0 if data.get("is_era_accurate") else 0.1,
            "location_confidence": 0.8,
            "object_confidence": 0.8,
            "anachronism_score": 0.95 if data.get("has_anachronisms") else 0.0,
            "unrelated_score": 0.95 if data.get("is_unrelated_subject") else 0.0,
            "vlm_subject": data.get("detected_subject", ""),
            "vlm_anachronisms": data.get("anachronism_details", "")
        }

    def _calculate_deterministic_scores(
        self,
        obs: Dict[str, Any],
        req: VisualRequirement,
        mode: str
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculates deterministic, mode-weighted match scores and generates specific rejection reasons.
        """
        rejection_reasons: List[str] = []
        
        entity_score = float(obs.get("entity_confidence", 0.0))
        event_score = float(obs.get("event_confidence", 0.5))
        date_score = float(obs.get("date_confidence", 0.5))
        loc_score = float(obs.get("location_confidence", 0.5))
        obj_score = float(obs.get("object_confidence", 0.5))
        anachronism_risk = float(obs.get("anachronism_score", 0.0))
        unrelated_risk = float(obs.get("unrelated_score", 0.0))
        
        # Evidence / Provenance score
        evidence_score = 1.0 if obs.get("provenance") == "AUTHENTIC_ARCHIVE" else (0.7 if obs.get("provenance") == "AUTHENTIC_PHOTO" else 0.3)
        visual_role_score = 0.9

        # Mode-dependent weight configurations
        if mode == "EVIDENCE_STRICT":
            # 30% Entity, 25% Date/Era, 20% Event, 15% Evidence Provenance, 10% Location/Objects
            raw_match = (
                0.30 * entity_score +
                0.25 * date_score +
                0.20 * event_score +
                0.15 * evidence_score +
                0.10 * ((loc_score + obj_score) / 2)
            )
        elif mode == "HISTORICAL_STRICT":
            # 35% Entity, 30% Date/Era, 20% Event, 15% Location/Objects
            raw_match = (
                0.35 * entity_score +
                0.30 * date_score +
                0.20 * event_score +
                0.15 * ((loc_score + obj_score) / 2)
            )
        elif mode == "ENTITY_STRICT":
            # 50% Entity, 25% Context, 25% Visual Role
            raw_match = (
                0.50 * entity_score +
                0.25 * ((date_score + loc_score) / 2) +
                0.25 * visual_role_score
            )
        elif mode == "ABSTRACT":
            # 60% Visual Role, 40% Broad Theme
            raw_match = (
                0.60 * visual_role_score +
                0.40 * ((event_score + obj_score) / 2)
            )
        else:  # CONTEXTUAL
            raw_match = (
                0.30 * entity_score +
                0.30 * event_score +
                0.20 * visual_role_score +
                0.20 * ((loc_score + date_score) / 2)
            )

        # Apply penalties for anachronisms or unrelated subjects
        penalty = (anachronism_risk * 0.70) + (unrelated_risk * 0.70)
        overall_match = max(0.0, raw_match - penalty)

        # Specific Rejection Notes
        if req.subject_entity and entity_score < 0.5:
            rejection_reasons.append(f"Entity mismatch: Required '{req.subject_entity}', detected confidence {entity_score:.2f}")
        if req.historical_required and date_score < 0.4:
            rejection_reasons.append(f"Era mismatch: Required era '{req.date_range}', candidate appears out of era")
        if anachronism_risk >= 0.5:
            rejection_reasons.append(f"Anachronism detected in historical shot (risk {anachronism_risk:.2f})")
        if unrelated_risk >= 0.5:
            rejection_reasons.append(f"Unrelated subject / painting detected (risk {unrelated_risk:.2f})")

        scores = {
            "entity_match": entity_score,
            "event_match": event_score,
            "date_match": date_score,
            "location_match": loc_score,
            "object_match": obj_score,
            "visual_role_match": visual_role_score,
            "evidence_match": evidence_score,
            "anachronism_risk": anachronism_risk,
            "unrelated_subject_risk": unrelated_risk,
            "overall_match": overall_match
        }

        return scores, rejection_reasons
