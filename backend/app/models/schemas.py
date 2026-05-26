"""
BrokerWeeklyIntel - Core Pydantic Data Models
These define the canonical shapes used across the entire system.
"""

from datetime import datetime
from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field


BrokerName = Literal[
    "Zerodha", "Groww", "Angel One", "Upstox", "Fyers",
    "ICICI Direct", "5Paisa", "Kotak Securities", "HDFC Sky", "Sharekhan"
]

SentimentLabel = Literal["positive", "negative", "neutral"]


class RawMention(BaseModel):
    """Normalized raw conversation item from any source."""
    id: str
    platform: Literal["x", "reddit", "youtube", "web", "linkedin", "forum"]
    broker: BrokerName
    text: str
    url: str
    author: Optional[str] = None
    published_at: datetime
    engagement: int = 0          # likes, upvotes, views, etc.
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class SentimentTopic(BaseModel):
    """A discovered topic with sentiment and evidence links."""
    topic_id: str
    title: str
    sentiment: SentimentLabel
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    volume: int
    key_phrases: List[str] = Field(default_factory=list)
    example_urls: List[str] = Field(default_factory=list)   # Direct links to posts
    broker: BrokerName


class FeatureMention(BaseModel):
    """Detection of a new or discussed product feature."""
    feature_name: str
    broker: BrokerName
    description: str
    first_seen: datetime
    sentiment: SentimentLabel
    reaction_volume: int
    example_posts: List[str]
    is_official_launch: bool = False


class RatingBreakdown(BaseModel):
    """Transparent scoring parameters (all 0-10)."""
    engagement: float
    sentiment_balance: float
    feature_response: float
    responsiveness: float
    content_quality: float
    platform_stability: float

    # Optional: weights used for this week
    weights: Dict[str, float] = Field(default_factory=dict)


class WeeklyBrokerReport(BaseModel):
    """Complete report for one broker in one week."""
    broker: BrokerName
    week_start: datetime
    week_end: datetime
    total_mentions: int
    positive_mentions: int
    negative_mentions: int
    overall_sentiment: float  # -1 to +1

    trending_positive: List[SentimentTopic]
    trending_negative: List[SentimentTopic]
    new_features: List[FeatureMention]

    rating_breakdown: RatingBreakdown
    final_score: float = Field(ge=0.0, le=10.0)

    key_insights: List[str]
    comparison_vs_previous: Optional[Dict[str, Any]] = None   # Δ from last 1-4 weeks


class WeeklyReport(BaseModel):
    """The full weekly intelligence deliverable."""
    week_label: str                    # e.g. "2025-W21"
    generated_at: datetime
    brokers: List[WeeklyBrokerReport]

    executive_summary: str
    top_positive_themes: List[str]
    top_negative_themes: List[str]

    metadata: Dict[str, Any] = Field(default_factory=dict)   # sources used, versions, etc.


class HistoricalTrend(BaseModel):
    """Time-series data for charts."""
    broker: BrokerName
    weeks: List[str]
    scores: List[float]
    sentiment_trend: List[float]
    mention_volume: List[int]
