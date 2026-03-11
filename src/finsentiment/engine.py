"""
SentimentEngine - Core engine for real-time financial sentiment analysis.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .collectors.base_collector import BaseCollector
from .collectors.news.reuters import ReutersCollector
from .collectors.news.seeking_alpha import SeekingAlphaCollector
from .collectors.news.yahoo_finance import YahooFinanceCollector


@dataclass
class SentimentResult:
    """Result of sentiment analysis for a single ticker."""
    ticker: str
    score: float
    label: str
    confidence: float
    source_count: int
    top_factors: List[str]


class SentimentEngine:
    """
    Main engine for real-time financial sentiment analysis.
    
    Orchestrates data collection, analysis, and signal generation.
    
    Example:
        >>> engine = SentimentEngine.from_config("config/")
        >>> engine.start()
        >>> sentiment = engine.get_sentiment("AAPL")
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("finsentiment.engine")
        self.collectors: List[BaseCollector] = []
        self.outputs: List[Any] = []
        self._running = False

    @classmethod
    def from_config(cls, config_path: str) -> "SentimentEngine":
        """Initialize engine from configuration directory."""
        engine = cls()

        sources_file = Path(config_path) / "sources.yaml"
        with sources_file.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        news_cfg = config.get("news", {})

        if news_cfg.get("reuters", {}).get("enabled", False):
            reuters_cfg = news_cfg["reuters"]
            engine.add_collector(
                ReutersCollector(
                    feeds=reuters_cfg.get("feeds"),
                    refresh_interval=reuters_cfg.get("refresh_interval", 300),
                )
            )

        if news_cfg.get("yahoo_finance", {}).get("enabled", False):
            yahoo_cfg = news_cfg["yahoo_finance"]
            engine.add_collector(
                YahooFinanceCollector(
                    tickers=yahoo_cfg.get("tickers", []),
                    refresh_interval=yahoo_cfg.get("refresh_interval", 300),
                )
            )

        if news_cfg.get("seeking_alpha", {}).get("enabled", False):
            seeking_cfg = news_cfg["seeking_alpha"]
            engine.add_collector(
                SeekingAlphaCollector(
                    feed_url=seeking_cfg.get("feed_url"),
                    refresh_interval=seeking_cfg.get("refresh_interval", 300),
                )
            )

        engine.logger.info("Engine initialized with %d collectors", len(engine.collectors))
        return engine

    def start(self) -> None:
        """Start real-time data collection from all registered collectors."""
        self._running = True
        self.logger.info("SentimentEngine started")
        # TODO: Implement background collection loop

    def stop(self) -> None:
        """Stop all collection activities."""
        self._running = False
        self.logger.info("SentimentEngine stopped")

    def get_sentiment(self, ticker: str) -> SentimentResult:
        """
        Get current sentiment for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "TSLA")
        """
        # TODO: Implement full sentiment aggregation pipeline
        return SentimentResult(
            ticker=ticker,
            score=0.0,
            label="NEUTRAL",
            confidence=0.0,
            source_count=0,
            top_factors=[]
        )

    def add_output(self, output: Any) -> None:
        """Register an output destination for trading signals."""
        self.outputs.append(output)
        self.logger.info(f"Added output handler: {type(output).__name__}")

    def add_collector(self, collector: BaseCollector) -> None:
        """Register a data collector."""
        self.collectors.append(collector)
        self.logger.info(f"Added collector: {collector.name}")
