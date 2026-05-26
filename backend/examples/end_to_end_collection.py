#!/usr/bin/env python
"""
BrokerWeeklyIntel - End-to-End Data Collection Example (Agent-Driven)

This is the recommended reference script for running real weekly collections
combining Web sources + X/Twitter using the Grok agent.

=============================================================================
FULL WORKFLOW (Run this inside a Grok chat session)
=============================================================================

1. Set your target week (start_date / end_date) and list of brokers.
2. Run the "QUERY GENERATION" section below.
3. Copy the generated queries.
4. In the same chat, call the agent's tools:
      - x_keyword_search (with the keyword queries)
      - x_semantic_search (with the semantic queries)
5. Paste the tool results back into this script (in the "INGEST X RESULTS" section).
6. Run the full collection pipeline.
7. Inspect the saved artifacts.

This gives you the exact same high-quality data that powered the v2.1 reports.

=============================================================================
"""

from datetime import datetime, timedelta
from pathlib import Path
import json
import asyncio
from typing import List, Dict, Any

# =============================================================================
# PROJECT IMPORTS
# =============================================================================
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Allow running from examples/

from app.data_collection import DataCollector
from app.data_collection.connectors.web_connector import create_web_connector
from app.data_collection.connectors.x_connector import XConnector, create_x_connector
from app.data_collection.models import NormalizedMention


# =============================================================================
# CONFIGURATION
# =============================================================================

# === CHANGE THESE FOR EACH RUN ===
WEEK_START = datetime(2026, 5, 19)          # Monday
WEEK_END   = datetime(2026, 5, 26)          # Sunday (inclusive)

BROKERS = [
    "Zerodha",
    "Groww",
    "Fyers",
    "Angel One",
    # "Upstox",
    # "ICICI Direct",
]

OUTPUT_DIR = Path("data/historical")        # Will create collection_YYYY-WXX_xxxxxx/

# For demo purposes (set to False when doing real collection)
DEMO_MODE = False


# =============================================================================
# STEP 1: GENERATE SMART QUERIES (Always works - no tools needed)
# =============================================================================

def generate_x_queries():
    """Generate high-quality queries for X search."""
    print("=" * 70)
    print("STEP 1: GENERATING SMART X QUERIES")
    print("=" * 70)

    all_keyword_queries = {}
    all_semantic_queries = {}

    for broker in BROKERS:
        keyword_qs = XConnector.get_keyword_queries(
            broker=broker,
            start_date=WEEK_START,
            end_date=WEEK_END,
            min_faves=1
        )
        semantic_qs = XConnector.get_semantic_queries(broker)

        all_keyword_queries[broker] = keyword_qs
        all_semantic_queries[broker] = semantic_qs

        print(f"\n--- {broker} ---")
        print("Keyword queries (use with x_keyword_search):")
        for q in keyword_qs:
            print(f"  • {q}")

        print("\nSemantic queries (use with x_semantic_search):")
        for q in semantic_qs:
            print(f"  • {q}")

    return all_keyword_queries, all_semantic_queries


# =============================================================================
# STEP 2: CALL AGENT TOOLS (You do this manually in the chat)
# =============================================================================
"""
EXAMPLE - Copy these patterns and run them in your Grok chat:

# For Zerodha (example)
zerodha_keyword_posts = await x_keyword_search(
    query='@zerodhaonline (terminal mode OR "fixed deposits" OR "coin fd") since:2026-05-19 until:2026-05-26 min_faves:1',
    limit=10,
    mode="Latest"
)

zerodha_semantic_posts = await x_semantic_search(
    query="real user reactions to Zerodha Terminal Mode or Coin Fixed Deposits",
    limit=8,
    from_date="2026-05-19",
    to_date="2026-05-26"
)

# Repeat for other brokers...
"""

# =============================================================================
# STEP 3: INGEST X RESULTS (Paste tool output here)
# =============================================================================

