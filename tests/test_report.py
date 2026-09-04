from datetime import date, datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from wechat_hot_radar.models import CollectionResult, SourceHealth
from wechat_hot_radar.report import write_reports


class ReportTests(unittest.TestCase):
    def test_empty_result_abstains_and_writes_all_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            metadata = write_reports(
                CollectionResult([], [SourceHealth("empty", "empty")], []),
                output_dir=output,
                target_date=date(2026, 9, 4),
                timezone_name="Asia/Tokyo",
                top_n=50,
                generated_at=datetime(2026, 9, 4, 12, tzinfo=timezone.utc),
            )
            self.assertEqual(metadata["status"], "ABSTAIN")
            for name in ("latest.md", "latest.json", "main.csv", "candidates.csv", "discovery.csv"):
                self.assertTrue((output / name).is_file())
            saved = json.loads((output / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["main"], [])


if __name__ == "__main__":
    unittest.main()
