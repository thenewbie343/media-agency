"""
Test Suite: YouTube Discovery + Authorized Media Layer
======================================================
Tests:
1. Schema validation (YouTubeAssetState, YouTubeDiscovery, TrustedChannel, EvidenceAsset)
2. Trusted channel registry lookup (NASA, NARA, AP Archive)
3. Asset state resolution (Authorized vs Reference vs Unusable)
4. Alternative archive query generation
5. YouTube rights audit gate (Adversarial rejection of unauthorized YouTube assets)
6. Pre-flight checks & mock search
"""

import unittest
from datetime import datetime, timezone

from agents.schema import (
    YouTubeAssetState,
    YouTubeDiscovery,
    TrustedChannel,
    EvidenceAsset,
    Shot,
    ScriptManifest,
)
from agents.youtube_discovery import (
    load_trusted_channels,
    resolve_channel_trust,
    is_channel_authorized,
    get_youtube_asset_state,
    resolve_youtube_to_archive_query,
    audit_youtube_rights,
)


class TestYouTubeDiscoveryLayer(unittest.TestCase):

    def setUp(self):
        self.channels = load_trusted_channels()

    def test_01_trusted_channel_registry_loaded(self):
        """Verify trusted channels JSON is loaded and contains NASA and NARA."""
        self.assertGreater(len(self.channels), 0)
        # NASA
        nasa = resolve_channel_trust("UCLA_DiR1FfKNvjuUpBHmylQ")
        self.assertIsNotNone(nasa)
        self.assertEqual(nasa["channel_name"], "NASA")
        self.assertEqual(nasa["trust_level"], "authorized_media")
        self.assertEqual(nasa["permitted_media_policy"], "public_domain")
        self.assertTrue(is_channel_authorized("UCLA_DiR1FfKNvjuUpBHmylQ"))

        # AP Archive (discovery only)
        ap = resolve_channel_trust("UCWOA1ZGiwLbDQJk2xZb0HA")
        self.assertIsNotNone(ap)
        self.assertEqual(ap["trust_level"], "discovery_only")
        self.assertFalse(is_channel_authorized("UCWOA1ZGiwLbDQJk2xZb0HA"))

    def test_02_asset_state_resolution(self):
        """Verify authorized channels yield YOUTUBE_AUTHORIZED while others yield YOUTUBE_REFERENCE."""
        # NASA -> AUTHORIZED
        state_nasa = get_youtube_asset_state("UCLA_DiR1FfKNvjuUpBHmylQ")
        self.assertEqual(state_nasa, "YOUTUBE_AUTHORIZED")

        # AP Archive -> REFERENCE
        state_ap = get_youtube_asset_state("UCWOA1ZGiwLbDQJk2xZb0HA")
        self.assertEqual(state_ap, "YOUTUBE_REFERENCE")

        # Unknown channel with creative commons -> AUTHORIZED
        state_cc = get_youtube_asset_state("UC_random_unknown", rights_status="creative_commons")
        self.assertEqual(state_cc, "YOUTUBE_AUTHORIZED")

        # Unknown channel default -> REFERENCE (safe default)
        state_unknown = get_youtube_asset_state("UC_random_unknown")
        self.assertEqual(state_unknown, "YOUTUBE_REFERENCE")

    def test_03_youtube_discovery_schema_validation(self):
        """Verify YouTubeDiscovery model validates correctly."""
        now = datetime.now(timezone.utc).isoformat()
        disc = YouTubeDiscovery(
            youtube_video_id="abc123xyz",
            channel_id="UCLA_DiR1FfKNvjuUpBHmylQ",
            channel_name="NASA",
            title="Apollo 11 Moon Landing Archival Restored",
            url="https://www.youtube.com/watch?v=abc123xyz",
            discovery_timestamp=now,
            source_role=YouTubeAssetState.AUTHORIZED,
            rights_status="public_domain",
            duration_seconds=184.0,
            candidate_timestamps=["01:14-01:20"],
        )
        self.assertEqual(disc.source_role, YouTubeAssetState.AUTHORIZED)
        self.assertEqual(disc.duration_seconds, 184.0)

    def test_04_alternative_archive_query_generation(self):
        """Verify YOUTUBE_REFERENCE items generate structured queries for Wikimedia/LOC/IA/NASA."""
        disc = {
            "title": "Rare Footage of 1983 Soviet Nuclear Bunker Alarm",
            "description": "Historical documentary reconstruction of the Serpukhov-15 bunker incident.",
            "channel_name": "Historical Archive Channel",
            "source_role": "YOUTUBE_REFERENCE"
        }
        queries = resolve_youtube_to_archive_query(disc)
        self.assertIn("wikimedia", queries)
        self.assertIn("internet_archive", queries)
        self.assertIn("loc", queries)
        self.assertIn("Serpukhov", queries["wikimedia"])

    def test_05_rights_audit_gate_rejection(self):
        """Verify audit_youtube_rights REJECTS unauthorized YouTube media in final render manifest."""
        manifest_violating = {
            "story_beats": [
                {
                    "narration_blocks": [
                        {
                            "shots": [
                                {
                                    "shot_id": "shot_001",
                                    "asset_provenance": "AUTHENTIC_ARCHIVE",
                                    "asset": {
                                        "source": "youtube_reference",
                                        "youtube_asset_state": "YOUTUBE_REFERENCE",
                                        "path": "visuals/shot_001.mp4"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        passed, violations = audit_youtube_rights(manifest_violating)
        self.assertFalse(passed)
        self.assertEqual(len(violations), 1)
        self.assertIn("BLOCKED", violations[0])

    def test_06_rights_audit_gate_approval(self):
        """Verify audit_youtube_rights PASSES authorized YouTube media."""
        manifest_valid = {
            "story_beats": [
                {
                    "narration_blocks": [
                        {
                            "shots": [
                                {
                                    "shot_id": "shot_001",
                                    "asset_provenance": "YOUTUBE_AUTHORIZED",
                                    "asset": {
                                        "source": "youtube_authorized",
                                        "youtube_asset_state": "YOUTUBE_AUTHORIZED",
                                        "path": "visuals/shot_001.mp4"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        passed, violations = audit_youtube_rights(manifest_valid)
        self.assertTrue(passed)
        self.assertEqual(len(violations), 0)

    def test_youtube_research_smoke(self):
        """Smoke test for YouTube researcher."""
        from agents.youtube_discovery import youtube_search_by_claim
        result = youtube_search_by_claim("Edward Bernays archival footage historical", max_results=1)
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()