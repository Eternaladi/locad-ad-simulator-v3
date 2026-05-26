from __future__ import annotations

import re
from typing import Any

from .copy_parser import extract_cta, extract_headline, copy_stats

CATEGORY_KEYWORDS = {
    "cost": ["cost", "costs", "save", "savings", "margin", "surcharge", "storage", "fee", "cheaper", "reduce", "cut"],
    "speed": ["same-day", "next-day", "fast", "faster", "delivery", "fulfillment", "sla", "prime-like", "3 days"],
    "inventory": ["inventory", "sync", "stock", "reserved", "visibility", "oversell", "marketplace"],
    "cross_border": ["cross-border", "gcc", "ksa", "uae", "compliance", "customs", "region", "expansion", "noon", "salla", "zid"],
    "scale": ["scale", "scaling", "grow", "growth", "order volume", "peak", "ramadan", "bfcm", "campaign"],
    "returns": ["return", "returns", "refund", "cx", "customer experience"],
}

PROOF_PATTERNS = {
    "number": r"\d+",
    "percentage": r"\d+(?:\.\d+)?\s*%",
    "case_study": r"case study|customer story|same-category",
    "benchmark": r"benchmark|before/after|comparison|vs\b",
    "sla": r"\bSLA\b|service level",
    "integration": r"Shopify|Amazon|Noon|Salla|Zid|Klaviyo|Gorgias|integration",
    "time_bound": r"\b\d+\s*(?:min|minute|hour|day|days|week|weeks)\b",
}


def _sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip(" -•\t") for p in pieces if p.strip(" -•\t")]


def _categories_for(text: str) -> list[str]:
    lower = text.lower()
    return sorted([cat for cat, words in CATEGORY_KEYWORDS.items() if any(w.lower() in lower for w in words)])


def proof_signals(copy_text: str) -> dict[str, bool]:
    return {name: bool(re.search(pattern, copy_text, flags=re.IGNORECASE)) for name, pattern in PROOF_PATTERNS.items()}


def extract_ad_claims(copy_text: str) -> dict[str, Any]:
    claims = []
    for idx, sent in enumerate(_sentences(copy_text), 1):
        cats = _categories_for(sent)
        if cats or idx == 1:
            claims.append({"id": f"claim_{idx}", "text": sent, "categories": cats})
    return {
        "headline": extract_headline(copy_text),
        "cta": extract_cta(copy_text),
        "stats": copy_stats(copy_text),
        "proof_signals": proof_signals(copy_text),
        "claims": claims,
        "categories": sorted({cat for c in claims for cat in c["categories"]}),
    }
