from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit


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
    # 仅由经过审查的来源核验器设置；JSON 输入不得赋值。
    source_verified: bool = False

    @property
    def evidence_present(self) -> bool:
        if not isinstance(self.source_url, str):
            return False
        try:
            source = urlsplit(self.source_url)
            valid_source = (source.scheme in {"http", "https"} and bool(source.hostname)
                            and source.username is None and source.password is None)
        except ValueError:
            return False
        return (
            self.lower_bound is not None
            and bool(self.raw)
            and valid_source
            and self.observed_at is not None
            and self.observed_at.tzinfo is not None
        )

    @property
    def verified(self) -> bool:
        """字段齐全仅表示有待核验证据，不代表来源或指标真实。"""
        return self.evidence_present and self.source_verified

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["observed_at"] = self.observed_at.isoformat() if self.observed_at else None
        value["verified"] = self.verified
        value["evidence_present"] = self.evidence_present
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
    page_evidence: dict[str, Any] = field(default_factory=dict)

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
            "page_evidence": self.page_evidence,
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
