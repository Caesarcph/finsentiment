from typing import List, Dict, Any
from ..base_collector import BaseCollector
import feedparser
from datetime import datetime, timezone
import time

class ReutersCollector(BaseCollector):
    """
    Collector for Reuters News via RSS feeds.
    """
    DEFAULT_FEEDS = [
        "http://feeds.reuters.com/reuters/businessNews",
        "http://feeds.reuters.com/reuters/technologyNews",
        "http://feeds.reuters.com/reuters/topNews"
    ]

    def __init__(self, feeds: List[str] = None, refresh_interval: int = 300):
        super().__init__(name="reuters", source_type="news", refresh_interval=refresh_interval)
        self.feeds = feeds or self.DEFAULT_FEEDS

    def _collect_implementation(self) -> List[Dict[str, Any]]:
        collected_data = []
        for feed_url in self.feeds:
            try:
                self.logger.debug(f"Fetching feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                # feedparser sets bozo=1 if there's a malformed XML, but often still parses content.
                if feed.bozo:
                     self.logger.warning(f"Potential issue parsing feed {feed_url}: {feed.bozo_exception}")

                for entry in feed.entries:
                    # Convert struct_time to ISO format if available
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                         dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                         pub_date = dt.isoformat()
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                         dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed), tz=timezone.utc)
                         pub_date = dt.isoformat()
                    else:
                        pub_date = entry.get('published') or entry.get('updated')

                    collected_data.append({
                        "source": "reuters",
                        "title": entry.get("title"),
                        "link": entry.get("link"),
                        "summary": entry.get("summary"),
                        "tags": [tag.term for tag in entry.get("tags", [])],
                        "published_at": pub_date,
                        "crawled_at": datetime.now(timezone.utc).isoformat()
                    })
            except Exception as e:
                self.logger.error(f"Failed to fetch RSS feed {feed_url}: {e}")
                
        return collected_data
