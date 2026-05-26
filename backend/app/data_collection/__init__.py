"""
BrokerWeeklyIntel - Data Collection Layer

This package provides a modular, extensible system for collecting competitor
intelligence from multiple sources (Web, X, Reddit, YouTube, official blogs, etc.).

Core principles:
- Consistent interface via BaseConnector
- Strong normalization into v2.1-ready models
- Graceful degradation when tools are limited
- Easy to extend with new sources

Public API:
    from app.data_collection.collector import DataCollector, run_weekly_collection
    from app.data_collection.models import CollectionResult, NormalizedMention, ...
"""

from app.data_collection.collector import DataCollector, run_weekly_collection
from app.data_collection.models import (
    CollectionResult,
    CollectionRun,
    NormalizedMention,
    BrokerFeatureUpdate,
    TechnicalIssue,
    KeyQuote,
)
from app.data_collection.base_connector import BaseConnector
from app.data_collection.normalizer import Normalizer
from app.data_collection.connectors.web_connector import (
    WebConnector,
    create_web_connector,
    OFFICIAL_SOURCES,
    PLAY_STORE_PACKAGES,
)
from app.data_collection.connectors.x_connector import (
    XConnector,
    create_x_connector,
)
from app.data_collection.connectors.apify_connector import (
    ApifyConnector,
    create_apify_connector,
    ACTOR_REGISTRY,
    get_recommended_actor,
)
from app.data_collection.connectors.firecrawl_connector import (
    FirecrawlConnector,
    create_firecrawl_connector,
    FIRECRAWL_SOURCES,
)

__all__ = [
    "DataCollector",
    "run_weekly_collection",
    "BaseConnector",
    "Normalizer",
    "WebConnector",
    "create_web_connector",
    "XConnector",
    "create_x_connector",
    "ApifyConnector",
    "create_apify_connector",
    "ACTOR_REGISTRY",
    "get_recommended_actor",
    "FirecrawlConnector",
    "create_firecrawl_connector",
    "FIRECRAWL_SOURCES",
    "OFFICIAL_SOURCES",
    "PLAY_STORE_PACKAGES",
    "CollectionResult",
    "CollectionRun",
    "NormalizedMention",
    "BrokerFeatureUpdate",
    "TechnicalIssue",
    "KeyQuote",
]
