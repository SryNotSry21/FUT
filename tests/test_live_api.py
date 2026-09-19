"""Live checks against FUT.GG. Skipped automatically if the network is blocked."""

from __future__ import annotations

import pytest

from futbot.market.futgg import FutGGClient
from futbot.market.service import MarketService


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.asyncio
async def test_live_search_mbappe() -> None:
    client = FutGGClient(game_year=27)
    try:
        cards = await client.search_players("mbappe")
    except Exception as exc:
        pytest.skip(f"FUT.GG not reachable: {exc}")
    finally:
        await client.aclose()
    assert cards, "expected at least one Mbappé card"
    assert any(card.ea_id == 231747 for card in cards)
    assert any(card.rating >= 90 for card in cards)


@pytest.mark.asyncio
async def test_live_price_blob_has_mbappe() -> None:
    client = FutGGClient(game_year=27)
    try:
        catalog = await client.fetch_catalog()
    except Exception as exc:
        pytest.skip(f"FUT.GG price CDN not reachable: {exc}")
    finally:
        await client.aclose()
    ps5 = catalog.ps5.get(231747)
    pc = catalog.pc.get(231747)
    assert ps5 is not None
    assert pc is not None
    assert ps5.price is None or ps5.price > 0
    assert len(catalog.ps5) > 1000


@pytest.mark.asyncio
async def test_live_market_service_quote() -> None:
    market = MarketService(game_year=27)
    try:
        quote = await market.quote("mbappe")
    except Exception as exc:
        pytest.skip(f"FUT.GG not reachable: {exc}")
    finally:
        await market.aclose()
    assert quote is not None
    assert quote.player.ea_id == 231747
    assert quote.ps5.platform == "ps5"
    assert quote.pc.platform == "pc"


@pytest.mark.asyncio
async def test_live_player_lookup_returns_names() -> None:
    client = FutGGClient(game_year=27)
    try:
        cards = await client.get_players([231747, 238794])
        hub = await client._get_json(
            "https://www.fut.gg/api/fut/players/v2/hub/231747/",
            params={"game": 27},
        )
    except Exception as exc:
        pytest.skip(f"FUT.GG not reachable: {exc}")
    finally:
        await client.aclose()
    from futbot.market.parse import first_matching_card

    assert cards[231747].name == "Kylian Mbappé"
    assert cards[238794].name
    assert "ID " not in cards[231747].name
    hub_card = first_matching_card(hub, 231747)
    assert hub_card is not None
    assert hub_card.name == "Kylian Mbappé"


@pytest.mark.asyncio
async def test_live_momentum_contains_prices() -> None:
    client = FutGGClient(game_year=27)
    try:
        movers = await client.momentum(hours=24)
    except Exception as exc:
        pytest.skip(f"FUT.GG momentum not reachable: {exc}")
    finally:
        await client.aclose()
    assert movers
    assert any(card.listed_price or card.momentum_pct for card in movers)
