from __future__ import annotations


def bar(score: float, width: int = 10) -> str:
    filled = int(round(max(0, min(10, score))))
    return "█" * filled + "░" * (width - filled)
