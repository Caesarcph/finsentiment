"""
FinSentiment - Real-time financial sentiment analysis engine.

Provides multi-source news/social media aggregation with hybrid
FinBERT + LLM analysis for trading signal generation.
"""

from .engine import SentimentEngine, SentimentResult

__version__ = "0.1.0"
__all__ = ["SentimentEngine", "SentimentResult"]
