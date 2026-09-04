import json
from datetime import date
from pathlib import Path
import tempfile
import unittest

from wechat_hot_radar.pipeline import canonical_url, run_pipeline


class PipelineTests(unittest.TestCase):
    def test_tracking_parameters_are_removed(self):
        url = "http://mp.weixin.qq.com/s?__biz=x&sn=y&scene=1&from=timeline"
        self.assertEqual(canonical_url(url), "https://mp.weixin.qq.com/s?__biz=x&sn=y")

    def test_filters_date_and_requires_wechat_url(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            (root / "data" / "inbox").mkdir(parents=True)
            config = {
                "schema_version": 1,
                "sources": [{"id": "inbox", "type": "json_directory", "path": "data/inbox"}],
                "classification": {"科技": ["AI"]},
            }
            (root / "config" / "sources.json").write_text(json.dumps(config), encoding="utf-8")
            records = [
                {
                    "title": "AI 今日进展",
                    "account": "测试号",
                    "url": "https://mp.weixin.qq.com/s?sn=valid",
                    "published_at": "2026-09-04T08:00:00+08:00",
                },
                {
                    "title": "昨日文章",
                    "account": "测试号",
                    "url": "https://mp.weixin.qq.com/s?sn=old",
                    "published_at": "2026-09-03T08:00:00+08:00",
                },
                {
                    "title": "非微信文章",
                    "account": "测试号",
                    "url": "https://example.org/article",
                    "published_at": "2026-09-04T08:00:00+08:00",
                },
            ]
            (root / "data" / "inbox" / "items.json").write_text(json.dumps(records), encoding="utf-8")
            result = run_pipeline(root / "config" / "sources.json", date(2026, 9, 4), "Asia/Shanghai")
            self.assertEqual(len(result.articles), 1)
            self.assertEqual(result.articles[0].category, "科技")


if __name__ == "__main__":
    unittest.main()
