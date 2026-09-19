from __future__ import annotations

import asyncio
import time

from futbot.market.compare import is_significant_move, rank_movers
from futbot.market.futbin import FutbinClient
from futbot.market.futgg import FutGGClient
from futbot.market.models import PlayerCard, PlayerQuote, Platform, PriceCatalog, PriceMove


class MarketService:
    def __init__(self, game_year: int = 27, cache_ttl: float = 60.0) -> None:
        self.game_year = game_year
        self.cache_ttl = cache_ttl
        self.futgg = FutGGClient(game_year=game_year)
        self.futbin = FutbinClient(game_year=game_year)
        self._catalog: PriceCatalog | None = None
        self._catalog_loaded_at = 0.0
        self._players: dict[int, PlayerCard] = {}
        self._lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self.futgg.aclose()
        await self.futbin.aclose()

    async def search(self, query: str, limit: int = 8) -> list[PlayerCard]:
        cards = await self.futgg.search_players(query, limit=limit)
        for card in cards:
            self._players[card.ea_id] = card
        return cards

    async def player_by_id(self, ea_id: int) -> PlayerCard | None:
        cached = self._players.get(ea_id)
        if cached:
            return cached
        card = await self.futgg.get_player(ea_id)
        if card:
            self._players[ea_id] = card
        return card

    async def resolve(self, query: str) -> PlayerCard | None:
        query = query.strip()
        if query.isdigit():
            return await self.player_by_id(int(query))
        matches = await self.search(query, limit=8)
        if not matches:
            return None
        lowered = query.lower()
        exact = [card for card in matches if card.name.lower() == lowered]
        if len(exact) == 1:
            return exact[0]
        return matches[0] if len(matches) == 1 else None

    async def catalog(self, force: bool = False) -> PriceCatalog:
        async with self._lock:
            now = time.monotonic()
            if (
                not force
                and self._catalog is not None
                and now - self._catalog_loaded_at < self.cache_ttl
            ):
                return self._catalog
            self._catalog = await self.futgg.fetch_catalog()
            self._catalog_loaded_at = now
            return self._catalog

    async def quote(self, query: str) -> PlayerQuote | None:
        player = await self.resolve(query)
        if player is None:
            matches = await self.search(query, limit=1)
            player = matches[0] if matches else None
        if player is None:
            return None
        return (await self.catalog()).quote(player)

    async def quote_player(self, player: PlayerCard) -> PlayerQuote:
        return (await self.catalog()).quote(player)

    async def compare_players(self, left_query: str, right_query: str) -> tuple[PlayerQuote, PlayerQuote] | None:
        left_matches, right_matches = await asyncio.gather(
            self.search(left_query, limit=1),
            self.search(right_query, limit=1),
        )
        if not left_matches or not right_matches:
            return None
        catalog = await self.catalog()
        return catalog.quote(left_matches[0]), catalog.quote(right_matches[0])

    async def movers(self, hours: int = 24) -> list[PlayerCard]:
        cards = await self.futgg.momentum(hours=hours)
        catalog = await self.catalog()
        enriched: list[PlayerCard] = []
        for card in cards:
            quote = catalog.quote(card)
            enriched.append(
                PlayerCard(
                    ea_id=card.ea_id,
                    name=card.name,
                    rating=card.rating,
                    position=card.position,
                    rarity=card.rarity,
                    club=card.club,
                    nation=card.nation,
                    league=card.league,
                    url=card.url,
                    image_url=card.image_url,
                    slug=card.slug,
                    base_player_ea_id=card.base_player_ea_id,
                    quality=card.quality,
                    momentum_pct=card.momentum_pct,
                    listed_price=quote.ps5.price or card.listed_price,
                )
            )
        return enriched

    async def scan_snapshot_moves(
        self,
        previous: dict[int, int],
        platform: Platform,
        threshold_pct: float,
        min_price: int,
        limit: int = 8,
    ) -> tuple[list[PriceMove], list[PriceMove]]:
        catalog = await self.catalog()
        current = catalog.snapshot(platform)
        risers, fallers = rank_movers(
            previous, current, threshold_pct=threshold_pct, min_price=min_price, limit=limit
        )
        return (
            [self._to_move(ea_id, old, new, pct, platform) for ea_id, old, new, pct in risers],
            [self._to_move(ea_id, old, new, pct, platform) for ea_id, old, new, pct in fallers],
        )

    def watch_move(
        self,
        ea_id: int,
        platform: Platform,
        old_price: int | None,
        new_price: int | None,
        threshold_pct: float,
        threshold_coins: int | None,
        player: PlayerCard | None = None,
    ) -> PriceMove | None:
        triggered, delta, pct = is_significant_move(
            old_price, new_price, threshold_pct, threshold_coins
        )
        if not triggered or old_price is None or new_price is None:
            return None
        return PriceMove(
            ea_id=ea_id,
            platform=platform,
            old_price=old_price,
            new_price=new_price,
            delta=delta,
            pct=pct,
            player=player,
        )

    def _to_move(
        self, ea_id: int, old: int, new: int, pct: float, platform: Platform
    ) -> PriceMove:
        return PriceMove(
            ea_id=ea_id,
            platform=platform,
            old_price=old,
            new_price=new,
            delta=new - old,
            pct=pct,
        )
