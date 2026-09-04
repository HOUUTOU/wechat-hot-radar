from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class MetricEvidence:
    """A metric and the evidence needed to audit it."""

    raw: str | None = None
    lower_bound: int | None = None
    upper_bound: int | None = None
    exact: bool = False
    source_url: str | None = None
    observed_at: datetime | None = None
    evidence_tier: str = "unknown"

    @property
    def verified(self) -> bool:
        return (
            self.lower_bound is not None
            and bool(self.raw)
            and bool(self.source_url)
            and self.source_url.startswith(("https://", "http://"))
            and self.observed_at is not None
            and self.observed_at.tzinfo is not None
        )

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["observed_at"] = self.observed_at.isoformat() if self.observed_at else None
        value["verified"] = self.verified
        return value


@dataclass(frozen=True)
class Article:
    title: str
    account: str
    url: str
    published_at: datetime
    discovered_by: tuple[str, ...]
    share: MetricEvidence = field(default_factory=MetricEvidence)
    like: MetricEvidence = field(default_factory=MetricEvidence)
    category: str = "其他"
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "account": self.account,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "discovered_by": list(self.discovered_by),
            "share": self.share.to_dict(),
            "like": self.like.to_dict(),
            "category": self.category,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class SourceHealth:
    source_id: str
    status: str
    fetched: int = 0
    accepted: int = 0
    rejected: int = 0
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CollectionResult:
    articles: list[Article]
    health: list[SourceHealth]
    warnings: list[str]
