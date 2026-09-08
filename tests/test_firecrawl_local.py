"""仅使用模拟 Firecrawl 响应；不宣称微信或 Firecrawl 实机通过。"""
import io
import json
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from wechat_hot_radar.adapters.firecrawl_local import FirecrawlLocalAdapter, MAX_RESPONSE_BYTES
from wechat_hot_radar.pipeline import run_pipeline


URL = "https://mp.weixin.qq.com/s/synthetic-fixture"
BODY = '<meta property="og:title" content="Synthetic"><meta name="author" content="Fixture">' + "<script>var ct = '1788825600';</script>"


def response(**metadata):
    return {"success": True, "data": {"rawHtml": BODY,
            "metadata": {"statusCode": 200, "sourceURL": URL, **metadata}}}


class FirecrawlLocalTests(unittest.TestCase):
    def collect(self, payload):
        with patch.object(FirecrawlLocalAdapter, "_scrape", return_value=payload):
            return FirecrawlLocalAdapter("test", [URL]).collect()

    def test_cloud_and_non_loopback_endpoints_rejected(self):
        for endpoint in ("https://api.firecrawl.dev", "http://localhost:3002",
                         "http://127.0.0.1.evil.test:3002", "http://192.168.1.2:3002",
                         "http://user:pass@127.0.0.1:3002", "http://127.0.0.1:3002/path"):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                FirecrawlLocalAdapter("test", [], endpoint=endpoint)

    def test_non_article_targets_rejected(self):
        for url in ("http://mp.weixin.qq.com/s/x", "https://example.org/x",
                    "https://mp.weixin.qq.com/sogou", "https://user@mp.weixin.qq.com/s/x",
                    "https://mp.weixin.qq.com:443/s/x", URL + "\n", URL + "#fragment"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                FirecrawlLocalAdapter("test", [url])

    def test_url_budget_and_deduplication(self):
        with self.assertRaises(ValueError):
            FirecrawlLocalAdapter("test", [URL] * 21)
        self.assertEqual(len(FirecrawlLocalAdapter("test", [URL, URL]).urls), 1)

    def test_success_produces_discovery_only_with_hash(self):
        result = self.collect(response())
        self.assertEqual(result.health.status, "ok")
        article = result.articles[0]
        self.assertFalse(article.share.verified)
        self.assertIsNone(article.share.raw)
        self.assertIsNone(article.like.raw)
        self.assertEqual(len(article.page_evidence["raw_html_sha256"]), 64)
        self.assertIsNone(article.page_evidence["source_updated_at"])

    def test_api_success_does_not_override_page_failure(self):
        for code in (403, 404, 500, 304, None, "200", True):
            with self.subTest(code=code):
                self.assertEqual(self.collect(response(statusCode=code)).health.status, "failed")

    def test_source_mismatch_and_redirect_rejected(self):
        for fields in ({"sourceURL": None}, {"sourceURL": "https://example.org"},
                       {"finalURL": "https://example.org"}, {"error": "page failed"}):
            with self.subTest(fields=fields):
                self.assertEqual(self.collect(response(**fields)).articles, [])

    def test_challenge_rejected_even_with_article_metadata(self):
        payload = response()
        payload["data"]["rawHtml"] += '<div id="js_verify">challenge</div>'
        self.assertEqual(self.collect(payload).health.status, "failed")

    def test_missing_html_and_metadata_fail_closed(self):
        for payload in ({}, {"success": True, "data": {}}, {"success": True, "data": []}):
            with self.subTest(payload=payload):
                self.assertEqual(self.collect(payload).articles, [])

    def test_transport_failure_opens_circuit_without_leaking_error(self):
        with patch.object(FirecrawlLocalAdapter, "_scrape", side_effect=ConnectionRefusedError("SECRET")) as fetch:
            result = FirecrawlLocalAdapter("test", [URL, URL + "-2"]).collect()
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result.health.status, "failed")
        self.assertIn("skipped=1", result.health.message)
        self.assertNotIn("SECRET", str(result.warnings))

    @patch("wechat_hot_radar.adapters.firecrawl_local.http.client.HTTPConnection")
    def test_request_is_fresh_raw_html_with_no_auth_or_cloud_options(self, factory):
        reply = MagicMock(status=200)
        stream = io.BytesIO(json.dumps(response()).encode())
        reply.read1.side_effect = stream.read1
        factory.return_value.getresponse.return_value = reply
        result = FirecrawlLocalAdapter("test", [URL]).collect()
        self.assertEqual(result.health.status, "ok")
        args = factory.return_value.request.call_args.args
        self.assertEqual(args[:2], ("POST", "/v2/scrape"))
        body = json.loads(args[2])
        self.assertEqual(body["formats"], ["rawHtml"])
        self.assertEqual(body["maxAge"], 0)
        self.assertFalse(body["storeInCache"])
        self.assertNotIn("Authorization", args[3])
        factory.return_value.close.assert_called_once()

    @patch("wechat_hot_radar.adapters.firecrawl_local.http.client.HTTPConnection")
    def test_http_redirect_not_followed(self, factory):
        factory.return_value.getresponse.return_value.status = 302
        self.assertEqual(FirecrawlLocalAdapter("test", [URL]).collect().articles, [])
        factory.return_value.request.assert_called_once()

    @patch("wechat_hot_radar.adapters.firecrawl_local.http.client.HTTPConnection")
    def test_oversized_response_rejected(self, factory):
        reply = MagicMock(status=200)
        stream = io.BytesIO(b" " * (MAX_RESPONSE_BYTES + 1))
        reply.read1.side_effect = stream.read1
        factory.return_value.getresponse.return_value = reply
        self.assertEqual(FirecrawlLocalAdapter("test", [URL]).collect().health.status, "failed")

    def test_run_budget_skips_without_request(self):
        with patch("wechat_hot_radar.adapters.firecrawl_local.time.monotonic", side_effect=[0, 120]), \
                patch.object(FirecrawlLocalAdapter, "_scrape") as fetch:
            result = FirecrawlLocalAdapter("test", [URL]).collect()
        fetch.assert_not_called()
        self.assertIn("skipped=1", result.health.message)

    def test_disabled_source_never_constructs_client(self):
        with patch("wechat_hot_radar.pipeline.FirecrawlLocalAdapter") as adapter:
            result = run_pipeline(Path("config/firecrawl-local.example.json"), date(2026, 9, 8), "Asia/Shanghai")
        adapter.assert_not_called()
        self.assertEqual(result.articles, [])

    def test_bad_firecrawl_config_does_not_break_other_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            config = root / "config" / "sources.json"
            config.write_text(json.dumps({"schema_version": 1, "sources": [
                {"id": "bad", "type": "firecrawl_local", "endpoint": "https://api.firecrawl.dev"},
                {"id": "inbox", "type": "json_directory", "path": "data/inbox"},
            ]}))
            result = run_pipeline(config, date(2026, 9, 8), "Asia/Shanghai")
        self.assertEqual([item.status for item in result.health], ["failed", "empty"])

    @patch("wechat_hot_radar.adapters.firecrawl_local.http.client.HTTPConnection")
    def test_malformed_json_is_rejected(self, factory):
        reply = MagicMock(status=200)
        reply.read1.side_effect = [b"not JSON", b""]
        factory.return_value.getresponse.return_value = reply
        self.assertEqual(FirecrawlLocalAdapter("test", [URL]).collect().health.status, "failed")

    def test_timeout_opens_circuit(self):
        with patch.object(FirecrawlLocalAdapter, "_scrape", side_effect=TimeoutError) as fetch:
            result = FirecrawlLocalAdapter("test", [URL, URL + "-2"]).collect()
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result.health.status, "failed")


if __name__ == "__main__":
    unittest.main()
