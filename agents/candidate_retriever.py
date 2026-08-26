"""
Candidate Retriever
====================
Generates a diversified pool of 5–20 asset candidates per shot across
Wikimedia Commons, Library of Congress, Internet Archive, DuckDuckGo,
and authorized YouTube / stock providers.

Pre-fetches lightweight preview thumbnails for verification before high-res acquisition.
"""

import os
import re
import json
import logging
import urllib.parse
import requests
from typing import List, Dict, Any, Optional
from .schema import VisualRequirement, HistoricalFidelity

log = logging.getLogger("candidate_retriever")

WIKI_HEADERS = {
    "User-Agent": "MediaAgencyDocBot/1.0 (https://github.com/thenewbie343/media-agency; contact@mediaagency.ai)"
}


class CandidateRetriever:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(WIKI_HEADERS)

    def retrieve_candidates(self, req: VisualRequirement, max_candidates: int = 15) -> List[Dict[str, Any]]:
        """
        Retrieves a candidate pool of 5–20 candidates across authorized sources
        matching the VisualRequirement.
        """
        candidates: List[Dict[str, Any]] = []
        seen_urls = set()

        # Build clean search queries
        from .visual_requirement_builder import build_structured_search_query
        primary_query = build_structured_search_query(req)
        
        # Build secondary fallback query
        sub_components = []
        if req.subject_entity: sub_components.append(req.subject_entity)
        if req.event: sub_components.append(req.event)
        elif req.location: sub_components.append(req.location)
        secondary_query = " ".join(sub_components) if sub_components else primary_query

        log.info(f"Retrieving candidate pool for [{req.shot_id}] with query: '{primary_query}'")

        # ── 1. Wikimedia Commons & Wikipedia Lead Images ──
        if "wikimedia" in req.allowed_sources:
            wiki_candidates = self._search_wikimedia(primary_query, secondary_query, limit=8)
            for c in wiki_candidates:
                if c["highres_url"] not in seen_urls:
                    seen_urls.add(c["highres_url"])
                    candidates.append(c)

        # ── 2. Library of Congress (loc.gov) ──
        if "loc" in req.allowed_sources:
            loc_candidates = self._search_library_of_congress(primary_query, limit=5)
            for c in loc_candidates:
                if c["highres_url"] not in seen_urls:
                    seen_urls.add(c["highres_url"])
                    candidates.append(c)

        # ── 3. Internet Archive (archive.org) ──
        if "internet_archive" in req.allowed_sources:
            ia_candidates = self._search_internet_archive(primary_query, limit=5)
            for c in ia_candidates:
                if c["highres_url"] not in seen_urls:
                    seen_urls.add(c["highres_url"])
                    candidates.append(c)

        # ── 4. DuckDuckGo Verified Web Search (Multi-Candidate) ──
        if ("ddg_verified" in req.allowed_sources or "ddg" in req.allowed_sources) and len(candidates) < max_candidates:
            ddg_candidates = self._search_duckduckgo(primary_query, limit=8)
            for c in ddg_candidates:
                if c["highres_url"] not in seen_urls:
                    seen_urls.add(c["highres_url"])
                    candidates.append(c)

        # ── 5. Pexels (STRICTLY for Non-Historical / Contextual shots) ──
        if "pexels" in req.allowed_sources and not req.historical_required and not req.evidence_required:
            pexels_candidates = self._search_pexels(secondary_query, limit=5)
            for c in pexels_candidates:
                if c["highres_url"] not in seen_urls:
                    seen_urls.add(c["highres_url"])
                    candidates.append(c)

        log.info(f"Retrieved {len(candidates)} candidates for [{req.shot_id}]")
        return candidates[:max_candidates]

    def _search_wikimedia(self, query: str, fallback_query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """Searches Wikimedia Commons API for authentic archival files."""
        results = []
        clean_q = re.sub(r'[^\w\s]', ' ', query).strip()
        search_terms = [clean_q]
        if fallback_query and fallback_query != query:
            search_terms.append(re.sub(r'[^\w\s]', ' ', fallback_query).strip())
        
        # Add 2-3 word concise query
        words = clean_q.split()
        if len(words) > 3:
            search_terms.append(" ".join(words[:3]))

        try:
            for term in search_terms:
                if len(results) >= limit:
                    break
                url = "https://commons.wikimedia.org/w/api.php"
                params = {
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": f"{term} filetype:bitmap",
                    "gsrnamespace": 6,
                    "gsrlimit": limit,
                    "prop": "imageinfo",
                    "iiprop": "url|size|extmetadata",
                    "format": "json"
                }
                resp = self.session.get(url, params=params, timeout=10)
                if resp.status_code == 200:
                    pages = resp.json().get("query", {}).get("pages", {})
                    for page_id, p in pages.items():
                        if "imageinfo" in p and p["imageinfo"]:
                            info = p["imageinfo"][0]
                            ext = info.get("extmetadata", {})
                            title = p.get("title", "").replace("File:", "")
                            desc = ext.get("ImageDescription", {}).get("value", "")
                            artist = ext.get("Artist", {}).get("value", "")
                            date_str = ext.get("DateTimeOriginal", {}).get("value", "") or ext.get("DateTime", {}).get("value", "")
                            
                            results.append({
                                "candidate_id": f"wiki_{page_id}",
                                "provider": "wikimedia",
                                "title": title,
                                "description": f"{desc} {artist}".strip()[:400],
                                "date": date_str,
                                "creator": artist,
                                "preview_url": info.get("thumburl") or info.get("url"),
                                "highres_url": info.get("url"),
                                "provenance": "AUTHENTIC_ARCHIVE",
                                "rights_status": "public_domain",
                                "metadata": {
                                    "file_size": info.get("size"),
                                    "width": info.get("width"),
                                    "height": info.get("height")
                                }
                            })
            
            # B. If direct search returned few results, query Wikipedia lead article image
            if len(results) < 3 and fallback_query:
                page_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles={urllib.parse.quote(fallback_query)}"
                r_page = self.session.get(page_url, timeout=10)
                if r_page.status_code == 200:
                    p_data = r_page.json().get("query", {}).get("pages", {})
                    for p_id, p_info in p_data.items():
                        if p_id != "-1" and "original" in p_info:
                            img_src = p_info["original"]["source"]
                            results.append({
                                "candidate_id": f"wiki_lead_{p_id}",
                                "provider": "wikimedia_wikipedia",
                                "title": fallback_query,
                                "description": f"Lead Wikipedia archive image for {fallback_query}",
                                "date": None,
                                "creator": "Wikipedia Commons",
                                "preview_url": img_src,
                                "highres_url": img_src,
                                "provenance": "AUTHENTIC_ARCHIVE",
                                "rights_status": "public_domain",
                                "metadata": {}
                            })
        except Exception as e:
            log.warning(f"Wikimedia search failed for '{query}': {e}")

        return results

    def _search_library_of_congress(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches Library of Congress (loc.gov) API for public domain historical prints & photos."""
        results = []
        try:
            url = "https://www.loc.gov/search/"
            params = {
                "q": query,
                "fo": "json",
                "fa": "original-format:photo,print,drawing",
                "c": limit
            }
            resp = self.session.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                items = resp.json().get("results", [])
                for i, item in enumerate(items):
                    img_url = item.get("image_url")
                    if isinstance(img_url, list) and img_url:
                        img_url = img_url[0]
                    if img_url and isinstance(img_url, str):
                        if not img_url.startswith("http"):
                            img_url = f"https:{img_url}"
                        
                        results.append({
                            "candidate_id": f"loc_{i}_{abs(hash(img_url)) % 10000}",
                            "provider": "library_of_congress",
                            "title": item.get("title", ""),
                            "description": " ".join(item.get("description", []))[:400] if isinstance(item.get("description"), list) else str(item.get("description", ""))[:400],
                            "date": item.get("date", ""),
                            "creator": "Library of Congress",
                            "preview_url": img_url,
                            "highres_url": img_url,
                            "provenance": "AUTHENTIC_ARCHIVE",
                            "rights_status": "public_domain",
                            "metadata": {}
                        })
        except Exception as e:
            log.warning(f"Library of Congress search failed for '{query}': {e}")
            
        return results

    def _search_internet_archive(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches Internet Archive (archive.org) API for historical image items."""
        results = []
        try:
            url = "https://archive.org/advancedsearch.php"
            params = {
                "q": f"{query} AND mediatype:(image)",
                "fl[]": "identifier,title,description,date,creator",
                "rows": limit,
                "output": "json"
            }
            resp = self.session.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                docs = resp.json().get("response", {}).get("docs", [])
                for doc in docs:
                    identifier = doc.get("identifier")
                    if identifier:
                        thumb_url = f"https://archive.org/services/img/{identifier}"
                        results.append({
                            "candidate_id": f"ia_{identifier}",
                            "provider": "internet_archive",
                            "title": doc.get("title", ""),
                            "description": str(doc.get("description", ""))[:400],
                            "date": doc.get("date", ""),
                            "creator": str(doc.get("creator", "")),
                            "preview_url": thumb_url,
                            "highres_url": thumb_url,
                            "provenance": "AUTHENTIC_ARCHIVE",
                            "rights_status": "public_domain",
                            "metadata": {}
                        })
        except Exception as e:
            log.warning(f"Internet Archive search failed for '{query}': {e}")

        return results

    def _search_duckduckgo(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """Searches DuckDuckGo Image Search without aggressive word truncation."""
        results = []
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    from ddgs import DDGS
                except ImportError:
                    from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                ddg_results = list(ddgs.images(query, max_results=limit))
                for i, r in enumerate(ddg_results):
                    img_url = r.get("image")
                    thumb_url = r.get("thumbnail") or img_url
                    if img_url:
                        results.append({
                            "candidate_id": f"ddg_{i}_{abs(hash(img_url)) % 10000}",
                            "provider": "duckduckgo",
                            "title": r.get("title", ""),
                            "description": f"{r.get('title', '')} from {r.get('source', '')}",
                            "date": None,
                            "creator": r.get("source", ""),
                            "preview_url": thumb_url,
                            "highres_url": img_url,
                            "provenance": "AUTHENTIC_PHOTO",
                            "rights_status": "unknown",
                            "metadata": {
                                "width": r.get("width"),
                                "height": r.get("height")
                            }
                        })
        except Exception as e:
            log.warning(f"DuckDuckGo candidate search failed for '{query}': {e}")

        return results

    def _search_pexels(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches Pexels API (strictly for non-historical b-roll)."""
        results = []
        pexels_key = os.environ.get("PEXELS_KEY", "3QjOv4tHN73fLie2daMFqgZDv9w2GRuBoTv5UBhyHYD5da26gVw8kqS4")
        if not pexels_key:
            return results
        try:
            headers = {"Authorization": pexels_key}
            r = requests.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params={"query": query, "per_page": limit, "orientation": "landscape"},
                timeout=12
            )
            if r.status_code == 200:
                photos = r.json().get("photos", [])
                for p in photos:
                    img_url = p.get("src", {}).get("large2x") or p.get("src", {}).get("original")
                    thumb_url = p.get("src", {}).get("small") or img_url
                    results.append({
                        "candidate_id": f"pexels_{p.get('id')}",
                        "provider": "pexels",
                        "title": p.get("alt", "Pexels stock image"),
                        "description": p.get("alt", ""),
                        "date": None,
                        "creator": p.get("photographer", "Pexels"),
                        "preview_url": thumb_url,
                        "highres_url": img_url,
                        "provenance": "STOCK",
                        "rights_status": "creative_commons",
                        "metadata": {
                            "width": p.get("width"),
                            "height": p.get("height")
                        }
                    })
        except Exception as e:
            log.warning(f"Pexels candidate search failed for '{query}': {e}")

        return results
