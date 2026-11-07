from typing import Protocol, TypeVar
from datetime import datetime
from dataclasses import dataclass

T = TypeVar("T")


class WeatherCache(Protocol):
    async def get(self, key: str): ...

    async def set(
        self,
        key: str,
        value: object,
        ttl_seconds: int,
    ) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def clear(self) -> None: ...


@dataclass(frozen=True, slots=True)
class CacheEntry:
    data: object
    fetched_at: datetime
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        return datetime.now(self.expires_at.tzinfo) >= self.expires_at
