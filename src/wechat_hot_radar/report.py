from __future__ import annotations

import csv
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .models import Article, CollectionResult
from .ranking import rank_articles


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _status(main_count: int, requested: int) -> str:
    if main_count >= requested:
        return "PASS"
    if main_count > 0:
        return "PARTIAL"
    return "ABSTAIN"


def _metric_text(article: Article, field: str) -> str:
    metric = getattr(article, field)
    return metric.raw if metric.verified and metric.raw else "未公开"


def _markdown_table(articles: list[Article], include_share: bool = True) -> list[str]:
    header = "| 排名 | 文章 | 公众号 | 分类 | 转发 | 点赞 | 发布时间 |"
    separator = "|---:|---|---|---|---:|---:|---|"
    rows = [header, separator]
    for index, article in enumerate(articles, 1):
        title = article.title.replace("|", "\\|")
        account = article.account.replace("|", "\\|")
        share = _metric_text(article, "share") if include_share else "未公开"
        like = _metric_text(article, "like")
        rows.append(
            f"| {index} | [{title}]({article.url}) | {account} | {article.category} | "
            f"{share} | {like} | {article.published_at.isoformat()} |"
        )
    if not articles:
        rows.append("| — | 暂无满足证据要求的文章 | — | — | — | — | — |")
    return rows


def _csv_text(articles: list[Article], list_name: str) -> str:
    import io

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "list",
            "rank",
            "title",
            "account",
            "category",
            "url",
            "published_at",
            "share_raw",
            "share_lower_bound",
            "share_source_url",
            "like_raw",
            "like_lower_bound",
            "like_source_url",
        ]
    )
    def safe(value: Any) -> Any:
        if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    for index, article in enumerate(articles, 1):
        writer.writerow(
            [safe(value) for value in [
                list_name,
                index,
                article.title,
                article.account,
                article.category,
                article.url,
                article.published_at.isoformat(),
                article.share.raw if article.share.verified else "",
                article.share.lower_bound if article.share.verified else "",
                article.share.source_url if article.share.verified else "",
                article.like.raw if article.like.verified else "",
                article.like.lower_bound if article.like.verified else "",
                article.like.source_url if article.like.verified else "",
            ]]
        )
    return buffer.getvalue()


def write_reports(
    result: CollectionResult,
    *,
    output_dir: Path,
    target_date: date,
    timezone_name: str,
    top_n: int,
    generated_at: datetime,
) -> dict[str, Any]:
    main, candidates, discovery_only = rank_articles(result.articles, top_n)
    status = _status(len(main), top_n)
    metadata = {
        "schema_version": 1,
        "status": status,
        "requested_top_n": top_n,
        "target_date": target_date.isoformat(),
        "timezone": timezone_name,
        "generated_at": generated_at.isoformat(),
        "discovered_articles": len(result.articles),
        "verified_share_articles": len(main),
        "candidate_articles": len(candidates),
        "discovery_only_articles": len(discovery_only),
        "source_health": [item.to_dict() for item in result.health],
        "warnings": result.warnings,
        "ranking_rule": "verified share lower bound DESC, verified like lower bound DESC, published_at DESC",
        "main": [article.to_dict() for article in main],
        "candidates": [article.to_dict() for article in candidates],
        "discovery_only": [article.to_dict() for article in discovery_only],
    }

    lines = [
        "# 微信公众号当日热榜",
        "",
        f"- 状态：**{status}**",
        f"- 目标日期：{target_date.isoformat()}（{timezone_name}）",
        f"- 生成时间：{generated_at.isoformat()}",
        f"- 主榜有效条目：{len(main)} / {top_n}",
        f"- 候选条目：{len(candidates)}",
        f"- 仅发现条目：{len(discovery_only)}",
        "- 排序：可验证转发量优先，其次可验证点赞量，最后发布时间。",
        "",
    ]
    if status != "PASS":
        lines.extend(
            [
                "> 数据不足时不会补造条目。PARTIAL 表示主榜不足 50 条；ABSTAIN 表示没有文章满足转发证据要求。",
                "",
            ]
        )
    lines.extend(["## 转发证据主榜", "", *_markdown_table(main), "", "## 点赞候选榜", ""])
    lines.append("> 下列文章没有可验证转发量，不能与主榜直接比较。")
    lines.extend(["", *_markdown_table(candidates, include_share=False), "", "## 仅发现文章", ""])
    lines.append("> 下列文章的转发和点赞均未公开，仅按发布时间排列，不属于热度榜。")
    lines.extend(["", *_markdown_table(discovery_only, include_share=False), "", "## 来源健康状态", ""])
    lines.extend(["| 来源 | 状态 | 获取 | 接受 | 拒绝 | 说明 |", "|---|---|---:|---:|---:|---|"])
    for health in result.health:
        message = health.message.replace("|", "\\|")
        lines.append(
            f"| {health.source_id} | {health.status} | {health.fetched} | {health.accepted} | "
            f"{health.rejected} | {message} |"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_text(output_dir / "latest.md", "\n".join(lines) + "\n")
    _atomic_text(output_dir / "latest.json", json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    _atomic_text(output_dir / "main.csv", _csv_text(main, "main"))
    _atomic_text(output_dir / "candidates.csv", _csv_text(candidates, "candidate"))
    _atomic_text(output_dir / "discovery.csv", _csv_text(discovery_only, "discovery_only"))
    return metadata
