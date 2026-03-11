"""
SentimentEngine - Core engine for real-time financial sentiment analysis.
"""

import logging
import threading
import time
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
        self._collection_thread: Optional[threading.Thread] = None
        self._collected_data: Dict[str, List[Dict[str, Any]]] = {}
        self._data_lock = threading.Lock()

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
        
        # Start background collection thread
        self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        self.logger.info("Background collection thread started")
    
    def _collection_loop(self) -> None:
        """Background loop to periodically collect data from all collectors."""
        while self._running:
            for collector in self.collectors:
                if not self._running:
                    break
                try:
                    data = collector.collect()
                    if data:
                        with self._data_lock:
                            collector_name = collector.name
                            if collector_name not in self._collected_data:
                                self._collected_data[collector_name] = []
                            self._collected_data[collector_name].extend(data)
                            # Keep only last 100 items per collector to limit memory
                            self._collected_data[collector_name] = self._collected_data[collector_name][-100:]
                except Exception as exc:
                    self.logger.error(f"Collection error in background loop: {exc}")
            
            # Sleep for 30 seconds before next collection cycle
            time.sleep(30)

    def stop(self) -> None:
        """Stop all collection activities."""
        self._running = False
        self.logger.info("SentimentEngine stopped")

    def get_sentiment(self, ticker: str) -> SentimentResult:
        """
        Get current sentiment for a specific ticker.

        Current implementation provides a lightweight heuristic score from
        collected headlines/summaries and explicit ticker tags.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "TSLA")
        """
        positive_words = {"beat", "surge", "growth", "upgrade", "bullish", "record"}
        negative_words = {"miss", "drop", "downgrade", "bearish", "lawsuit", "warning"}

        normalized_ticker = ticker.upper()
        relevant_texts: List[str] = []

        # First, try to use data from background collection
        with self._data_lock:
            for source_data in self._collected_data.values():
                for item in source_data:
                    item_ticker = str(item.get("ticker", "")).upper()
                    item_tickers = [str(t).upper() for t in item.get("tickers", [])]
                    title = str(item.get("title", "") or "")
                    summary = str(item.get("summary", "") or "")
                    combined = f"{title} {summary}".lower()

                    if (
                        item_ticker == normalized_ticker
                        or normalized_ticker in item_tickers
                        or normalized_ticker.lower() in combined
                    ):
                        relevant_texts.append(combined)

        # If no background data, fall back to real-time collection
        if not relevant_texts:
            for collector in self.collectors:
                for item in collector.collect():
                    item_ticker = str(item.get("ticker", "")).upper()
                    item_tickers = [str(t).upper() for t in item.get("tickers", [])]
                    title = str(item.get("title", "") or "")
                    summary = str(item.get("summary", "") or "")
                    combined = f"{title} {summary}".lower()

                    if (
                        item_ticker == normalized_ticker
                        or normalized_ticker in item_tickers
                        or normalized_ticker.lower() in combined
                    ):
                        relevant_texts.append(combined)

        if not relevant_texts:
            return SentimentResult(
                ticker=normalized_ticker,
                score=0.0,
                label="NEUTRAL",
                confidence=0.0,
                source_count=0,
                top_factors=[],
            )

        pos_hits = sum(sum(word in text for word in positive_words) for text in relevant_texts)
        neg_hits = sum(sum(word in text for word in negative_words) for text in relevant_texts)
        raw = pos_hits - neg_hits
        score = max(-1.0, min(1.0, raw / max(len(relevant_texts), 1)))

        if score > 0.15:
            label = "BULLISH"
        elif score < -0.15:
            label = "BEARISH"
        else:
            label = "NEUTRAL"

        confidence = min(1.0, (abs(score) + min(len(relevant_texts), 10) / 10) / 2)
        top_factors = [
            f"positive_hits={pos_hits}",
            f"negative_hits={neg_hits}",
            f"matched_items={len(relevant_texts)}",
        ]

        return SentimentResult(
            ticker=normalized_ticker,
            score=round(score, 4),
            label=label,
            confidence=round(confidence, 4),
            source_count=len(relevant_texts),
            top_factors=top_factors,
        )

    def add_output(self, output: Any) -> None:
        """Register an output destination for trading signals."""
        self.outputs.append(output)
        self.logger.info(f"Added output handler: {type(output).__name__}")

    def add_collector(self, collector: BaseCollector) -> None:
        """Register a data collector."""
        self.collectors.append(collector)
        self.logger.info(f"Added collector: {collector.name}")
    
    def get_collected_data(self, source: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get collected data, optionally filtered by source.
        
        Args:
            source: Filter by collector name (e.g., "reuters"), or None for all.
        
        Returns:
            Dictionary mapping source names to lists of collected items.
        """
        with self._data_lock:
            if source is None:
                return dict(self._collected_data)
            return {source: self._collected_data.get(source, [])}
