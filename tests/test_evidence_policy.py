"""合成数据仅用于验证拒答规则，不是正式榜单数据。"""
from dataclasses import replace
from datetime import date, datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from wechat_hot_radar.adapters.json_directory import article_from_payload
from wechat_hot_radar.metrics import metric_from_payload, parse_metric
from wechat_hot_radar.models import CollectionResult
from wechat_hot_radar.pipeline import _choose_metric
from wechat_hot_radar.ranking import rank_articles
from wechat_hot_radar.report import write_reports


class EvidencePolicyTests(unittest.TestCase):
    def payload(self):
        return {"raw": "10万+", "source_url": "https://example.org/proof",
                "observed_at": "2026-09-08T08:00:00+08:00", "evidence_tier": "official_backend",
                "verified": True, "source_verified": True}

    def test_import_cannot_self_certify(self):
        metric = metric_from_payload(self.payload())
        self.assertTrue(metric.evidence_present)
        self.assertFalse(metric.source_verified)
        self.assertFalse(metric.verified)
        self.assertFalse(metric.to_dict()["verified"])

    def test_external_official_tier_does_not_override_internal_verified_metric(self):
        untrusted = metric_from_payload(self.payload())
        internal = replace(untrusted, source_verified=True, evidence_tier="community")
        self.assertEqual(_choose_metric(internal, untrusted), internal)
        self.assertEqual(_choose_metric(untrusted, internal), internal)

    def test_source_flag_alone_is_insufficient(self):
        self.assertFalse(replace(parse_metric(None), source_verified=True).verified)

    def test_malformed_source_url_does_not_crash(self):
        for value in (123, {}, [], "https://", "https://[", "https://user:secret@example.org"):
            with self.subTest(value=value):
                metric = metric_from_payload({**self.payload(), "source_url": value})
                self.assertFalse(metric.evidence_present)
                self.assertFalse(metric.verified)

    def test_forged_fifty_articles_abstain(self):
        articles = [article_from_payload({
            "title": f"Synthetic {index}", "account": "Test fixture",
            "url": f"https://mp.weixin.qq.com/s/test-{index}",
            "published_at": "2026-09-08T08:00:00+08:00",
            "share": self.payload(), "like": self.payload(),
        }, "fixture") for index in range(50)]
        main, candidates, discovery = rank_articles(articles)
        self.assertEqual((len(main), len(candidates), len(discovery)), (0, 0, 50))
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            result = write_reports(CollectionResult(articles, [], []), output_dir=output,
                                   target_date=date(2026, 9, 8), timezone_name="Asia/Shanghai",
                                   top_n=50, generated_at=datetime.now(timezone.utc))
            self.assertEqual(result["status"], "ABSTAIN")
            self.assertNotIn("10万+", (output / "discovery.csv").read_text())
            self.assertIn("未核验", (output / "latest.md").read_text())
            saved = json.loads((output / "latest.json").read_text())
            self.assertFalse(saved["discovery_only"][0]["share"]["verified"])


if __name__ == "__main__":
    unittest.main()
