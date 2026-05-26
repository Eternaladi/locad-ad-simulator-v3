"""Market-aware validation layer for Locad Ad Simulator v2."""
from .market_loader import load_market_context, MARKET_ICP_FILES, VALID_MARKETS
from .persona_scorer import score_buyer_personas
from .market_report import build_market_fit_summary

__all__ = [
    "load_market_context",
    "MARKET_ICP_FILES",
    "VALID_MARKETS",
    "score_buyer_personas",
    "build_market_fit_summary",
]
