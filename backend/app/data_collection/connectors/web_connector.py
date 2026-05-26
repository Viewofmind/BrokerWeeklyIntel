"""
BrokerWeeklyIntel - Data Collection Layer
Web Connector (Highest Priority & Most Reliable Source)

This connector is the backbone of data collection because:
- Official broker sources are authoritative and high-signal.
- They rarely suffer from rate limits or authentication issues.
- They provide excellent coverage for NEW FEATURES and TECHNICAL ANNOUNCEMENTS.
- Perfect fallback when X/Twitter or Reddit tools are limited (as seen in v2.1 testing).

Supported sources:
- Official broker blogs / update pages (Z-Connect, Groww Updates, Fyers Notice Board, etc.)
- Google Play Store "What's new" changelogs
- News articles and press releases (via targeted discovery)

Design:
- Heavy use of known good URLs + targeted fetching (more reliable than pure search).
- Date-aware filtering.
- Graceful degradation (one source failing doesn't break the run).
- Seamless integration with the central Normalizer.
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin

import httpx

from app.data_collection.base_connector import BaseConnector
from app.data_collection.models import (
    RawSearchResult,
    BrokerName,
    Platform,
)


# =============================================================================
# Official Source Registry (easy to extend)
# =============================================================================

OFFICIAL_SOURCES: Dict[str, List[Dict[str, Any]]] = {
    "Zerodha": [
        {
            "type": "blog",
            "name": "Z-Connect Business Updates",
            "url": "https://zerodha.com/z-connect/category/business-updates",
            "base_url": "https://zerodha.com",
        },
        {
            "type": "blog",
            "name": "Z-Connect Main",
            "url": "https://zerodha.com/z-connect/",
            "base_url": "https://zerodha.com",
        },
    ],
    "Groww": [
        {
            "type": "blog",
            "name": "Groww Product Updates",
            "url": "https://groww.in/updates",
            "base_url": "https://groww.in",
        },
    ],
    "Fyers": [
        {
            "type": "blog",
            "name": "Fyers Notice Board",
            "url": "https://fyers.in/notice-board/",
            "base_url": "https://fyers.in",
        },
        {
            "type": "blog",
            "name": "Fyers Blog",
            "url": "https://fyers.in/blogs/",
            "base_url": "https://fyers.in",
        },
    ],
    "Angel One": [
        {
            "type": "blog",
            "name": "Angel One Updates",
            "url": "https://www.angelone.in/news/product-updates",
            "base_url": "https://www.angelone.in",
        },
    ],
}

# Play Store package IDs (most important for changelogs)
PLAY_STORE_PACKAGES: Dict[str, str] = {
    "Zerodha": "com.zerodha.kite3",
    "Groww": "com.groww.invest",
    "Fyers": "com.fyers",
    "Angel One": "com.msf.angelmobile",
    "Upstox": "com.upstox.trade",
    "ICICI Direct": "com.icici.direct",
}

# Common user-agent to avoid simple blocks
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class WebConnector(BaseConnector):
    """
    Production-grade Web Connector for official broker sources.

    Features:
    - Fetches from curated list of high-signal official pages.
    - Extracts Play Store changelogs (critical for new feature detection).
    - Proper date range filtering.
    - Returns RawSearchResult objects ready for the Normalizer.
    - Excellent error isolation and logging.
    """

    name = "web"
    supports_parallel = True

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.client: Optional[httpx.AsyncClient] = None
        self.timeout = httpx.Timeout(25.0, connect=10.0)
        self.max_retries = 2

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy initialization of async HTTP client."""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
                follow_redirects=True,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self.client

    async def close(self):
        """Cleanup HTTP client."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            self.logger.debug("WebConnector HTTP client closed")

    # -------------------------------------------------------------------------
    # Core Search Method (required by BaseConnector)
    # -------------------------------------------------------------------------
    async def search(
        self,
        brokers: List[BrokerName],
        start_date: datetime,
        end_date: datetime,
        limit_per_broker: int = 50,
    ) -> List[RawSearchResult]:
        """
        Collect data from web sources for the given brokers and date window.

        Strategy:
        1. For each broker, fetch from its known official blog / update pages.
        2. Fetch the latest Play Store changelog (very high value for features).
        3. Parse items that fall within [start_date, end_date].
        4. Convert to RawSearchResult objects.
        """
        self.logger.info(
            f"WebConnector starting collection for {len(brokers)} brokers | "
            f"{start_date.date()} → {end_date.date()}"
        )

        all_results: List[RawSearchResult] = []
        client = await self._get_client()

        for broker in brokers:
            broker_results = await self._collect_for_broker(
                client, broker, start_date, end_date
            )
            all_results.extend(broker_results[:limit_per_broker])

            if broker_results:
                self.logger.info(f"  {broker}: collected {len(broker_results)} items from web sources")

        self.logger.info(f"WebConnector finished. Total raw results: {len(all_results)}")
        return all_results

    async def _collect_for_broker(
        self,
        client: httpx.AsyncClient,
        broker: BrokerName,
        start_date: datetime,
        end_date: datetime,
    ) -> List[RawSearchResult]:
        """Collect from all configured sources for one broker."""
        results: List[RawSearchResult] = []

        # 1. Official blog / update pages
        sources = OFFICIAL_SOURCES.get(broker, [])
        for source in sources:
            try:
                items = await self._fetch_official_blog(
                    client, broker, source, start_date, end_date
                )
                results.extend(items)
            except Exception as e:
                self.logger.warning(f"Failed to fetch {source['name']} for {broker}: {e}")

        # 2. Play Store changelog (extremely valuable for feature tracking)
        try:
            play_results = await self._fetch_play_store_changelog(
                client, broker, start_date, end_date
            )
            results.extend(play_results)
        except Exception as e:
            self.logger.warning(f"Play Store fetch failed for {broker}: {e}")

        return results

    # -------------------------------------------------------------------------
    # Official Blog / Update Page Fetching
    # -------------------------------------------------------------------------
    async def _fetch_official_blog(
        self,
        client: httpx.AsyncClient,
        broker: BrokerName,
        source: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> List[RawSearchResult]:
        """Fetch and parse a single official blog/update page."""
        url = source["url"]
        self.logger.debug(f"Fetching {source['name']} ({url})")

        try:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            self.logger.warning(f"HTTP error fetching {url}: {e}")
            return []

        # Different parsers per source type (pragmatic regex-based extraction)
        if "zerodha" in url.lower() or "z-connect" in url.lower():
            posts = self._parse_zerodha_zconnect(html, start_date, end_date)
        elif "groww" in url.lower():
            posts = self._parse_groww_updates(html, start_date, end_date)
        else:
            # Generic parser for other blogs
            posts = self._parse_generic_blog(html, start_date, end_date, base_url=source.get("base_url", ""))

        results = []
        for post in posts:
            results.append(
                RawSearchResult(
                    source=f"web:{source['name']}",
                    query=f"{broker} official update",
                    broker=broker,
                    platform="blog",
                    raw_data={
                        "text": post["title"] + "\n" + post.get("excerpt", ""),
                        "url": post["url"],
                        "title": post["title"],
                        "published_at": post["date"].isoformat(),
                        "engagement": 0,
                        "source_name": source["name"],
                    },
                    metadata={
                        "source_type": source["type"],
                        "official": True,
                    },
                )
            )
        return results

    def _parse_zerodha_zconnect(
        self, html: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Parse Zerodha Z-Connect pages."""
        posts = []
        # Z-Connect typically uses articles with dates
        # Look for patterns like "May 22, 2026" or "22 May 2026"
        date_pattern = re.compile(
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})',
            re.IGNORECASE
        )

        # Find post containers (rough but effective)
        article_blocks = re.findall(
            r'<article[^>]*>(.*?)</article>|<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
            html,
            re.DOTALL | re.IGNORECASE
        )

        for block in article_blocks:
            block_text = " ".join(block).strip()
            if not block_text:
                continue

            # Extract title
            title_match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', block_text, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else "Zerodha Update"

            # Extract link
            link_match = re.search(r'href=["\']([^"\']+)["\']', block_text)
            url = link_match.group(1) if link_match else "https://zerodha.com/z-connect/"
            if url.startswith("/"):
                url = "https://zerodha.com" + url

            # Extract date
            date_match = date_pattern.search(block_text)
            if not date_match:
                continue

            try:
                post_date = self._parse_human_date(date_match.group(1))
                if start_date <= post_date <= end_date:
                    posts.append({
                        "title": title[:200],
                        "url": url,
                        "date": post_date,
                        "excerpt": block_text[:300],
                    })
            except Exception:
                continue

        return posts

    def _parse_groww_updates(
        self, html: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Parse Groww /updates page (very clean structure)."""
        posts = []
        # Groww uses cards with dates like "May 14, 2026"
        date_pattern = re.compile(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{4})', re.I)

        # Find update cards
        cards = re.findall(r'<div[^>]*class="[^"]*update[^"]*"[^>]*>(.*?)</div>|<article[^>]*>(.*?)</article>', html, re.DOTALL | re.I)

        for card in cards:
            text = " ".join(card)
            date_match = date_pattern.search(text)
            if not date_match:
                continue

            try:
                post_date = self._parse_human_date(date_match.group(1))
                if not (start_date <= post_date <= end_date):
                    continue

                title_match = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', text, re.DOTALL)
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else "Groww Update"

                link_match = re.search(r'href=["\']([^"\']+)["\']', text)
                url = link_match.group(1) if link_match else "https://groww.in/updates"
                if url.startswith("/"):
                    url = "https://groww.in" + url

                posts.append({
                    "title": title[:200],
                    "url": url,
                    "date": post_date,
                    "excerpt": text[:400],
                })
            except Exception:
                continue

        return posts

    def _parse_generic_blog(
        self, html: str, start_date: datetime, end_date: datetime, base_url: str = ""
    ) -> List[Dict[str, Any]]:
        """Generic fallback parser for other broker blogs."""
        posts = []
        date_pattern = re.compile(
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})',
            re.IGNORECASE
        )

        # Find any links that look like blog posts near dates
        links_with_dates = re.findall(
            r'(<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</a>).*?(' + date_pattern.pattern + ')',
            html,
            re.DOTALL | re.IGNORECASE
        )

        for link_html, href, _, date_str in links_with_dates:
            try:
                post_date = self._parse_human_date(date_str)
                if not (start_date <= post_date <= end_date):
                    continue

                title = re.sub(r'<[^>]+>', '', link_html).strip()[:200]
                full_url = urljoin(base_url or "https://example.com", href)

                posts.append({
                    "title": title,
                    "url": full_url,
                    "date": post_date,
                    "excerpt": "",
                })
            except Exception:
                continue

        return posts[:30]  # safety cap

    # -------------------------------------------------------------------------
    # Play Store Changelogs (Critical for v2.1 New Features)
    # -------------------------------------------------------------------------
    async def _fetch_play_store_changelog(
        self,
        client: httpx.AsyncClient,
        broker: BrokerName,
        start_date: datetime,
        end_date: datetime,
    ) -> List[RawSearchResult]:
        """Fetch and parse the latest Play Store 'What's new' section."""
        package_id = PLAY_STORE_PACKAGES.get(broker)
        if not package_id:
            return []

        url = f"https://play.google.com/store/apps/details?id={package_id}&hl=en_IN"
        self.logger.debug(f"Fetching Play Store changelog for {broker}: {url}")

        try:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            self.logger.warning(f"Play Store fetch failed for {broker}: {e}")
            return []

        # Extract "What's new" section (Play Store structure changes over time)
        changelog_match = re.search(
            r'(?:What\'s new|Recent changes|New in this version).*?(?=<div|<span|Updated)',
            html,
            re.DOTALL | re.IGNORECASE
        )

        changelog_text = ""
        if changelog_match:
            changelog_text = re.sub(r'<[^>]+>', ' ', changelog_match.group(0)).strip()[:1500]

        # Try to extract last updated date
        updated_match = re.search(r'Updated on\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})', html, re.IGNORECASE)
        update_date = datetime.utcnow()
        if updated_match:
            try:
                update_date = self._parse_human_date(updated_match.group(1))
            except Exception:
                pass

        if not changelog_text or update_date < start_date or update_date > end_date:
            return []

        return [
            RawSearchResult(
                source="web:play_store",
                query=f"{broker} app update changelog",
                broker=broker,
                platform="play_store",
                raw_data={
                    "text": f"Play Store update for {broker}: {changelog_text}",
                    "url": url,
                    "title": f"{broker} - Play Store Update",
                    "published_at": update_date.isoformat(),
                    "engagement": 0,
                    "package_id": package_id,
                },
                metadata={
                    "source_type": "play_store_changelog",
                    "official": True,
                    "high_value_for_features": True,
                },
            )
        ]

    # -------------------------------------------------------------------------
    # Date Parsing Helpers
    # -------------------------------------------------------------------------
    def _parse_human_date(self, date_str: str) -> datetime:
        """Parse common human-readable date formats."""
        date_str = date_str.strip().replace(",", " ").replace(".", "")
        formats = [
            "%d %b %Y",
            "%d %B %Y",
            "%b %d %Y",
            "%B %d %Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # Fallback
        return datetime.utcnow() - timedelta(days=30)

    # -------------------------------------------------------------------------
    # Normalizer Integration
    # -------------------------------------------------------------------------
    async def normalize(self, raw_results: List[RawSearchResult]) -> List["NormalizedMention"]:
        """
        Convert raw web results into NormalizedMention using the central Normalizer.
        """
        from app.data_collection.normalizer import Normalizer

        normalizer = Normalizer()
        return normalizer.normalize_raw_results(raw_results)

    # -------------------------------------------------------------------------
    # Health Check (important for monitoring)
    # -------------------------------------------------------------------------
    async def health_check(self) -> Dict[str, Any]:
        """Check connectivity to key web sources."""
        client = await self._get_client()
        results = {}
        test_urls = [
            ("Zerodha Z-Connect", "https://zerodha.com/z-connect/"),
            ("Groww Updates", "https://groww.in/updates"),
            ("Fyers Notice Board", "https://fyers.in/notice-board/"),
            ("Play Store (Zerodha)", "https://play.google.com/store/apps/details?id=com.zerodha.kite3"),
        ]

        for name, url in test_urls:
            try:
                start = datetime.utcnow()
                resp = await client.get(url, timeout=15.0)
                latency = (datetime.utcnow() - start).total_seconds() * 1000
                results[name] = {
                    "status": "ok" if resp.status_code < 400 else "error",
                    "status_code": resp.status_code,
                    "latency_ms": round(latency, 1),
                    "url": url,
                }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e)[:100],
                    "url": url,
                }

        overall_ok = all(r.get("status") == "ok" for r in results.values())

        return {
            "status": "healthy" if overall_ok else "degraded",
            "connector": self.name,
            "sources_checked": len(results),
            "details": results,
            "note": "Official blogs and Play Store are the most reliable sources for feature and stability signals.",
        }


