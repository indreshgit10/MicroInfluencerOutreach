"""
Filtering and Classification Engine
Evaluates discovered influencers against multi-dimensional criteria:
- Follower count (5,000 - 100,000 for micro-influencer designation)
- Engagement rate threshold
- Category / niche alignment
- Brand-fit criteria and content relevance
Outputs clear 'passed'/'failed' status and detailed reasons for each candidate.
"""

import json
import logging
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import (
    RAW_DATA_PATH, FILTERED_DATA_PATH, FILTERED_DATA_CSV,
    MIN_FOLLOWERS, MAX_FOLLOWERS, MIN_ENGAGEMENT_RATE, DEFAULT_TARGET_NICHE
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FilterEngine")

class InfluencerFilterClassifier:
    def __init__(
        self,
        target_category: str = DEFAULT_TARGET_NICHE,
        min_followers: int = MIN_FOLLOWERS,
        max_followers: int = MAX_FOLLOWERS,
        min_engagement_rate: float = MIN_ENGAGEMENT_RATE
    ):
        self.target_category = target_category
        self.min_followers = min_followers
        self.max_followers = max_followers
        self.min_engagement_rate = min_engagement_rate

    def evaluate_influencer(self, profile: Dict[str, Any]) -> Tuple[bool, List[str], str, str, int]:
        """
        Evaluates a single influencer profile against the filtering rules.
        Returns:
            (passed, failure_reasons, reason_summary, classification_tier, brand_fit_score)
        """
        reasons = []
        name = profile.get("name", "Unknown")
        followers = profile.get("follower_count", 0)
        engagement = profile.get("engagement_rate", 0.0)
        category = profile.get("category", "")
        niche = profile.get("niche", "")
        tone = profile.get("content_tone", "").lower()
        themes = [t.lower() for t in profile.get("content_themes", [])]

        # 1. Follower Count Criteria (Micro-influencer definition: 5,000 - 100,000)
        if followers < self.min_followers:
            reasons.append(f"Follower count ({followers:,}) is below micro-influencer minimum of {self.min_followers:,}")
        elif followers > self.max_followers:
            reasons.append(f"Follower count ({followers:,}) exceeds micro-influencer cap of {self.max_followers:,} (classified as Macro-creator)")

        # 2. Engagement Rate Criteria
        if engagement < self.min_engagement_rate:
            reasons.append(f"Engagement rate ({engagement}%) is below minimum requirement of {self.min_engagement_rate}%")

        # 3. Category / Niche Criteria
        category_match = (
            self.target_category.lower() in category.lower() or 
            self.target_category.lower() in niche.lower()
        )
        if not category_match:
            reasons.append(f"Category mismatch: creator is in '{category} / {niche}', expected '{self.target_category}'")

        # 4. Brand-Fit and Content Relevance
        disqualified_keywords = ["scraped", "obsolete", "bot", "meme coins", "pump signals", "monotone text re-upload"]
        is_spam_or_disqualified = any(
            kw in tone or any(kw in th for th in themes)
            for kw in disqualified_keywords
        )
        if is_spam_or_disqualified:
            reasons.append("Brand-fit failure: Low-relevance, automated, or flagged content themes")

        # Determine pass/fail
        passed = (len(reasons) == 0)

        # Brand Fit Scoring (0 - 100 scale)
        brand_fit_score = 50
        if passed:
            # Engagement bonus
            if engagement >= 5.0:
                brand_fit_score += 25
            elif engagement >= 3.5:
                brand_fit_score += 15
            else:
                brand_fit_score += 5
            
            # Contact availability bonus
            if profile.get("contact_email") and profile.get("contact_email") != "Not Found":
                brand_fit_score += 15
            
            # Content richness
            if len(themes) >= 3:
                brand_fit_score += 10
            
            tier = (
                "Tier 1: High Engagement Micro-Creator" if engagement >= 5.0
                else "Tier 2: Core Micro-Creator" if engagement >= 3.5
                else "Tier 3: Standard Micro-Creator"
            )
            reason_summary = f"Passed: Active {category} micro-influencer with {followers:,} followers and solid {engagement}% engagement."
        else:
            brand_fit_score = max(10, 50 - (len(reasons) * 15))
            tier = f"Disqualified ({reasons[0].split(':')[0]})"
            reason_summary = f"Failed filtering: {'; '.join(reasons)}"

        return passed, reasons, reason_summary, tier, brand_fit_score

    def run_filtering(self, raw_profiles: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Filters discovered profiles and saves evaluated results."""
        if raw_profiles is None:
            if not RAW_DATA_PATH.exists():
                raise FileNotFoundError(f"Raw data file not found at {RAW_DATA_PATH}. Run discovery first.")
            with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
                raw_profiles = json.load(f)

        logger.info(f"Filtering {len(raw_profiles)} influencers against target category '{self.target_category}'...")
        filtered_results = []
        passed_count = 0
        failed_count = 0

        for profile in raw_profiles:
            evaluated = dict(profile)
            passed, reasons, summary, tier, score = self.evaluate_influencer(profile)
            evaluated["passed"] = passed
            evaluated["filter_status"] = "PASSED" if passed else "FAILED"
            evaluated["failure_reasons"] = reasons
            evaluated["classification_reason"] = summary
            evaluated["classification_tier"] = tier
            evaluated["brand_fit_score"] = score
            filtered_results.append(evaluated)

            if passed:
                passed_count += 1
            else:
                failed_count += 1

        logger.info(f"Filtering complete. Total: {len(filtered_results)} | Passed: {passed_count} | Failed: {failed_count}")
        self.save_artifacts(filtered_results)
        return filtered_results

    def save_artifacts(self, results: List[Dict[str, Any]]):
        """Saves filtered candidates with pass/fail reasons to JSON and CSV."""
        with open(FILTERED_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved filtered JSON to {FILTERED_DATA_PATH}")

        # CSV format
        fieldnames = [
            "name", "platform", "follower_count", "engagement_rate", "category",
            "niche", "filter_status", "passed", "brand_fit_score", "classification_tier", 
            "classification_reason", "contact_email", "profile_url"
        ]
        with open(FILTERED_DATA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        logger.info(f"Saved filtered CSV to {FILTERED_DATA_CSV}")

if __name__ == "__main__":
    classifier = InfluencerFilterClassifier()
    res = classifier.run_filtering()
    passed = [r for r in res if r["passed"]]
    print(f"Filtering summary: {len(passed)}/{len(res)} influencers passed filtering.")
