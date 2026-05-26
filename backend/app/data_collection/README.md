# Data Collection Layer

This is the foundation of BrokerWeeklyIntel. All intelligence starts here.

## Goals

- Collect high-signal data about Indian stock brokers from many sources

## Credentials (Apify + Firecrawl)

The project now has a real Apify token stored for the whole project:

- Root: `BrokerWeeklyIntel/.env` → `APIFY_API_TOKEN` + `ENABLE_APIFY=true`
- Backend: `backend/.env` (same values)

The Python `Settings` loader (`app/core/config.py`) and `DataCollector` will automatically pick these up.

To run with all four sources (Web + X + Apify + Firecrawl):

```bash
cd BrokerWeeklyIntel
python -m backend.app.data_collection.collector run-weekly --use-apify --use-firecrawl
# or the convenience script
python backend/scripts/run_weekly.py
```

See `.env.example` (both root and backend/) for the full template. Never commit real tokens.
- Normalize everything into consistent, v2.1-ready models
- Support weekly automated runs + manual deep dives
- Be resilient when individual sources (X, Apify, etc.) are rate-limited or unavailable

## Current Structure

```
data_collection/
├── __init__.py
├── models.py                 # Rich Pydantic models (v2.1 aligned)
├── base_connector.py         # Abstract interface all sources must follow
├── normalizer.py             # Central cleaning + tagging logic
├── collector.py              # Main orchestrator + CLI entrypoint
├── connectors/
│   ├── web_connector.py        # Official blogs, Play Store, news (highest priority)
│   ├── x_connector.py          # X/Twitter (keyword + semantic)
│   ├── apify_connector.py      # Smart multi-platform Apify (with intelligent actor registry)
│   ├── firecrawl_connector.py  # High-quality web extraction via Firecrawl (clean Markdown + metadata)
│   └── reddit_connector.py     # Thin wrapper (delegates to ApifyConnector)
├── README.md
└── ../examples/end_to_end_collection.py   # ← Recommended starting point
```

## How to Add a New Source

1. Create a new file in `connectors/`, e.g. `youtube_connector.py`
2. Inherit from `BaseConnector`
3. Implement:
   - `async def search(...) -> List[RawSearchResult]`
   - `async def health_check() -> Dict`
4. (Optional) Override `normalize()` if you have source-specific logic
5. Register the connector in `collector.py` or when instantiating `DataCollector`
6. Add any new required fields to `models.py` if needed

Example skeleton:

```python
from app.data_collection.base_connector import BaseConnector
from app.data_collection.models import RawSearchResult, BrokerName

class YouTubeConnector(BaseConnector):
    name = "youtube"

    async def search(self, brokers, start_date, end_date, ...):
        # Use web_search with "site:youtube.com" + broker name + date
        # Or future dedicated YouTube comment scraper
        ...
```

## Running Collection Manually

```python
import asyncio
from datetime import datetime
from app.data_collection.collector import run_weekly_collection

# Basic run (Web + X only - recommended default)
result = await run_weekly_collection()

# Run with all available sources (requires API keys)
result = await run_weekly_collection(
    week_start=datetime(2026, 5, 19),
    use_apify=True,
    use_firecrawl=True,
)
```

You can also control connectors explicitly:

```python
from app.data_collection import DataCollector
from app.data_collection.connectors import (
    create_web_connector, create_x_connector,
    create_apify_connector, create_firecrawl_connector,
)

collector = DataCollector(
    use_web=True,
    use_x=True,
    use_apify=True,      # requires APIFY_API_TOKEN
    use_firecrawl=True,  # requires FIRECRAWL_API_KEY
)
result = await collector.run_collection(...)
```

## Artifacts

By default, collection runs write to `data/historical/collection_YYYY-WXX_<runid>/`:
- Per-broker normalized JSON
- Lightweight raw results
- `collection_run.json` (metadata + errors)

## Firecrawl Connector

`FirecrawlConnector` provides high-quality web scraping using the Firecrawl API.

**Strengths**:
- Returns clean Markdown instead of raw HTML
- Excellent metadata extraction (publish dates, titles, authors)
- Much better than regex-based parsing for blog and news pages
- Ideal complement to the existing `WebConnector`

Set `FIRECRAWL_API_KEY` in your environment to enable it.

It can be used alongside or instead of `WebConnector` for official broker sources.

## Smart Apify Connector (Intelligent Actor Selection)

The `ApifyConnector` is designed to be **AI-friendly**:

```python
from app.data_collection import create_apify_connector, get_recommended_actor

apify = create_apify_connector()

# Ask the system what the best tool is
rec = get_recommended_actor(platform="reddit", use_case="glitches")
print(rec["primary"])           # → "clockworks/reddit-scraper"

# Or use the powerful platform-aware search
results = await apify.search_platform(
    platform="reddit",
    brokers=["Zerodha", "Groww"],
    start_date=...,
    end_date=...,
    use_case="discussions"
)
```

Supported platforms (with registry entries): Reddit, Instagram, YouTube, TikTok, LinkedIn, Facebook.

## DataCollector Configuration

The `DataCollector` and `run_weekly_collection()` now support all four connectors:

**Default behavior (recommended):**
- WebConnector + XConnector are always included.

**Opt-in advanced sources:**
- Set `ENABLE_APIFY=true` + provide `APIFY_API_TOKEN`
- Set `ENABLE_FIRECRAWL=true` + provide `FIRECRAWL_API_KEY`

You can also control them per-call:

```python
result = await run_weekly_collection(
    use_apify=True,
    use_firecrawl=True,
)
```

Graceful degradation: If a key is missing when the corresponding flag is enabled, a warning is logged and collection continues with the available connectors.

## Alignment with v2.1 Reports

The models in this layer directly support the richer v2.1 output:
- `BrokerFeatureUpdate` → New Features table
- `KeyQuote` + `negative_themes` → User Quotes & Sentiment Themes section
- `TechnicalIssue` with `issue_type` (feature_specific / platform_wide) → Improved Technical tracking
- `CollectionResult` can be easily transformed into the final `WeeklyReport` + dashboard JSON

## Status (Updated)

- **DataCollector**: Production-ready (parallel execution, deduplication, rich artifacts)
- **WebConnector**: Production-ready (official blogs + Play Store)
- **XConnector**: Production-ready (agent-optimized with excellent query generation + ingestion)
- Normalizer: Good (heuristic tagging for features, glitches, and themes)
- Full end-to-end examples: Available

## Recommended Next Step: End-to-End Example

The best way to understand and use the full Data Collection Layer is to follow this guided example:

**`backend/examples/end_to_end_collection.py`**

This script walks you through:
1. Generating smart queries for X using `XConnector`
2. Calling `x_keyword_search` + `x_semantic_search` (as the Grok agent)
3. Ingesting X results
4. Running Web + X together through the `DataCollector`
5. Saving properly structured artifacts

Run it directly:
```bash
python backend/examples/end_to_end_collection.py
```

See the main project `docs/ARCHITECTURE.md` for the broader picture.
