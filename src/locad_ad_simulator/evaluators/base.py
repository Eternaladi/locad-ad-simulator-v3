from __future__ import annotations

import re
from typing import Iterable

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "our", "are", "into",
    "without", "across", "all", "has", "have", "not", "but", "can", "will", "brand", "brands"
}


def tokens(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9+.-]*", text) if len(t) > 2 and t.lower() not in STOPWORDS}


def overlap_score(text: str, candidates: Iterable[str]) -> tuple[float, list[str]]:
    text_tokens = tokens(text)
    matches: list[tuple[float, str]] = []
    for candidate in candidates:
        cand_tokens = tokens(candidate)
        if not cand_tokens:
            continue
        overlap = len(text_tokens & cand_tokens) / max(len(cand_tokens), 1)
        if overlap > 0:
            matches.append((overlap, candidate))
    matches.sort(reverse=True, key=lambda x: x[0])
    score = sum(m[0] for m in matches[:4]) / min(len(matches), 4) if matches else 0.0
    return score, [m[1] for m in matches[:5]]


def clamp_score(value: float, lo: float = 1.0, hi: float = 10.0) -> float:
    return round(max(lo, min(hi, value)), 1)


def bool_rate(items: list[bool]) -> float:
    return round(sum(items) / len(items), 3) if items else 0.0
