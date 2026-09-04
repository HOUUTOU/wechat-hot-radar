from __future__ import annotations

from collections.abc import Mapping, Sequence


def classify(title: str, summary: str, account: str, rules: Mapping[str, Sequence[str]]) -> str:
    haystack = f"{title} {summary} {account}".lower()
    best_category = "其他"
    best_score = 0
    for category, keywords in rules.items():
        score = sum(1 for keyword in keywords if str(keyword).lower() in haystack)
        if score > best_score:
            best_category = category
            best_score = score
    return best_category
