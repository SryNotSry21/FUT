from __future__ import annotations


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
