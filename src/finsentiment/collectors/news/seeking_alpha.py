from typing import List, Dict, Any
from ..base_collector import BaseCollector
import feedparser
from datetime import datetime, timezone
import time

class SeekingAlphaCollector(BaseCollector):
    """
    Collector for Seeking Alpha Market Currents via RSS.
    """
    DEFAULT_FEED = "https://seekingalpha.com/market_currents.xml"

    def __init__(self, feed_url: str = None, refresh_interval: int = 300):
        super().__init__(name="seeking_alpha", source_type="news", refresh_interval=refresh_interval)
        self.feed_url = feed_url or self.DEFAULT_FEED

    def _collect_implementation(self) -> List[Dict[str, Any]]:
        collected_data = []
        try:
            self.logger.debug(f"Fetching feed: {self.feed_url}")
            feed = feedparser.parse(self.feed_url)

            if feed.bozo:
                self.logger.warning(f"Potential issue parsing feed {self.feed_url}: {feed.bozo_exception}")

            for entry in feed.entries:
                # Handle dates
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                    pub_date = dt.isoformat()
                else:
                    pub_date = entry.get('published')

                # Extract stock tickers if available (often in 'category' or tags)
                # SA feeds often put tickers in categories like "NASDAQ:AAPL" or just "AAPL"
                tickers = []
                if 'tags' in entry:
                    tickers = [tag.term for tag in entry.tags]

                collected_data.append({
                    "source": "seeking_alpha",
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "summary": entry.get("summary"), # SA summaries can be short
                    "tickers": tickers,
                    "published_at": pub_date,
                    "crawled_at": datetime.now(timezone.utc).isoformat(),
                    "id": entry.get("id")
                })
        except Exception as e:
            self.logger.error(f"Failed to fetch Seeking Alpha feed: {e}")
            
        return collected_data
