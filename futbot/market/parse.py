from __future__ import annotations

from typing import Any, Iterable

from futbot.market.models import PlayerCard

_PLAYER_LIST_KEYS = (
    "currentVersions",
    "playerItems",
    "items",
    "results",
    "players",
)


def _nested_name(payload: Any) -> str:
    if isinstance(payload, dict):
        return str(payload.get("name") or "")
    return ""


def _player_name(payload: dict[str, Any]) -> str:
    common = str(payload.get("commonName") or payload.get("cardName") or "").strip()
    if common:
        return common
    first = str(payload.get("firstName") or "").strip()
    last = str(payload.get("lastName") or "").strip()
    joined = " ".join(part for part in (first, last) if part)
    return joined or "Unbekannt"


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
        name=_player_name(payload),
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


def iter_player_items(payload: Any) -> Iterable[dict[str, Any]]:
    """Walk FUT.GG search, hub and player-items payloads for card dicts."""
    if payload is None:
        return
    if isinstance(payload, list):
        for item in payload:
            yield from iter_player_items(item)
        return
    if not isinstance(payload, dict):
        return
    nested = payload.get("player")
    if isinstance(nested, dict) and nested.get("eaId") is not None:
        yield from iter_player_items(nested)
    if payload.get("eaId") is not None:
        yield payload
    data = payload.get("data")
    if data is not None and data is not payload:
        yield from iter_player_items(data)
    for key in _PLAYER_LIST_KEYS:
        nested_list = payload.get(key)
        if nested_list:
            yield from iter_player_items(nested_list)


def cards_from_payload(payload: Any) -> list[PlayerCard]:
    cards: list[PlayerCard] = []
    seen: set[int] = set()
    for item in iter_player_items(payload):
        try:
            card = parse_player_card(item)
        except (KeyError, TypeError, ValueError):
            continue
        if card.ea_id in seen:
            continue
        seen.add(card.ea_id)
        cards.append(card)
    return cards


def first_matching_card(payload: Any, ea_id: int) -> PlayerCard | None:
    for card in cards_from_payload(payload):
        if card.ea_id == ea_id:
            return card
    return None


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
