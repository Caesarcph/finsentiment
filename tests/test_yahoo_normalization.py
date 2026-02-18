from finsentiment.collectors.news.yahoo_finance import YahooFinanceCollector


class _FakeTicker:
    def __init__(self, _symbol: str):
        self.news = [
            {
                "content": {
                    "title": "Apple momentum stays strong",
                    "summary": "Analysts lifted guidance.",
                    "pubDate": 1704067200,
                    "canonicalUrl": {"url": "https://example.com/aapl"},
                    "provider": {"displayName": "Yahoo Finance"},
                }
            }
        ]


def test_yahoo_collector_normalizes_output(monkeypatch):
    monkeypatch.setattr("finsentiment.collectors.news.yahoo_finance.yf.Ticker", _FakeTicker)

    collector = YahooFinanceCollector(tickers=["AAPL"], refresh_interval=0)
    data = collector.collect()

    assert len(data) == 1
    item = data[0]
    assert item["summary"] == "Analysts lifted guidance."
    assert item["published_at"] == "2024-01-01T00:00:00+00:00"
    assert item["timestamp"] == item["published_at"]
