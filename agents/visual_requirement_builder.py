"""
Visual Requirement Builder
===========================
Constructs normalized, context-locked VisualRequirement specifications from Shot data,
ContinuityMetadata, story beat context, and documentary claims.

Enforces context locks (Entity, Event, Date/Era, Location, Required/Forbidden Objects)
and prevents query contamination from generic narration words.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from .schema import VisualRequirement, HistoricalFidelity, Shot, ContinuityMetadata

log = logging.getLogger("visual_requirement_builder")


def _extract_year_from_text(text: str) -> Optional[int]:
    """Extracts a 4-digit year between 1000 and 2099 from text."""
    if not text:
        return None
    match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', text)
    if match:
        return int(match.group(1))
    return None


def _clean_keywords(text: str) -> List[str]:
    """Strips punctuation and noise words to isolate clean semantic keywords."""
    if not text:
        return []
    noise = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "from",
        "of", "is", "was", "were", "are", "been", "be", "have", "has", "had", "this", "that",
        "these", "those", "cinematic", "dramatic", "scene", "shot", "footage", "photo", "image",
        "4k", "hd", "macro", "close", "wide", "medium", "slow", "fast", "huge", "shocking",
        "truth", "secret", "reveal", "millions", "billions", "history", "documentary"
    }
    words = [w for w in re.sub(r'[^\w\s]', ' ', text).split() if len(w) > 2 and w.lower() not in noise]
    return words


def build_visual_requirement(shot: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> VisualRequirement:
    """
    Constructs an authoritative, normalized VisualRequirement from Shot metadata and context.
    """
    context = context or {}
    shot_id = shot.get("shot_id", "shot_unknown")
    claim_id = shot.get("linked_claim_id")
    visual_job = str(shot.get("visual_job", "ESTABLISH_WORLD"))
    visual_type = shot.get("visual_type", "real_photo")
    provenance = shot.get("asset_provenance", "STOCK")
    
    # 1. Continuity Extraction
    continuity = shot.get("continuity", {})
    if isinstance(continuity, ContinuityMetadata):
        continuity = continuity.model_dump()
    elif not isinstance(continuity, dict):
        continuity = {}

    time_period = continuity.get("time_period") or context.get("time_period")
    start_year = continuity.get("start_year") or context.get("start_year")
    end_year = continuity.get("end_year") or context.get("end_year")
    location = continuity.get("location") or context.get("location")
    environment = continuity.get("environment") or context.get("environment")
    characters = continuity.get("characters") or []
    
    # If years are missing, attempt extraction from time_period, visual_description, or topic
    extracted_year = _extract_year_from_text(f"{time_period} {shot.get('visual_description', '')} {context.get('topic', '')}")
    if not start_year and extracted_year:
        start_year = extracted_year
    if not end_year and start_year:
        end_year = start_year

    date_range = str(start_year) if start_year else time_period

    # 2. Subject Entity Extraction
    subject_entity = None
    if characters and len(characters) > 0:
        subject_entity = characters[0]
    elif continuity.get("character_id"):
        subject_entity = continuity["character_id"]
    elif context.get("protagonist"):
        subject_entity = context["protagonist"]
    elif context.get("topic"):
        # If topic contains a specific figure or company/event name
        subject_entity = context["topic"]

    # Refine entity from visual_description if entity is generic
    vdesc = shot.get("visual_description", "")
    for entity_candidate in ["Napoleon Bonaparte", "Napoleon", "Stanislav Petrov", "Petrov", "Vijay Mallya", "Winston Churchill"]:
        if entity_candidate.lower() in vdesc.lower() or entity_candidate.lower() in str(context).lower():
            subject_entity = entity_candidate
            break

    # 3. Specific Event Extraction
    event = None
    cut_reason = shot.get("cut_reason", "")
    if "coronation" in vdesc.lower() or "coronation" in cut_reason.lower():
        event = "Imperial Coronation"
    elif "russia" in vdesc.lower() or "1812" in vdesc.lower() or "retreat" in vdesc.lower() or "campaign" in vdesc.lower():
        event = "Russian Campaign 1812"
    elif "saint helena" in vdesc.lower() or "exile" in vdesc.lower():
        event = "Exile on Saint Helena"
    elif "false alarm" in vdesc.lower() or "serpukhov" in vdesc.lower():
        event = "1983 Soviet Nuclear False Alarm"
    elif context.get("event"):
        event = context["event"]

    # 4. Determine Historical Fidelity & Requirements
    is_historical = False
    evidence_required = False
    
    # Check if era is historical (< 2000) or historical keywords present
    if start_year and start_year < 2000:
        is_historical = True
    elif time_period and any(h in time_period.lower() for h in ["1800", "19th", "18th", "17th", "1945", "1983", "soviet", "ancient", "historical", "empire"]):
        is_historical = True
    elif subject_entity and any(h in subject_entity.lower() for h in ["napoleon", "churchill", "caesar", "alexander", "petrov"]):
        is_historical = True

    if provenance in ["AUTHENTIC_ARCHIVE", "HISTORICAL_DOCUMENT", "AUTHENTIC_PHOTO", "ARCHIVAL_FOOTAGE", "DOCUMENT"] or visual_type.startswith("EVIDENCE_"):
        evidence_required = True

    # Fidelity classification
    if visual_type in ["motion_graphics", "text_stat", "TYPOGRAPHY_REVEAL", "BLACK_HOLD"]:
        fidelity = HistoricalFidelity.ABSTRACT
    elif is_historical:
        if evidence_required or provenance in ["AUTHENTIC_ARCHIVE", "HISTORICAL_DOCUMENT", "AUTHENTIC_PHOTO", "ARCHIVAL_FOOTAGE"]:
            fidelity = HistoricalFidelity.STRICT_ARCHIVAL
        elif visual_type in ["RECONSTRUCTION", "ai_video", "ai_image"]:
            fidelity = HistoricalFidelity.MODERN_RECONSTRUCTION_ALLOWED
        else:
            fidelity = HistoricalFidelity.ERA_ACCURATE
    else:
        fidelity = HistoricalFidelity.OPTIONAL

    # 5. Build Context-Sensitive Forbidden Objects (Anti-Garbage & Anachronism Locks)
    forbidden_objects: List[str] = []
    
    # Context-driven era anachronisms
    if is_historical and (start_year and start_year < 1900):
        forbidden_objects.extend([
            "smartphone", "mobile phone", "laptop", "computer monitor", "modern keyboard",
            "modern car", "contemporary automobile", "modern truck", "modern bus",
            "modern aircraft", "commercial jet", "airplane", "military drone", "drone",
            "modern skyscraper", "contemporary glass building", "asphalt highway with road markings",
            "modern streetlights", "traffic lights", "modern clothing", "t-shirt", "jeans", "modern wristwatch",
            "plastic bottle", "paper coffee cup", "disposable cup", "speedometer", "digital display"
        ])
    elif is_historical and (start_year and start_year < 1960):
        forbidden_objects.extend([
            "smartphone", "mobile phone", "laptop", "computer monitor", "modern flatscreen",
            "modern drone", "contemporary jet", "modern sports car", "contemporary vehicle",
            "modern skyscraper", "plastic cup", "digital LED screen"
        ])

    # Entity mismatch / Unrelated Subject Locks
    if subject_entity:
        entity_lower = subject_entity.lower()
        if "napoleon" in entity_lower:
            forbidden_objects.extend([
                "Mao Zedong", "Mao", "Joseph Stalin", "Stalin", "Adolf Hitler", "Hitler", "Winston Churchill",
                "modern soldier", "contemporary military", "unrelated mythological painting", "Psyche Revived by Cupid",
                "Cupid and Psyche", "religious Renaissance Madonna", "unrelated Asian calligraphy", "unrelated Asian map",
                "American civil war general", "modern politician"
            ])
        elif "petrov" in entity_lower or "soviet" in str(context).lower():
            forbidden_objects.extend([
                "Mao Zedong", "American drone", "modern smartphone", "modern NASDAQ chart", "unrelated Chinese calligraphy"
            ])

    # 6. Extract Required Objects from description and visual job
    required_objects: List[str] = []
    desc_lower = vdesc.lower()
    for obj_key in [
        "printing press", "coronation crown", "imperial robe", "winter coat", "snow", "military uniform",
        "parchment document", "classified stamp", "radar screen", "bunker control panel", "telex machine",
        "financial ledger", "stock certificate", "map", "signature", "seal"
    ]:
        if obj_key in desc_lower:
            required_objects.append(obj_key)

    # 7. Allowed Sources based on Fidelity and Role
    allowed_sources: List[str] = []
    if fidelity == HistoricalFidelity.STRICT_ARCHIVAL:
        allowed_sources = ["wikimedia", "loc", "internet_archive", "youtube_authorized", "evidence_card"]
    elif fidelity == HistoricalFidelity.ERA_ACCURATE:
        allowed_sources = ["wikimedia", "loc", "internet_archive", "youtube_authorized", "ddg_verified", "evidence_card"]
    elif fidelity == HistoricalFidelity.MODERN_RECONSTRUCTION_ALLOWED:
        allowed_sources = ["flux_reconstruction", "pollinations_reconstruction", "wikimedia", "loc", "internet_archive"]
    elif fidelity == HistoricalFidelity.ABSTRACT:
        allowed_sources = ["motion_graphic", "typography_reveal", "map_graphic", "timeline_graphic", "black_hold"]
    else:
        allowed_sources = ["wikimedia", "pexels", "pixabay", "ddg_verified", "flux_reconstruction", "pollinations_reconstruction"]

    # 8. Assemble the VisualRequirement
    req = VisualRequirement(
        shot_id=shot_id,
        claim_id=claim_id,
        visual_job=visual_job,
        subject_entity=subject_entity,
        event=event,
        location=location,
        time_period=time_period,
        date_range=date_range,
        start_year=start_year,
        end_year=end_year,
        required_objects=required_objects,
        forbidden_objects=list(set(forbidden_objects)),
        visual_type=visual_type,
        evidence_required=evidence_required,
        provenance_required=provenance,
        historical_required=is_historical,
        historical_fidelity=fidelity,
        visual_purpose=shot.get("cut_reason") or shot.get("visual_intent"),
        allowed_sources=allowed_sources,
        unresolved_visual_requirement=False
    )
    
    return req


def build_structured_search_query(req: VisualRequirement) -> str:
    """
    Builds a clean, context-locked search query without narrative noise words.
    Template: [ENTITY] + [EVENT] + [DATE/PERIOD] + [LOCATION] + [OBJECT/EVIDENCE TYPE]
    """
    components: List[str] = []
    
    if req.subject_entity:
        components.append(req.subject_entity)
    if req.event:
        components.append(req.event)
    if req.date_range and req.date_range not in " ".join(components):
        components.append(req.date_range)
    if req.location and req.location not in " ".join(components):
        components.append(req.location)
    if req.required_objects:
        components.append(req.required_objects[0])
        
    if req.historical_required and not any(term in " ".join(components).lower() for term in ["painting", "photo", "document", "archival"]):
        components.append("historical painting document")

    query = " ".join(components).strip()
    return query if query else "historical documentary authentic"
