from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from .models import MetricEvidence


_MISSING = {"", "-", "--", "n/a", "na", "null", "none", "未公开", "未知"}
_NUMBER = re.compile(r"^(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[万千kKwW]?)\s*(?P<plus>\+)?$")


def _to_integer(value: str, unit: str) -> int:
    multiplier = 1
    if unit in {"万", "w", "W"}:
        multiplier = 10_000
    elif unit in {"千", "k", "K"}:
        multiplier = 1_000
    return int(float(value) * multiplier)


def parse_metric(
    raw: Any,
    *,
    source_url: str | None = None,
    observed_at: datetime | None = None,
    evidence_tier: str = "unknown",
) -> MetricEvidence:
    """Parse an exact value or visible band without inventing precision."""

    if raw is None:
        return MetricEvidence(source_url=source_url, observed_at=observed_at, evidence_tier=evidence_tier)

    if isinstance(raw, bool):
        return MetricEvidence(raw=str(raw), source_url=source_url, observed_at=observed_at, evidence_tier=evidence_tier)

    if isinstance(raw, int) and raw >= 0:
        return MetricEvidence(
            raw=str(raw),
            lower_bound=raw,
            upper_bound=raw,
            exact=True,
            source_url=source_url,
            observed_at=observed_at,
            evidence_tier=evidence_tier,
        )

    text = str(raw).strip().replace(",", "").replace("，", "")
    if text.lower() in _MISSING:
        return MetricEvidence(source_url=source_url, observed_at=observed_at, evidence_tier=evidence_tier)

    match = _NUMBER.fullmatch(text)
    if not match:
        return MetricEvidence(raw=text, source_url=source_url, observed_at=observed_at, evidence_tier=evidence_tier)

    if "." in match.group("value") and not match.group("unit"):
        return MetricEvidence(raw=text, source_url=source_url, observed_at=observed_at, evidence_tier=evidence_tier)

    lower = _to_integer(match.group("value"), match.group("unit"))
    plus = bool(match.group("plus"))
    return MetricEvidence(
        raw=text,
        lower_bound=lower,
        upper_bound=None if plus else lower,
        exact=not plus,
        source_url=source_url,
        observed_at=observed_at,
        evidence_tier=evidence_tier,
    )


def metric_from_payload(payload: Any, fallback_source_url: str | None = None) -> MetricEvidence:
    if not isinstance(payload, dict):
        return parse_metric(payload, source_url=fallback_source_url)

    observed_at = payload.get("observed_at")
    parsed_observed_at = None
    if observed_at:
        try:
            parsed_observed_at = datetime.fromisoformat(str(observed_at).replace("Z", "+00:00"))
            if parsed_observed_at.tzinfo is None:
                parsed_observed_at = None
        except ValueError:
            parsed_observed_at = None

    return parse_metric(
        payload.get("raw"),
        source_url=payload.get("source_url") or fallback_source_url,
        observed_at=parsed_observed_at,
        evidence_tier=str(payload.get("evidence_tier") or "unknown"),
    )
