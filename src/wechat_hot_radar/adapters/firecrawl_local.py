"""可选本机采集器：标准库、无云端/API Key/LLM 回退，只发现文章。"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import http.client
import json
import re
import time
from urllib.parse import urlsplit

from ..models import SourceHealth
from .base import AdapterResult
from .bing_rss import article_from_html


MAX_URLS = 20
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
REQUEST_TIMEOUT = 20
RUN_BUDGET_SECONDS = 120
_BLOCKED = re.compile(
    r'id\s*=\s*["\'](?:js_verify|verify_container)["\']'
    r'|<title[^>]*>\s*(?:环境异常|安全验证|访问验证|验证码|Access Denied)',
    re.IGNORECASE,
)


def _article_url(url: str) -> str:
    if not isinstance(url, str) or any(ord(ch) < 33 for ch in url):
        raise ValueError("invalid article URL")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "mp.weixin.qq.com"
            or parsed.username is not None or parsed.password is not None
            or parsed.port is not None or parsed.fragment
            or not (parsed.path == "/s" or parsed.path.startswith("/s/"))):
        raise ValueError("only direct HTTPS WeChat article URLs are accepted")
    return url


class FirecrawlLocalAdapter:
    def __init__(self, source_id: str, urls: list[str], *, endpoint: str = "http://127.0.0.1:3002"):
        # 使用 IP 字面量，避免代理环境变量、DNS 和隐式云端地址。
        if not isinstance(endpoint, str):
            raise ValueError("endpoint must be a local URL")
        parsed = urlsplit(endpoint)
        if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1"}
                or parsed.username is not None or parsed.password is not None
                or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
            raise ValueError("only loopback self-hosted Firecrawl is allowed; cloud is disabled")
        self.host = parsed.hostname
        self.port = parsed.port or 3002
        if not isinstance(urls, list) or len(urls) > MAX_URLS:
            raise ValueError(f"urls must be a list with at most {MAX_URLS} entries")
        self.urls = list(dict.fromkeys(_article_url(url) for url in urls))
        self.source_id = source_id

    def _scrape(self, url: str, timeout: float) -> dict:
        request = {
            "url": url,
            "formats": ["rawHtml"],
            "maxAge": 0,
            "storeInCache": False,
            "timeout": max(1, int(timeout * 1000) - 1000),
        }
        deadline = time.monotonic() + timeout
        connection = http.client.HTTPConnection(self.host, self.port, timeout=timeout)
        try:
            connection.request("POST", "/v2/scrape", json.dumps(request).encode("utf-8"),
                               {"Content-Type": "application/json", "Accept": "application/json"})
            response = connection.getresponse()
            # HTTPConnection 不跟随重定向；不重试、不切换云端。
            if response.status != 200:
                raise ValueError(f"local Firecrawl HTTP status {response.status}")
            chunks = []
            size = 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("local Firecrawl request deadline exceeded")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(min(65536, MAX_RESPONSE_BYTES + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > MAX_RESPONSE_BYTES:
                    raise ValueError("local Firecrawl response exceeds 2 MiB")
            payload = json.loads(b"".join(chunks))
            if not isinstance(payload, dict):
                raise ValueError("local Firecrawl returned a non-object response")
            return payload
        finally:
            connection.close()

    def collect(self) -> AdapterResult:
        articles = []
        warnings = []
        attempted = 0
        started = time.monotonic()
        for url in self.urls:
            remaining = RUN_BUDGET_SECONDS - (time.monotonic() - started)
            if remaining <= 1:
                warnings.append("run budget exhausted; remaining URLs skipped")
                break
            attempted += 1
            try:
                payload = self._scrape(url, min(REQUEST_TIMEOUT, remaining))
                if payload.get("success") is not True or not isinstance(payload.get("data"), dict):
                    raise ValueError("local Firecrawl did not return successful page data")
                data = payload["data"]
                metadata = data.get("metadata")
                if (not isinstance(metadata, dict) or type(metadata.get("statusCode")) is not int
                        or metadata["statusCode"] != 200 or metadata.get("error")):
                    raise ValueError("target page status is not a clean HTTP 200")
                if metadata.get("sourceURL") != url:
                    raise ValueError("page sourceURL does not match requested article")
                for field in ("url", "finalURL"):
                    if metadata.get(field) and metadata[field] != url:
                        raise ValueError("page redirected away from requested article")
                body = data.get("rawHtml")
                if not isinstance(body, str) or not body.strip() or _BLOCKED.search(body):
                    raise ValueError("raw article HTML absent or known challenge page detected")
                article = article_from_html(body, url, self.source_id)
                article = replace(article, page_evidence={
                    "source_url": url,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "raw_html_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                    "collector": "firecrawl_local",
                    "max_age_ms": 0,
                    "source_updated_at": None,
                    "note": "page metadata only; no engagement evidence; hash is not an authenticity proof",
                })
                articles.append(article)
            except Exception as exc:
                # 避免响应正文、凭据或上游错误信息进入公开报告。
                warnings.append(f"article request {attempted} rejected: {type(exc).__name__}")
                if isinstance(exc, (ConnectionError, OSError, http.client.HTTPException)):
                    warnings.append("local transport unavailable; circuit opened for this run")
                    break
        rejected = attempted - len(articles)
        skipped = len(self.urls) - attempted
        status = ("degraded" if warnings else "ok") if articles else ("failed" if warnings else "empty")
        return AdapterResult(articles, SourceHealth(
            self.source_id, status, fetched=attempted, accepted=len(articles), rejected=rejected,
            message=f"discovery only; skipped={skipped}; no share/like metric inferred",
        ), warnings)
