import pytest

from futbot.market.models import PlayerCard, PriceMove
from futbot.market.service import MarketService


def _card(ea_id: int = 231747, name: str = "Kylian Mbappé") -> PlayerCard:
    return PlayerCard(
        ea_id=ea_id,
        name=name,
        rating=91,
        position="ST",
        rarity="Rare",
        club="Real Madrid",
        nation="France",
        league="LALIGA EA SPORTS",
        url="https://www.fut.gg/players/231747/",
        image_url="",
    )


@pytest.mark.asyncio
async def test_hydrate_moves_updates_the_same_list() -> None:
    market = MarketService()

    async def fake_get_players(ea_ids):
        return {231747: _card(), 238794: _card(238794, "Vini Jr.")}

    market.futgg.get_players = fake_get_players  # type: ignore[method-assign]
    risers = [
        PriceMove(
            ea_id=231747,
            platform="ps5",
            old_price=100,
            new_price=150,
            delta=50,
            pct=50.0,
        )
    ]
    fallers = [
        PriceMove(
            ea_id=238794,
            platform="ps5",
            old_price=200,
            new_price=100,
            delta=-100,
            pct=-50.0,
        )
    ]
    await market.hydrate_moves(risers)
    await market.hydrate_moves(fallers)
    assert risers[0].player is not None
    assert risers[0].player.name == "Kylian Mbappé"
    assert fallers[0].player is not None
    assert fallers[0].player.name == "Vini Jr."


@pytest.mark.asyncio
async def test_concatenated_copy_must_not_be_used_for_hydration() -> None:
    """Regression: hydrating `risers + fallers` left the original alert lists nameless."""
    market = MarketService()

    async def fake_get_players(ea_ids):
        return {231747: _card()}

    market.futgg.get_players = fake_get_players  # type: ignore[method-assign]
    risers = [
        PriceMove(
            ea_id=231747,
            platform="ps5",
            old_price=100,
            new_price=150,
            delta=50,
            pct=50.0,
        )
    ]
    await market.hydrate_moves(risers + [])
    assert risers[0].player is None
    await market.hydrate_moves(risers)
    assert risers[0].player is not None
