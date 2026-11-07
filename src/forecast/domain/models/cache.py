"""Generic cache record with expiry metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CacheEntry[T]:
    """A cache record holding a deserialized value with expiry metadata."""

    data: T
    fetched_at: datetime
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        return datetime.now(self.expires_at.tzinfo) >= self.expires_at
