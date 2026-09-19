from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Platform = Literal["ps5", "pc"]
WatchPlatform = Literal["ps5", "pc", "beide"]

STATUS_ON_MARKET = 0
STATUS_SBC = 1
STATUS_OBJECTIVE = 2
STATUS_EXTINCT = 0  # extinct is status 0 with a null price
STATUS_TOKEN = 4


@dataclass(frozen=True)
class PlayerCard:
    ea_id: int
    name: str
    rating: int
    position: str
    rarity: str
    club: str
    nation: str
    league: str
    url: str
    image_url: str
    slug: str = ""
    base_player_ea_id: int | None = None
    quality: str = ""
    momentum_pct: float | None = None
    listed_price: int | None = None

    @property
    def label(self) -> str:
        version = self.rarity if self.rarity else "Karte"
        return f"{self.name} · {self.rating} {self.position} · {version}"


@dataclass(frozen=True)
class PlatformPrice:
    platform: Platform
    price: int | None
    is_sbc: bool = False
    is_objective: bool = False
    is_extinct: bool = False

    @property
    def on_market(self) -> bool:
        return self.price is not None and not self.is_sbc and not self.is_objective


@dataclass(frozen=True)
class PlayerQuote:
    player: PlayerCard
    ps5: PlatformPrice
    pc: PlatformPrice

    def price_for(self, platform: Platform) -> int | None:
        return self.ps5.price if platform == "ps5" else self.pc.price


@dataclass(frozen=True)
class PriceMove:
    ea_id: int
    platform: Platform
    old_price: int
    new_price: int
    delta: int
    pct: float
    player: PlayerCard | None = None

    @property
    def is_drop(self) -> bool:
        return self.delta < 0


@dataclass
class PriceCatalog:
    """Decoded FUT.GG price blobs for both platforms."""

    game_year: int
    ps5: dict[int, PlatformPrice] = field(default_factory=dict)
    pc: dict[int, PlatformPrice] = field(default_factory=dict)

    def quote(self, player: PlayerCard) -> PlayerQuote:
        fallback = PlatformPrice(platform="ps5", price=None, is_extinct=True)
        pc_fallback = PlatformPrice(platform="pc", price=None, is_extinct=True)
        return PlayerQuote(
            player=player,
            ps5=self.ps5.get(player.ea_id, fallback),
            pc=self.pc.get(player.ea_id, pc_fallback),
        )

    def snapshot(self, platform: Platform) -> dict[int, int]:
        source = self.ps5 if platform == "ps5" else self.pc
        return {
            ea_id: price.price
            for ea_id, price in source.items()
            if price.price is not None and price.price > 0
        }