def ingest_x_results() -> List[Dict[str, Any]]:
    """
    PASTE YOUR TOOL RESULTS HERE.

    This function should return a flat list of post dictionaries
    in the format returned by x_keyword_search / x_semantic_search.
    """
    if DEMO_MODE:
        print("\n[DEMO MODE] Using sample X posts...")
        # Small synthetic sample for testing the pipeline
        return [
            {
                "id": "1234567890",
                "text": "Terminal mode is very nice but it freezes during order placement. This is happening on every trade.",
                "url": "https://x.com/example/status/1234567890",
                "author_username": "trader_vignesh",
                "created_at": "2026-05-22T10:15:00Z",
                "public_metrics": {"like_count": 47, "retweet_count": 12},
            },
            {
                "id": "9876543210",
                "text": "Fyers just dropped Bar Replay + Fixed Deposits in one update. This is huge. Loving the new experience 🔥",
                "url": "https://x.com/example/status/9876543210",
                "author_username": "options_trader",
                "created_at": "2026-05-23T14:30:00Z",
                "public_metrics": {"like_count": 89},
            },
        ]

    # === REAL DATA GOES BELOW ===
    # Example structure (replace with actual tool output):
    # all_x_posts = []
    # all_x_posts.extend(zerodha_keyword_posts)
    # all_x_posts.extend(fyers_semantic_posts)
    # ... etc
    # return all_x_posts

    print("\n[REAL MODE] No X posts provided yet.")
    print("Please paste results from x_keyword_search / x_semantic_search above.")
    return []


# =============================================================================
# STEP 4 + 5: RUN FULL COLLECTION (Web + X)
# =============================================================================

async def run_full_collection(x_posts: List[Dict[str, Any]]):
    """Run Web + X collection through the DataCollector."""
    print("\n" + "=" * 70)
    print("STEP 4+5: RUNNING FULL DATA COLLECTION")
    print("=" * 70)

    # Create connectors
    web_connector = create_web_connector()
    x_connector = create_x_connector()

    # Ingest X data (if any)
    x_raw_results = []
    if x_posts:
        x_raw_results = x_connector.ingest_x_posts(x_posts)
        print(f"Ingested {len(x_raw_results)} posts from X")

    # Create collector with both connectors
    collector = DataCollector(
        connectors=[web_connector, x_connector],
        output_dir=OUTPUT_DIR,
        deduplicate=True,
    )

    print(f"\nCollecting for: {WEEK_START.date()} → {WEEK_END.date()}")
    print(f"Brokers: {BROKERS}")
    print(f"Connectors: Web + X")

    # Run collection
    # Note: Web runs autonomously. X data is pre-ingested.
    result = await collector.run_collection(
        week_start=WEEK_START,
        week_end=WEEK_END,
        brokers=BROKERS,
        save_artifacts=True,
    )

    await collector.close()

    print("\n✅ Collection completed!")
    print(f"   Raw results:     {result.run.total_raw_results}")
    print(f"   Normalized:      {result.run.total_normalized_mentions}")
    print(f"   Sources used:    {result.run.sources_used}")

    if result.normalized_artifacts_path:
        print(f"\n📁 Artifacts saved to:\n   {result.normalized_artifacts_path}")

    # Show per-broker breakdown
    print("\nPer-broker breakdown:")
    for broker, br in result.broker_results.items():
        print(f"  {broker}: {len(br.mentions)} mentions")

    return result


# =============================================================================
# MAIN ENTRYPOINT
# =============================================================================

async def main():
    print("\n" + "🚀" * 35)
    print("BrokerWeeklyIntel - End-to-End Collection Example")
    print("🚀" * 35 + "\n")

    # Step 1: Generate queries (always useful)
    keyword_queries, semantic_queries = generate_x_queries()

    # Step 3: Get X posts (user pastes here or DEMO_MODE)
    x_posts = ingest_x_results()

    # Step 4+5: Run the full pipeline
    result = await run_full_collection(x_posts)

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. Check the artifacts folder for normalized data + summary.json")
    print("2. Feed the normalized mentions into your analysis/scoring layer")
    print("3. Generate the final v2.1 Markdown + JSON report")
    print("\nTip: You can re-run this script with real X data anytime.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
