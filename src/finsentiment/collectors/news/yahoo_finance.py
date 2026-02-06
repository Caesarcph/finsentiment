from typing import List, Dict, Any
from ..base_collector import BaseCollector
import yfinance as yf
from datetime import datetime

class YahooFinanceCollector(BaseCollector):
    def __init__(self, tickers: List[str], refresh_interval: int = 300):
        super().__init__(name="yahoo_finance", source_type="news", refresh_interval=refresh_interval)
        self.tickers = tickers

    def _collect_implementation(self) -> List[Dict[str, Any]]:
        collected_data = []
        for ticker in self.tickers:
            try:
                # Using yfinance Ticker news
                t = yf.Ticker(ticker)
                news = t.news
                
                for item in news:
                    content = item.get("content", {})
                    provider = content.get("provider", {})
                    collected_data.append({
                        "source": "yahoo_finance",
                        "ticker": ticker,
                        "title": content.get("title"),
                        "link": content.get("canonicalUrl", {}).get("url"),
                        "publisher": provider.get("displayName"),
                        "timestamp": content.get("pubDate"),
                        "crawled_at": datetime.utcnow().isoformat()
                    })
            except Exception as e:
                self.logger.error(f"Failed to fetch news for {ticker}: {e}")
                
        return collected_data
