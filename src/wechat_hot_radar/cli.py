from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .pipeline import run_pipeline
from .report import write_reports


def _date(value: str, timezone_name: str) -> date:
    if value == "today":
        return datetime.now(ZoneInfo(timezone_name)).date()
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Free, truth-first WeChat article radar")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="collect, validate, rank and report")
    run.add_argument("--config", default="config/sources.json")
    run.add_argument("--date", default="today", help="YYYY-MM-DD or today")
    run.add_argument("--timezone", default="Asia/Tokyo")
    run.add_argument("--top", type=int, default=50)
    run.add_argument("--output", default="reports")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.top < 1 or args.top > 500:
        raise SystemExit("--top must be between 1 and 500")
    target_date = _date(args.date, args.timezone)
    result = run_pipeline(Path(args.config), target_date, args.timezone)
    metadata = write_reports(
        result,
        output_dir=Path(args.output),
        target_date=target_date,
        timezone_name=args.timezone,
        top_n=args.top,
        generated_at=datetime.now(ZoneInfo(args.timezone)),
    )
    print(json.dumps({key: metadata[key] for key in ("status", "target_date", "discovered_articles", "verified_share_articles", "candidate_articles", "discovery_only_articles")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
