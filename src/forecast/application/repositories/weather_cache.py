from typing import Protocol, TypeVar

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
