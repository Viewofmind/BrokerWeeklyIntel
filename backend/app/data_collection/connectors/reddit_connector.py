"""
BrokerWeeklyIntel - Data Collection Layer
Reddit Connector

Now powered by ApifyConnector for production-grade scraping.
Falls back to empty results if Apify is not configured.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from app.data_collection.base_connector import BaseConnector
from app.data_collection.models import RawSearchResult, BrokerName
from app.data_collection.connectors.apify_connector import (
    ApifyConnector,
    create_apify_connector,
    get_recommended_actor,
)


class RedditConnector(BaseConnector):
    """
    Connector for Reddit (r/IndianStreetBets, r/Zerodha, r/Groww, etc.).

    This is now a thin wrapper. Real implementation lives in ApifyConnector
    (which uses high-quality Apify Reddit actors and is the recommended path).
    """

    name = "reddit"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._apify: Optional[ApifyConnector] = None
        # Only create Apify backend if token is available
        try:
            self._apify = create_apify_connector(config=config)
        except Exception:
            self._apify = None

    async def search(
        self,
        brokers: List[BrokerName],
        start_date: datetime,
        end_date: datetime,
        limit_per_broker: int = 50,
    ) -> List[RawSearchResult]:
        if self._apify and self._apify.apify_token:
            self.logger.info("RedditConnector delegating to ApifyConnector (production Reddit scraping)")
            # Delegate fully — ApifyConnector already returns properly shaped RawSearchResult
            return await self._apify.search(brokers, start_date, end_date, limit_per_broker)

        self.logger.info("[FALLBACK] RedditConnector: No Apify token — returning empty (use ApifyConnector directly for Reddit)")
        return []

    async def health_check(self) -> Dict[str, Any]:
        if self._apify:
            apify_health = await self._apify.health_check()
            apify_health["wrapped_by"] = "RedditConnector"
            return apify_health

        return {
            "status": "no_apify_token",
            "message": "RedditConnector is a thin wrapper. Use create_apify_connector() directly for full Reddit scraping.",
            "recommendation": "Set APIFY_API_TOKEN and use ApifyConnector or DataCollector with it registered.",
        }

    async def close(self):
        if self._apify:
            await self._apify.close()
