from __future__ import annotations

from typing import Any

from futbot.market.models import PlayerCard


def _nested_name(payload: Any) -> str:
    if isinstance(payload, dict):
        return str(payload.get("name") or "")
    return ""


def parse_player_card(payload: dict[str, Any]) -> PlayerCard:
    url = str(payload.get("url") or "")
    if url and not url.startswith("http"):
        url = f"https://www.fut.gg{url}"
    image = (
        payload.get("cardImageUrl")
        or payload.get("imageUrl")
        or payload.get("simpleCardImageUrl")
        or ""
    )
    listed = payload.get("currentDbPrice") or payload.get("price")
    momentum = payload.get("momentumPercentage")
    return PlayerCard(
        ea_id=int(payload["eaId"]),
        name=str(payload.get("commonName") or payload.get("cardName") or "Unbekannt"),
        rating=int(payload.get("overall") or 0),
        position=str(payload.get("position") or "?"),
        rarity=str(payload.get("rarityName") or "Karte"),
        club=_nested_name(payload.get("club") or payload.get("uniqueClub")),
        nation=_nested_name(payload.get("nation")),
        league=_nested_name(payload.get("league")),
        url=url,
        image_url=str(image),
        slug=str(payload.get("slug") or ""),
        base_player_ea_id=int(payload["basePlayerEaId"])
        if payload.get("basePlayerEaId") is not None
        else int(payload["eaId"]),
        quality=str(payload.get("quality") or ""),
        momentum_pct=float(momentum) if momentum is not None else None,
        listed_price=int(listed) if listed not in (None, 0, "") else None,
    )


def parse_global_search_hit(payload: dict[str, Any]) -> PlayerCard | None:
    meta = payload.get("meta") or {}
    if meta.get("kind") not in (None, "player"):
        return None
    ea_id = meta.get("basePlayerEaId")
    if ea_id is None:
        raw_id = str(payload.get("id") or "")
        if raw_id.startswith("player:"):
            ea_id = raw_id.split(":", 1)[1]
    if ea_id is None:
        return None
    first = meta.get("firstName") or ""
    last = meta.get("lastName") or ""
    name = " ".join(part for part in (first, last) if part).strip() or "Unbekannt"
    url = str(meta.get("url") or "")
    if url and not url.startswith("http"):
        url = f"https://www.fut.gg{url}"
    return PlayerCard(
        ea_id=int(ea_id),
        name=name,
        rating=int(meta.get("overall") or 0),
        position=str(meta.get("position") or "?"),
        rarity="Karte",
        club="",
        nation="",
        league="",
        url=url,
        image_url=str(meta.get("imageUrl") or ""),
        slug="",
        base_player_ea_id=int(ea_id),
    )
