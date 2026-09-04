from __future__ import annotations

import json

from ..models import SourceHealth
from .base import AdapterResult, fetch_bytes
from .json_directory import article_from_payload


class JsonUrlAdapter:
    """Read the public source contract from an HTTPS URL."""

    def __init__(self, source_id: str, url: str):
        self.source_id = source_id
        self.url = url

    def collect(self) -> AdapterResult:
        if not self.url.startswith("https://"):
            return AdapterResult([], SourceHealth(self.source_id, "failed", message="JSON URL must use HTTPS"), [])
        warnings: list[str] = []
        rejected = 0
        try:
            payload = json.loads(fetch_bytes(self.url).decode("utf-8"))
            records = payload if isinstance(payload, list) else payload.get("articles", [])
            if not isinstance(records, list):
                raise ValueError("root must be a list or contain an articles list")
        except Exception as exc:
            return AdapterResult(
                [],
                SourceHealth(self.source_id, "failed", message=f"{type(exc).__name__}: {exc}"),
                [],
            )

        articles = []
        for index, record in enumerate(records):
            try:
                if not isinstance(record, dict):
                    raise ValueError("article record must be an object")
                articles.append(article_from_payload(record, self.source_id))
            except (KeyError, TypeError, ValueError) as exc:
                rejected += 1
                warnings.append(f"record[{index}] rejected: {exc}")
        return AdapterResult(
            articles,
            SourceHealth(
                self.source_id,
                "ok" if articles else "empty",
                fetched=len(records),
                accepted=len(articles),
                rejected=rejected,
                message=self.url,
            ),
            warnings,
        )
