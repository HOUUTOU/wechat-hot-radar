from __future__ import annotations

import time
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from ..models import Article, SourceHealth


USER_AGENT = "wechat-hot-radar/0.1 (+https://github.com/HOUUTOU/wechat-hot-radar)"


@dataclass
class AdapterResult:
    articles: list[Article]
    health: SourceHealth
    warnings: list[str]


class SourceAdapter(Protocol):
    def collect(self) -> AdapterResult: ...


def fetch_bytes(url: str, *, timeout: float = 15.0, attempts: int = 2) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:  # network errors vary by runner
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(0.5 * (attempt + 1))
    assert last_error is not None
    raise last_error
