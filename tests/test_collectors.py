import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from finsentiment.collectors.news.yahoo_finance import YahooFinanceCollector

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_yahoo_collector():
    print("Testing YahooFinanceCollector...")
    # Test with a common ticker
    collector = YahooFinanceCollector(tickers=["AAPL"], refresh_interval=0)
    data = collector.collect()
    
    print(f"Collected {len(data)} items")
    if data:
        print("Sample item:", data[0])
    
    assert isinstance(data, list)

if __name__ == "__main__":
    test_yahoo_collector()
