"""
BrokerWeeklyIntel - Data Collection Layer
Main DataCollector Orchestrator (Production Implementation)

This is the central coordinator for all data collection activities.

Responsibilities:
- Orchestrate one or more connectors (Web, X, Reddit, etc.)
- Run collection in parallel where possible
- Deduplicate mentions across sources
- Normalize raw data using the central Normalizer
- Persist both raw and normalized artifacts
- Provide health aggregation across connectors
- Offer clean APIs for scripts and the scheduler

Recommended usage:
    from app.data_collection.collector import DataCollector, run_weekly_collection

    # Simple usage (Web + X only)
    result = await run_weekly_collection()

    # Full collection with all available sources
    result = await run_weekly_collection(
        use_apify=True,
        use_firecrawl=True,
    )

    # Advanced: explicit connectors
    from app.data_collection.connectors import (
        create_web_connector, create_x_connector,
        create_apify_connector, create_firecrawl_connector,
    )
    collector = DataCollector(connectors=[
        create_web_connector(),
        create_x_connector(),
        create_apify_connector(),
        create_firecrawl_connector(),
    ])
    result = await collector.run_collection(...)
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any

from app.data_collection.models import (
    CollectionResult,
    CollectionRun,
    BrokerCollectionResult,
    BrokerName,
    NormalizedMention,
    RawSearchResult,
)
from app.data_collection.base_connector import BaseConnector
from app.data_collection.normalizer import Normalizer

logger = logging.getLogger(__name__)


class DataCollector:
    """
    Production Data Collection Orchestrator.

    Supports four connectors out of the box:
    - WebConnector   (official blogs, Play Store) - always recommended
    - XConnector     (X/Twitter)                   - always recommended
    - ApifyConnector (Reddit + multi-platform)    - opt-in, requires APIFY_API_TOKEN
    - FirecrawlConnector (high-quality Markdown)  - opt-in, requires FIRECRAWL_API_KEY

    Features:
    - Parallel execution across connectors using asyncio
    - Cross-source deduplication
    - Automatic normalization
    - Rich artifact persistence (raw + normalized + summary)
    - Health aggregation
    - Graceful error handling per connector
    - Easy opt-in for advanced sources via boolean flags
    """

    DEFAULT_BROKERS: List[BrokerName] = [
        "Zerodha", "Groww", "Angel One", "Upstox", "Fyers",
        "ICICI Direct", "5Paisa", "Kotak Securities"
    ]

    def __init__(
        self,
        connectors: Optional[List[BaseConnector]] = None,
        normalizer: Optional[Normalizer] = None,
        output_dir: Optional[Path] = None,
        deduplicate: bool = True,
        # --- New opt-in connector flags (recommended way to enable advanced sources) ---
        use_web: bool = True,
        use_x: bool = True,
        use_apify: bool = False,
        use_firecrawl: bool = False,
    ):
        self.logger = logger

        # If explicit connectors list is provided, use it directly (full control)
        if connectors is not None:
            self.connectors: List[BaseConnector] = connectors
        else:
            # Build default set of connectors based on flags + available credentials
            self.connectors = self._build_default_connectors(
                use_web=use_web,
                use_x=use_x,
                use_apify=use_apify,
                use_firecrawl=use_firecrawl,
            )

        self.normalizer = normalizer or Normalizer()
        self.output_dir = output_dir or Path("data/historical")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.deduplicate = deduplicate

    def _build_default_connectors(
        self,
        use_web: bool,
        use_x: bool,
        use_apify: bool,
        use_firecrawl: bool,
    ) -> List[BaseConnector]:
        """
        Build the default set of connectors based on flags and credential availability.
        Always starts with Web + X (core sources) and adds advanced ones only when requested.
        """
        connectors: List[BaseConnector] = []
        from app.core.config import get_settings
        settings = get_settings()

        # --- Core connectors (enabled by default) ---
        if use_web:
            try:
                from app.data_collection.connectors.web_connector import create_web_connector
                connectors.append(create_web_connector())
                self.logger.debug("Added WebConnector")
            except Exception as e:
                self.logger.warning(f"Failed to initialize WebConnector: {e}")

        if use_x:
            try:
                from app.data_collection.connectors.x_connector import create_x_connector
                connectors.append(create_x_connector())
                self.logger.debug("Added XConnector")
            except Exception as e:
                self.logger.warning(f"Failed to initialize XConnector: {e}")

        # --- Advanced / opt-in connectors ---
        if use_apify:
            if settings.apify_api_token:
                try:
                    from app.data_collection.connectors.apify_connector import create_apify_connector
                    connectors.append(create_apify_connector())
                    self.logger.info("Added ApifyConnector (Reddit + multi-platform)")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize ApifyConnector: {e}")
            else:
                self.logger.warning(
                    "use_apify=True but no APIFY_API_TOKEN found. Skipping ApifyConnector."
                )

        if use_firecrawl:
            if settings.firecrawl_api_key:
                try:
                    from app.data_collection.connectors.firecrawl_connector import create_firecrawl_connector
                    connectors.append(create_firecrawl_connector())
                    self.logger.info("Added FirecrawlConnector (high-quality web extraction)")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize FirecrawlConnector: {e}")
            else:
                self.logger.warning(
                    "use_firecrawl=True but no FIRECRAWL_API_KEY found. Skipping FirecrawlConnector."
                )

        if not connectors:
            self.logger.warning("No connectors were initialized. Collection will return empty results.")

        return connectors

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def register_connector(self, connector: BaseConnector) -> None:
        """Register an additional connector at runtime."""
        self.connectors.append(connector)
        self.logger.info(f"Registered connector: {connector.name}")

    async def run_collection(
        self,
        week_start: datetime,
        week_end: Optional[datetime] = None,
        brokers: Optional[List[BrokerName]] = None,
        save_artifacts: bool = True,
    ) -> CollectionResult:
        """
        Recommended public method for running a collection.

        This is the main entry point used by scripts and schedulers.
        """
        return await self.collect_for_week(
            week_start=week_start,
            week_end=week_end,
            brokers=brokers,
            save_artifacts=save_artifacts,
        )

    async def collect_for_week(
        self,
        week_start: datetime,
        week_end: Optional[datetime] = None,
        brokers: Optional[List[BrokerName]] = None,
        save_artifacts: bool = True,
    ) -> CollectionResult:
        """
        Collect data for a specific week across all registered connectors.
        """
        if week_end is None:
            week_end = week_start + timedelta(days=6)

        brokers = brokers or self.DEFAULT_BROKERS

        run = CollectionRun(
            week_start=week_start,
            week_end=week_end,
            brokers=brokers,
            sources_used=[c.name for c in self.connectors],
        )

        self.logger.info(
            f"Starting collection run {run.run_id[:8]} | "
            f"{week_start.date()} → {week_end.date()} | "
            f"Brokers: {len(brokers)} | Connectors: {len(self.connectors)}"
        )

        # Step 1: Run all connectors in parallel
        raw_results, errors = await self._run_connectors_in_parallel(
            brokers, week_start, week_end
        )

        # Step 2: Normalize all raw results
        normalized_mentions = self.normalizer.normalize_raw_results(raw_results)

        # Step 3: Deduplicate (if enabled)
        if self.deduplicate:
            before = len(normalized_mentions)
            normalized_mentions = self._deduplicate_mentions(normalized_mentions)
            self.logger.info(f"Deduplication: {before} → {len(normalized_mentions)} mentions")

        # Step 4: Group by broker
        broker_results = self._group_by_broker(normalized_mentions, brokers)

        # Finalize run metadata
        run.completed_at = datetime.utcnow()
        run.total_raw_results = len(raw_results)
        run.total_normalized_mentions = len(normalized_mentions)
        run.errors = errors

        result = CollectionResult(
            run=run,
            broker_results=broker_results,
        )

        # Step 5: Persist artifacts
        if save_artifacts:
            self._save_artifacts(result, raw_results, normalized_mentions)

        self.logger.info(
            f"Collection complete | "
            f"Raw: {run.total_raw_results} | "
            f"Normalized: {run.total_normalized_mentions} | "
            f"Errors: {len(errors)}"
        )

        return result

    async def collect_last_7_days(
        self,
        brokers: Optional[List[BrokerName]] = None,
        save_artifacts: bool = True,
    ) -> CollectionResult:
        """Convenience wrapper for the last 7 days."""
        end = datetime.utcnow()
        start = end - timedelta(days=7)
        return await self.run_collection(start, end, brokers, save_artifacts)

    async def get_health(self) -> Dict[str, Any]:
        """Aggregate health status from all registered connectors."""
        if not self.connectors:
            return {"status": "no_connectors", "connectors": []}

        tasks = [connector.health_check() for connector in self.connectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        connector_health = []
        for connector, health in zip(self.connectors, results):
            if isinstance(health, Exception):
                connector_health.append({
                    "name": connector.name,
                    "status": "error",
                    "error": str(health),
                })
            else:
                connector_health.append({
                    "name": connector.name,
                    **health
                })

        overall_status = "healthy"
        if any(h.get("status") == "error" for h in connector_health):
            overall_status = "degraded"
        if all(h.get("status") == "error" for h in connector_health):
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "connectors": connector_health,
        }

    async def close(self):
        """Cleanup all connectors."""
        for connector in self.connectors:
            try:
                await connector.close()
            except Exception as e:
                self.logger.warning(f"Error closing connector {connector.name}: {e}")

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------
    async def _run_connectors_in_parallel(
        self,
        brokers: List[BrokerName],
        start_date: datetime,
        end_date: datetime,
    ) -> Tuple[List[RawSearchResult], List[str]]:
        """Execute all connectors concurrently with error isolation."""
        tasks = [
            self._safe_collect(connector, brokers, start_date, end_date)
            for connector in self.connectors
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_raw: List[RawSearchResult] = []
        errors: List[str] = []

        for connector, result in zip(self.connectors, results):
            if isinstance(result, Exception):
                error_msg = f"{connector.name}: {result}"
                errors.append(error_msg)
                self.logger.error(f"Connector failed: {error_msg}")
            else:
                raw, _ = result
                all_raw.extend(raw)
                self.logger.debug(f"{connector.name} returned {len(raw)} raw results")

        return all_raw, errors

    async def _safe_collect(
        self,
        connector: BaseConnector,
        brokers: List[BrokerName],
        start: datetime,
        end: datetime,
    ) -> Tuple[List[RawSearchResult], List[NormalizedMention]]:
        """Safe wrapper around a single connector's search + normalize."""
        try:
            raw = await connector.search(brokers, start, end)
            normalized = await connector.normalize(raw)

            # Fallback to central normalizer if connector didn't normalize
            if not normalized and raw:
                normalized = self.normalizer.normalize_raw_results(raw)

            return raw, normalized
        except Exception as e:
            self.logger.exception(f"Error in connector {connector.name}")
            raise

    def _deduplicate_mentions(
        self, mentions: List[NormalizedMention]
    ) -> List[NormalizedMention]:
        """
        Deduplicate mentions across sources.

        Strategy:
        - Primary key: (broker, url)
        - Secondary: content hash of normalized text
        """
        seen: Set[str] = set()
        unique: List[NormalizedMention] = []

        for mention in mentions:
            # Primary dedup key
            key = f"{mention.broker}|{mention.url}"

            # Fallback content hash for cases where URL might differ slightly
            content_hash = hashlib.md5(
                mention.text.lower().encode("utf-8")
            ).hexdigest()[:12]
            fallback_key = f"{mention.broker}|{content_hash}"

            if key not in seen and fallback_key not in seen:
                seen.add(key)
                seen.add(fallback_key)
                unique.append(mention)

        return unique

    def _group_by_broker(
        self, mentions: List[NormalizedMention], brokers: List[BrokerName]
    ) -> Dict[BrokerName, BrokerCollectionResult]:
        """Group normalized mentions by broker."""
        grouped: Dict[BrokerName, List[NormalizedMention]] = {b: [] for b in brokers}

        for mention in mentions:
            if mention.broker in grouped:
                grouped[mention.broker].append(mention)

        result = {}
        for broker, broker_mentions in grouped.items():
            result[broker] = BrokerCollectionResult(
                broker=broker,
                mentions=broker_mentions,
            )
        return result

    def _save_artifacts(
        self,
        result: CollectionResult,
        raw_results: List[RawSearchResult],
        normalized_mentions: List[NormalizedMention],
    ) -> None:
        """Persist collection artifacts in a structured way."""
        week_label = result.run.week_start.strftime("%Y-W%W")
        run_id_short = result.run.run_id[:8]
        base_dir = self.output_dir / f"collection_{week_label}_{run_id_short}"
        base_dir.mkdir(parents=True, exist_ok=True)

        # 1. Per-broker normalized data (most useful for downstream)
        for broker, br in result.broker_results.items():
            safe_name = broker.lower().replace(" ", "_")
            path = base_dir / f"{safe_name}_mentions.json"
            data = [m.model_dump(mode="json") for m in br.mentions]
            path.write_text(json.dumps(data, indent=2, default=str))

        # 2. Full collection run metadata
        meta_path = base_dir / "collection_run.json"
        meta_path.write_text(result.run.model_dump_json(indent=2))

        # 3. Summary (very useful for reporting and debugging)
        summary = {
            "run_id": result.run.run_id,
            "week": week_label,
            "date_range": {
                "start": result.run.week_start.isoformat(),
                "end": result.run.week_end.isoformat(),
            },
            "brokers": result.run.brokers,
            "sources": result.run.sources_used,
            "totals": {
                "raw_results": result.run.total_raw_results,
                "normalized_mentions": result.run.total_normalized_mentions,
                "errors": len(result.run.errors),
            },
            "per_broker": {
                broker: {
                    "mentions": len(br.mentions),
                }
                for broker, br in result.broker_results.items()
            },
            "errors": result.run.errors,
        }
        summary_path = base_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, default=str))

        # 4. Lightweight raw results (for debugging)
        raw_path = base_dir / "raw_results.jsonl"
        with open(raw_path, "w") as f:
            for r in raw_results:
                lightweight = {
                    "source": r.source,
                    "broker": r.broker,
                    "platform": r.platform,
                    "text": (r.raw_data.get("text") or "")[:400],
                    "url": r.raw_data.get("url"),
                    "published_at": r.raw_data.get("published_at"),
                }
                f.write(json.dumps(lightweight, default=str) + "\n")

        result.raw_artifacts_path = str(raw_path)
        result.normalized_artifacts_path = str(base_dir)

        self.logger.info(f"Artifacts written to: {base_dir}")

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# =============================================================================
# High-level Convenience Function (used by scripts)
# =============================================================================

