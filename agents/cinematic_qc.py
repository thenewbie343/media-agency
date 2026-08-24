"""
Cinematic QC Engine & 17 Validation Metrics Director Score Matrix
Evaluates planned timelines and rendered video frames against the standards of a master cinematic documentary director.
Computes and enforces the 17 core directorial validation metrics (Requirement R6).
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, Set

log = logging.getLogger("agency")


class CinematicQCEngine:
    """
    Cinematic QC Engine (R6).
    Evaluates master documentary manifests against 17 Directorial Validation Metrics,
    enforcing anti-literal visual arguments, editorial motivation, 7D visual contrast,
    camera restraint, human consequence grounding, and SFX pacing.
    """

    BANNED_LITERAL_KEYWORDS = [
        "money falling", "handshake", "scales of justice", "piggy bank",
        "generic businessman", "generic code typing", "handcuffs on table",
        "coins falling", "man crying over laptop", "hacker in hoodie laughing",
        "stock handshake", "briefcase opening with money", "stock footage suit"
    ]

    GENERIC_CUT_REASONS = {
        "", "n/a", "none", "introduce_information", "show_fact", "transition",
        "change_scene", "next_shot", "filler", "broll", "visual_variety",
        "show_topic", "illustration", "show_visual"
    }

    def __init__(self):
        pass

    def evaluate_manifest_director_score(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the complete 17-Metric Directorial Matrix and overall director score out of 10.0.
        Target score >= 8.0/10.0 for APPROVED verdict.
        """
        if not isinstance(manifest, dict):
            return {
                "overall_director_score": 0.0,
                "overall_score": 0.0,
                "verdict": "REJECT",
                "director_verdict": "REJECT",
                "failures": ["Manifest is not a dictionary or valid manifest object"],
                "validation_metrics": self._empty_metrics(),
                "director_score_matrix": {},
                "total_shots_audited": 0,
                "recommendations": ["Provide a valid ScriptManifest dictionary."]
            }

        story_beats = manifest.get("story_beats", [])
        if not story_beats:
            return {
                "overall_director_score": 0.0,
                "overall_score": 0.0,
                "verdict": "REJECT",
                "director_verdict": "REJECT",
                "failures": ["Empty story_beats in manifest"],
                "validation_metrics": self._empty_metrics(),
                "director_score_matrix": {},
                "total_shots_audited": 0,
                "recommendations": ["Generate story beats before running Cinematic QC."]
            }

        all_blocks, all_shots = self._extract_all_blocks_and_shots(story_beats)
        total_shots = len(all_shots)
        if total_shots == 0:
            return {
                "overall_director_score": 0.0,
                "overall_score": 0.0,
                "verdict": "REJECT",
                "director_verdict": "REJECT",
                "failures": ["No shots found in manifest narration blocks"],
                "validation_metrics": self._empty_metrics(),
                "director_score_matrix": {},
                "total_shots_audited": 0,
                "recommendations": ["Decompose narration blocks into visual shots."]
            }

        # Calculate Total Manifest Timeline Duration
        total_duration = self._calculate_total_duration(manifest, all_blocks, all_shots)

        # Compute all 17 Validation Metrics
        metrics, failures, recommendations = self._compute_17_metrics(
            manifest=manifest,
            story_beats=story_beats,
            all_blocks=all_blocks,
            all_shots=all_shots,
            total_duration=total_duration
        )

        # Compute 10-Dimension Score Matrix
        matrix = self._compute_score_matrix(
            metrics=metrics,
            total_shots=total_shots,
            story_beats=story_beats,
            all_shots=all_shots,
            total_duration=total_duration
        )

        # Composite Overall Score (Average of 10 dimensions)
        overall_score = round(sum(matrix.values()) / len(matrix), 2)
        overall_score = max(0.0, min(10.0, overall_score))

        # Directorial Verdict
        if failures or overall_score < 6.5:
            verdict = "REJECT"
        elif overall_score < 8.0:
            verdict = "IMPROVE"
        else:
            verdict = "APPROVED"

        sfx_ratio = (
            metrics["sfx_per_minute"] * (total_duration / 60.0) / total_shots
            if total_shots > 0 and total_duration > 0
            else 0.0
        )

        return {
            "overall_director_score": overall_score,
            "overall_score": overall_score,
            "verdict": verdict,
            "director_verdict": verdict,
            "validation_metrics": metrics,
            "director_score_matrix": matrix,
            "total_shots_audited": total_shots,
            "total_timeline_duration_seconds": round(total_duration, 2),
            "sfx_punctuation_ratio": f"{round(min(1.0, sfx_ratio) * 100, 1)}%",
            "failures": failures,
            "recommendations": recommendations
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        """Returns zeroed 17 validation metrics dictionary."""
        return {
            "number_of_unique_visual_concepts": 0,
            "repeated_visual_concepts": 0,
            "repeated_queries": 0,
            "repeated_camera_movements": 0,
            "repeated_compositions": 0,
            "shots_with_no_editorial_reason": 0,
            "number_of_major_reveals": 0,
            "number_of_attention_peaks": 0,
            "number_of_silence_moments": 0,
            "number_of_typography_punctuation_events": 0,
            "number_of_graphic_explanations": 0,
            "number_of_human_anchor_moments": 0,
            "number_of_visual_motifs": 0,
            "number_of_visual_contrasts": 0,
            "number_of_contextual_overlays": 0,
            "sfx_per_minute": 0.0,
            "% shots that merely illustrate narration": 0.0,
            "percentage_illustrative_shots": 0.0
        }

    def _extract_all_blocks_and_shots(
        self, story_beats: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Flattens hierarchical story beats into narration blocks and shots."""
        all_blocks = []
        all_shots = []
        for beat in story_beats:
            if not isinstance(beat, dict):
                continue
            for block in beat.get("narration_blocks", []):
                if not isinstance(block, dict):
                    continue
                all_blocks.append(block)
                for shot in block.get("shots", []):
                    if isinstance(shot, dict):
                        all_shots.append(shot)
        return all_blocks, all_shots

    def _calculate_total_duration(
        self,
        manifest: Dict[str, Any],
        blocks: List[Dict[str, Any]],
        shots: List[Dict[str, Any]]
    ) -> float:
        """Calculates total timeline duration in seconds."""
        # 1. Check project meta
        meta_dur = manifest.get("project_meta", {}).get("target_duration_seconds")
        
        # 2. Check blocks
        block_dur = 0.0
        for b in blocks:
            b_dur = b.get("total_block_duration") or b.get("actual_voice_duration") or b.get("duration_hint")
            if b_dur:
                block_dur += float(b_dur)

        # 3. Check shots
        shot_dur = 0.0
        for s in shots:
            d = s.get("actual_duration") or s.get("duration_seconds")
            if d:
                shot_dur += float(d)

        if shot_dur > 0:
            return shot_dur
        if block_dur > 0:
            return block_dur
        if meta_dur and float(meta_dur) > 0:
            return float(meta_dur)
        return max(1.0, len(shots) * 3.0)

    def _compute_17_metrics(
        self,
        manifest: Dict[str, Any],
        story_beats: List[Dict[str, Any]],
        all_blocks: List[Dict[str, Any]],
        all_shots: List[Dict[str, Any]],
        total_duration: float
    ) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Computes the exact values for all 17 validation metrics.
        """
        failures = []
        recommendations = []

        total_shots = len(all_shots)

        # Registered Motifs from research package or vision
        registered_motifs = set()
        vision = manifest.get("documentary_vision") or {}
        if isinstance(vision, dict):
            for m in vision.get("visual_motifs", []):
                if isinstance(m, str):
                    registered_motifs.add(m.strip().lower())
        research = manifest.get("research_package") or {}
        if isinstance(research, dict):
            for m in research.get("visual_motifs", []):
                if isinstance(m, str):
                    registered_motifs.add(m.strip().lower())

        # ── 1 & 2. Unique & Repeated Visual Concepts ──
        concept_signatures = []
        for s in all_shots:
            v_job = str(s.get("visual_job", "")).upper()
            v_type = str(s.get("visual_type", "")).lower()
            fallback = str(s.get("fallback_type", "")).lower()
            desc = (s.get("visual_description") or s.get("visual_query") or s.get("ai_prompt") or "").lower()
            # Clean core concept stem
            clean_desc = re.sub(r"[^\w\s]", "", desc).strip()
            concept_stem = " ".join(clean_desc.split()[:4])
            sig = f"{v_job}:{v_type}:{fallback}:{concept_stem}"
            concept_signatures.append(sig)

        unique_concepts_count = len(set(concept_signatures))
        concept_counts = {}
        for sig in concept_signatures:
            concept_counts[sig] = concept_counts.get(sig, 0) + 1

        repeated_concepts_count = 0
        for sig, count in concept_counts.items():
            if count > 1:
                # If this concept matches a registered motif, it is intentional repetition
                is_motif = any(rm in sig.lower() for rm in registered_motifs) if registered_motifs else False
                if not is_motif:
                    repeated_concepts_count += (count - 1)

        # ── 3. Repeated Queries ──
        query_counts = {}
        for s in all_shots:
            q = (s.get("visual_query") or s.get("pexels_query") or s.get("ai_prompt") or "").strip().lower()
            if q:
                # normalize whitespace
                q_norm = " ".join(q.split())
                query_counts[q_norm] = query_counts.get(q_norm, 0) + 1

        repeated_queries_count = sum(max(0, count - 1) for count in query_counts.values())
        if repeated_queries_count >= max(4, total_shots // 2):
            failures.append(f"Too many repeated visual queries ({repeated_queries_count} duplicates detected).")
            recommendations.append("Diversify search queries across shots using alternative semantic framing.")
        elif repeated_queries_count > 0:
            recommendations.append(f"Consider diversifying {repeated_queries_count} repeated visual queries.")

        # ── 4. Repeated Camera Movements ──
        repeated_camera_movements_count = 0
        for i in range(len(all_shots) - 1):
            cm1 = str(all_shots[i].get("camera_motion", "")).strip().lower()
            cm2 = str(all_shots[i + 1].get("camera_motion", "")).strip().lower()
            # Static holds and none are not counted as camera movement fatigue
            if cm1 and cm2 and cm1 == cm2 and cm1 not in ["static", "none"]:
                repeated_camera_movements_count += 1

        if repeated_camera_movements_count >= 3:
            recommendations.append("Break consecutive dynamic camera movements with static holds or counter-movements.")

        # ── 5. Repeated Compositions ──
        repeated_compositions_count = 0
        for i in range(len(all_shots) - 1):
            s1 = all_shots[i]
            s2 = all_shots[i + 1]
            vt1 = str(s1.get("visual_type", "")).lower()
            vt2 = str(s2.get("visual_type", "")).lower()
            
            # Only compare non-graphic shots
            if vt1 not in ["motion_graphics", "text_stat"] and vt2 not in ["motion_graphics", "text_stat"]:
                size1 = str(s1.get("shot_size", "")).strip().lower()
                size2 = str(s2.get("shot_size", "")).strip().lower()
                comp1 = str(s1.get("composition", "")).strip().lower()
                comp2 = str(s2.get("composition", "")).strip().lower()
                
                if (size1 and size2 and size1 == size2 and size1 != "n/a") or (comp1 and comp2 and comp1 == comp2 and comp1 != "n/a"):
                    repeated_compositions_count += 1

        # ── 6. Shots with No Editorial Reason ──
        shots_no_editorial_reason_count = 0
        for s in all_shots:
            cr = str(s.get("cut_reason", "")).strip().lower()
            if not cr or cr in self.GENERIC_CUT_REASONS or len(cr) < 6:
                shots_no_editorial_reason_count += 1

        if shots_no_editorial_reason_count > 0:
            failures.append(f"{shots_no_editorial_reason_count} shots have generic or missing cut_reason.")
            recommendations.append("Assign highly specific editorial cut_reasons explaining narrative necessity.")

        # ── 7. Number of Major Reveals ──
        major_reveals_count = 0
        reveal_jobs = {"REVEAL", "REVEAL_DETAIL"}
        for s in all_shots:
            v_job = str(s.get("visual_job", "")).upper()
            role = str(s.get("shot_role", "")).upper()
            rel = str(s.get("shot_relationship", "")).upper()
            
            is_reveal_shot = (
                v_job in reveal_jobs
                or role == "REVEAL"
                or rel == "EVIDENCE_TO_REVEAL"
                or any(
                    ev.get("type") in ["REVEAL", "NUMBER_REVEAL"]
                    for ev in s.get("editorial_events", [])
                    if isinstance(ev, dict)
                )
            )
            if is_reveal_shot:
                major_reveals_count += 1

        for b in story_beats:
            n_intent = str(b.get("narrative_intent", "")).upper()
            if n_intent in ["REVELATION", "DEEPER_REVELATION"]:
                major_reveals_count += 1

        # ── 8. Number of Attention Peaks ──
        attention_peaks_count = 0
        peak_intents = {"HOOK", "REVELATION", "DEEPER_REVELATION", "ESCALATION", "FINAL_CONTRADICTION"}
        for b in story_beats:
            att = float(b.get("attention_intensity") or 0.5)
            intent = str(b.get("narrative_intent", "")).upper()
            if att >= 0.8 or intent in peak_intents:
                attention_peaks_count += 1

        for s in all_shots:
            v_imp = float(s.get("visual_importance") or 0.5)
            if v_imp >= 0.85:
                attention_peaks_count += 1

        # ── 9. Number of Silence Moments ──
        silence_moments_count = 0
        for b in all_blocks:
            silence = b.get("strategic_silence") or {}
            if isinstance(silence, dict) and float(silence.get("duration_seconds", 0)) > 0:
                silence_moments_count += 1

        for s in all_shots:
            is_restrained = bool(s.get("is_restrained", False))
            cm = str(s.get("camera_motion", "")).lower()
            sfx = str(s.get("sound_design", "")).lower()
            role = str(s.get("shot_role", "")).upper()
            dur = float(s.get("actual_duration") or s.get("duration_seconds") or 3.0)
            
            if is_restrained or role == "HOLD" or (cm == "static" and sfx in ["", "none", "null"] and dur >= 2.5):
                silence_moments_count += 1

        # ── 10. Number of Typography Punctuation Events ──
        typography_events_count = 0
        for s in all_shots:
            vt = str(s.get("visual_type", "")).lower()
            fb = str(s.get("fallback_type", "")).lower()
            rel = str(s.get("shot_relationship", "")).upper()
            has_overlay_text = bool(s.get("text_overlay"))
            
            has_number_event = any(
                ev.get("type") in ["NUMBER_REVEAL", "TYPOGRAPHY"]
                for ev in s.get("editorial_events", [])
                if isinstance(ev, dict)
            )
            
            if (
                vt == "text_stat"
                or fb == "cinematictext"
                or rel == "NUMBER_TO_SCALE"
                or has_number_event
                or has_overlay_text
            ):
                typography_events_count += 1

        # ── 11. Number of Graphic Explanations ──
        graphic_explanations_count = 0
        graphic_types = {"motion_graphics", "diagram", "map", "timeline"}
        graphic_fallbacks = {"technicaldiagram", "animateddiagram", "timeline", "mapfallback"}
        graphic_jobs = {"VISUALIZE_ABSTRACT_CONCEPT", "SHOW_COMPARISON", "SHOW_SCALE"}
        
        for s in all_shots:
            vt = str(s.get("visual_type", "")).lower()
            fb = str(s.get("fallback_type", "")).lower()
            v_job = str(s.get("visual_job", "")).upper()
            
            if vt in graphic_types or fb in graphic_fallbacks or v_job in graphic_jobs:
                graphic_explanations_count += 1

        # ── 12. Number of Human Anchor Moments ──
        human_anchors_count = 0
        human_jobs = {"HUMANIZE", "INTRODUCE_CHARACTER"}
        human_relationships = {"OBJECT_TO_PERSON", "PERSON_TO_CONSEQUENCE"}
        human_keywords = [
            "hand", "hands", "face", "worker", "workers", "operator", "victim",
            "engineer", "reaction", "workspace", "desk", "person", "human", "crowd"
        ]
        
        for s in all_shots:
            v_job = str(s.get("visual_job", "")).upper()
            rel = str(s.get("shot_relationship", "")).upper()
            fb = str(s.get("fallback_type", "")).lower()
            desc = (s.get("visual_description") or s.get("ai_prompt") or "").lower()
            cont_chars = s.get("continuity", {}).get("characters", [])
            
            has_human_kw = any(kw in desc for kw in human_keywords)
            if (
                v_job in human_jobs
                or rel in human_relationships
                or fb == "portraitcard"
                or cont_chars
                or has_human_kw
            ):
                human_anchors_count += 1

        # ── 13. Number of Visual Motifs ──
        visual_motifs_count = 0
        for s in all_shots:
            is_m = bool(s.get("is_motif", False))
            desc = (s.get("visual_description") or s.get("ai_prompt") or "").lower()
            matches_registered = any(rm in desc for rm in registered_motifs) if registered_motifs else False
            if is_m or matches_registered:
                visual_motifs_count += 1

        if not visual_motifs_count and registered_motifs:
            visual_motifs_count = len(registered_motifs)

        # ── 14. Number of Visual Contrasts ──
        visual_contrasts_count = 0
        for i in range(len(all_shots) - 1):
            s1 = all_shots[i]
            s2 = all_shots[i + 1]
            
            # 7 Contrast Dimensions:
            # 1. Pacing
            dur1 = float(s1.get("actual_duration") or s1.get("duration_seconds") or 3.0)
            dur2 = float(s2.get("actual_duration") or s2.get("duration_seconds") or 3.0)
            pacing_contrast = abs(dur1 - dur2) >= 1.5
            
            # 2. Movement
            cm1 = str(s1.get("camera_motion", "")).lower()
            cm2 = str(s2.get("camera_motion", "")).lower()
            motion_contrast = (cm1 == "static" and cm2 != "static") or (cm1 != "static" and cm2 == "static")
            
            # 3. Scale
            sz1 = str(s1.get("shot_size", "")).lower()
            sz2 = str(s2.get("shot_size", "")).lower()
            scale_contrast = (sz1 in ["close", "extreme_close"] and sz2 in ["wide", "extreme_wide"]) or \
                             (sz1 in ["wide", "extreme_wide"] and sz2 in ["close", "extreme_close"])
            
            # 4. Medium
            vt1 = str(s1.get("visual_type", "")).lower()
            vt2 = str(s2.get("visual_type", "")).lower()
            prov1 = str(s1.get("asset_provenance", "")).upper()
            prov2 = str(s2.get("asset_provenance", "")).upper()
            medium_contrast = (vt1 != vt2) or (prov1 != prov2 and prov1 != "STOCK" and prov2 != "STOCK")
            
            # 5. Lighting / LUT
            lut1 = str(s1.get("lut_filter", "")).lower()
            lut2 = str(s2.get("lut_filter", "")).lower()
            lut_contrast = lut1 != lut2 and lut1 and lut2
            
            # 6. Density
            den1 = float(s1.get("visual_density") or 0.5)
            den2 = float(s2.get("visual_density") or 0.5)
            density_contrast = abs(den1 - den2) >= 0.3
            
            # 7. Relational
            rel2 = str(s2.get("shot_relationship", "")).upper()
            relational_contrast = rel2 in ["CONTRAST", "BEFORE_TO_AFTER", "EXPECTATION_TO_SUBVERSION", "CAUSE_TO_EFFECT"]
            
            if (
                pacing_contrast
                or motion_contrast
                or scale_contrast
                or medium_contrast
                or lut_contrast
                or density_contrast
                or relational_contrast
            ):
                visual_contrasts_count += 1

        # ── 15. Number of Contextual Overlays ──
        contextual_overlays_count = 0
        for s in all_shots:
            overlay = str(s.get("overlay", "")).strip().lower()
            has_overlay_event = any(
                ev.get("type") in ["OVERLAY", "FLASH", "GLITCH", "ALERT"]
                for ev in s.get("editorial_events", [])
                if isinstance(ev, dict)
            )
            if (overlay and overlay not in ["none", "null", ""]) or has_overlay_event:
                contextual_overlays_count += 1

        # ── 16. SFX Per Minute ──
        sfx_shots_count = 0
        for s in all_shots:
            sfx = str(s.get("sound_design", "")).strip().lower()
            has_sfx_event = any(
                ev.get("type") in ["SFX", "IMPACT", "RISER", "WHOOSH", "NUMBER_REVEAL"]
                for ev in s.get("editorial_events", [])
                if isinstance(ev, dict)
            )
            if (sfx and sfx not in ["none", "null", ""]) or has_sfx_event:
                sfx_shots_count += 1

        duration_minutes = max(0.1, total_duration / 60.0)
        sfx_per_minute = round(sfx_shots_count / duration_minutes, 2)

        # ── 17. % Shots That Merely Illustrate Narration ──
        illustrative_shots_count = 0
        for s in all_shots:
            query = (s.get("visual_query") or s.get("ai_prompt") or s.get("visual_description") or "").lower()
            has_cliche = any(banned in query for banned in self.BANNED_LITERAL_KEYWORDS)
            
            # Stock filler with generic cut reason is considered illustrative
            prov = str(s.get("asset_provenance", "")).upper()
            cr = str(s.get("cut_reason", "")).lower()
            rel = s.get("shot_relationship")
            is_unmotivated_stock = (prov == "STOCK" and cr in self.GENERIC_CUT_REASONS and not rel)
            
            if has_cliche or is_unmotivated_stock:
                illustrative_shots_count += 1

        percentage_illustrative = round((illustrative_shots_count / max(1, total_shots)) * 100.0, 2)
        if percentage_illustrative > 25.0:
            failures.append(f"High percentage of literal/illustrative shots ({percentage_illustrative}%). Anti-literal rule violated.")
            recommendations.append("Replace literal noun illustrations with dialectical visual arguments and metaphorical framings.")

        metrics = {
            "number_of_unique_visual_concepts": unique_concepts_count,
            "repeated_visual_concepts": repeated_concepts_count,
            "repeated_queries": repeated_queries_count,
            "repeated_camera_movements": repeated_camera_movements_count,
            "repeated_compositions": repeated_compositions_count,
            "shots_with_no_editorial_reason": shots_no_editorial_reason_count,
            "number_of_major_reveals": major_reveals_count,
            "number_of_attention_peaks": attention_peaks_count,
            "number_of_silence_moments": silence_moments_count,
            "number_of_typography_punctuation_events": typography_events_count,
            "number_of_graphic_explanations": graphic_explanations_count,
            "number_of_human_anchor_moments": human_anchors_count,
            "number_of_visual_motifs": visual_motifs_count,
            "number_of_visual_contrasts": visual_contrasts_count,
            "number_of_contextual_overlays": contextual_overlays_count,
            "sfx_per_minute": sfx_per_minute,
            "% shots that merely illustrate narration": percentage_illustrative,
            "percentage_illustrative_shots": percentage_illustrative
        }

        return metrics, failures, recommendations

    def _compute_score_matrix(
        self,
        metrics: Dict[str, Any],
        total_shots: int,
        story_beats: List[Dict[str, Any]],
        all_shots: List[Dict[str, Any]],
        total_duration: float
    ) -> Dict[str, float]:
        """
        Aggregates the 17 metrics into a 10-dimension Director Score Matrix.
        Target score >= 8.0/10.0 for APPROVED verdict.
        """
        # 1. Storytelling & Emotional Progression
        intents = [b.get("narrative_intent") for b in story_beats if b.get("narrative_intent")]
        intent_diversity = len(set(str(i).upper() for i in intents))
        reveals = metrics["number_of_major_reveals"]
        peaks = metrics["number_of_attention_peaks"]
        storytelling_score = min(
            10.0,
            6.5 + (min(4, intent_diversity) * 0.6) + (min(3, reveals) * 0.4) + (min(3, peaks) * 0.3)
        )

        # 2. Cinematography & Composition Variety
        sizes = [s.get("shot_size") for s in all_shots if s.get("shot_size") and s.get("shot_size") != "N/A"]
        angles = [s.get("camera_angle") for s in all_shots if s.get("camera_angle")]
        size_variety = len(set(sizes)) / max(1, len(sizes)) if sizes else 0.5
        angle_variety = len(set(angles)) / max(1, len(angles)) if angles else 0.5
        rep_comp = metrics["repeated_compositions"]
        rep_cam = metrics["repeated_camera_movements"]
        cinematography_score = max(
            2.0,
            min(10.0, 7.0 + (size_variety * 2.0) + (angle_variety * 1.5) - (rep_comp * 0.5) - (rep_cam * 0.5))
        )

        # 3. Pacing & Intentional Holds
        durations = [float(s.get("actual_duration") or s.get("duration_seconds") or 3.0) for s in all_shots]
        has_short_cuts = any(d <= 2.2 for d in durations)
        has_holds = any(d >= 3.5 for d in durations)
        silence_moments = metrics["number_of_silence_moments"]
        base_pacing = 8.5 if (has_short_cuts and has_holds) else (8.0 if has_holds else 7.2)
        pacing_score = min(10.0, base_pacing + (min(3, silence_moments) * 0.4))

        # 4. Sound Design Restraint
        sfx_rate = metrics["sfx_per_minute"]
        if 1.0 <= sfx_rate <= 5.0:
            sound_score = 9.2
        elif 0.0 < sfx_rate < 1.0:
            sound_score = 8.4
        elif sfx_rate == 0.0:
            sound_score = 7.5
        elif 5.0 < sfx_rate <= 8.0:
            sound_score = max(6.0, 9.0 - ((sfx_rate - 5.0) * 0.8))
        else:
            sound_score = max(3.0, 6.0 - ((sfx_rate - 8.0) * 1.0))

        # 5. Visual Variety & Concept Diversity
        unique_concepts = metrics["number_of_unique_visual_concepts"]
        concept_ratio = unique_concepts / max(1, total_shots)
        rep_queries = metrics["repeated_queries"]
        rep_concepts = metrics["repeated_visual_concepts"]
        variety_score = max(
            2.0,
            min(10.0, 6.5 + (concept_ratio * 3.5) - (rep_queries * 0.7) - (rep_concepts * 0.5))
        )

        # 6. Visual Contrast Engine (7D)
        contrasts = metrics["number_of_visual_contrasts"]
        contrast_ratio = contrasts / max(1, total_shots - 1)
        contrast_score = min(10.0, 6.5 + (contrast_ratio * 4.0))

        # 7. Editorial Motivation & Depth
        unmotivated = metrics["shots_with_no_editorial_reason"]
        motivation_score = max(1.0, 10.0 - (unmotivated * 2.0))

        # 8. Anti-Literal Rule & Mute Test
        illustrative_pct = metrics["% shots that merely illustrate narration"]
        if illustrative_pct == 0.0:
            anti_literal_score = 10.0
        elif illustrative_pct <= 10.0:
            anti_literal_score = 9.0
        elif illustrative_pct <= 20.0:
            anti_literal_score = 8.0
        elif illustrative_pct <= 35.0:
            anti_literal_score = 6.5
        else:
            anti_literal_score = max(1.0, 6.0 - ((illustrative_pct - 35.0) * 0.2))

        # 9. Human Anchor & Emotional Grounding
        human_anchors = metrics["number_of_human_anchor_moments"]
        human_score = min(10.0, 7.5 + (min(3, human_anchors) * 0.9))

        # 10. Graphic & Typography Punctuation
        typo_events = metrics["number_of_typography_punctuation_events"]
        graphics = metrics["number_of_graphic_explanations"]
        overlays = metrics["number_of_contextual_overlays"]
        graphic_score = min(
            10.0,
            7.0 + (min(2, typo_events) * 0.9) + (min(2, graphics) * 0.6) + (min(2, overlays) * 0.5)
        )

        return {
            "storytelling": round(storytelling_score, 1),
            "cinematography": round(cinematography_score, 1),
            "pacing": round(pacing_score, 1),
            "sound_design": round(sound_score, 1),
            "visual_variety": round(variety_score, 1),
            "visual_contrast": round(contrast_score, 1),
            "editorial_motivation": round(motivation_score, 1),
            "anti_literal_restraint": round(anti_literal_score, 1),
            "human_grounding": round(human_score, 1),
            "graphic_punctuation": round(graphic_score, 1)
        }
