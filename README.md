# 📊 FinSentiment

> Financial news sentiment engine (early prototype) — multi-source news collection with a simple sentiment score; LLM/FinBERT analysis and MT5 signal integration are planned.

[![CI](https://github.com/Caesarcph/finsentiment/actions/workflows/ci.yml/badge.svg)](https://github.com/Caesarcph/finsentiment/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Status:** Early-stage prototype. Implemented today: news collectors for Yahoo Finance (via `yfinance`), Reuters RSS and Seeking Alpha RSS; a YAML-configured `SentimentEngine` with a background polling loop; a keyword-based sentiment score per ticker; a rolling-hash `Deduplicator`; and a diagnostics CLI. Not implemented yet: FinBERT/LLM analysis, social and official sources, REST API, MT5 bridge, webhooks, database storage, Docker — see the Development Roadmap section below.

## 🎯 Overview

FinSentiment aims to be a sentiment analysis pipeline that:

1. **Collects** financial news (implemented for 3 news sources) and social media (planned)
2. **Analyzes** sentiment — currently a keyword heuristic; a FinBERT + LLM ensemble is planned
3. **Outputs** trading signals compatible with MT5 and other platforms (planned)

Intended as a companion for the [llm-rl-mt5-trading](https://github.com/Caesarcph/llm-rl-mt5-trading) system.

## ✨ Key Features

### Implemented
- 📰 **News collectors**: Yahoo Finance (per-ticker news via `yfinance`), Reuters (RSS, stdlib XML parsing), Seeking Alpha (Market Currents RSS via `feedparser`)
- ⏱️ **Collector framework**: `BaseCollector` with per-source refresh-interval rate limiting and error handling
- 🔁 **Background collection**: `SentimentEngine.start()` polls all collectors in a daemon thread and keeps the last 100 items per source in memory
- 🧮 **Heuristic sentiment**: `get_sentiment(ticker)` matches items by ticker/text and scores them with small positive/negative keyword lists (score in [-1, 1], label BULLISH/BEARISH/NEUTRAL)
- 🧹 **Deduplication**: `Deduplicator` (rolling MD5 window over source/title/link/summary) — available as a standalone processor, not yet wired into the engine
- 🩺 **Diagnostics CLI**: disk/connectivity health check and collector smoke tests

> Note: the default Reuters feed URLs are the legacy `feeds.reuters.com` RSS endpoints, which may no longer be served; override them in `sources.yaml` if needed. All collectors return an empty list on network errors.

### Planned

#### Data Collection
- 📰 **More news sources**: Bloomberg
- 🐦 **Social Media**: Twitter/X financial accounts, Reddit (r/wallstreetbets, r/stocks), StockTwits — config stubs exist (disabled), no collectors yet
- 📢 **Official Sources**: SEC filings, Fed announcements, earnings calls
- 🌐 **Multi-language**: English and Chinese (Sina Finance, Eastmoney)

#### Analysis Engine
- 🧠 **Hybrid Model**: FinBERT base + GPT-4/Claude for nuance detection
- 📈 **Entity Recognition**: Company, ticker, sector extraction
- ⏰ **Temporal Decay**: Recent news weighted higher
- 🎯 **Aspect Sentiment**: Bullish on earnings ≠ bullish on management

#### Output & Integration
- 📡 **REST API**: JSON endpoints for any trading system
- 🔌 **MT5 Bridge**: Direct signal injection to MetaTrader 5
- 📊 **Webhooks**: Slack, Discord, Telegram alerts
- 💾 **Database**: PostgreSQL storage with TimescaleDB

## 🏗️ Architecture

Current tree:

```
finsentiment/
├── src/finsentiment/
│   ├── __init__.py                 # exports SentimentEngine, SentimentResult
│   ├── engine.py                   # SentimentEngine: config loading, polling loop, heuristic scoring
│   ├── collectors/
│   │   ├── base_collector.py       # Abstract collector interface + rate limiting
│   │   └── news/
│   │       ├── reuters.py          # Reuters RSS
│   │       ├── seeking_alpha.py    # Seeking Alpha RSS (feedparser)
│   │       └── yahoo_finance.py    # Yahoo Finance news (yfinance)
│   ├── processors/
│   │   └── deduplicator.py         # Near-duplicate detection (rolling hash window)
│   ├── utils/
│   │   └── diagnostics.py          # Health check + collector smoke-test CLI
│   └── config/
│       └── sources.yaml            # Data source configuration
├── tests/
│   ├── test_collectors.py          # Yahoo collector smoke test (network; tolerates failure)
│   ├── test_deduplicator.py
│   └── test_yahoo_normalization.py
├── pytest.ini
└── requirements.txt
```

Planned modules (not yet created): `collectors/news/bloomberg.py`, `collectors/news/sina_finance.py`, `collectors/social/` (twitter, reddit, stocktwits), `collectors/official/` (sec_edgar, fed_releases), `processors/cleaner.py`, `processors/entity_extractor.py`, `analyzers/` (finbert, llm, ensemble, aspect), `signals/` (aggregator, decay, generator), `integrations/` (mt5_bridge, webhook, database), `api/` (FastAPI app), `config/models.yaml`, `config/signals.yaml`.

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Caesarcph/finsentiment.git
cd finsentiment

# Install dependencies (yfinance, feedparser, PyYAML, pytest)
pip install -r requirements.txt

# The package is not pip-installable yet; put src/ on the path
export PYTHONPATH=src   # Windows PowerShell: $env:PYTHONPATH="src"
```

### Configuration

Sources are configured in `src/finsentiment/config/sources.yaml` (excerpt):

```yaml
news:
  reuters:
    enabled: true
    refresh_interval: 300  # seconds
    feeds:
      - "http://feeds.reuters.com/reuters/businessNews"

  yahoo_finance:
    enabled: true
    refresh_interval: 300
    tickers: ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMD"]

  seeking_alpha:
    enabled: true
    refresh_interval: 300
    feed_url: "https://seekingalpha.com/market_currents.xml"

social:            # placeholders only — no social collectors are implemented yet
  twitter:
    enabled: false
  reddit:
    enabled: false
```

### Basic Usage

```python
from finsentiment import SentimentEngine

# Initialize engine (reads sources.yaml from this directory)
engine = SentimentEngine.from_config("src/finsentiment/config")

# Start background collection (polls collectors every 30 s, in-memory only)
engine.start()

# Get current sentiment for a ticker (keyword heuristic)
sentiment = engine.get_sentiment("AAPL")
print(f"AAPL Sentiment: {sentiment.score:.2f} ({sentiment.label})")
print(f"Based on {sentiment.source_count} matching items")
print(f"Factors: {sentiment.top_factors}")
# e.g. Factors: ['positive_hits=3', 'negative_hits=1', 'matched_items=5']

# Inspect raw collected items
print(engine.get_collected_data("yahoo_finance"))

engine.stop()
```

If nothing has been collected yet (or all sources fail), `get_sentiment` returns a NEUTRAL result with `source_count=0`.

### Deduplication

```python
from finsentiment.processors import Deduplicator

unique_items = Deduplicator(capacity=10_000).process(items)
```

### Diagnostics

```bash
python -m finsentiment.utils.diagnostics --health
python -m finsentiment.utils.diagnostics --reuters
python -m finsentiment.utils.diagnostics --yahoo AAPL MSFT
```

### Running Tests

```bash
pytest
```

## 🔭 Planned Design

The sections below describe the target design. None of this is implemented yet.

### REST API (planned)

```bash
# Planned: FastAPI server
# GET /api/v1/sentiment/AAPL
{
  "ticker": "AAPL",
  "sentiment_score": 0.72,
  "sentiment_label": "BULLISH",
  "confidence": 0.89,
  "source_breakdown": {
    "news": {"score": 0.68, "count": 23},
    "social": {"score": 0.75, "count": 156}
  },
  "aspects": {"earnings": 0.82, "product": 0.71, "management": 0.65},
  "signal": {"action": "BUY", "strength": 0.65, "timeframe": "4H"},
  "updated_at": "2024-12-15T14:30:00Z"
}
# Planned: WebSocket real-time updates at /ws/sentiment/AAPL
```

### Signal Generation Logic (planned)

```python
# Sketch of the planned signal generation algorithm (pseudocode)
def generate_signal(sentiment_data):
    # 1. Aggregate with temporal decay
    weighted_score = 0
    total_weight = 0

    for source in sentiment_data.sources:
        age_hours = (now - source.timestamp).hours
        weight = source.reliability * exp(-0.1 * age_hours)
        weighted_score += source.sentiment * weight
        total_weight += weight

    final_score = weighted_score / total_weight

    # 2. Apply confidence threshold
    if sentiment_data.confidence < 0.6:
        return Signal(action="HOLD", reason="Low confidence")

    # 3. Generate signal
    if final_score > 0.6:
        return Signal(action="BUY", strength=min((final_score - 0.5) * 2, 1.0))
    elif final_score < 0.4:
        return Signal(action="SELL", strength=min((0.5 - final_score) * 2, 1.0))
    else:
        return Signal(action="HOLD", reason="Neutral sentiment")
```

### Model Configuration (planned)

```yaml
# Planned: config/models.yaml
finbert:
  model: "ProsusAI/finbert"
  device: "cuda"  # or "cpu"
  batch_size: 32

llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  temperature: 0.1
  use_for:
    - nuance_detection      # "despite" clauses, sarcasm
    - entity_disambiguation # "Apple" company vs fruit
    - aspect_extraction     # What specifically is positive?

ensemble:
  weights:
    finbert: 0.6
    llm: 0.4
  min_agreement: 0.7  # Require models to agree
```

## 🛠️ Development Roadmap

### Phase 1: Data Collection
- [x] News collector framework with rate limiting (refresh-interval based)
- [x] Reuters, Yahoo Finance, Seeking Alpha integrations
- [ ] Twitter/X and Reddit collectors
- [ ] Deduplication pipeline (`Deduplicator` exists; not yet wired into the engine)

### Phase 2: Analysis Engine
- [ ] FinBERT integration with GPU support
- [ ] LLM analyzer for edge cases
- [ ] Entity extraction (tickers, companies)
- [ ] Aspect-based sentiment analysis

### Phase 3: Signal Generation
- [ ] Multi-source aggregation with decay
- [ ] Confidence scoring (only a basic heuristic confidence today)
- [ ] Signal generation rules
- [ ] Backtesting integration

### Phase 4: Integrations
- [ ] REST API with FastAPI
- [ ] WebSocket real-time updates
- [ ] MT5 bridge connector
- [ ] Webhook notifications

### Phase 5: Chinese Language Support
- [ ] Sina Finance collector
- [ ] Eastmoney collector
- [ ] Chinese FinBERT model
- [ ] Translation pipeline for cross-reference

### Phase 6: Production Hardening
- [ ] Packaging (`pyproject.toml`)
- [ ] Docker containerization
- [ ] Kubernetes deployment configs
- [ ] Monitoring and alerting
- [ ] Documentation and examples

## 📈 Performance Metrics

No accuracy, latency or throughput benchmarks have been run yet. Evaluation against human-labelled data is planned once the FinBERT/LLM analyzers exist.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Priority Areas
1. Additional news source connectors
2. Model-based sentiment analysis (FinBERT / LLM)
3. Improved Chinese language models
4. More trading platform integrations

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Not financial advice. Always do your own research before trading.

---

**Star ⭐ this repo if you find it useful!**
