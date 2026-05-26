"""
BrokerWeeklyIntel - Data Collection Layer
Firecrawl Connector (High-Quality Web Content Extraction)

This connector uses Firecrawl (https://firecrawl.dev) to fetch and extract
clean, structured content from broker blogs, announcement pages, and news.

Why Firecrawl?
- Converts pages to high-quality Markdown (much better than raw HTML + regex)
- Extracts structured metadata (title, publish date, author, etc.)
- Handles JavaScript-rendered content reliably
- Provides optional LLM-powered extraction and summarization

This connector is designed to **complement or gradually replace** parts of
the regex-heavy parsing currently in `WebConnector`.

Design Philosophy:
- Targeted scraping of known high-value URLs (more reliable than broad crawling)
- Clean output ready for the Normalizer
- Easy to extend with new sources
- Graceful degradation when Firecrawl is unavailable or rate-limited

Usage:

    from app.data_collection.connectors.firecrawl_connector import create_firecrawl_connector

    firecrawl = create_firecrawl_connector()

    results = await firecrawl.search(
        brokers=["Zerodha", "Fyers", "Groww"],
        start_date=datetime(2026, 5, 19),
        end_date=datetime(2026, 5, 26),
        limit_per_broker=30,
    )

    # Or scrape a specific URL directly
    single = await firecrawl.scrape_url("https://zerodha.com/z-connect/...")
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.data_collection.base_connector import BaseConnector
from app.data_collection.models import BrokerName, RawSearchResult


# =============================================================================
# Firecrawl Configuration & High-Value Sources
# =============================================================================

FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"

# Curated list of high-signal pages where clean extraction matters most.
# These are the same pages the WebConnector targets, but we let Firecrawl
# do the heavy lifting for content parsing.
FIRECRAWL_SOURCES: Dict[str, List[Dict[str, Any]]] = {
    "Zerodha": [
        {
            "name": "Z-Connect Business Updates",
            "url": "https://zerodha.com/z-connect/category/business-updates",
            "type": "blog_listing",
            "priority": "high",
        },
        {
            "name": "Z-Connect Main",
            "url": "https://zerodha.com/z-connect/",
            "type": "blog_listing",
            "priority": "high",
        },
    ],
    "Groww": [
        {
            "name": "Groww Product Updates",
            "url": "https://groww.in/updates",
            "type": "blog_listing",
            "priority": "high",
        },
    ],
    "Fyers": [
        {
            "name": "Fyers Notice Board",
            "url": "https://fyers.in/notice-board/",
            "type": "blog_listing",
            "priority": "high",
        },
        {
            "name": "Fyers Blog",
            "url": "https://fyers.in/blogs/",
            "type": "blog_listing",
            "priority": "medium",
        },
    ],
    "Angel One": [
        {
            "name": "Angel One Product Updates",
            "url": "https://www.angelone.in/news/product-updates",
            "type": "blog_listing",
            "priority": "high",
        },
    ],
    "Upstox": [
        {
            "name": "Upstox Blog",
            "url": "https://upstox.com/blog/",
            "type": "blog_listing",
            "priority": "medium",
        },
    ],
    "ICICI Direct": [
        {
            "name": "ICICI Direct News & Updates",
            "url": "https://www.icicidirect.com/research/news",
            "type": "news",
            "priority": "medium",
        },
    ],
}


class FirecrawlConnector(BaseConnector):
    """
    Production-grade connector that uses Firecrawl for superior web content extraction.

    Focuses on quality over quantity. Best used for official broker blogs and
    high-value announcement pages where clean Markdown + metadata is critical.
    """

    name = "firecrawl"
    supports_parallel = True

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

        # API key resolution order: explicit config > env var > project Settings
        self.api_key: Optional[str] = self.config.get("firecrawl_api_key")

        if not self.api_key:
            self.api_key = os.getenv("FIRECRAWL_API_KEY")

        if not self.api_key:
            try:
                from app.core.config import get_settings
                settings = get_settings()
                # Allow either naming convention
                self.api_key = getattr(settings, "firecrawl_api_key", None) or \
                               getattr(settings, "FIRECRAWL_API_KEY", None)
            except Exception:
                pass

        self.timeout = httpx.Timeout(60.0, connect=15.0)  # Firecrawl can be slow
        self._client: Optional[httpx.AsyncClient] = None

        # Allow overriding source list (advanced)
        self.sources: Dict[str, List[Dict[str, Any]]] = self.config.get(
            "sources", FIRECRAWL_SOURCES
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self._client = httpx.AsyncClient(
                base_url=FIRECRAWL_BASE_URL,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self.logger.debug("FirecrawlConnector HTTP client closed")

    # -------------------------------------------------------------------------
    # Core Search Method
    # -------------------------------------------------------------------------
    async def search(
        self,
        brokers: List[BrokerName],
        start_date: datetime,
        end_date: datetime,
        limit_per_broker: int = 50,
    ) -> List[RawSearchResult]:
        """
        Scrape known high-value broker sources using Firecrawl.

        This is the main entry point compatible with DataCollector.
        """
        if not self.api_key:
            self.logger.warning(
                "FirecrawlConnector: No FIRECRAWL_API_KEY configured. "
                "Returning empty results. Set the key to enable high-quality extraction."
            )
            return []

        self.logger.info(
            f"FirecrawlConnector starting for {len(brokers)} brokers | "
            f"{start_date.date()} → {end_date.date()}"
        )

        all_results: List[RawSearchResult] = []
        client = await self._get_client()

        for broker in brokers:
            broker_sources = self.sources.get(broker, [])
            if not broker_sources:
                continue

            broker_results: List[RawSearchResult] = []

            for source in broker_sources:
                try:
                    items = await self._scrape_source(
                        client, broker, source, start_date, end_date
                    )
                    broker_results.extend(items)
                except Exception as e:
                    self.logger.warning(
                        f"Firecrawl failed for {source.get('name')} ({broker}): {e}"
                    )

            # Respect limit
            broker_results = broker_results[:limit_per_broker]
            all_results.extend(broker_results)

            if broker_results:
                self.logger.info(
                    f"  {broker}: extracted {len(broker_results)} items via Firecrawl"
                )

        self.logger.info(f"FirecrawlConnector finished. Total raw results: {len(all_results)}")
        return all_results

    async def _scrape_source(
        self,
        client: httpx.AsyncClient,
        broker: BrokerName,
        source: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> List[RawSearchResult]:
        """Scrape a single source URL using Firecrawl and convert results."""
        url = source["url"]
        source_name = source.get("name", url)

        self.logger.debug(f"Firecrawling {source_name} ({url})")

        payload = {
            "url": url,
            "formats": ["markdown"],   # "metadata" is no longer a valid format option
            "onlyMainContent": True,
            "waitFor": 2000,
        }

        try:
            response = await client.post("/scrape", json=payload)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                self.logger.warning(f"Firecrawl scrape failed for {url}: {data}")
                return []

            result_data = data.get("data", {})
            markdown = result_data.get("markdown", "")
            metadata = result_data.get("metadata", {})

            # Try to extract publish date
            published_at = self._extract_publish_date(metadata, markdown)

            # Basic date filtering at source level
            if published_at and not (start_date <= published_at <= end_date):
                return []

            # Create RawSearchResult
            raw_result = RawSearchResult(
                source=f"firecrawl:scrape:{source.get('type', 'web')}",
                query=source_name,
                broker=broker,
                platform="web",
                raw_data={
                    "url": url,
                    "title": metadata.get("title") or metadata.get("ogTitle"),
                    "markdown": markdown[:15000],  # Keep reasonable size
                    "description": metadata.get("description") or metadata.get("ogDescription"),
                    "published_at": published_at.isoformat() if published_at else None,
                    "author": metadata.get("author"),
                    "language": metadata.get("language"),
                    "source_name": source_name,
                },
                metadata={
                    "firecrawl_metadata": {
                        k: v for k, v in metadata.items()
                        if k in ["title", "description", "ogTitle", "publishDate", "author"]
                    },
                    "extraction_method": "firecrawl_scrape",
                },
            )

            return [raw_result]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                self.logger.error("Firecrawl API: Payment required / quota exceeded")
            elif e.response.status_code == 429:
                self.logger.warning("Firecrawl rate limit hit")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error scraping {url} with Firecrawl: {e}")
            raise

    def _extract_publish_date(
        self, metadata: Dict[str, Any], markdown: str
    ) -> Optional[datetime]:
        """Best-effort extraction of publish date from Firecrawl metadata or content."""
        candidates = [
            metadata.get("publishDate"),
            metadata.get("og:published_time"),
            metadata.get("article:published_time"),
            metadata.get("datePublished"),
        ]

        for candidate in candidates:
            if isinstance(candidate, str):
                try:
                    # Handle common formats
                    if candidate.endswith("Z"):
                        candidate = candidate[:-1] + "+00:00"
                    return datetime.fromisoformat(candidate.replace("Z", "+00:00"))
                except Exception:
                    continue

        # Fallback: very naive scan of markdown for dates (can be improved)
        # Many Indian broker blogs put dates near the top
        import re
        date_patterns = [
            r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
            r"(\d{4}-\d{2}-\d{2})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, markdown[:2000], re.IGNORECASE)
            if match:
                try:
                    return datetime.strptime(match.group(1), "%Y-%m-%d")
                except Exception:
                    pass

        return None

    # -------------------------------------------------------------------------
    # Flexible Single-URL Scraping (very useful for targeted work)
    # -------------------------------------------------------------------------
    async def scrape_url(
        self,
        url: str,
        formats: Optional[List[str]] = None,
        only_main_content: bool = True,
    ) -> Dict[str, Any]:
        """
        Low-level method to scrape any URL with Firecrawl.

        Useful when you want raw Firecrawl output or need to scrape a one-off page.
        """
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY is required for scraping")

        client = await self._get_client()
        payload = {
            "url": url,
            "formats": formats or ["markdown"],
            "onlyMainContent": only_main_content,
        }

        response = await client.post("/scrape", json=payload)
        response.raise_for_status()
        return response.json()

    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------
    async def health_check(self) -> Dict[str, Any]:
        """Check if Firecrawl is reachable and the API key is valid."""
        if not self.api_key:
            return {
                "status": "no_api_key",
                "connector": self.name,
                "message": "FIRECRAWL_API_KEY not configured",
            }

        try:
            client = await self._get_client()
            # Firecrawl doesn't have a dedicated /health, so we do a cheap scrape
            # of a known public page with minimal cost.
            test_payload = {
                "url": "https://example.com",
                "formats": ["markdown"],
                "onlyMainContent": True,
            }
            resp = await client.post("/scrape", json=test_payload, timeout=15.0)

            if resp.status_code == 200:
                return {
                    "status": "healthy",
                    "connector": self.name,
                    "api_key_present": True,
                    "message": "Successfully reached Firecrawl API",
                }
            else:
                return {
                    "status": "degraded",
                    "connector": self.name,
                    "status_code": resp.status_code,
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "connector": self.name,
                "error": str(e),
            }


# =============================================================================
# Factory Function
# =============================================================================

def create_firecrawl_connector(
    firecrawl_api_key: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> FirecrawlConnector:
    """
    Create a FirecrawlConnector.

    Args:
        firecrawl_api_key: Explicit API key (overrides env and settings)
        config: Additional configuration
    """
    cfg: Dict[str, Any] = dict(config or {})
    if firecrawl_api_key:
        cfg["firecrawl_api_key"] = firecrawl_api_key

    return FirecrawlConnector(config=cfg)


__all__ = [
    "FirecrawlConnector",
    "create_firecrawl_connector",
    "FIRECRAWL_SOURCES",
]