async def run_weekly_collection(
    week_start: Optional[datetime] = None,
    week_end: Optional[datetime] = None,
    brokers: Optional[List[BrokerName]] = None,
    output_dir: Optional[str] = None,
    connectors: Optional[List[BaseConnector]] = None,
    # --- New convenient flags for enabling advanced sources ---
    use_apify: bool = False,
    use_firecrawl: bool = False,
    use_web: bool = True,
    use_x: bool = True,
) -> CollectionResult:
    """
    High-level convenience function for running a weekly collection.

    This is the recommended entry point from scripts and the scheduler.

    By default only WebConnector + XConnector are used (core, always-available sources).
    Apify and Firecrawl are opt-in because they require paid API keys.

    Examples:
        # Basic run (Web + X only)
        result = await run_weekly_collection()

        # Full power run with all sources
        result = await run_weekly_collection(
            week_start=...,
            week_end=...,
            use_apify=True,
            use_firecrawl=True,
        )
    """
    if week_start is None:
        # Default to previous full week (Monday-Sunday)
        today = datetime.utcnow().date()
        days_since_monday = today.weekday()
        week_start = datetime.combine(
            today - timedelta(days=days_since_monday + 7), datetime.min.time()
        )
        week_end = week_start + timedelta(days=6)
    elif week_end is None:
        week_end = week_start + timedelta(days=6)

    # If explicit connectors list is passed, use it (highest priority, full control)
    if connectors is not None:
        collector_connectors = connectors
    else:
        # If user didn't explicitly pass flags, fall back to settings
        if not any([use_apify, use_firecrawl]):
            from app.core.config import get_settings
            s = get_settings()
            use_apify = s.enable_apify
            use_firecrawl = s.enable_firecrawl

        collector_connectors = None  # Let DataCollector build based on the (possibly updated) flags

    async with DataCollector(
        connectors=collector_connectors,
        output_dir=Path(output_dir) if output_dir else None,
        use_web=use_web,
        use_x=use_x,
        use_apify=use_apify,
        use_firecrawl=use_firecrawl,
    ) as collector:
        return await collector.run_collection(
            week_start=week_start,
            week_end=week_end,
            brokers=brokers,
        )


# =============================================================================
# CLI / Manual Execution Support
# =============================================================================

if __name__ == "__main__":
    import asyncio

    async def main():
        print("=" * 70)
        print("BrokerWeeklyIntel - Data Collection (Manual Run)")
        print("=" * 70)

        result = await run_weekly_collection()

        print("\nCollection Summary:")
        print(f"  Run ID:        {result.run.run_id}")
        print(f"  Week:          {result.run.week_start.date()} → {result.run.week_end.date()}")
        print(f"  Raw results:   {result.run.total_raw_results}")
        print(f"  Mentions:      {result.run.total_normalized_mentions}")
        print(f"  Errors:        {len(result.run.errors)}")

        if result.normalized_artifacts_path:
            print(f"\nArtifacts saved to: {result.normalized_artifacts_path}")

        print("\nDone.")

    asyncio.run(main())
