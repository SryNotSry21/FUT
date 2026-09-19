from futbot.formatting import format_coins, format_delta, format_pct, move_display_name, movers_embed
from futbot.market.models import PlayerCard, PriceMove


def _card(**overrides) -> PlayerCard:
    data = dict(
        ea_id=231747,
        name="Kylian Mbappé",
        rating=91,
        position="ST",
        rarity="Rare",
        club="Real Madrid",
        nation="France",
        league="LALIGA EA SPORTS",
        url="https://www.fut.gg/players/231747/",
        image_url="",
    )
    data.update(overrides)
    return PlayerCard(**data)


def _move(player: PlayerCard | None = None, ea_id: int = 231747) -> PriceMove:
    return PriceMove(
        ea_id=ea_id,
        platform="ps5",
        old_price=1_000_000,
        new_price=1_200_000,
        delta=200_000,
        pct=20.0,
        player=player,
    )


def test_format_coins_german_thousands() -> None:
    assert format_coins(3_800_000) == "3.800.000 Coins"
    assert format_coins(None) == "—"


def test_format_pct_and_delta() -> None:
    assert format_pct(-12.5) == "-12,5 %"
    assert "▼" in format_delta(-20_000, -10.0)
    assert "+" in format_delta(20_000, 10.0)


def test_move_list_prefers_player_name_over_id() -> None:
    named = _move(_card())
    unnamed = _move(None, ea_id=37576)
    embed = movers_embed("Scan", [named], [unnamed])
    risers = embed.fields[0].value
    fallers = embed.fields[1].value
    assert "Kylian Mbappé" in risers
    assert "ID 231747" not in risers
    assert "ID 37576" in fallers
    assert move_display_name(named).startswith("Kylian Mbappé")
