from __future__ import annotations

import logging
from typing import Any

import httpx

from futbot.market.models import PlayerCard, PriceCatalog
from futbot.market.parse import parse_global_search_hit, parse_player_card
from futbot.market.prices import decode_platform_prices, merge_price_blobs

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.fut.gg/",
    "Origin": "https://www.fut.gg",
}

SITE = "https://www.fut.gg"
CDN_S3 = "https://s3.eu-west-2.amazonaws.com/game-assets.fut.gg"
CDN_R2 = "https://r2.fut.gg"


class FutGGClient:
    def __init__(self, game_year: int = 27, timeout: float = 20.0) -> None:
        self.game_year = game_year
        self._client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def search_players(self, query: str, limit: int = 8) -> list[PlayerCard]:
        query = query.strip()
        if not query:
            return []
        if query.isdigit():
            by_id = await self.get_player(int(query))
            return [by_id] if by_id else []

        listed = await self._get_json(
            f"{SITE}/api/fut/players/v2/{self.game_year}/",
            params={"name": query},
        )
        cards = [parse_player_card(item) for item in listed.get("data") or []]
        if cards:
            return cards[:limit]

        fallback = await self._get_json(
            f"{SITE}/api/fut/global-search/{self.game_year}/players/",
            params={"q": query},
        )
        results = ((fallback.get("data") or {}).get("results")) or []
        parsed: list[PlayerCard] = []
        for hit in results:
            card = parse_global_search_hit(hit)
            if card:
                parsed.append(card)
        return parsed[:limit]

    async def get_player(self, ea_id: int) -> PlayerCard | None:
        for url, params in (
            (f"{SITE}/api/fut/players/v2/hub/{ea_id}/", {"game": self.game_year}),
            (f"{SITE}/api/fut/{self.game_year}/player-items/", {"ids": ea_id}),
            (f"{SITE}/api/fut/players/v2/{self.game_year}/", {"eaId": ea_id}),
        ):
            try:
                payload = await self._get_json(url, params=params)
            except httpx.HTTPError:
                continue
            card = _first_matching_card(payload, ea_id)
            if card:
                return card
        return None

    async def momentum(self, hours: int = 24) -> list[PlayerCard]:
        payload = await self._get_json(
            f"{SITE}/api/fut/players/v2/momentum/{hours}/",
            params={"game": self.game_year},
        )
        return [parse_player_card(item) for item in payload.get("data") or []]

    async def fetch_catalog(self) -> PriceCatalog:
        index = await self._load_blob("player-prices-index")
        ps5_blob = await self._load_price_side("ps5", index)
        pc_blob = await self._load_price_side("pc", index)
        return PriceCatalog(
            game_year=self.game_year,
            ps5=decode_platform_prices(ps5_blob, "ps5"),
            pc=decode_platform_prices(pc_blob, "pc"),
        )

    async def _load_price_side(self, platform: str, index: dict[str, Any]) -> dict[str, Any]:
        dyn_name = f"player-prices-{'pc' if platform == 'pc' else 'ps5'}-dyn"
        static_name = f"player-prices-{'pc' if platform == 'pc' else 'ps5'}"
        try:
            dyn = await self._load_blob(dyn_name)
            merged = merge_price_blobs(index, dyn)
            if len(merged.get("p") or []) == reconstruct_len(index):
                return merged
        except Exception:
            logger.warning("Dyn price blob %s failed, falling back to static", dyn_name, exc_info=True)
        static = await self._load_blob(static_name)
        if "p" in static and "d" in static:
            return static
        return merge_price_blobs(index, static)

    async def _load_blob(self, name: str) -> dict[str, Any]:
        s3_url = f"{CDN_S3}/{self.game_year}/cdn-data/{name}.json"
        try:
            return await self._get_json(s3_url)
        except httpx.HTTPError:
            logger.info("S3 miss for %s, trying R2 manifest", name)
        manifest = await self._get_json(f"{CDN_R2}/{self.game_year}/manifest.json")
        version = manifest.get("_version", 1)
        digest = manifest.get(name)
        if not digest:
            raise LookupError(f"Manifest has no entry for {name}")
        return await self._get_json(
            f"{CDN_R2}/{self.game_year}/{name}.v{version}.{digest}.json"
        )

    async def _get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Unexpected JSON from {url}")
        return payload


def reconstruct_len(index: dict[str, Any]) -> int:
    return 1 + len(index.get("d") or [])


def _first_matching_card(payload: dict[str, Any], ea_id: int) -> PlayerCard | None:
    candidates: list[Any] = []
    if isinstance(payload.get("data"), list):
        candidates.extend(payload["data"])
    elif isinstance(payload.get("data"), dict):
        data = payload["data"]
        candidates.extend(data.get("playerItems") or data.get("items") or [])
        if "eaId" in data:
            candidates.append(data)
    for item in candidates:
        if isinstance(item, dict) and int(item.get("eaId") or 0) == ea_id:
            return parse_player_card(item)
        if isinstance(item, dict) and "player" in item:
            nested = item["player"]
            if isinstance(nested, dict) and int(nested.get("eaId") or 0) == ea_id:
                return parse_player_card(nested)
    return None
