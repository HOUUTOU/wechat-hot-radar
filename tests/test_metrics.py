from datetime import datetime, timezone
import unittest

from wechat_hot_radar.metrics import parse_metric


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.observed = datetime(2026, 9, 4, 3, 0, tzinfo=timezone.utc)

    def parse(self, value):
        return parse_metric(
            value,
            source_url="https://example.org/evidence",
            observed_at=self.observed,
            evidence_tier="community",
        )

    def test_exact_integer(self):
        metric = self.parse(321)
        self.assertEqual(metric.lower_bound, 321)
        self.assertEqual(metric.upper_bound, 321)
        self.assertTrue(metric.exact)
        self.assertTrue(metric.verified)

    def test_ten_thousand_plus_keeps_band(self):
        metric = self.parse("10万+")
        self.assertEqual(metric.lower_bound, 100_000)
        self.assertIsNone(metric.upper_bound)
        self.assertFalse(metric.exact)
        self.assertTrue(metric.verified)

    def test_decimal_unit(self):
        metric = self.parse("3.2万")
        self.assertEqual(metric.lower_bound, 32_000)

    def test_invalid_text_is_not_verified(self):
        metric = self.parse("很多")
        self.assertFalse(metric.verified)
        self.assertIsNone(metric.lower_bound)

    def test_unitless_decimal_is_rejected(self):
        metric = self.parse("3.2")
        self.assertFalse(metric.verified)

    def test_missing_evidence_is_not_verified(self):
        metric = parse_metric("10万+")
        self.assertFalse(metric.verified)

    def test_naive_observation_is_not_verified(self):
        metric = parse_metric(
            "10万+",
            source_url="https://example.org/evidence",
            observed_at=datetime(2026, 9, 4, 3, 0),
        )
        self.assertFalse(metric.verified)


if __name__ == "__main__":
    unittest.main()
