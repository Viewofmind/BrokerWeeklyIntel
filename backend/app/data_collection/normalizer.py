"""
BrokerWeeklyIntel - Data Collection Layer
Normalizer

Responsible for turning heterogeneous raw data from many sources into
the canonical NormalizedMention model (and enriching with v2.1 tags).
"""

import re
import logging
from datetime import datetime
from typing import List, Optional, Any

from app.data_collection.models import (
    RawSearchResult,
    NormalizedMention,
    BrokerName,
    Platform,
    TechnicalIssueType,
)

logger = logging.getLogger(__name__)


class Normalizer:
    """
    Central normalizer for the Data Collection Layer.

    Goals:
    - Deduplicate across sources
    - Extract basic signals (feature launch, glitch, etc.)
    - Tag for v2.1 downstream use (negative_theme, technical_issue_type)
    """

    # Simple keyword heuristics (can be replaced later with LLM or better rules)
    FEATURE_KEYWORDS = [
        "launched", "new feature", "now live", "introducing", "released",
        "added", "rolling out", "update", "version", "bar replay", "trailing stop",
        "fixed deposits", "terminal mode", "advance payoff"
    ]

    GLITCH_KEYWORDS = [
        "crash", "down", "not working", "stuck", "failed", "outage",
        "lag", "freeze", "slow", "error", "not loading", "payment failed"
    ]

    NEGATIVE_THEME_KEYWORDS = {
        "Performance": ["slow", "lag", "freeze", "stuck", "crash"],
        "Reliability": ["failed", "not working", "payment failed", "unreliable"],
        "Support": ["support", "customer care", "no reply", "ignored"],
        "Charges": ["fee", "charge", "expensive", "brokerage"],
        "UX": ["ui", "interface", "confusing", "hard to find"],
        "Features/Gaps": ["missing", "wish", "should have", "no support for"],
    }

    def __init__(self):
        self.logger = logger

    def normalize_raw_results(
        self,
        raw_results: List[RawSearchResult],
        broker: Optional[BrokerName] = None,
    ) -> List[NormalizedMention]:
        """Normalize a batch of raw results into NormalizedMention objects."""
        normalized: List[NormalizedMention] = []
        seen_urls: set[str] = set()

        for raw in raw_results:
            try:
                mention = self._normalize_one(raw, broker)
                if mention.url in seen_urls:
                    continue
                seen_urls.add(mention.url)
                normalized.append(mention)
            except Exception as e:
                self.logger.warning(f"Failed to normalize result from {raw.source}: {e}")
                continue

        return normalized

    def _normalize_one(
        self, raw: RawSearchResult, default_broker: Optional[BrokerName]
    ) -> NormalizedMention:
        """Convert a single RawSearchResult into NormalizedMention."""
        text = raw.raw_data.get("text") or raw.raw_data.get("title") or ""
        url = raw.raw_data.get("url") or raw.raw_data.get("link") or ""
        author = raw.raw_data.get("author") or raw.raw_data.get("username")
        published_at = self._parse_date(raw.raw_data.get("published_at") or raw.raw_data.get("date"))
        engagement = int(raw.raw_data.get("engagement", 0) or 0)

        # Determine broker if not provided
        detected_broker = default_broker or self._detect_broker(text)

        if not detected_broker:
            # Fallback - this should be rare if connectors are broker-aware
            detected_broker = "Zerodha"  # conservative default

        # Basic tagging
        tags: List[str] = []
        negative_theme = None
        technical_issue_type = None

        lower_text = text.lower()

        if any(kw in lower_text for kw in self.FEATURE_KEYWORDS):
            tags.append("feature_launch")

        if any(kw in lower_text for kw in self.GLITCH_KEYWORDS):
            tags.append("glitch")
            # Heuristic: if the glitch mentions a specific new feature, mark as feature_specific
            if any(kw in lower_text for kw in ["terminal", "fd", "fixed deposit", "bar replay", "trailing"]):
                technical_issue_type = "feature_specific"
            else:
                technical_issue_type = "platform_wide"

        # Negative theme detection
        for theme, keywords in self.NEGATIVE_THEME_KEYWORDS.items():
            if any(kw in lower_text for kw in keywords):
                negative_theme = theme  # type: ignore
                tags.append("negative")
                break

        if "good" in lower_text or "love" in lower_text or "excellent" in lower_text:
            tags.append("positive")

        platform = self._normalize_platform(raw.platform)

        return NormalizedMention(
            platform=platform,
            broker=detected_broker,
            text=text[:2000],  # safety cap
            url=url,
            author=author,
            published_at=published_at,
            engagement=engagement,
            tags=tags,
            negative_theme=negative_theme,
            technical_issue_type=technical_issue_type,
            raw_metadata={
                "source": raw.source,
                "original_query": raw.query,
                **raw.metadata,
            },
        )

    def _detect_broker(self, text: str) -> Optional[BrokerName]:
        """Very lightweight broker detection from text."""
        text_lower = text.lower()
        mapping = {
            "zerodha": "Zerodha",
            "groww": "Groww",
            "angel one": "Angel One",
            "upstox": "Upstox",
            "fyers": "Fyers",
            "icici direct": "ICICI Direct",
            "5paisa": "5Paisa",
            "kotak": "Kotak Securities",
        }
        for key, broker in mapping.items():
            if key in text_lower:
                return broker  # type: ignore
        return None

    def _normalize_platform(self, platform: str) -> Platform:
        mapping = {
            "x": "x",
            "twitter": "x",
            "reddit": "reddit",
            "youtube": "youtube",
            "web": "web",
            "instagram": "instagram",
            "z-connect": "blog",
            "fyers blog": "blog",
        }
        return mapping.get(platform.lower(), "web")  # type: ignore

    def _parse_date(self, date_value: Any) -> datetime:
        if isinstance(date_value, datetime):
            return date_value
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            except Exception:
                pass
        return datetime.utcnow()
