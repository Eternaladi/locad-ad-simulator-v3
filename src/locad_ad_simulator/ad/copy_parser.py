from __future__ import annotations

import re


def split_lines(copy_text: str) -> list[str]:
    return [line.strip() for line in copy_text.splitlines() if line.strip()]


def first_sentence(text: str) -> str:
    match = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
    return match[0].strip() if match else text.strip()


def extract_headline(copy_text: str) -> str:
    lines = split_lines(copy_text)
    return lines[0] if lines else first_sentence(copy_text)


def extract_cta(copy_text: str) -> str | None:
    lines = split_lines(copy_text)
    cta_terms = ["book", "demo", "start", "get", "see", "check", "audit", "talk", "learn"]
    for line in reversed(lines):
        lower = line.lower()
        if any(term in lower for term in cta_terms):
            return line
    return None


def copy_stats(copy_text: str) -> dict[str, int | bool]:
    words = re.findall(r"\b\w+\b", copy_text)
    return {
        "word_count": len(words),
        "line_count": len(split_lines(copy_text)),
        "has_number": bool(re.search(r"\d", copy_text)),
        "has_percentage": "%" in copy_text,
        "has_cta": extract_cta(copy_text) is not None,
    }
