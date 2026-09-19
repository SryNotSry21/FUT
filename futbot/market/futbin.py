from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from futbot.market.models import PlayerCard

logger = logging.getLogger(__name__)

SITE = "https://www.futbin.com"


class FutbinClient:
    """Optional second source for name search / price comparison."""

    def __init__(self, game_year: int = 27, timeout: float = 15.0) -> None:
        self.game_year = game_year
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                "Referer": SITE,
            },
            timeout=timeout,
            follow_redirects=True,
        )
        self._last_request = 0.0

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search_players(self, query: str, limit: int = 5) -> list[PlayerCard]:
        query = query.strip()
        if not query:
            return []
        await self._throttle()
        try:
            response = await self._client.get(
                f"{SITE}/players/search",
                params={
                    "targetPage": "PLAYER_PAGE",
                    "query": query,
                    "year": str(self.game_year),
                    "evolutions": "false",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            logger.info("FUTBIN search unavailable")
            return []
        if not isinstance(payload, list):
            return []
        cards: list[PlayerCard] = []
        for item in payload[:limit]:
            card = _parse_futbin_search(item, self.game_year)
            if card:
                cards.append(card)
        return cards

    async def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < 0.5:
            import asyncio

            await asyncio.sleep(0.5 - elapsed)
        self._last_request = time.monotonic()


def _parse_futbin_search(item: dict[str, Any], year: int) -> PlayerCard | None:
    try:
        futbin_id = int(item["id"])
    except (KeyError, TypeError, ValueError):
        return None
    loc = (item.get("location") or {}).get("url") or f"/{year}/player/{futbin_id}"
    url = loc if str(loc).startswith("http") else f"{SITE}{loc}"
    rating_raw = (item.get("ratingSquare") or {}).get("rating") or 0
    image = (((item.get("playerImage") or {}).get("fixed") or {}).get("url") or {}).get(
        "image1x"
    ) or ""
    club = ((item.get("clubImage") or {}).get("fixed") or {}).get("name") or ""
    nation = ((item.get("nationImage") or {}).get("fixed") or {}).get("name") or ""
    return PlayerCard(
        ea_id=futbin_id,
        name=str(item.get("name") or "Unbekannt"),
        rating=int(rating_raw),
        position=str(item.get("position") or "?"),
        rarity=str(item.get("version") or "Normal"),
        club=str(club),
        nation=str(nation),
        league="",
        url=url,
        image_url=str(image),
        slug=str(loc),
    )
