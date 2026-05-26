# BrokerWeeklyIntel - Architecture Overview

This document describes the clean, layered architecture of the Weekly Competitor Intelligence System.

## Guiding Principles

1. **Strict Layer Separation** — No layer may bypass the one below it.
2. **Evidence & Explainability** — Every rating number and insight must be traceable to source posts/threads.
3. **Idempotent & Reproducible** — Re-running analysis for the same week produces identical results (given same input data).
4. **Graceful Degradation** — Missing data from one source (e.g. rate-limited Twitter) must not break the entire report.
5. **Historical First** — The system is built around weekly snapshots that are never mutated after creation.

---

## High-Level Data Flow

```
[External Sources]
   X/Twitter • Reddit • YouTube • Blogs • Forums • Apify Actors
            │
            ▼
┌──────────────────────────────┐
│   Data Collection Layer      │  ← connectors/ + collectors
│   - Raw post/thread objects  │
│   - Deduplication            │
│   - Time window filtering    │
└──────────────┬───────────────┘
               │ Normalized Items
               ▼
┌──────────────────────────────┐
│   Analysis & Scoring Engine  │
│   - Sentiment (multi-model)  │
│   - Topic clustering         │
│   - Feature mention detection│
│   - Broker-specific signals  │
└──────────────┬───────────────┘
               │ Enriched Signals
               ▼
┌──────────────────────────────┐
│   Feature Tracking Module    │
│   - Official announcements   │
│   - User reaction aggregation│
│   - "New this week" flag     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Rating & Comparison Engine │
│   - Parameter scoring        │
│   - Weighted final score     │
│   - Δ vs previous 4 weeks    │
│   - Improvement/Decline flags│
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Report Generation          │
│   - Markdown template        │
│   - PDF (professional)       │
│   - JSON snapshot (immutable)│
└──────────────┬───────────────┘
               │
               ▼
   [Dashboard + API + Storage]
   - Current week view
   - Historical explorer
   - Trend charts
   - REST API for future consumers
```

---

## Layer Responsibilities (Detailed)

### 1. Data Collection Layer (`backend/app/services/data_collection/`)

- **XCollector**: Uses X keyword/semantic search (or Apify Twitter actor for scale + historical)
- **RedditCollector**: PRAW or Apify Reddit actor
- **WebCollector**: Official broker blogs, press releases, status pages via search + httpx
- **YouTubeCollector**: Video titles + top comments for major broker channels
- **ApifyOrchestrator**: Fallback / heavy lifting for platforms without good APIs

Responsibilities:
- Respect rate limits & ToS
- Normalize to common `RawMention` schema
- Filter to 7-day window (configurable)
- Persist raw data for auditability (optional, privacy-aware)

### 2. Analysis & Scoring Engine (`analysis/` + `scoring/`)

- Sentiment per mention (positive / negative / neutral + confidence)
- Topic extraction & clustering (simple keyword + optional MiroFish-Offline for high-quality offline clusters)
- Signal categorization:
  - App performance (crash, slow, order issues)
  - Support quality
  - Pricing / charges complaints
  - New feature reactions
  - General brand sentiment

**Scoring Parameters (example weights — tunable):**
- Engagement (volume + reach of conversations)
- Sentiment Balance (pos vs neg ratio + intensity)
- Feature Response (how broker reacts to feedback)
- Responsiveness (support mentions, outage handling)
- Content Quality (educational posts, transparency)
- Platform Stability (technical issues volume)

Final score = weighted sum, clamped 0–10.

### 3. Feature Tracking Module (`feature_tracking/`)

- Detects "new feature" language in official + user posts
- Matches against known previous features
- Aggregates user sentiment specifically around each new launch
- Stores feature timeline per broker

### 4. Report Generation (`report_generation/`)

- Jinja2 or simple string templates for Markdown
- ReportLab canvas or HTML→PDF for polished weekly PDF
- Always generates:
  - `BrokerWeeklyIntel_YYYY-WW.md`
  - `BrokerWeeklyIntel_YYYY-WW.pdf`
  - `snapshot_YYYY-WW.json` (complete machine-readable data)

### 5. Dashboard (Next.js Frontend)

- `/` — Current week executive summary + top positives/negatives
- `/reports` — Historical week selector + full report viewer
- `/trends` — Line charts per broker + parameter radar
- Broker detail pages
- "Deep Analysis" button (future: triggers MiroFish job)

### 6. Automation & Storage

- `schedulers/weekly_runner.py` — Orchestrates full pipeline
- GitHub Action `.github/workflows/weekly-intel.yml` — Runs every Sunday
- SQLite (dev) / Postgres (prod) for structured data
- File-based `data/historical/*.json` for cheap, git-friendly, auditable snapshots

---

## Technology Decisions & Rationale

- **Next.js 15 App Router** — Best DX + performance for internal dashboard in 2025/26
- **FastAPI** — Async, great OpenAPI docs, Python ecosystem
- **Apify first** — Most reliable way to get clean structured data from X/Reddit at scale without fighting APIs
- **MiroFish-Offline hook** — When you need serious topic modeling without sending data to OpenAI
- **ReportLab** — Reliable PDF generation without heavy browser dependencies
- **File + SQLite hybrid** — Simple, no cloud bill for historical data, easy to backup

---

## Extension Points

- Add new broker → just add name to `BROKERS` env + update search queries
- Add new data source → implement `BaseCollector` interface
- Change scoring model → edit `scoring/engine.py` (weights live in config)
- Swap PDF engine → replace only the `pdf.py` renderer

---

## Security & Privacy Notes

- Never store full user profiles or DM content
- All collected data is public conversation only
- Credentials live only in environment / secret manager
- Historical snapshots can be anonymized or redacted if needed

---

**Status**: This architecture is the target. Scaffolding matches the layer structure exactly. Implementation will follow layer-by-layer.

Next: Choose the first module to implement.
