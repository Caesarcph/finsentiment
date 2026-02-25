from __future__ import annotations

import hashlib
from collections import deque
from typing import Any, Deque, Dict, Iterable, Set


class Deduplicator:
    """Remove duplicate records using a rolling hash window."""

    def __init__(self, capacity: int = 10_000) -> None:
        self.capacity = max(1, capacity)
        self._seen: Set[str] = set()
        self._order: Deque[str] = deque()

    def _hash_item(self, item: Dict[str, Any]) -> str:
        """Build a deterministic hash from stable text fields."""
        base = "|".join(
            [
                str(item.get("source", "")),
                str(item.get("title", "")),
                str(item.get("link", "")),
                str(item.get("summary", "")),
            ]
        )
        return hashlib.md5(base.encode("utf-8")).hexdigest()

    def is_duplicate(self, item: Dict[str, Any]) -> bool:
        """Return True if the item hash exists in the current rolling window."""
        item_hash = self._hash_item(item)
        if item_hash in self._seen:
            return True

        if len(self._order) >= self.capacity:
            oldest = self._order.popleft()
            self._seen.discard(oldest)

        self._order.append(item_hash)
        self._seen.add(item_hash)
        return False

    def process(self, items: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Filter duplicates while preserving original input order."""
        return [item for item in items if not self.is_duplicate(item)]
