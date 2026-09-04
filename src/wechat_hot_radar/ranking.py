from __future__ import annotations

from .models import Article


def _verified_value(article: Article, name: str) -> int:
    metric = getattr(article, name)
    return metric.lower_bound if metric.verified and metric.lower_bound is not None else -1


def rank_articles(articles: list[Article], top_n: int = 50) -> tuple[list[Article], list[Article], list[Article]]:
    """Return separate share, like-only and discovery-only rankings."""

    main = [article for article in articles if article.share.verified]
    candidates = [article for article in articles if not article.share.verified and article.like.verified]
    discovery_only = [article for article in articles if not article.share.verified and not article.like.verified]

    main.sort(
        key=lambda article: (
            _verified_value(article, "share"),
            _verified_value(article, "like"),
            article.published_at.timestamp(),
            article.title,
        ),
        reverse=True,
    )
    candidates.sort(
        key=lambda article: (
            _verified_value(article, "like"),
            article.published_at.timestamp(),
            article.title,
        ),
        reverse=True,
    )
    discovery_only.sort(
        key=lambda article: (article.published_at.timestamp(), article.title),
        reverse=True,
    )
    return main[:top_n], candidates[:top_n], discovery_only[:top_n]
