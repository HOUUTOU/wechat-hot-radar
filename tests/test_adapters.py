from datetime import datetime, timezone
import json
import unittest
from unittest.mock import patch

from wechat_hot_radar.adapters.json_url import JsonUrlAdapter
from wechat_hot_radar.adapters.rss_wechat import _feed_links


class AdapterTests(unittest.TestCase):
    def test_rss_extracts_only_direct_wechat_articles(self):
        body = b"""<?xml version='1.0'?>
        <rss><channel>
          <item><link>https://mp.weixin.qq.com/s?sn=ok</link></item>
          <item><link>https://example.org/not-wechat</link></item>
        </channel></rss>"""
        self.assertEqual(_feed_links(body), ["https://mp.weixin.qq.com/s?sn=ok"])

    @patch("wechat_hot_radar.adapters.json_url.fetch_bytes")
    def test_json_url_keeps_evidence_requirements(self, fetch):
        fetch.return_value = json.dumps(
            [
                {
                    "title": "Test",
                    "account": "Account",
                    "url": "https://mp.weixin.qq.com/s?sn=ok",
                    "published_at": "2026-09-04T08:00:00+08:00",
                    "share": {
                        "raw": "10万+",
                        "source_url": "https://example.org/evidence",
                        "observed_at": "2026-09-04T12:00:00+08:00",
                        "evidence_tier": "community"
                    }
                }
            ]
        ).encode()
        result = JsonUrlAdapter("public-json", "https://example.org/feed.json").collect()
        self.assertEqual(result.health.status, "ok")
        self.assertTrue(result.articles[0].share.evidence_present)
        self.assertFalse(result.articles[0].share.verified)

    def test_json_url_rejects_plain_http(self):
        result = JsonUrlAdapter("public-json", "http://example.org/feed.json").collect()
        self.assertEqual(result.health.status, "failed")


if __name__ == "__main__":
    unittest.main()
