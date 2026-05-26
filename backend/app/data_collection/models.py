"""
BrokerWeeklyIntel - Data Collection Layer Models (v2.1 aligned)

These Pydantic models define the internal shapes used by the Data Collection Layer.
They are designed to feed directly into analysis, scoring, and the rich v2.1 report/JSON output.
"""

from datetime import datetime
from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid


# =============================================================================
# Type Aliases
# =============================================================================

BrokerName = Literal[
    "Zerodha", "Groww", "Angel One", "Upstox", "Fyers",
    "ICICI Direct", "5Paisa", "Kotak Securities", "HDFC Sky", "Sharekhan"
]

Platform = Literal["x", "reddit", "youtube", "web", "instagram", "forum", "blog", "play_store"]

SentimentLabel = Literal["positive", "negative", "neutral", "mixed"]

TechnicalIssueType = Literal["feature_specific", "platform_wide"]

Severity = Literal["critical", "high", "medium", "low"]


# =============================================================================
# Raw & Intermediate Models
# =============================================================================

class RawSearchResult(BaseModel):
    """Unprocessed result returned by any connector (search, scrape, API, etc.)."""
    source: str                          # e.g. "web_search", "x_keyword", "zconnect_comments"
    query: str
    broker: Optional[BrokerName] = None
    platform: Platform
    raw_data: Dict[str, Any]             # Original payload from the tool
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RawMention(BaseModel):
    """Lightly cleaned item before full normalization."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: Platform
    broker: BrokerName
    text: str
    url: str
    author: Optional[str] = None
    published_at: datetime
    engagement: int = 0
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# v2.1 Rich Normalized Models
# =============================================================================

class KeyQuote(BaseModel):
    """High-value direct user quote for the v2.1 report and dashboard."""
    quote: str
    context: str                           # e.g. "Reaction to Fyers 22 May Bar Replay update"
    sentiment: SentimentLabel
    source_url: str
    author: Optional[str] = None
    platform: Platform
    broker: BrokerName


class NegativeTheme(BaseModel):
    """Categorized negative feedback (v2.1 requirement)."""
    theme: Literal[
        "Performance", "Support", "Charges", "Reliability", "UX", 
        "Features/Gaps", "Transparency", "Other"
    ]
    count: int = 0
    example_quotes: List[str] = Field(default_factory=list)
    severity: Severity = "medium"


class TechnicalIssue(BaseModel):
    """Tracked technical problem (improved v2.1 tracking)."""
    description: str
    severity: Severity
    issue_type: TechnicalIssueType          # feature_specific vs platform_wide
    volume: int = 1
    first_seen: datetime
    last_seen: datetime
    affected_brokers: List[BrokerName] = Field(default_factory=list)
    evidence_urls: List[str] = Field(default_factory=list)
    broker_response: Optional[str] = None   # e.g. "Acknowledged in Z-Connect post"


class BrokerFeatureUpdate(BaseModel):
    """Detected new feature or meaningful product update (v2.1 table ready)."""
    feature_name: str
    broker: BrokerName
    approx_launch_date: datetime
    description: str
    user_reaction: Literal["Positive", "Mixed", "Negative", "Too early to tell"]
    discussion_volume: Literal["High", "Medium", "Low"] = "Medium"
    evidence_links: List[str] = Field(default_factory=list)
    key_quotes: List[KeyQuote] = Field(default_factory=list)


class NormalizedMention(BaseModel):
    """
    Clean, canonical mention used throughout the system.
    This is the primary output of the Data Collection Layer.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    broker: BrokerName
    platform: Platform
    text: str
    url: str
    author: Optional[str] = None
    published_at: datetime
    engagement: int = 0

    # Derived / enriched fields
    sentiment: Optional[SentimentLabel] = None
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    topics: List[str] = Field(default_factory=list)

    # v2.1 classification tags
    tags: List[Literal["feature_launch", "glitch", "support", "positive", "negative", "comparison"]] = Field(default_factory=list)
    negative_theme: Optional[Literal["Performance", "Support", "Charges", "Reliability", "UX", "Features/Gaps", "Other"]] = None
    technical_issue_type: Optional[TechnicalIssueType] = None

    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("engagement")
    @classmethod
    def engagement_non_negative(cls, v: int) -> int:
        return max(0, v)


# =============================================================================
# Collection Run Metadata
# =============================================================================

class CollectionRun(BaseModel):
    """Metadata about a single data collection execution."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    week_start: datetime
    week_end: datetime
    brokers: List[BrokerName]
    sources_used: List[str]
    total_raw_results: int = 0
    total_normalized_mentions: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)
    notes: str = ""


# =============================================================================
# Aggregated v2.1 Output (ready for report generation & JSON snapshot)
# =============================================================================

class BrokerCollectionResult(BaseModel):
    """Per-broker output from the collection phase (feeds v2.1 report sections)."""
    broker: BrokerName
    mentions: List[NormalizedMention]
    new_features: List[BrokerFeatureUpdate] = Field(default_factory=list)
    technical_issues: List[TechnicalIssue] = Field(default_factory=list)
    key_quotes: List[KeyQuote] = Field(default_factory=list)
    negative_themes: Dict[str, int] = Field(default_factory=dict)   # theme -> count
    feature_specific_issues: int = 0
    platform_wide_issues: int = 0

    @property
    def total_mentions(self) -> int:
        return len(self.mentions)


class CollectionResult(BaseModel):
    """Complete result of a data collection run for one week."""
    run: CollectionRun
    broker_results: Dict[BrokerName, BrokerCollectionResult]
    raw_artifacts_path: Optional[str] = None   # Where raw JSON/responses were saved
    normalized_artifacts_path: Optional[str] = None

    def get_all_mentions(self) -> List[NormalizedMention]:
        mentions: List[NormalizedMention] = []
        for result in self.broker_results.values():
            mentions.extend(result.mentions)
        return mentions
