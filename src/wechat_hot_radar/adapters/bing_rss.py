from __future__ import annotations

import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from ..models import Article, SourceHealth
from .base import AdapterResult, fetch_bytes


_META = re.compile(
    r'<meta\s+(?:property|name)=["\'](?P<name>[^"\']+)["\']\s+content=["\'](?P<content>.*?)["\']',
    re.IGNORECASE,
)
_CT = re.compile(r'(?:var\s+ct|["\']create_time["\']\s*:?)\s*=*\s*["\'](?P<value>\d{10})["\']')
_NICKNAME = re.compile(r'var\s+nickname\s*=\s*htmlDecode\(["\'](?P<value>.*?)["\']\)')


def _wechat_url(value: str) -> str | None:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or parsed.hostname != "mp.weixin.qq.com":
        return None
    if not parsed.path.startswith("/s"):
        return None
    return value


def _extract_verified_article(url: str, source_id: str) -> Article:
    body = fetch_bytes(url, timeout=12.0, attempts=2).decode("utf-8", errors="replace")
    return article_from_html(body, url, source_id)


def article_from_html(body: str, url: str, source_id: str) -> Article:
    """提取页面声明的文章身份；不核验或推测互动指标。"""
    metadata = {match.group("name").lower(): html.unescape(match.group("content")) for match in _META.finditer(body)}
    title = metadata.get("og:title") or metadata.get("twitter:title")
    account = metadata.get("og:site_name") or metadata.get("author")
    ct_match = _CT.search(body)
    if not account:
        nick_match = _NICKNAME.search(body)
        account = html.unescape(nick_match.group("value")) if nick_match else None
    if not title or not account or not ct_match:
        raise ValueError("article metadata could not be verified")
    published_at = datetime.fromtimestamp(int(ct_match.group("value")), tz=timezone.utc)
    return Article(
        title=title.strip(),
        account=account.strip(),
        url=url,
        published_at=published_at,
        discovered_by=(source_id,),
        summary=metadata.get("og:description", "").strip(),
    )


class BingRssWechatAdapter:
    """Discover public WeChat URLs, then verify metadata on the article page.

    Search results are never treated as engagement evidence.
    """

    endpoint = "https://www.bing.com/search"

    def __init__(self, source_id: str, queries: list[str], target_date: str, max_per_query: int = 20):
        self.source_id = source_id
        self.queries = queries
        self.target_date = target_date
        self.max_per_query = max(1, min(max_per_query, 50))

    def _discover(self, query: str) -> list[str]:
        search = f'site:mp.weixin.qq.com/s "{query}" {self.target_date}'
        url = f"{self.endpoint}?{urllib.parse.urlencode({'q': search, 'format': 'rss', 'count': self.max_per_query})}"
        root = ET.fromstring(fetch_bytes(url, timeout=15.0, attempts=2))
        links: list[str] = []
        for item in root.findall(".//item"):
            link = item.findtext("link") or ""
            verified_url = _wechat_url(link.strip())
            if verified_url:
                links.append(verified_url)
        return links

    def collect(self) -> AdapterResult:
        warnings: list[str] = []
        urls: set[str] = set()
        with ThreadPoolExecutor(max_workers=min(8, max(1, len(self.queries)))) as executor:
            query_futures = {executor.submit(self._discover, query): query for query in self.queries}
            for future in as_completed(query_futures):
                try:
                    urls.update(future.result())
                except Exception as exc:
                    query = query_futures[future]
                    warnings.append(f"query {query!r} failed: {type(exc).__name__}: {exc}")

        articles: list[Article] = []
        rejected = 0
        with ThreadPoolExecutor(max_workers=min(8, max(1, len(urls)))) as executor:
            futures = {executor.submit(_extract_verified_article, url, self.source_id): url for url in urls}
            for future in as_completed(futures):
                try:
                    articles.append(future.result())
                except Exception as exc:
                    rejected += 1
                    warnings.append(f"{futures[future]} rejected: {type(exc).__name__}: {exc}")

        if articles:
            status = "ok" if not warnings else "degraded"
        else:
            status = "empty" if not warnings else "failed"
        return AdapterResult(
            articles=articles,
            health=SourceHealth(
                source_id=self.source_id,
                status=status,
                fetched=len(urls),
                accepted=len(articles),
                rejected=rejected,
                message="discovery only; no engagement metric is inferred",
            ),
            warnings=warnings,
        )
