"""
YouTube Discovery + Authorized Media Layer
===========================================
Provides claim-driven YouTube search, trusted channel resolution,
rights-safe asset state classification, caption/timestamp extraction,
and alternative archive source discovery.

YouTube is an ENORMOUS visual research/discovery layer.
It is NOT a free media library.
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timezone

log = logging.getLogger("youtube_discovery")

# ============================================================================
# Trusted Channel Registry
# ============================================================================

_TRUSTED_CHANNELS: dict = {}  # channel_id -> TrustedChannel dict
_REGISTRY_LOADED = False

def load_trusted_channels(config_path: Optional[str] = None) -> dict:
    """Load the trusted channel registry from config/trusted_channels.json."""
    global _TRUSTED_CHANNELS, _REGISTRY_LOADED
    
    if _REGISTRY_LOADED and _TRUSTED_CHANNELS:
        return _TRUSTED_CHANNELS
    
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "trusted_channels.json")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            channels = json.load(f)
        _TRUSTED_CHANNELS = {ch["channel_id"]: ch for ch in channels}
        _REGISTRY_LOADED = True
        log.info(f"Loaded {len(_TRUSTED_CHANNELS)} trusted YouTube channels.")
    except FileNotFoundError:
        log.warning(f"Trusted channels config not found at {config_path}. YouTube discovery will treat all channels as REFERENCE.")
        _TRUSTED_CHANNELS = {}
        _REGISTRY_LOADED = True
    except Exception as e:
        log.warning(f"Failed to load trusted channels: {e}")
        _TRUSTED_CHANNELS = {}
        _REGISTRY_LOADED = True
    
    return _TRUSTED_CHANNELS


def resolve_channel_trust(channel_id: str) -> Optional[dict]:
    """Look up a channel in the trusted registry. Returns the channel dict or None."""
    channels = load_trusted_channels()
    return channels.get(channel_id)


def is_channel_authorized(channel_id: str) -> bool:
    """Check if a channel has authorized_media or project_owned trust level."""
    ch = resolve_channel_trust(channel_id)
    if not ch:
        return False
    return ch.get("trust_level") in ("authorized_media", "project_owned")


def get_youtube_asset_state(channel_id: str, rights_status: str = "unknown") -> str:
    """
    Resolve the YouTubeAssetState for a video based on channel trust and rights.
    
    Returns: "YOUTUBE_AUTHORIZED", "YOUTUBE_REFERENCE", or "YOUTUBE_UNUSABLE"
    """
    ch = resolve_channel_trust(channel_id)
    
    # Explicitly authorized channels with permissive policies
    if ch:
        trust = ch.get("trust_level", "discovery_only")
        policy = ch.get("permitted_media_policy", "no_reuse")
        
        if trust in ("authorized_media", "project_owned"):
            if policy in ("public_domain", "creative_commons", "full_authorization"):
                return "YOUTUBE_AUTHORIZED"
            elif policy == "fair_use_clips":
                return "YOUTUBE_AUTHORIZED"
        
        # Channel is known but only for discovery
        if trust == "discovery_only":
            return "YOUTUBE_REFERENCE"
    
    # Rights-based classification for unknown channels
    if rights_status in ("public_domain", "creative_commons"):
        return "YOUTUBE_AUTHORIZED"
    elif rights_status in ("project_owned", "explicit_permission"):
        return "YOUTUBE_AUTHORIZED"
    elif rights_status == "standard_youtube_license":
        return "YOUTUBE_REFERENCE"
    
    # Default: treat as reference-only (safe default)
    return "YOUTUBE_REFERENCE"


# ============================================================================
# YouTube Data API v3 Search
# ============================================================================

def _parse_iso8601_duration(duration_str: str) -> float:
    """Parse ISO 8601 duration (e.g. 'PT4M13S') to seconds."""
    if not duration_str:
        return 0.0
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return 0.0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def youtube_search_by_claim(claim_text: str, max_results: int = 5,
                            channel_filter: Optional[str] = None) -> list:
    """
    Search YouTube by CLAIM text (not broad topic).
    Returns a list of YouTubeDiscovery-compatible dicts with asset state resolved.
    
    Requires: YOUTUBE_API_KEY environment variable.
    """
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        log.warning("YOUTUBE_API_KEY not set. Skipping YouTube discovery.")
        return []
    
    try:
        import requests
    except ImportError:
        log.warning("requests not available for YouTube API.")
        return []
    
    # Build search request
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "q": claim_text,
        "type": "video",
        "maxResults": min(max_results, 25),
        "order": "relevance",
        "key": api_key,
        "safeSearch": "none",
        "relevanceLanguage": "en"
    }
    if channel_filter:
        search_params["channelId"] = channel_filter
    
    try:
        resp = requests.get(search_url, params=search_params, timeout=15)
        if resp.status_code != 200:
            log.warning(f"YouTube Search API returned {resp.status_code}: {resp.text[:200]}")
            return []
        
        search_data = resp.json()
        items = search_data.get("items", [])
        if not items:
            log.info(f"YouTube search returned 0 results for: {claim_text[:60]}")
            return []
        
        # Collect video IDs for batch detail fetch
        video_ids = [item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")]
        
        # Fetch video details (duration, etc.)
        details_url = "https://www.googleapis.com/youtube/v3/videos"
        details_params = {
            "part": "contentDetails,snippet",
            "id": ",".join(video_ids),
            "key": api_key
        }
        details_resp = requests.get(details_url, params=details_params, timeout=15)
        detail_map = {}
        if details_resp.status_code == 200:
            for item in details_resp.json().get("items", []):
                detail_map[item["id"]] = item
        
        # Build discovery objects
        now = datetime.now(timezone.utc).isoformat()
        discoveries = []
        
        for i, item in enumerate(items):
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            
            snippet = item.get("snippet", {})
            channel_id = snippet.get("channelId", "")
            channel_name = snippet.get("channelTitle", "")
            
            # Get duration from details
            detail = detail_map.get(video_id, {})
            content_details = detail.get("contentDetails", {})
            duration_seconds = _parse_iso8601_duration(content_details.get("duration", ""))
            
            # Resolve asset state from channel trust
            asset_state = get_youtube_asset_state(channel_id)
            
            # Determine rights status from license
            detail_snippet = detail.get("snippet", snippet)
            license_content = detail_snippet.get("licensedContent", False)
            
            rights = "unknown"
            ch_trust = resolve_channel_trust(channel_id)
            if ch_trust:
                policy = ch_trust.get("permitted_media_policy", "no_reuse")
                if policy == "public_domain":
                    rights = "public_domain"
                elif policy == "creative_commons":
                    rights = "creative_commons"
                else:
                    rights = "standard_youtube_license"
            
            # Generate alternative archive query for REFERENCE videos
            alt_query = None
            if asset_state != "YOUTUBE_AUTHORIZED":
                title_clean = re.sub(r'[^\w\s]', '', snippet.get("title", ""))
                alt_query = f"{title_clean} archival footage public domain"
            
            discovery = {
                "youtube_video_id": video_id,
                "channel_id": channel_id,
                "channel_name": channel_name,
                "title": snippet.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "description": (snippet.get("description", "") or "")[:500],
                "publication_date": snippet.get("publishedAt", ""),
                "duration_seconds": duration_seconds,
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "discovery_timestamp": now,
                "linked_claim_id": None,
                "source_role": asset_state,
                "rights_status": rights,
                "authorization_reference": None,
                "relevance_score": round(1.0 - (i * 0.15), 2),
                "candidate_timestamps": None,
                "visual_description": snippet.get("description", "")[:200],
                "alternative_archive_query": alt_query
            }
            discoveries.append(discovery)
        
        authorized = sum(1 for d in discoveries if d["source_role"] == "YOUTUBE_AUTHORIZED")
        reference = sum(1 for d in discoveries if d["source_role"] == "YOUTUBE_REFERENCE")
        log.info(f"YouTube search: {len(discoveries)} results ({authorized} authorized, {reference} reference) for: {claim_text[:50]}")
        
        return discoveries
        
    except Exception as e:
        log.warning(f"YouTube search failed: {e}")
        return []


# ============================================================================
# Caption / Transcript Support
# ============================================================================

def fetch_youtube_captions(video_id: str) -> Optional[list]:
    """
    Fetches available caption tracks for a video via YouTube Data API.
    Returns a list of caption track metadata, or None if unavailable.
    
    Note: Actual transcript download requires OAuth2 authorization.
    This function returns metadata about available caption tracks.
    """
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        return None
    
    try:
        import requests
        url = "https://www.googleapis.com/youtube/v3/captions"
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": api_key
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            return [
                {
                    "track_id": item["id"],
                    "language": item["snippet"].get("language", ""),
                    "name": item["snippet"].get("name", ""),
                    "track_kind": item["snippet"].get("trackKind", ""),
                    "is_auto_generated": item["snippet"].get("trackKind") == "ASR"
                }
                for item in items
            ]
        return None
    except Exception as e:
        log.warning(f"Caption fetch failed for {video_id}: {e}")
        return None


def find_caption_timestamps(captions_text: str, search_terms: list) -> list:
    """
    Searches caption text for specific names, events, dates, phrases.
    Returns candidate timestamp ranges.
    
    Input: Raw caption text with timestamps (e.g. from youtube-transcript-api).
    """
    timestamps = []
    lines = captions_text.split("\n") if captions_text else []
    
    for term in search_terms:
        term_lower = term.lower()
        for i, line in enumerate(lines):
            if term_lower in line.lower():
                # Extract timestamp if present (format: HH:MM:SS or MM:SS)
                ts_match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?)', line)
                if ts_match:
                    start = ts_match.group(1)
                    # Estimate ~6 second clip
                    timestamps.append(f"{start}")
    
    return timestamps


# ============================================================================
# Alternative Archive Source Resolution
# ============================================================================

def resolve_youtube_to_archive_query(discovery: dict) -> dict:
    """
    Takes a YOUTUBE_REFERENCE discovery and generates structured queries 
    for rights-cleared archive sources.
    
    Returns a dict with queries for different archives:
    {
        "wikimedia": "...",
        "internet_archive": "...",
        "loc": "...",
        "europeana": "...",
        "nasa": "..." (if space-related)
    }
    """
    title = discovery.get("title", "")
    description = discovery.get("description", "")
    channel = discovery.get("channel_name", "")
    
    # Extract key terms
    combined = f"{title} {description}"
    # Remove common YouTube noise words
    noise = {"official", "video", "hd", "4k", "full", "documentary", "watch", "subscribe", "like", "rare", "footage", "clip", "channel"}
    words = [w for w in re.findall(r'\b[A-Za-z0-9]+\b', combined) if w.lower() not in noise and len(w) > 2]
    key_terms = " ".join(words[:10])
    
    queries = {
        "wikimedia": f"{key_terms} filetype:bitmap OR filetype:video",
        "internet_archive": key_terms,
        "loc": key_terms,
        "europeana": key_terms,
    }
    
    # Check if space/NASA related
    space_terms = {"nasa", "space", "apollo", "shuttle", "iss", "mars", "moon", "satellite", "rocket", "astronaut"}
    if any(t in combined.lower() for t in space_terms):
        queries["nasa"] = key_terms
    
    return queries


# ============================================================================
# YouTube Rights Audit Gate
# ============================================================================

def audit_youtube_rights(manifest_dict: dict) -> Tuple[bool, list]:
    """
    Scans every shot's asset metadata in the manifest.
    REJECTS any shot where source contains 'youtube' AND 
    youtube_asset_state != 'YOUTUBE_AUTHORIZED'.
    
    Returns (passed: bool, violations: list[str])
    """
    violations = []
    
    for beat in manifest_dict.get("story_beats", []):
        for block in beat.get("narration_blocks", []):
            for shot in block.get("shots", []):
                asset = shot.get("asset", {})
                source = (asset.get("source") or "").lower()
                
                if "youtube" in source:
                    yt_state = asset.get("youtube_asset_state", "")
                    if yt_state != "YOUTUBE_AUTHORIZED":
                        shot_id = shot.get("shot_id", "unknown")
                        violations.append(
                            f"Shot {shot_id}: source='{source}', youtube_asset_state='{yt_state}' — "
                            f"BLOCKED. Only YOUTUBE_AUTHORIZED may enter final render."
                        )
                
                # Also check asset_provenance at shot level
                provenance = shot.get("asset_provenance", "")
                if provenance == "YOUTUBE_AUTHORIZED":
                    yt_state = asset.get("youtube_asset_state", "")
                    if yt_state != "YOUTUBE_AUTHORIZED":
                        shot_id = shot.get("shot_id", "unknown")
                        violations.append(
                            f"Shot {shot_id}: provenance='YOUTUBE_AUTHORIZED' but asset state='{yt_state}' — MISMATCH."
                        )
    
    passed = len(violations) == 0
    if passed:
        log.info("✅ YouTube Rights Audit PASSED. No unauthorized YouTube media in manifest.")
    else:
        log.error(f"❌ YouTube Rights Audit FAILED. {len(violations)} violation(s):")
        for v in violations:
            log.error(f"  • {v}")
    
    return passed, violations
