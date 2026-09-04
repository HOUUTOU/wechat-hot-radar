from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..metrics import metric_from_payload
from ..models import Article, SourceHealth
from .base import AdapterResult


def parse_datetime(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("datetime must include a timezone offset")
    return parsed


class JsonDirectoryAdapter:
    """Read auditable article records submitted as JSON files."""

    def __init__(self, source_id: str, directory: Path):
        self.source_id = source_id
        self.directory = directory

    def collect(self) -> AdapterResult:
        articles: list[Article] = []
        warnings: list[str] = []
        rejected = 0
        files = sorted(self.directory.glob("*.json")) if self.directory.exists() else []
        for path in files:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                records = payload if isinstance(payload, list) else payload.get("articles", [])
                if not isinstance(records, list):
                    raise ValueError("root must be a list or contain an articles list")
                for index, record in enumerate(records):
                    try:
                        if not isinstance(record, dict):
                            raise ValueError("article record must be an object")
                        articles.append(article_from_payload(record, self.source_id))
                    except (KeyError, TypeError, ValueError) as exc:
                        rejected += 1
                        warnings.append(f"{path.name}[{index}] rejected: {exc}")
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                rejected += 1
                warnings.append(f"{path.name} rejected: {exc}")

        status = "ok" if articles else "empty"
        return AdapterResult(
            articles=articles,
            health=SourceHealth(
                source_id=self.source_id,
                status=status,
                fetched=len(articles) + rejected,
                accepted=len(articles),
                rejected=rejected,
                message=f"read {len(files)} JSON file(s)",
            ),
            warnings=warnings,
        )


def article_from_payload(payload: dict[str, Any], source_id: str) -> Article:
    url = str(payload["url"]).strip()
    discovered = payload.get("discovered_by") or [source_id]
    return Article(
        title=str(payload["title"]).strip(),
        account=str(payload["account"]).strip(),
        url=url,
        published_at=parse_datetime(payload["published_at"]),
        discovered_by=tuple(str(item) for item in discovered),
        share=metric_from_payload(payload.get("share")),
        like=metric_from_payload(payload.get("like")),
        category=str(payload.get("category") or "其他"),
        summary=str(payload.get("summary") or ""),
    )
