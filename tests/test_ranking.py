from datetime import datetime, timezone
import unittest

from wechat_hot_radar.metrics import parse_metric
from wechat_hot_radar.models import Article
from wechat_hot_radar.ranking import rank_articles


OBSERVED = datetime(2026, 9, 4, 6, 0, tzinfo=timezone.utc)


def metric(value):
    return parse_metric(value, source_url="https://example.org/e", observed_at=OBSERVED, evidence_tier="community")


def article(title, share=None, like=None, hour=1):
    return Article(
        title=title,
        account="测试公众号",
        url=f"https://mp.weixin.qq.com/s?sn={title}",
        published_at=datetime(2026, 9, 4, hour, tzinfo=timezone.utc),
        discovered_by=("test",),
        share=metric(share) if share is not None else parse_metric(None),
        like=metric(like) if like is not None else parse_metric(None),
    )


class RankingTests(unittest.TestCase):
    def test_share_is_primary(self):
        high_like = article("A", share=100, like=100_000)
        high_share = article("B", share=101, like=1)
        main, _, _ = rank_articles([high_like, high_share])
        self.assertEqual([item.title for item in main], ["B", "A"])

    def test_like_breaks_share_tie(self):
        low_like = article("A", share="10万+", like=10)
        high_like = article("B", share="10万+", like=11)
        main, _, _ = rank_articles([low_like, high_like])
        self.assertEqual([item.title for item in main], ["B", "A"])

    def test_unknown_share_is_separate(self):
        verified = article("A", share=1, like=1)
        unknown = article("B", like=1_000_000)
        main, candidates, discovery = rank_articles([unknown, verified])
        self.assertEqual([item.title for item in main], ["A"])
        self.assertEqual([item.title for item in candidates], ["B"])
        self.assertEqual(discovery, [])

    def test_no_metrics_is_discovery_only(self):
        item = article("A")
        main, candidates, discovery = rank_articles([item])
        self.assertEqual(main, [])
        self.assertEqual(candidates, [])
        self.assertEqual([value.title for value in discovery], ["A"])


if __name__ == "__main__":
    unittest.main()
