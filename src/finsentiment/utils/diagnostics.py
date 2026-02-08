import argparse
import logging
import sys
import shutil
import socket
from typing import List
from ..collectors.news.reuters import ReutersCollector
from ..collectors.news.yahoo_finance import YahooFinanceCollector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_system_health():
    """Checks basic system health metrics (disk space, connectivity)."""
    logger.info("Checking system health...")
    
    # 1. Disk Space
    total, used, free = shutil.disk_usage("/")
    free_gb = free // (2**30)
    logger.info(f"Disk Space: {free_gb} GB free")
    if free_gb < 5:
        logger.warning("Low disk space! (< 5GB)")

    # 2. Connectivity
    try:
        # Connect to 8.8.8.8 (Google DNS) on port 53 (DNS)
        # This is a low-level check that doesn't require HTTP
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        logger.info("Internet Connectivity: OK")
    except OSError:
        logger.error("Internet Connectivity: FAILED")

def test_reuters():
    logger.info("Testing ReutersCollector...")
    collector = ReutersCollector()
    data = collector.collect()
    logger.info(f"Collected {len(data)} items from Reuters.")
    for item in data[:3]:  # Show first 3
        print(f"  - [{item.get('published_at')}] {item.get('title')}")

def test_yahoo(tickers: List[str]):
    logger.info(f"Testing YahooFinanceCollector for {tickers}...")
    collector = YahooFinanceCollector(tickers=tickers)
    data = collector.collect()
    logger.info(f"Collected {len(data)} items from Yahoo Finance.")
    for item in data[:3]:
        print(f"  - [{item.get('timestamp')}] {item.get('ticker')}: {item.get('title')}")

def main():
    parser = argparse.ArgumentParser(description="FinSentiment Diagnostics Tool")
    parser.add_argument("--reuters", action="store_true", help="Test Reuters Collector")
    parser.add_argument("--yahoo", nargs="+", help="Test Yahoo Collector with specific tickers (e.g. AAPL MSFT)")
    parser.add_argument("--health", action="store_true", help="Check system health (disk, connectivity)")
    
    args = parser.parse_args()

    if not (args.reuters or args.yahoo or args.health):
        parser.print_help()
        sys.exit(1)

    if args.health:
        check_system_health()

    if args.reuters:
        test_reuters()
        
    if args.yahoo:
        test_yahoo(args.yahoo)

if __name__ == "__main__":
    main()
