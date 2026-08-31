import json
import logging
import os
from typing import Dict, Any, List, Optional
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

# YouTube Discovery integration (graceful import)
try:
    from .youtube_discovery import youtube_search_by_claim
    _YOUTUBE_AVAILABLE = True
except ImportError:
    _YOUTUBE_AVAILABLE = False

from pydantic_core import ValidationError
from .base_agent import BaseAgent
from .schema import (
    DocumentaryResearchPackage,
    EvidenceItem,
    NumberItem,
    PersonAnchor,
    TurningPointItem,
    MajorRevealItem,
)

log = logging.getLogger("agency")


class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    def _execute_youtube_search(self, topic: str) -> List[dict]:
        """Executes claim-driven YouTube search for archival footage discovery."""
        if not _YOUTUBE_AVAILABLE:
            log.info("YouTube discovery module not available. Skipping YouTube search.")
            return []
        
        if not os.environ.get("SOURCE_YT") and not os.environ.get("YOUTUBE_TOKEN_JSON"):
            log.info("SOURCE_YT and YOUTUBE_TOKEN_JSON not set. Skipping YouTube discovery.")
            return []
        
        youtube_discoveries = []
        claim_queries = [
            f"{topic} evidence documents primary source",
            f"{topic} archival footage historical",
            f"{topic} original recording testimony interview",
        ]
        
        for query in claim_queries:
            try:
                results = youtube_search_by_claim(query, max_results=3)
                youtube_discoveries.extend(results)
            except Exception as e:
                log.warning(f"YouTube search failed for '{query}': {e}")
        
        if youtube_discoveries:
            authorized = sum(1 for d in youtube_discoveries if d.get("source_role") == "YOUTUBE_AUTHORIZED")
            reference = sum(1 for d in youtube_discoveries if d.get("source_role") == "YOUTUBE_REFERENCE")
            log.info(f"YouTube discovery: {len(youtube_discoveries)} videos found ({authorized} authorized, {reference} reference)")
        
        return youtube_discoveries

    def _execute_multi_query_search(self, topic: str) -> str:
        """Executes a multi-query search to gather authentic facts, evidence, and visual opportunities."""
        raw_snippets: List[str] = []
        if not DDGS:
            log.warning("DuckDuckGo search client not available. Relying on LLM domain knowledge.")
            return "No web search client available. Use authoritative internal historical knowledge."

        queries = [
            f"{topic} central question controversy mystery investigation",
            f"{topic} evidence documents telex financial records audit numbers",
            f"{topic} key figures timeline turning points major reveals",
            f"{topic} visual motifs archival photos physical objects",
        ]

        for query in queries:
            try:
                with DDGS() as ddgs:
                    results = ddgs.text(query, max_results=4)
                    if results:
                        for r in results:
                            body = r.get("body", "").strip()
                            title = r.get("title", "").strip()
                            if body:
                                raw_snippets.append(f"[{title}]: {body}")
            except Exception as e:
                log.warning(f"Search query failed for '{query}': {e}")

        if not raw_snippets:
            raw_snippets.append("Search yielded no external snippets. Rely on detailed domain facts.")

        # --- YouTube Discovery Integration ---
        youtube_discoveries = self._execute_youtube_search(topic)
        if youtube_discoveries:
            raw_snippets.append("\n--- YouTube Archival Discovery ---")
            for disc in youtube_discoveries[:6]:  # Top 6 discoveries
                state = disc.get("source_role", "YOUTUBE_REFERENCE")
                state_label = "✅ AUTHORIZED" if state == "YOUTUBE_AUTHORIZED" else "🔍 REFERENCE ONLY"
                raw_snippets.append(
                    f"[YouTube {state_label}] \"{disc.get('title', '')}\" "
                    f"by {disc.get('channel_name', '')} — {disc.get('description', '')[:120]}"
                )
            raw_snippets.append("--- End YouTube Discovery ---")

        return "\n\n".join(raw_snippets)

    def research_topic(self, topic: str) -> Dict[str, Any]:
        """
        Investigates the topic via multi-query search and compiles a full 24-field
        DocumentaryResearchPackage validated against the Pydantic v2 schema.
        """
        print(f"[*] ResearcherAgent conducting deep investigative research on: {topic}")
        log.info(f"Conducting deep research for topic: {topic}")

        # 1. Gather raw facts via targeted multi-query search
        facts_text = self._execute_multi_query_search(topic)

        # 2. Schema definition for LLM
        schema_json = json.dumps(DocumentaryResearchPackage.model_json_schema(), indent=2)

        system_prompt = f"""You are an elite Investigative Documentary Researcher and Chief Journalist (style of Frontline, BBC Panorama, HBO Documentaries).
Your mission is to analyze the investigative subject and produce an authentic, granular, multi-dimensional 'DocumentaryResearchPackage'.
The documentary narration will be in Hindi, but this research package MUST be compiled in rigorous, detailed English.

REQUIRED 24 INVESTIGATIVE DIMENSIONS (ABSOLUTE MANDATE):
1. `topic`: The central subject name.
2. `central_question`: The burning investigative question driving the film.
3. `documentary_thesis`: The overarching editorial argument.
4. `central_contradiction`: The core paradox (e.g. public glory vs. internal ruin).
5. `audience_initial_belief`: What ordinary viewers assume before watching.
6. `what_the_audience_thinks_is_true`: The conventional myth or public narrative.
7. `what_is_actually_more_complicated`: The hidden systemic truth uncovered by investigation.
8. `protagonist_or_human_anchor`: The key human anchors grounding the emotional stakes.
9. `antagonistic_force_or_system`: The opposing force, corporate bureaucracy, or corrupt system.
10. `stakes`: Universal human consequences, losses, or systemic transformations.
11. `historical_context`: Geopolitical, technological, or economic backdrop.
12. `turning_points`: Array of chronological inflection points, each with `timeframe`, `event`, and `consequence`.
13. `major_reveals`: Array of drip-fed revelations across phases (FIRST_DISCOVERY, REVELATION, DEEPER_REVELATION, FINAL_CONTRADICTION, PAYOFF), each with `phase`, `revelation`, and `evidence_backing`.
14. `final_payoff`: The lasting philosophical or moral takeaway.
15. `evidence_items`: Array of specific physical/digital artifacts (e.g. memos, telexes, logs, photos, court filings, ledgers, contracts) with `title`, `evidence_type`, `description`, `source_reference`, `visual_cue`.
16. `people`: Array of real key figures with `name`, `role`, `significance`, `visual_description`.
17. `locations`: Specific real-world locations and environments.
18. `physical_objects`: Tangible artifacts, devices, documents, or props.
19. `numbers`: Specific numbers or statistics with `raw_value` (e.g. '$81,000,000', '11:47 AM'), `metric_label`, `visual_treatment` ('odometer_counter', 'typographic_impact', 'split_comparison', 'callout_badge', 'data_stream'), and `editorial_context`.
20. `dates`: Critical chronological dates.
21. `archival_opportunities`: Authentic historical footage and photo opportunities.
22. `reconstruction_opportunities`: AI reenactment and forensic reconstruction opportunities.
23. `motion_graphic_opportunities`: Data flows, architectural schematics, network graphs, and timelines.
24. `visual_motifs`: Recurring visual symbols to escalate across chapters.
25. `ending_image_opportunity`: A haunting, memorable final lingering image for the documentary climax.

CRITICAL RULES:
- DO NOT use generic placeholders (e.g. 'Evidence 1', 'Person A', '$100'). Provide authentic, concrete historical facts, real names, exact dates, and specific dollar figures or quantities.
- Return ONLY valid JSON strictly adhering to the schema below.

JSON SCHEMA:
{schema_json}"""

        prompt = f"""Investigative Topic: {topic}

Verified Search Snippets & Context:
{facts_text}

Generate the complete DocumentaryResearchPackage JSON."""

        raw_output = self.call_llm(prompt, system_prompt)

        # Handle string or dict output
        if isinstance(raw_output, str):
            try:
                raw_output = json.loads(raw_output)
            except Exception as e:
                log.error(f"Failed to parse LLM JSON string: {e}")
                raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        if not isinstance(raw_output, dict):
            raw_output = self._get_mock_fallback(prompt, system_prompt, True)

        # 3. Validate and enforce Pydantic model conformance
        try:
            package = DocumentaryResearchPackage.model_validate(raw_output)
            print("[*] ResearcherAgent: DocumentaryResearchPackage successfully validated against schema!")
            return package.model_dump()
        except ValidationError as val_err:
            log.warning(f"ResearchPackage schema validation error: {val_err}. Attempting schema repair...")
            # Try targeted repair
            repair_prompt = f"""Your JSON failed validation against DocumentaryResearchPackage schema.
Error:
{str(val_err)}

Broken JSON:
{json.dumps(raw_output, indent=2)}

Return the corrected JSON strictly conforming to the DocumentaryResearchPackage schema."""
            repair_system = "You are a JSON repair assistant. Fix schema errors and return valid JSON."
            try:
                repaired = self.call_llm(repair_prompt, repair_system)
                if isinstance(repaired, str):
                    repaired = json.loads(repaired)
                package = DocumentaryResearchPackage.model_validate(repaired)
                print("[*] ResearcherAgent: Repaired DocumentaryResearchPackage validated successfully!")
                return package.model_dump()
            except Exception as repair_e:
                log.error(f"Schema repair failed: {repair_e}. Using sanitized fallback package.")
                fallback = self._get_mock_fallback(prompt, system_prompt, True)
                package = DocumentaryResearchPackage.model_validate(fallback)
                return package.model_dump()

