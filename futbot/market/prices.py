from __future__ import annotations

from typing import Any

from futbot.market.models import Platform, PlatformPrice

# Mirrors FUT.GG's reconstructPlayerPrice() in the web client.
# IDs are stored as id0 plus a delta array. Prices/status live in parallel arrays.


def reconstruct_ids(blob: dict[str, Any]) -> list[int]:
    if "id0" not in blob or "d" not in blob:
        return []
    ids = [int(blob["id0"])]
    current = ids[0]
    for delta in blob["d"]:
        current += int(delta)
        ids.append(current)
    return ids


def merge_price_blobs(index_blob: dict[str, Any], price_blob: dict[str, Any]) -> dict[str, Any]:
    """Combine the ID index with a dyn/static price payload."""
    merged = dict(index_blob)
    merged["p"] = price_blob.get("p", [])
    merged["s"] = price_blob.get("s", index_blob.get("s", []))
    return merged


def decode_platform_prices(blob: dict[str, Any], platform: Platform) -> dict[int, PlatformPrice]:
    ids = reconstruct_ids(blob)
    prices = blob.get("p") or []
    statuses = blob.get("s") or []
    sbcs = blob.get("sbcs") or {}
    result: dict[int, PlatformPrice] = {}
    if not ids or not prices:
        return result
    if len(prices) != len(ids):
        raise ValueError(
            f"Price blob/index length mismatch: {len(prices)} prices vs {len(ids)} ids"
        )

    for index, ea_id in enumerate(ids):
        status = int(statuses[index]) if index < len(statuses) and statuses[index] is not None else 0
        is_sbc = status == 1
        is_objective = status == 2
        raw_price = prices[index]
        sbc_requirement = sbcs.get(str(ea_id), sbcs.get(ea_id)) if is_sbc else None
        if sbc_requirement is not None or is_sbc:
            price = None
        elif raw_price in (None, 0):
            price = None
        else:
            price = int(raw_price)
        result[int(ea_id)] = PlatformPrice(
            platform=platform,
            price=price,
            is_sbc=is_sbc,
            is_objective=is_objective,
            is_extinct=status == 0 and price is None,
        )
    return result
