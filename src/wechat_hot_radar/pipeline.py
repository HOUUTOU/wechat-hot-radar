from __future__ import annotations

import json
import urllib.parse
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .adapters import BingRssWechatAdapter, JsonDirectoryAdapter, JsonUrlAdapter, RssWechatAdapter
from .classify import classify
from .models import Article, CollectionResult, MetricEvidence, SourceHealth


_TIER_PRIORITY = {
    "official_backend": 50,
    "official_public": 40,
    "audited_public_provider": 30,
    "community": 20,
    "unknown": 0,
}
_TRACKING_PARAMS = {"scene", "clicktime", "enterid", "from", "isappinstalled", "sessionid", "subscene"}


def canonical_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url.strip())
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    kept = sorted((key, value) for key, value in query if key.lower() not in _TRACKING_PARAMS)
    return urllib.parse.urlunparse(("https", parsed.netloc.lower(), parsed.path, "", urllib.parse.urlencode(kept), ""))


def _metric_priority(metric: MetricEvidence) -> tuple[int, float]:
    observed = metric.observed_at.timestamp() if metric.observed_at else -1.0
    return _TIER_PRIORITY.get(metric.evidence_tier, 0), observed


def _choose_metric(left: MetricEvidence, right: MetricEvidence) -> MetricEvidence:
    return right if _metric_priority(right) > _metric_priority(left) else left


def _merge(left: Article, right: Article) -> Article:
    return replace(
        left,
        discovered_by=tuple(sorted(set(left.discovered_by + right.discovered_by))),
        share=_choose_metric(left.share, right.share),
        like=_choose_metric(left.like, right.like),
        summary=left.summary or right.summary,
    )


def _valid_wechat_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.hostname == "mp.weixin.qq.com" and parsed.path.startswith("/s")


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported config schema_version")
    if not isinstance(payload.get("sources"), list):
        raise ValueError("config.sources must be a list")
    return payload


def run_pipeline(config_path: Path, target_date: date, timezone_name: str) -> CollectionResult:
    config = load_config(config_path)
    timezone = ZoneInfo(timezone_name)
    collected: list[Article] = []
    health: list[SourceHealth] = []
    warnings: list[str] = []

    for source in config["sources"]:
        if not source.get("enabled", True):
            continue
        source_id = str(source.get("id") or "unnamed")
        source_type = source.get("type")
        try:
            if source_type == "json_directory":
                location = (config_path.parent.parent / str(source["path"])).resolve()
                adapter = JsonDirectoryAdapter(source_id, location)
            elif source_type == "json_url":
                adapter = JsonUrlAdapter(source_id, str(source["url"]))
            elif source_type == "rss_wechat":
                adapter = RssWechatAdapter(source_id, [str(value) for value in source.get("urls", [])])
            elif source_type == "bing_rss_wechat":
                adapter = BingRssWechatAdapter(
                    source_id,
                    [str(value) for value in source.get("queries", [])],
                    target_date.isoformat(),
                    int(source.get("max_per_query", 20)),
                )
            else:
                health.append(SourceHealth(source_id, "failed", message=f"unsupported source type: {source_type}"))
                continue
            result = adapter.collect()
            collected.extend(result.articles)
            health.append(result.health)
            warnings.extend(result.warnings)
        except Exception as exc:
            health.append(SourceHealth(source_id, "failed", message=f"{type(exc).__name__}: {exc}"))

    rules = config.get("classification", {})
    deduplicated: dict[str, Article] = {}
    for article in collected:
        if not article.title or not article.account or not _valid_wechat_url(article.url):
            warnings.append(f"invalid article identity rejected: {article.url}")
            continue
        local_date = article.published_at.astimezone(timezone).date()
        if local_date != target_date:
            continue
        if article.share.raw and not article.share.verified:
            warnings.append(f"unverified share metric ignored: {article.url}")
        if article.like.raw and not article.like.verified:
            warnings.append(f"unverified like metric ignored: {article.url}")
        categorized = replace(
            article,
            url=canonical_url(article.url),
            category=classify(article.title, article.summary, article.account, rules),
        )
        key = categorized.url
        deduplicated[key] = _merge(deduplicated[key], categorized) if key in deduplicated else categorized

    return CollectionResult(list(deduplicated.values()), health, warnings)
