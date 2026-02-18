from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import yfinance as yf

from ..base_collector import BaseCollector


class YahooFinanceCollector(BaseCollector):
    """Collect news for configured tickers via yfinance."""

    def __init__(self, tickers: List[str], refresh_interval: int = 300):
        super().__init__(name="yahoo_finance", source_type="news", refresh_interval=refresh_interval)
        self.tickers = tickers

    def _normalize_timestamp(self, pub_date: Any) -> Optional[str]:
        """Normalize Yahoo pubDate (epoch/int/ISO text) to ISO-8601 string."""
        if pub_date in (None, ""):
            return None

        if isinstance(pub_date, (int, float)):
            try:
                return datetime.fromtimestamp(pub_date, tz=timezone.utc).isoformat()
            except (ValueError, OSError, OverflowError):
                return str(pub_date)

        return str(pub_date)

    def _collect_implementation(self) -> List[Dict[str, Any]]:
        collected_data: List[Dict[str, Any]] = []
        for ticker in self.tickers:
            try:
                t = yf.Ticker(ticker)
                news = t.news or []

                for item in news:
                    content = item.get("content", {})
                    provider = content.get("provider", {})
                    published_at = self._normalize_timestamp(content.get("pubDate"))
                    collected_data.append(
                        {
                            "source": "yahoo_finance",
                            "ticker": ticker,
                            "title": content.get("title"),
                            "summary": content.get("summary") or "",
                            "link": content.get("canonicalUrl", {}).get("url"),
                            "publisher": provider.get("displayName"),
                            "published_at": published_at,
                            # Keep legacy key for compatibility with existing callers.
                            "timestamp": published_at,
                            "crawled_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )
            except Exception as e:
                self.logger.error(f"Failed to fetch news for {ticker}: {e}")

        return collected_data
