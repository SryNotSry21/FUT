from __future__ import annotations

import math
from dataclasses import replace

from futbot.market.models import Bargain, BargainReason, PlayerCard, Platform


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


def crossed_below_target(
    old_price: int | None,
    new_price: int | None,
    target: int | None,
) -> bool:
    """True when the price moves from above the target to at or below it."""
    if target is None or target <= 0 or new_price is None:
        return False
    if new_price > target:
        return False
    if old_price is None:
        return False
    return old_price > target


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
YEAR_MAX_RATING_DROP = 2
YEAR_MAX_RATIO = 8.0


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


def rank_year_bargains(
    current_ps5: dict[int, int],
    current_pc: dict[int, int],
    last_ps5: dict[int, int],
    last_pc: dict[int, int],
    *,
    min_price: int = 15_000,
    min_pct: float = 20.0,
    min_delta: int = 20_000,
    max_price: int = MAX_REALISTIC_BIN,
    limit: int = 10,
) -> list[Bargain]:
    """Cards whose current BIN is well below last year's BIN for the same id."""
    found: list[Bargain] = []
    for ea_id in set(current_ps5) | set(current_pc):
        last_options: list[tuple[Platform, int]] = []
        if ea_id in last_ps5:
            last_options.append(("ps5", last_ps5[ea_id]))
        if ea_id in last_pc:
            last_options.append(("pc", last_pc[ea_id]))
        if not last_options:
            continue
        fair_platform, fair_price = max(last_options, key=lambda item: item[1])
        now_options: list[tuple[Platform, int]] = []
        if ea_id in current_ps5:
            now_options.append(("ps5", current_ps5[ea_id]))
        if ea_id in current_pc:
            now_options.append(("pc", current_pc[ea_id]))
        if not now_options:
            continue
        cheap_platform, cheap_price = min(now_options, key=lambda item: item[1])
        if cheap_price < min_price or fair_price < min_price or fair_price > max_price:
            continue
        if cheap_price <= 0 or fair_price <= 0 or cheap_price >= fair_price:
            continue
        delta = fair_price - cheap_price
        pct_below = (delta / fair_price) * 100.0
        if pct_below < min_pct or delta < min_delta:
            continue
        found.append(
            Bargain(
                ea_id=ea_id,
                cheap_platform=cheap_platform,
                cheap_price=cheap_price,
                fair_platform=fair_platform,
                fair_price=fair_price,
                pct_below=pct_below,
                reason="vorjahr",
            )
        )
    found.sort(key=lambda item: item.pct_below, reverse=True)
    return found[:limit]


def is_same_player_card(current: PlayerCard, previous: PlayerCard | None) -> bool:
    """Keep YoY bargains only when the reused card id is still the same player."""
    if previous is None:
        return current.base_player_ea_id == current.ea_id
    return current.base_player_ea_id == previous.base_player_ea_id


def comparable_year_card(current: PlayerCard, previous: PlayerCard | None) -> bool:
    """YoY fair value only for the same player at a similar overall."""
    if not is_same_player_card(current, previous):
        return False
    if previous is None:
        return True
    return current.rating >= previous.rating - YEAR_MAX_RATING_DROP


def bargain_score(cheap_price: int, pct_below: float, coins_saved: int) -> float:
    """Prefer real coin savings, then a strong percent gap."""
    return coins_saved * math.sqrt(max(pct_below, 1.0))


def rank_ps_bargains(
    current: dict[int, int],
    last_scan: dict[int, int],
    last_year: dict[int, int],
    *,
    min_price: int = 15_000,
    min_pct: float = 20.0,
    min_delta: int = 20_000,
    max_price: int = MAX_REALISTIC_BIN,
    limit: int = 40,
) -> list[Bargain]:
    """PS BIN vs the better of last scan and last year's PS BIN."""
    found: list[Bargain] = []
    for ea_id, cheap_price in current.items():
        if cheap_price < min_price or cheap_price > max_price:
            continue
        scan_fair = last_scan.get(ea_id)
        year_fair = last_year.get(ea_id)
        if scan_fair is not None and not min_price <= scan_fair <= max_price:
            scan_fair = None
        if year_fair is not None and not min_price <= year_fair <= max_price:
            year_fair = None
        if year_fair is not None and year_fair / max(cheap_price, 1) > YEAR_MAX_RATIO:
            year_fair = None
        if scan_fair is not None and scan_fair <= cheap_price:
            scan_fair = None
        if year_fair is not None and year_fair <= cheap_price:
            year_fair = None
        refs = [price for price in (scan_fair, year_fair) if price]
        if not refs:
            continue
        fair_price = max(refs)
        delta = fair_price - cheap_price
        pct_below = (delta / fair_price) * 100.0
        if pct_below < min_pct or delta < min_delta:
            continue
        if scan_fair and year_fair:
            reason: BargainReason = "beides"
        elif year_fair:
            reason = "vorjahr"
        else:
            reason = "markt"
        found.append(
            Bargain(
                ea_id=ea_id,
                cheap_platform="ps5",
                cheap_price=cheap_price,
                fair_platform="ps5",
                fair_price=fair_price,
                pct_below=pct_below,
                reason=reason,
                scan_fair=scan_fair,
                year_fair=year_fair,
            )
        )
    found.sort(
        key=lambda deal: bargain_score(deal.cheap_price, deal.pct_below, deal.fair_price - deal.cheap_price),
        reverse=True,
    )
    return found[:limit]


def finalize_ps_bargain(
    deal: Bargain,
    current: PlayerCard,
    previous: PlayerCard | None,
    *,
    min_pct: float,
    min_delta: int,
) -> Bargain | None:
    """Drop last-year refs that are a worse/different card, then rebuild fair value."""

    scan_fair = deal.scan_fair
    year_fair = deal.year_fair
    if year_fair is not None and not comparable_year_card(current, previous):
        year_fair = None
    refs: list[tuple[str, int]] = []
    if scan_fair is not None and scan_fair > deal.cheap_price:
        refs.append(("markt", scan_fair))
    if year_fair is not None and year_fair > deal.cheap_price:
        refs.append(("vorjahr", year_fair))
    if not refs:
        return None
    if len(refs) == 2:
        reason = "beides"
        fair_price = max(scan_fair or 0, year_fair or 0)
    else:
        reason, fair_price = refs[0]
    delta = fair_price - deal.cheap_price
    pct_below = (delta / fair_price) * 100.0
    if pct_below < min_pct or delta < min_delta:
        return None
    return replace(
        deal,
        fair_price=fair_price,
        pct_below=pct_below,
        reason=reason,  # type: ignore[arg-type]
        player=current,
        scan_fair=scan_fair,
        year_fair=year_fair,
    )


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
