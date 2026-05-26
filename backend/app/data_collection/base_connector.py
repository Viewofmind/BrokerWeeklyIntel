"""
BrokerWeeklyIntel - Data Collection Layer
Abstract Base Connector

All data source connectors must inherit from this class.
This enforces a consistent interface so new sources (Discord, LinkedIn, App Store reviews, etc.)
can be added with minimal friction.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from app.data_collection.models import RawSearchResult, NormalizedMention, BrokerName


logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.

    Responsibilities:
    - Accept a standardized date range
    - Return raw results
    - (Optional) Return already-normalized mentions
    - Report source name and health/status
    """

    name: str = "base"
    supports_parallel: bool = True

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"data_collection.{self.name}")

    @abstractmethod
    async def search(
        self,
        brokers: List[BrokerName],
        start_date: datetime,
        end_date: datetime,
        limit_per_broker: int = 50,
    ) -> List[RawSearchResult]:
        """
        Perform a search / scrape for the given brokers and date range.

        Must be implemented by every connector.
        Should be idempotent / safe to call multiple times.
        """
        raise NotImplementedError

    async def normalize(self, raw_results: List[RawSearchResult]) -> List[NormalizedMention]:
        """
        Convert RawSearchResult objects into NormalizedMention objects.

        Default implementation is a no-op (returns empty). Most connectors
        should override this or delegate to the central Normalizer.
        """
        return []

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return status information (rate limits, auth status, last error, etc.)."""
        raise NotImplementedError

    def get_source_name(self) -> str:
        return self.name

    async def close(self):
        """Cleanup resources (close HTTP clients, etc.). Override if needed."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
