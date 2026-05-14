import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CachedElement:
    element_id: str
    wrapper: Any
    metadata: Dict[str, Any]
    created_at: float


class ElementCache:
    def __init__(self, ttl_seconds: int = 600) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: Dict[str, CachedElement] = {}

    def put(self, element_id: str, wrapper: Any, metadata: Dict[str, Any]) -> None:
        self._items[element_id] = CachedElement(
            element_id=element_id,
            wrapper=wrapper,
            metadata=metadata,
            created_at=time.time(),
        )

    def get(self, element_id: str) -> Optional[CachedElement]:
        item = self._items.get(element_id)
        if item is None:
            return None
        if time.time() - item.created_at > self.ttl_seconds:
            self._items.pop(element_id, None)
            return None
        return item

    def clear(self) -> None:
        self._items.clear()
