"""News collectors.

Some collectors rely on optional third-party dependencies (e.g. ``feedparser``).
To keep the package importable in minimal environments (and to avoid import-time
failures in unrelated code paths), we guard those imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from .yahoo_finance import YahooFinanceCollector

# Optional collectors
try:
    from .reuters import ReutersCollector  # requires: feedparser
except ModuleNotFoundError:  # pragma: no cover
    ReutersCollector = None  # type: ignore[assignment]

try:
    from .seeking_alpha import SeekingAlphaCollector
except ModuleNotFoundError:  # pragma: no cover
    SeekingAlphaCollector = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover
    # For type-checkers: expose symbols when deps are installed.
    from .reuters import ReutersCollector as _ReutersCollector
    from .seeking_alpha import SeekingAlphaCollector as _SeekingAlphaCollector


__all__: List[str] = ["YahooFinanceCollector"]
if ReutersCollector is not None:
    __all__.append("ReutersCollector")
if SeekingAlphaCollector is not None:
    __all__.append("SeekingAlphaCollector")
