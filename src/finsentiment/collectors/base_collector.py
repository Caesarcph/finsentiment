import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseCollector(ABC):
    """Abstract base class for all data collectors (news, social, official)."""

    def __init__(self, name: str, source_type: str, refresh_interval: int = 300) -> None:
        self.name = name
        self.source_type = source_type
        self.refresh_interval = refresh_interval
        self.logger = logging.getLogger(f"finsentiment.collectors.{name}")
        self._last_collection_time: float = 0.0

    def collect(self) -> List[Dict[str, Any]]:
        """Trigger collection with basic rate limiting and error handling."""
        now = time.time()
        if now - self._last_collection_time < self.refresh_interval:
            self.logger.debug(f"Skipping collection for {self.name}: rate limited")
            return []

        try:
            self.logger.info(f"Starting collection for {self.name}")
            data = self._collect_implementation()
            self._last_collection_time = time.time()
            self.logger.info(f"Collected {len(data)} items from {self.name}")
            return data
        except Exception as exc:
            self.logger.error(f"Error collecting from {self.name}: {exc}")
            return []

    @abstractmethod
    def _collect_implementation(self) -> List[Dict[str, Any]]:
        """Fetch and normalize records for this source."""
        raise NotImplementedError
