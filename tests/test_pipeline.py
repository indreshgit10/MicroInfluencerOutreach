"""
Unit & Integration Tests for Automated Micro-Influencer Outreach System
Tests discovery, filtering rules, enrichment schema, word count guardrails, and sending layer.
"""

import unittest
import json
from pathlib import Path

from backend.pipeline.discovery import InfluencerDiscoveryEngine
from backend.pipeline.filter_classify import InfluencerFilterClassifier
from backend.pipeline.enrichment import InfluencerEnrichmentEngine
from backend.pipeline.personalization import MessagePersonalizationEngine
from backend.pipeline.sending_layer import OutreachSendingLayer
from backend.config import DATA_DIR

class TestInfluencerPipeline(unittest.TestCase):

    def setUp(self):
        self.discovery = InfluencerDiscoveryEngine(target_niche="Technology")
        self.classifier = InfluencerFilterClassifier(target_category="Technology")
        self.enricher = InfluencerEnrichmentEngine()
        self.personalizer = MessagePersonalizationEngine()
        self.sender = OutreachSendingLayer(mode="simulation")

    def test_01_discovery_count_and_fields(self):
        """Validates that discovery retrieves >= 50 real influencers with required keys."""
        results = self.discovery.run_discovery(min_count=50)
        self.assertGreaterEqual(len(results), 50, "Discovery must yield at least 50 candidates")
        
        sample = results[0]
        required_keys = ["name", "platform", "follower_count", "engagement_rate", "category", "niche", "profile_url"]
        for key in required_keys:
            self.assertIn(key, sample, f"Missing required key '{key}' in discovered profile")

    def test_02_filtering_logic_micro_range(self):
        """Ensures macro (>100k) and nano (<5k) influencers are appropriately disqualified."""
        macro_profile = {
            "name": "Macro Test",
            "follower_count": 150000,
            "engagement_rate": 3.0,
            "category": "Technology",
            "niche": "AI",
            "content_tone": "Educational"
        }
        passed, reasons, summary, tier, score = self.classifier.evaluate_influencer(macro_profile)
        self.assertFalse(passed, "Macro creator should fail filtering")
        self.assertTrue(any("exceeds micro-influencer cap" in r for r in reasons))

        nano_profile = {
            "name": "Nano Test",
            "follower_count": 2000,
            "engagement_rate": 4.0,
            "category": "Technology",
            "niche": "AI",
            "content_tone": "Educational"
        }
        passed_nano, reasons_nano, _, _, _ = self.classifier.evaluate_influencer(nano_profile)
        self.assertFalse(passed_nano, "Nano creator should fail filtering")
        self.assertTrue(any("below micro-influencer minimum" in r for r in reasons_nano))

    def test_03_filtering_engagement_and_niche(self):
        """Ensures low engagement and off-niche profiles are disqualified."""
        low_eng = {
            "name": "Low Engagement Test",
            "follower_count": 25000,
            "engagement_rate": 0.5,
            "category": "Technology",
            "niche": "AI",
            "content_tone": "Educational"
        }
        passed, reasons, _, _, _ = self.classifier.evaluate_influencer(low_eng)
        self.assertFalse(passed, "Creator with <1.5% engagement should fail")

        off_niche = {
            "name": "Beauty Creator Test",
            "follower_count": 30000,
            "engagement_rate": 4.5,
            "category": "Beauty",
            "niche": "Cosmetics",
            "content_tone": "Glam"
        }
        passed_off, reasons_off, _, _, _ = self.classifier.evaluate_influencer(off_niche)
        self.assertFalse(passed_off, "Creator outside target category should fail")

    def test_04_profile_enrichment_mandatory_fields(self):
        """Ensures all mandatory and optional fields are enriched and email is never guessed."""
        raw_mock = {
            "name": "Jane Developer",
            "platform": "YouTube",
            "profile_url": "https://youtube.com/@janedev",
            "follower_count": 32000,
            "engagement_rate": 4.8,
            "category": "Technology",
            "niche": "Web Architecture",
            "contact_email": "", # Missing email
            "content_themes": ["Next.js", "Docker"]
        }
        enriched = self.enricher.enrich_profile(raw_mock)
        self.assertEqual(enriched["contact_email"], "Not Found", "Missing email must be explicitly 'Not Found'")
        self.assertFalse(enriched["has_valid_email"])
        self.assertIn("estimated_active_reach", enriched)
        self.assertIn("recommended_collab_angle", enriched)

    def test_05_personalization_word_count_guardrails(self):
        """Validates that email pitch is strictly 60-90 words and DM is strictly 15-30 words."""
        candidate = {
            "name": "Alex Mercer",
            "platform": "YouTube",
            "niche": "Generative AI",
            "content_themes": ["LangChain", "Vector Databases"],
            "recent_post_title": "Building Autonomous Multi-Agent Workflows",
            "content_tone": "Technical and hands-on",
            "audience_geography": "United States, Germany",
            "collab_type": "Sponsorship"
        }
        subject, email_pitch, ig_dm = self.personalizer.generate_heuristic_messages(candidate)
        
        email_words = len(email_pitch.split())
        dm_words = len(ig_dm.split())

        self.assertTrue(60 <= email_words <= 90, f"Email pitch word count {email_words} is outside 60-90 words")
        self.assertTrue(15 <= dm_words <= 30, f"DM word count {dm_words} is outside 15-30 words")
        self.assertIn("Alex", email_pitch, "Email should be personalized with recipient's name")

    def test_06_sending_layer_duplicate_prevention(self):
        """Tests that duplicate outreach is caught and recorded properly."""
        candidates = [
            {
                "name": "Dupe Test 1",
                "contact_email": "dupe.creator@example.com",
                "email_subject": "Collab Test",
                "email_pitch": "This is a test pitch for influencer outreach verification.",
                "instagram_dm": "Quick DM test."
            },
            {
                "name": "Dupe Test 1",
                "contact_email": "dupe.creator@example.com",
                "email_subject": "Collab Test Second Run",
                "email_pitch": "This is a duplicate test pitch.",
                "instagram_dm": "Quick DM duplicate."
            }
        ]
        logs = self.sender.process_outreach(candidates, simulate_all=True)
        # Should only send once to dupe.creator@example.com
        dupe_logs = [l for l in logs if l.get("email") == "dupe.creator@example.com"]
        self.assertEqual(len(dupe_logs), 1, "Duplicate outreach should be prevented")

if __name__ == "__main__":
    unittest.main()
