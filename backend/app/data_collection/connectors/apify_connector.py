"""
BrokerWeeklyIntel - Data Collection Layer
Smart Multi-Platform Apify Connector (Intelligent Actor Selection)

This is the central, AI-friendly connector for scraping social platforms
using Apify Store actors. It features an intelligent actor registry so the
system (or Grok) can dynamically choose the best tool for the job.

Key Capabilities:
- Multi-platform support (Reddit, Instagram, YouTube, TikTok, LinkedIn, Facebook, etc.)
- Intelligent actor recommendation via `get_recommended_actor()`
- Registry-driven design — easy to extend with new platforms/use cases
- First-class Reddit implementation (posts + comments)
- Full compatibility with `BaseConnector` + `DataCollector`
- Returns clean `RawSearchResult` objects

Architecture Philosophy:
The AI should be able to say:
  "I need recent user discussions about broker glitches on Reddit"
→ connector.get_recommended_actor("reddit", "glitches")
→ connector.search_platform("reddit", brokers=..., ...)

Usage Examples:

    from app.data_collection.connectors.apify_connector import create_apify_connector

    apify = create_apify_connector()

    # 1. Ask the system what actor to use
    recommendation = apify.get_recommended_actor(platform="reddit", use_case="glitches")
    print(recommendation["primary"])   # e.g. "clockworks/reddit-scraper"

    # 2. Direct platform-aware search (recommended for new code)
    results = await apify.search_platform(
        platform="reddit",
        brokers=["Zerodha", "Groww"],
        start_date=...,
        end_date=...,
        use_case="discussions"
    )

    # 3. Classic interface (still works for DataCollector compatibility)
    results = await apify.search(
        brokers=["Zerodha", "Groww"],
        start_date=...,
        end_date=...
    )

Configuration:
- Set `APIFY_API_TOKEN` in your environment / .env
- Override actors per platform via config dict if needed
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.data_collection.base_connector import BaseConnector
from app.data_collection.models import BrokerName, RawSearchResult

if TYPE_CHECKING:
    from apify_client import ApifyClientAsync


# =============================================================================
# INTELLIGENT ACTOR REGISTRY
# =============================================================================
#
# This is the heart of the "smart" connector.
# The AI / calling code can query this registry to make informed decisions
# about which Apify actor to use for a given platform + intent.
#
# Structure:
#   platform -> use_case -> {
#       "primary": "actor/name",
#       "fallbacks": [...],
#       "description": "...",
#       "best_for": [...],
#       "notes": "..."
#   }
#
# Add new platforms and use cases here as we discover better actors.

ACTOR_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {
    "reddit": {
        "discussions": {
            "primary": "clockworks/reddit-scraper",
            "fallbacks": ["reedsy/reddit-scraper"],
            "description": "General Reddit posts and comments. Good for sentiment, complaints, and feature discussions.",
            "best_for": ["user sentiment", "glitches", "feature reactions", "broker comparisons"],
            "input_hints": {"sort": "new", "skipComments": False},
        },
        "comments": {
            "primary": "clockworks/reddit-scraper",
            "fallbacks": [],
            "description": "Optimized for deep comment threads (high signal for pain points).",
            "best_for": ["detailed complaints", "support issues", "long-form feedback"],
            "input_hints": {"skipComments": False, "maxItems": 200},
        },
        "glitches": {
            "primary": "clockworks/reddit-scraper",
            "fallbacks": ["reedsy/reddit-scraper"],
            "description": "Same actor as discussions, but with stronger glitch-related keywords recommended.",
            "best_for": ["crashes", "freezes", "technical issues", "outages"],
        },
        "new_features": {
            "primary": "clockworks/reddit-scraper",
            "fallbacks": [],
            "description": "Good for reactions to product launches and updates.",
            "best_for": ["feature launches", "UI changes", "new tools"],
        },
    },

    "instagram": {
        "posts": {
            "primary": "apify/instagram-scraper",
            "fallbacks": ["clockworks/instagram-scraper"],
            "description": "Instagram posts, reels, and captions from public profiles and hashtags.",
            "best_for": ["visual reactions", "influencer opinions", "broker marketing analysis"],
        },
        "comments": {
            "primary": "apify/instagram-scraper",
            "fallbacks": [],
            "description": "Instagram comments under posts (high engagement signal).",
        },
    },

    "youtube": {
        "comments": {
            "primary": "apify/youtube-comments-scraper",
            "fallbacks": ["clockworks/youtube-comments-scraper"],
            "description": "YouTube video comments — excellent for long-form user opinions and tutorials.",
            "best_for": ["in-depth reviews", "tutorial reactions", "complaints"],
        },
        "videos": {
            "primary": "apify/youtube-scraper",
            "fallbacks": [],
            "description": "Video metadata, titles, and descriptions for broker-related content.",
        },
    },

    "tiktok": {
        "posts": {
            "primary": "clockworks/tiktok-scraper",
            "fallbacks": ["apify/tiktok-scraper"],
            "description": "TikTok videos and captions. Good for younger trader sentiment.",
            "best_for": ["viral complaints", "quick tips", "youth sentiment"],
        },
    },

    "linkedin": {
        "posts": {
            "primary": "apify/linkedin-posts-scraper",
            "fallbacks": [],
            "description": "LinkedIn posts and comments. High signal for professional / B2B feedback.",
            "best_for": ["institutional feedback", "feature requests from power users"],
        },
    },

    "facebook": {
        "posts": {
            "primary": "apify/facebook-posts-scraper",
            "fallbacks": [],
            "description": "Facebook posts and groups (useful for older demographic in India).",
        },
    },
}

# Default platform when none is specified
DEFAULT_PLATFORM = "reddit"

# Default use case when none is specified
DEFAULT_USE_CASE = "discussions"


class ApifyConnector(BaseConnector):
    """
    Smart, multi-platform Apify connector with intelligent actor selection.

    This connector is designed so that both humans and AI agents can ask:
    "What is the best tool for scraping X on platform Y for use case Z?"
    and then use it seamlessly.
    """

    name = "apify"
    supports_parallel = True

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # Token handling (supports both explicit config and project Settings)
        self.apify_token: Optional[str] = self.config.get("apify_api_token")
        if not self.apify_token:
            try:
                from app.core.config import get_settings
                self.apify_token = get_settings().apify_api_token
            except Exception:
                self.apify_token = None

        self._client: Optional["ApifyClientAsync"] = None

        # Per-platform actor overrides (advanced usage)
        self.actor_overrides: Dict[str, str] = self.config.get("actor_overrides", {})

        # Default platform for the classic `search()` interface
        self.default_platform: str = self.config.get("default_platform", DEFAULT_PLATFORM)

    # -------------------------------------------------------------------------
    # INTELLIGENT ACTOR SELECTION (Core AI-facing feature)
    # -------------------------------------------------------------------------

    def get_recommended_actor(
        self,
        platform: str,
        use_case: str = DEFAULT_USE_CASE,
    ) -> Dict[str, Any]:
        """
        Returns the best Apify actor recommendation for a given platform and use case.

        This is the primary method the AI (Grok) should call to make dynamic decisions.

        Example:
            rec = apify.get_recommended_actor("reddit", "glitches")
            actor = rec["primary"]
        """
        platform = platform.lower()
        use_case = use_case.lower()

        platform_registry = ACTOR_REGISTRY.get(platform, {})
        use_case_entry = platform_registry.get(use_case) or platform_registry.get(DEFAULT_USE_CASE, {})

        if not use_case_entry:
            # Fallback to any available entry for the platform
            use_case_entry = next(iter(platform_registry.values()), {})

        result = {
            "platform": platform,
            "use_case": use_case,
            "primary": use_case_entry.get("primary"),
            "fallbacks": use_case_entry.get("fallbacks", []),
            "description": use_case_entry.get("description", "No description available."),
            "best_for": use_case_entry.get("best_for", []),
            "notes": use_case_entry.get("notes", ""),
        }

        # Allow runtime overrides
        if platform in self.actor_overrides:
            result["primary"] = self.actor_overrides[platform]
            result["notes"] = (result["notes"] + " (overridden via config)").strip()

        return result

    def list_supported_platforms(self) -> List[str]:
        """Returns all platforms that have at least one registered actor."""
        return list(ACTOR_REGISTRY.keys())

    def get_registry(self) -> Dict[str, Any]:
        """Returns the full actor registry (useful for debugging / AI context)."""
        return ACTOR_REGISTRY

    # -------------------------------------------------------------------------
    # Client Management
    # -------------------------------------------------------------------------

    async def _get_client(self) -> Optional["ApifyClientAsync"]:
        if self._client is None and self.apify_token:
            try:
                from apify_client import ApifyClientAsync
                self._client = ApifyClientAsync(token=self.apify_token)
            except ImportError:
                self.logger.error("apify-client is not installed. Run: pip install apify-client")
                return None
        return self._client

    async def close(self):
        if self._client:
            try:
                http_client = getattr(self._client, "_http_client", None)
                if http_client:
                    await http_client.aclose()
            except Exception:
                pass
            self._client = None

    # -------------------------------------------------------------------------
    # Main Search Interfaces
    # -------------------------------------------------------------------------

    async def search(
        self,
        brokers: List[BrokerName],
        start_date: datetime,
        end_date: datetime,
        limit_per_broker: int = 50,
        **kwargs,
    ) -> List[RawSearchResult]:
        """
        Standard BaseConnector interface (for compatibility with DataCollector).

        By default uses the configured `default_platform` (usually Reddit).
        You can pass `platform=...` and `use_case=...` via kwargs for more control.
        """
        platform = kwargs.get("platform", self.default_platform)
        use_case = kwargs.get("use_case", DEFAULT_USE_CASE)

        return await self.search_platform(
            platform=platform,
            brokers=brokers,
            start_date=start_date,
            end_date=end_date,
            limit_per_broker=limit_per_broker,
            use_case=use_case,
            **kwargs,
        )

    async def search_platform(
        self,
        platform: str,
        brokers: List[BrokerName],
        start_date: datetime,
        end_date: datetime,
        limit_per_broker: int = 50,
        use_case: str = DEFAULT_USE_CASE,
        **kwargs,
    ) -> List[RawSearchResult]:
        """
        The powerful, platform-aware search method.

        This is the preferred entry point when you know the platform.
        """
        platform = platform.lower()
        self.logger.info(
            f"ApifyConnector: Searching platform='{platform}' (use_case='{use_case}') "
            f"for {len(brokers)} brokers"
        )

        if platform == "reddit":
            return await self._search_reddit(
                brokers, start_date, end_date, limit_per_broker, use_case, **kwargs
            )

        # Future platforms
        if platform in ACTOR_REGISTRY:
            self.logger.warning(
                f"Platform '{platform}' is registered but not yet fully implemented. "
                f"Returning empty results."
            )
            return []

        self.logger.error(f"Unsupported platform: {platform}")
        return []

    # -------------------------------------------------------------------------
    # Platform Implementations
    # -------------------------------------------------------------------------

    async def _search_reddit(
        self,
        brokers: List[BrokerName],
        start_date: datetime,
        end_date: datetime,
        limit_per_broker: int,
        use_case: str,
        **kwargs,
    ) -> List[RawSearchResult]:
        """Reddit implementation using the recommended actor from the registry."""
        if not self.apify_token:
            self.logger.warning("No Apify token configured. Skipping Reddit collection.")
            return []

        client = await self._get_client()
        if not client:
            return []

        rec = self.get_recommended_actor("reddit", use_case)
        actor_name = rec["primary"]

        if not actor_name:
            self.logger.error("No primary Reddit actor found in registry.")
            return []

        self.logger.info(f"Using Reddit actor: {actor_name} (use_case={use_case})")

        # Broker keyword configuration (can be extended)
        broker_keywords = {
            "Zerodha": ["zerodha", "kite", "coin", "terminal"],
            "Groww": ["groww"],
            "Fyers": ["fyers", "bar replay"],
            "Angel One": ["angel one", "angelone"],
            "Upstox": ["upstox"],
            "ICICI Direct": ["icici direct"],
        }

        all_results: List[RawSearchResult] = []

        for broker in brokers:
            keywords = broker_keywords.get(broker, [broker.lower()])
            search_query = " OR ".join(keywords)

            run_input = {
                "search": search_query,
                "subreddits": [
                    "IndianStreetBets", "Zerodha", "Groww", "IndiaInvestments",
                    "StockMarketIndia", "personalfinanceindia"
                ],
                "maxItems": min(80, limit_per_broker * 3),
                "sort": "new",
                "skipComments": False,
                "onlyPostsNewerThan": start_date.strftime("%Y-%m-%d"),
            }

            try:
                run = await client.actor(actor_name).call(run_input=run_input)
                dataset_id = run.get("defaultDatasetId")
                if not dataset_id:
                    continue

                items = (await client.dataset(dataset_id).list_items(limit=200)).items

                for item in items:
                    raw = self._map_reddit_item_to_raw(item, broker, actor_name)
                    if raw:
                        pub_date = self._extract_date(item)
                        if pub_date and start_date <= pub_date <= end_date:
                            all_results.append(raw)

            except Exception as e:
                err_str = str(e)
                if "not found" in err_str.lower():
                    self.logger.error(
                        f"Reddit actor '{actor_name}' not found or inaccessible. "
                        f"Try a different actor using get_recommended_actor() or config overrides."
                    )
                else:
                    self.logger.warning(f"Reddit scrape failed for {broker}: {e}")

        # Deduplicate by URL
        seen = set()
        unique = []
        for r in all_results:
            url = r.raw_data.get("url")
            if url and url not in seen:
                seen.add(url)
                unique.append(r)

        return unique[: len(brokers) * limit_per_broker]

    def _map_reddit_item_to_raw(
        self, item: Dict[str, Any], broker: BrokerName, actor: str
    ) -> Optional[RawSearchResult]:
        try:
            title = item.get("title", "") or ""
            body = item.get("body", "") or item.get("selftext", "") or ""
            text = (title + "\n" + body).strip()

            if not text:
                return None

            url = item.get("url") or item.get("permalink")
            if url and not str(url).startswith("http"):
                url = f"https://reddit.com{url}"

            created = self._extract_date(item)

            return RawSearchResult(
                source=f"apify:{actor}",
                query=f"broker:{broker}",
                broker=broker,
                platform="reddit",
                raw_data={
                    "id": str(item.get("id", "")),
                    "text": text,
                    "title": title,
                    "url": url,
                    "author": item.get("author"),
                    "subreddit": item.get("subreddit"),
                    "score": item.get("score", 0),
                    "num_comments": item.get("numComments", 0),
                    "created": created.isoformat() if created else None,
                    "is_comment": bool(item.get("isComment")),
                },
                metadata={
                    "actor": actor,
                    "subreddit": item.get("subreddit"),
                    "score": item.get("score", 0),
                },
            )
        except Exception:
            return None

    def _extract_date(self, item: Dict[str, Any]) -> Optional[datetime]:
        for key in ("createdUtc", "created", "created_utc", "timestamp"):
            val = item.get(key)
            if isinstance(val, (int, float)):
                return datetime.fromtimestamp(val, tz=timezone.utc).replace(tzinfo=None)
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    pass
        return None

    # -------------------------------------------------------------------------
    # Health & Diagnostics
    # -------------------------------------------------------------------------

    async def health_check(self) -> Dict[str, Any]:
        token_ok = bool(self.apify_token)
        return {
            "status": "configured" if token_ok else "no_token",
            "connector": self.name,
            "apify_token_present": token_ok,
            "default_platform": self.default_platform,
            "supported_platforms": self.list_supported_platforms(),
            "registry_version": "1.0",
            "capabilities": [
                "Intelligent actor recommendation via get_recommended_actor()",
                "Multi-platform registry (Reddit primary)",
                "Graceful degradation",
            ],
        }


# =============================================================================
# Factory
# =============================================================================

def create_apify_connector(
    apify_api_token: Optional[str] = None,
    default_platform: str = DEFAULT_PLATFORM,
    actor_overrides: Optional[Dict[str, str]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> ApifyConnector:
    """
    Factory for creating a configured ApifyConnector.

    Example with overrides:
        create_apify_connector(
            actor_overrides={"reddit": "some-other/reddit-actor"}
        )
    """
    cfg: Dict[str, Any] = dict(config or {})
    if apify_api_token:
        cfg["apify_api_token"] = apify_api_token
    if default_platform:
        cfg["default_platform"] = default_platform
    if actor_overrides:
        cfg["actor_overrides"] = actor_overrides

    return ApifyConnector(config=cfg)


__all__ = [
    "ApifyConnector",
    "create_apify_connector",
    "ACTOR_REGISTRY",
    "get_recommended_actor",  # convenience re-export
]

# Convenience re-export of the method on the factory for one-liner usage
def get_recommended_actor(platform: str, use_case: str = DEFAULT_USE_CASE) -> Dict[str, Any]:
    """Convenience function that creates a temporary connector just to query the registry."""
    return create_apify_connector().get_recommended_actor(platform, use_case)
