from __future__ import annotations

import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models import SourceHealth
from .base import AdapterResult, fetch_bytes
from .bing_rss import _extract_verified_article, _wechat_url


def _feed_links(body: bytes) -> list[str]:
    root = ET.fromstring(body)
    links: list[str] = []
    for item in root.findall(".//item"):
        value = (item.findtext("link") or "").strip()
        if verified := _wechat_url(value):
            links.append(verified)
    for entry in root.findall(".//{*}entry"):
        for link in entry.findall("{*}link"):
            value = (link.get("href") or "").strip()
            if verified := _wechat_url(value):
                links.append(verified)
                break
    return list(dict.fromkeys(links))


class RssWechatAdapter:
    def __init__(self, source_id: str, urls: list[str]):
        self.source_id = source_id
        self.urls = urls

    def collect(self) -> AdapterResult:
        warnings: list[str] = []
        discovered: set[str] = set()
        for url in self.urls:
            if not url.startswith("https://"):
                warnings.append(f"non-HTTPS feed rejected: {url}")
                continue
            try:
                discovered.update(_feed_links(fetch_bytes(url)))
            except Exception as exc:
                warnings.append(f"feed failed {url}: {type(exc).__name__}: {exc}")

        articles = []
        rejected = 0
        with ThreadPoolExecutor(max_workers=min(8, max(1, len(discovered)))) as executor:
            futures = {executor.submit(_extract_verified_article, url, self.source_id): url for url in discovered}
            for future in as_completed(futures):
                try:
                    articles.append(future.result())
                except Exception as exc:
                    rejected += 1
                    warnings.append(f"{futures[future]} rejected: {type(exc).__name__}: {exc}")
        status = "ok" if articles and not warnings else "degraded" if articles else "empty" if not warnings else "failed"
        return AdapterResult(
            articles,
            SourceHealth(
                self.source_id,
                status,
                fetched=len(discovered),
                accepted=len(articles),
                rejected=rejected,
                message="RSS discovery only; article metadata verified at original URL",
            ),
            warnings,
        )
