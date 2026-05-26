"""
Data Collection Connectors

Currently implemented (stubs):
- WebConnector (highest priority + most reliable)
- XConnector
- RedditConnector

Add new ones here (YouTube, Discord, App Store reviews, etc.).
"""

from app.data_collection.connectors.web_connector import WebConnector
from app.data_collection.connectors.x_connector import XConnector
from app.data_collection.connectors.reddit_connector import RedditConnector
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
    "WebConnector",
    "XConnector",
    "RedditConnector",
    "ApifyConnector",
    "create_apify_connector",
    "ACTOR_REGISTRY",
    "get_recommended_actor",
    "FirecrawlConnector",
    "create_firecrawl_connector",
    "FIRECRAWL_SOURCES",
]
