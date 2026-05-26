# BrokerWeeklyIntel

**Automated Weekly Competitor Intelligence System for India's Leading Stock Brokers**

Professional-grade platform that delivers deep, link-backed, actionable intelligence every Sunday on Zerodha, Groww, Angel One, Upstox, Fyers, ICICI Direct, and other major Indian brokers.

---

## Why BrokerWeeklyIntel?

Indian retail trading is hyper-competitive. The broker with the best app experience, fastest support response, clearest communication, and most loved (or least hated) features wins market share.

Most teams rely on anecdotal feedback or sporadic manual searches. **BrokerWeeklyIntel** turns this into a repeatable, objective, data-driven process.

### What You Get Every Week

- **Sentiment overview** — Positive vs negative conversation volume across platforms
- **Trending positive topics** — With direct links to the best posts/threads
- **Trending negative topics** — Bugs, outages, support horror stories, hidden charges, UI complaints — all with evidence
- **New feature tracking** — What launched this week + real user reactions (not just marketing copy)
- **Software & performance signals** — Crashes, slowness, order execution issues, API problems
- **Objective weekly rating** (0–10) for every broker with clear parameter breakdown
- **Historical trend** — Is this broker improving or declining? Evidence from last 4+ weeks
- **Beautiful PDF + Markdown reports** + interactive dashboard

---

## Supported Brokers (Default)

- Zerodha
- Groww
- Angel One
- Upstox
- Fyers
- ICICI Direct
- 5Paisa
- Kotak Securities
- HDFC Sky
- Sharekhan

Easily extensible via config.

---

## Architecture (Clean Layered Design)

```
┌─────────────────────────────────────────────────────────────┐
│                    Automation / Scheduling                   │
│   (APScheduler • GitHub Actions • Weekly Sunday 8:30 AM IST) │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                  Report Generation Layer                     │
│   Markdown Renderer  •  PDF Generator (ReportLab)  •  JSON   │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│               Analysis & Scoring Engine                      │
│   • Sentiment aggregation (multi-platform)                   │
│   • Topic clustering (MiroFish-Offline hook)                 │
│   • New feature detection + reaction scoring                 │
│   • Multi-parameter rating (Engagement, Sentiment Balance,   │
│     Feature Response, Responsiveness, Content Quality, etc.) │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                  Data Collection Layer                       │
│   X/Twitter (API + Apify) • Reddit • YouTube • Blogs         │
│   Forums • News • Discord (via search) • LinkedIn signals    │
│   Web search for official announcements                      │
└─────────────────────────────────────────────────────────────┘
                                │
                    Persistent Storage (SQLite / Postgres)
                    Historical Weekly Snapshots (JSON)
```

**Strict separation of concerns.** Every score is explainable with source evidence.

---

## Tech Stack

**Frontend (Dashboard)**
- Next.js 15 (App Router) + TypeScript
- Tailwind CSS + shadcn/ui
- Recharts / Tremor for trend visualizations
- Modern, fast, professional UI

**Backend (Analysis & API)**
- Python 3.11+ + FastAPI + Pydantic v2
- SQLAlchemy + Alembic
- APScheduler
- ReportLab + Markdown for reports

**Integrations & Data**
- Apify Actors (battle-tested scrapers)
- X/Twitter API v2
- PRAW (Reddit)
- Built-in hooks for MiroFish-Offline (https://github.com/nikmcfly/MiroFish-Offline)
- Graceful degradation when APIs are rate-limited

**DevOps**
- Docker Compose (full local stack)
- GitHub Actions (weekly automated runs + report commit)
- Structured logging

---

## Project Structure (High-Level)

```
BrokerWeeklyIntel/
├── frontend/                 # Next.js 15 dashboard
├── backend/
│   ├── app/
│   │   ├── api/v1/routers/   # FastAPI routes
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/
│   │   │   ├── data_collection/     # X, Reddit, Apify, Web collectors
│   │   │   ├── analysis/            # Sentiment, clustering
│   │   │   ├── scoring/             # Rating engine
│   │   │   ├── feature_tracking/    # New feature detection
│   │   │   └── report_generation/   # MD + PDF
│   │   ├── schedulers/              # Weekly runner
│   │   └── core/                    # Config, DB
│   └── data/                 # SQLite dev DB
├── data/historical/          # Weekly JSON snapshots (versioned)
├── reports/                  # Generated .md + .pdf outputs
├── .github/workflows/        # Automated weekly analysis
├── scripts/                  # Helper scripts
└── docs/
```

---

## Current Status

**Scaffolding Complete** ✅

- Full professional folder structure with clean architecture
- Base configuration (`.env.example`, `.gitignore`, `LICENSE`, `Makefile`)
- Python package scaffolding + requirements
- This README

**Modules Remaining (build order to be decided with you)**

1. Data Collection Layer
2. Analysis & Scoring Engine + Feature Tracking
3. Report Generation (Markdown + PDF)
4. Dashboard UI (Next.js + shadcn + charts)
5. Automation & Scheduling + Storage layer
6. Polish, testing, MiroFish integration, production hardening

---

## Getting Started (After Modules Are Built)

```bash
# 1. Clone & setup
cp .env.example .env
# fill your keys

# 2. Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# alembic upgrade head

# 3. Frontend
cd ../frontend
npm install

# 4. Run everything locally (once implemented)
make dev-backend   # port 8000
make dev-frontend  # port 3000
make weekly        # run full pipeline manually
```

Full instructions will be updated as modules are completed.

---

## Roadmap Highlights

- [ ] Data collectors with robust error handling & deduplication
- [ ] Multi-signal sentiment + topic engine
- [ ] New feature detection from official + user conversations
- [ ] Explainable 0–10 scoring with parameter weights
- [ ] Historical comparison & improvement/decline detection
- [ ] Beautiful weekly PDF report (email-ready)
- [ ] Modern interactive dashboard with broker trend charts
- [ ] One-click "deep dive" using MiroFish-Offline
- [ ] Automated Sunday delivery (GitHub Action + optional email/Slack)
- [ ] Self-hosted or cloud deployment guide

---

## Philosophy & Principles

- **Evidence first** — Every claim has links or screenshots.
- **Objective scoring** — No black-box magic. Parameters are transparent.
- **Respect the platforms** — Rate limits, ToS, and robots.txt are non-negotiable.
- **Historical memory** — Trends matter more than any single week.
- **Actionable output** — Reports should drive real product & support decisions.

---

## License

MIT License — see [LICENSE](LICENSE) file.

Built with care for the Indian fintech community.

**Author / Maintainer**: Gunjan Chokshi

---

> **Next step**: Tell me which module to build first:
> - **Data Collection Layer** (recommended starting point)
> - **Scoring System & Analysis Engine**
> - **Dashboard UI (Next.js)**
> - **Automation / Scheduling + Report Generation**
>
> Or suggest a different order / priority.

Let's build something excellent. 🚀
