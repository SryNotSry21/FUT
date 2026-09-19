from __future__ import annotations

from futbot.market.models import Bargain, Platform


def percent_change(old: int, new: int) -> float:
    if old <= 0:
        return 0.0
    return ((new - old) / old) * 100.0


def is_significant_move(
    old_price: int | None,
    new_price: int | None,
    threshold_pct: float,
    threshold_coins: int | None = None,
    min_price: int = 0,
) -> tuple[bool, int, float]:
    """Return (triggered, coin_delta, percent_delta)."""
    if old_price is None or new_price is None:
        return False, 0, 0.0
    if old_price <= 0 or new_price < 0:
        return False, 0, 0.0
    if min_price and min(old_price, new_price) < min_price:
        return False, 0, 0.0
    delta = new_price - old_price
    pct = percent_change(old_price, new_price)
    if threshold_coins is not None and threshold_coins > 0 and abs(delta) >= threshold_coins:
        return True, delta, pct
    if threshold_pct > 0 and abs(pct) >= threshold_pct:
        return True, delta, pct
    return False, delta, pct


def rank_movers(
    previous: dict[int, int],
    current: dict[int, int],
    threshold_pct: float,
    min_price: int,
    limit: int = 10,
) -> tuple[list[tuple[int, int, int, float]], list[tuple[int, int, int, float]]]:
    """Return (risers, fallers) as (ea_id, old, new, pct) sorted by abs(pct)."""
    risers: list[tuple[int, int, int, float]] = []
    fallers: list[tuple[int, int, int, float]] = []
    for ea_id, new_price in current.items():
        old_price = previous.get(ea_id)
        triggered, delta, pct = is_significant_move(
            old_price, new_price, threshold_pct, min_price=min_price
        )
        if not triggered or old_price is None:
            continue
        row = (ea_id, old_price, new_price, pct)
        if delta >= 0:
            risers.append(row)
        else:
            fallers.append(row)
    risers.sort(key=lambda item: item[3], reverse=True)
    fallers.sort(key=lambda item: item[3])
    return risers[:limit], fallers[:limit]


# EA range-max placeholders (e.g. 15.000.000) are not real BINs.
MAX_REALISTIC_BIN = 12_000_000


def rank_platform_bargains(
    ps5: dict[int, int],
    pc: dict[int, int],
    *,
    min_price: int = 15_000,
    min_pct: float = 20.0,
    min_delta: int = 20_000,
    max_price: int = MAX_REALISTIC_BIN,
    max_ratio: float = 5.0,
    limit: int = 10,
) -> list[Bargain]:
    """Cards whose BIN on one platform is well below the other platform's BIN."""
    found: list[Bargain] = []
    for ea_id, ps_price in ps5.items():
        pc_price = pc.get(ea_id)
        if pc_price is None:
            continue
        cheap_price = min(ps_price, pc_price)
        fair_price = max(ps_price, pc_price)
        if cheap_price < min_price or fair_price > max_price:
            continue
        if fair_price <= 0 or cheap_price <= 0:
            continue
        if fair_price / cheap_price > max_ratio:
            continue
        delta = fair_price - cheap_price
        pct_below = (delta / fair_price) * 100.0
        if pct_below < min_pct or delta < min_delta:
            continue
        cheap_platform: Platform = "ps5" if ps_price <= pc_price else "pc"
        fair_platform: Platform = "pc" if cheap_platform == "ps5" else "ps5"
        found.append(
            Bargain(
                ea_id=ea_id,
                cheap_platform=cheap_platform,
                cheap_price=cheap_price,
                fair_platform=fair_platform,
                fair_price=fair_price,
                pct_below=pct_below,
                reason="plattform",
            )
        )
    found.sort(key=lambda item: item.pct_below, reverse=True)
    return found[:limit]


def bargains_from_drops(
    fallers: list[tuple[int, int, int, float]],
    platform: Platform,
) -> list[Bargain]:
    """Turn snapshot crashes into 'below recent market' bargains."""
    bargains: list[Bargain] = []
    for ea_id, old_price, new_price, pct in fallers:
        bargains.append(
            Bargain(
                ea_id=ea_id,
                cheap_platform=platform,
                cheap_price=new_price,
                fair_platform=platform,
                fair_price=old_price,
                pct_below=abs(pct),
                reason="markt",
            )
        )
    return bargains
