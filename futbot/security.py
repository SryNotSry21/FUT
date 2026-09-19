from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


def can_manage_watch(*, actor_id: int, owner_id: int, is_guild_manager: bool) -> bool:
    """Owner or a member with Manage Server may change/delete a watch."""
    return is_guild_manager or actor_id == owner_id


def can_post_manual_alert(*, actor_id: int, owner_id: int | None, is_guild_manager: bool) -> bool:
    """Manual /alert into the shared channel requires a matching watch or Manage Server."""
    if is_guild_manager:
        return True
    return owner_id is not None and actor_id == owner_id


class CooldownMap:
    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        self._hits: dict[int, float] = {}

    def remaining(self, key: int) -> float:
        last = self._hits.get(key, 0.0)
        wait = self.seconds - (time.monotonic() - last)
        return wait if wait > 0 else 0.0

    def hit(self, key: int) -> bool:
        if self.remaining(key) > 0:
            return False
        self._hits[key] = time.monotonic()
        return True


class TtlCache:
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[float, object]] = {}

    def get(self, key: str):
        packed = self._items.get(key)
        if packed is None:
            return None
        stored_at, value = packed
        if time.monotonic() - stored_at >= self.ttl_seconds:
            self._items.pop(key, None)
            return None
        return value

    def set(self, key: str, value: object) -> None:
        self._items[key] = (time.monotonic(), value)


async def cached_call(cache: TtlCache, key: str, factory: Callable[[], Awaitable[T]]) -> T:
    cached = cache.get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    value = await factory()
    cache.set(key, value)
    return value
