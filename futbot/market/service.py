from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence
from dataclasses import replace

from futbot.market.compare import (
    bargains_from_drops,
    crossed_below_target,
    is_significant_move,
    percent_change,
    rank_movers,
    rank_platform_bargains,
)
from futbot.market.futgg import FutGGClient
from futbot.market.models import Bargain, PlayerCard, PlayerQuote, Platform, PriceCatalog, PriceMove


class MarketService:
    def __init__(self, game_year: int = 27, cache_ttl: float = 60.0) -> None:
        self.game_year = game_year
        self.cache_ttl = cache_ttl
        self.futgg = FutGGClient(game_year=game_year)
        self._catalog: PriceCatalog | None = None
        self._catalog_loaded_at = 0.0
        self._players: dict[int, PlayerCard] = {}
        self._lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self.futgg.aclose()

    async def search(self, query: str, limit: int = 8) -> list[PlayerCard]:
        cards = await self.futgg.search_players(query, limit=limit)
        for card in cards:
            self._players[card.ea_id] = card
        return cards

    async def player_by_id(self, ea_id: int) -> PlayerCard | None:
        found = await self.players_by_ids([ea_id])
        return found.get(int(ea_id))

    async def players_by_ids(self, ea_ids: Sequence[int]) -> dict[int, PlayerCard]:
        unique = list(dict.fromkeys(int(ea_id) for ea_id in ea_ids))
        result: dict[int, PlayerCard] = {}
        missing: list[int] = []
        for ea_id in unique:
            cached = self._players.get(ea_id)
            if cached:
                result[ea_id] = cached
            else:
                missing.append(ea_id)
        if missing:
            fetched = await self.futgg.get_players(missing)
            for ea_id, card in fetched.items():
                self._players[ea_id] = card
                result[ea_id] = card
        return result

    async def hydrate_moves(self, moves: list[PriceMove]) -> None:
        missing_ids = [move.ea_id for move in moves if move.player is None]
        if not missing_ids:
            return
        cards = await self.players_by_ids(missing_ids)
        for index, move in enumerate(moves):
            card = move.player or cards.get(move.ea_id)
            if card is not None and move.player is None:
                moves[index] = replace(move, player=card)

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
                    listed_price=card.listed_price or quote.ps5.price,
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
        ranked_up, ranked_down = rank_movers(
            previous, current, threshold_pct=threshold_pct, min_price=min_price, limit=limit
        )
        risers = [self._to_move(ea_id, old, new, pct, platform) for ea_id, old, new, pct in ranked_up]
        fallers = [self._to_move(ea_id, old, new, pct, platform) for ea_id, old, new, pct in ranked_down]
        await self.players_by_ids([move.ea_id for move in risers + fallers])
        await self.hydrate_moves(risers)
        await self.hydrate_moves(fallers)
        return risers, fallers

    async def hydrate_bargains(self, bargains: list[Bargain]) -> None:
        missing_ids = [deal.ea_id for deal in bargains if deal.player is None]
        if not missing_ids:
            return
        cards = await self.players_by_ids(missing_ids)
        for index, deal in enumerate(bargains):
            card = deal.player or cards.get(deal.ea_id)
            if card is not None and deal.player is None:
                bargains[index] = replace(deal, player=card)

    async def platform_bargains(
        self,
        min_price: int = 15_000,
        min_pct: float = 20.0,
        limit: int = 8,
    ) -> list[Bargain]:
        catalog = await self.catalog()
        deals = rank_platform_bargains(
            catalog.snapshot("ps5"),
            catalog.snapshot("pc"),
            min_price=min_price,
            min_pct=min_pct,
            limit=limit,
        )
        await self.hydrate_bargains(deals)
        return deals

    async def below_recent_bargains(
        self,
        previous: dict[int, int],
        platform: Platform,
        min_price: int = 15_000,
        min_pct: float = 15.0,
        limit: int = 8,
    ) -> list[Bargain]:
        catalog = await self.catalog()
        current = catalog.snapshot(platform)
        _risers, fallers = rank_movers(
            previous, current, threshold_pct=min_pct, min_price=min_price, limit=limit
        )
        deals = bargains_from_drops(fallers, platform)
        await self.hydrate_bargains(deals)
        return deals

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

    def watch_below_move(
        self,
        ea_id: int,
        platform: Platform,
        old_price: int | None,
        new_price: int | None,
        target_below: int | None,
        player: PlayerCard | None = None,
    ) -> PriceMove | None:
        if not crossed_below_target(old_price, new_price, target_below):
            return None
        assert old_price is not None and new_price is not None and target_below is not None
        return PriceMove(
            ea_id=ea_id,
            platform=platform,
            old_price=old_price,
            new_price=new_price,
            delta=new_price - old_price,
            pct=percent_change(old_price, new_price),
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
            player=self._players.get(ea_id),
        )
