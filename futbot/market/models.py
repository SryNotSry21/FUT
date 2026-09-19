from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

Platform = Literal["ps5", "pc"]
WatchPlatform = Literal["ps5", "pc", "beide"]
BargainReason = Literal["plattform", "markt", "vorjahr", "beides", "tief"]

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


@dataclass(frozen=True)
class PriceStats:
    """Recent PlayStation BIN range for one card (low + average)."""

    ea_id: int
    last: int
    low: int
    average: int
    samples: int


@dataclass(frozen=True)
class Bargain:
    """Card priced below a fair reference (recent average BIN, optionally at the low)."""

    ea_id: int
    cheap_platform: Platform
    cheap_price: int
    fair_platform: Platform
    fair_price: int
    pct_below: float
    reason: BargainReason
    player: PlayerCard | None = None
    scan_fair: int | None = None
    year_fair: int | None = None
    avg_price: int | None = None
    low_price: int | None = None
    at_low: bool = False

    @property
    def delta(self) -> int:
        return self.cheap_price - self.fair_price


def aggregate_price_stats(
    snapshots: Sequence[Mapping[int, int]],
    *,
    min_price: int = 0,
    max_price: int = 12_000_000,
) -> dict[int, PriceStats]:
    """Build last/low/average from chronological PlayStation snapshots."""
    sums: dict[int, int] = {}
    counts: dict[int, int] = {}
    lows: dict[int, int] = {}
    lasts: dict[int, int] = {}
    for snapshot in snapshots:
        for raw_id, raw_price in snapshot.items():
            ea_id = int(raw_id)
            price = int(raw_price)
            if price < min_price or price > max_price:
                continue
            sums[ea_id] = sums.get(ea_id, 0) + price
            counts[ea_id] = counts.get(ea_id, 0) + 1
            lows[ea_id] = min(lows.get(ea_id, price), price)
            lasts[ea_id] = price
    return {
        ea_id: PriceStats(
            ea_id=ea_id,
            last=lasts[ea_id],
            low=lows[ea_id],
            average=sums[ea_id] // counts[ea_id],
            samples=counts[ea_id],
        )
        for ea_id in lasts
    }


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
