from abc import ABC, abstractmethod
from typing import List, Dict, Any
import time
import logging

class BaseCollector(ABC):
    """
    Abstract base class for all data collectors (news, social, official).
    Handles common logic like rate limiting and logging.
    """
    
    def __init__(self, name: str, source_type: str, refresh_interval: int = 300):
        self.name = name
        self.source_type = source_type
        self.refresh_interval = refresh_interval
        self.logger = logging.getLogger(f"finsentiment.collectors.{name}")
        self._last_collection_time = 0

    def collect(self) -> List[Dict[str, Any]]:
        """
        Public method to trigger collection. Handles rate limiting.
        """
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
        except Exception as e:
            self.logger.error(f"Error collecting from {self.name}: {str(e)}")
            return []

    @abstractmethod
    def _collect_implementation(self) -> List[Dict[str, Any]]:
        """
        Implementation specific logic to fetch data.
        Must return a list of dictionaries (normalized data).
        """
        pass