# Convenience factory
def create_web_connector(**kwargs) -> WebConnector:
    """Factory function for easy instantiation."""
    return WebConnector(config=kwargs)


# =============================================================================
# Manual Testing / Example Usage
# =============================================================================
if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta

    async def demo():
        print("=" * 70)
        print("WebConnector Demo - Collecting from official sources")
        print("=" * 70)

        connector = create_web_connector()
        brokers = ["Zerodha", "Groww", "Fyers"]

        # Last 14 days for demo
        end = datetime.utcnow()
        start = end - timedelta(days=14)

        print(f"\nCollecting for: {brokers}")
        print(f"Date range: {start.date()} → {end.date()}\n")

        try:
            results = await connector.search(brokers, start, end, limit_per_broker=20)
            print(f"✅ Collected {len(results)} raw items from web sources\n")

            # Show sample
            for r in results[:5]:
                print(f"  • [{r.broker}] {r.raw_data.get('title', 'Update')[:70]}")
                print(f"    Source: {r.source} | Date: {r.raw_data.get('published_at', 'N/A')[:10]}")
                print(f"    URL: {r.raw_data.get('url', 'N/A')}\n")

            # Health check
            health = await connector.health_check()
            print("Health check status:", health.get("status"))
            print("Sources checked:", health.get("sources_checked"))

        finally:
            await connector.close()

        print("\n" + "=" * 70)
        print("Demo complete. In production, results are passed to the Normalizer.")
        print("=" * 70)

    asyncio.run(demo())
