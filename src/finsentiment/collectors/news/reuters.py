from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base_collector import BaseCollector

class ReutersCollector(BaseCollector):
    """
    Collector for Reuters News via RSS feeds.
    """
    DEFAULT_FEEDS = [
        "http://feeds.reuters.com/reuters/businessNews",
        "http://feeds.reuters.com/reuters/technologyNews",
        "http://feeds.reuters.com/reuters/topNews"
    ]

    def __init__(self, feeds: Optional[List[str]] = None, refresh_interval: int = 300) -> None:
        super().__init__(name="reuters", source_type="news", refresh_interval=refresh_interval)
        self.feeds = feeds or self.DEFAULT_FEEDS

    def _collect_implementation(self) -> List[Dict[str, Any]]:
        """
        Implementation to collect data from Reuters RSS feeds.
        Uses a simple HTTP GET request and basic XML parsing to avoid dependency on feedparser.
        """
        collected_data = []
        try:
            import urllib.request
            import xml.etree.ElementTree as ET
        except ImportError:
            self.logger.error("urllib or xml modules not available")
            return []
            
        for feed_url in self.feeds:
            try:
                self.logger.debug(f"Fetching feed: {feed_url}")
                response = urllib.request.urlopen(feed_url)
                content = response.read().decode('utf-8')
                
                root = ET.fromstring(content)
                items = root.findall('.//item')
                
                for item in items:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    desc_elem = item.find('description')
                    pubdate_elem = item.find('pubDate')
                    
                    pub_date = None
                    if pubdate_elem is not None and pubdate_elem.text:
                        # Parse RSS pubDate format to ISO
                        try:
                            dt = datetime.strptime(pubdate_elem.text, '%a, %d %b %Y %H:%M:%S %z')
                            pub_date = dt.isoformat()
                        except ValueError:
                            pub_date = pubdate_elem.text
                    
                    collected_data.append({
                        "source": "reuters",
                        "title": title_elem.text if title_elem is not None else "",
                        "link": link_elem.text if link_elem is not None else "",
                        "summary": desc_elem.text if desc_elem is not None else "",
                        "tags": [],
                        "published_at": pub_date,
                        "crawled_at": datetime.now(timezone.utc).isoformat()
                    })
            except Exception as e:
                self.logger.error(f"Failed to fetch RSS feed {feed_url}: {e}")
                
        return collected_data
