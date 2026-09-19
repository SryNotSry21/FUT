from futbot.market.compare import bargains_from_drops, rank_platform_bargains
from futbot.formatting import format_bargain_line
from futbot.market.models import Bargain, PlayerCard


def test_platform_bargain_flags_cheaper_side() -> None:
    deals = rank_platform_bargains(
        ps5={1: 215_000, 2: 500_000},
        pc={1: 1_000_000, 2: 510_000},
        min_price=15_000,
        min_pct=20,
        min_delta=20_000,
    )
    assert len(deals) == 1
    deal = deals[0]
    assert deal.ea_id == 1
    assert deal.cheap_platform == "ps5"
    assert deal.cheap_price == 215_000
    assert deal.fair_price == 1_000_000
    assert 78 < deal.pct_below < 79


def test_platform_bargain_ignores_range_max_placeholder() -> None:
    deals = rank_platform_bargains(
        ps5={10: 402_000},
        pc={10: 15_000_000},
        min_price=15_000,
        min_pct=20,
    )
    assert deals == []


def test_platform_bargain_ignores_extreme_ratio() -> None:
    deals = rank_platform_bargains(
        ps5={11: 200_000},
        pc={11: 2_500_000},
        min_price=15_000,
        min_pct=20,
        max_ratio=5.0,
    )
    assert deals == []


def test_bargains_from_drops_use_old_price_as_fair_value() -> None:
    deals = bargains_from_drops([(166149, 1_500_000, 690_000, -54.0)], "ps5")
    assert deals[0].fair_price == 1_500_000
    assert deals[0].cheap_price == 690_000
    assert deals[0].reason == "markt"


def test_bargain_line_shows_fair_to_cheap_not_delta() -> None:
    card = PlayerCard(
        ea_id=1,
        name="Laura Georges",
        rating=87,
        position="CB",
        rarity="Base Hero",
        club="",
        nation="",
        league="",
        url="",
        image_url="",
    )
    deal = Bargain(
        ea_id=1,
        cheap_platform="ps5",
        cheap_price=215_000,
        fair_platform="pc",
        fair_price=1_000_000,
        pct_below=78.5,
        reason="plattform",
        player=card,
    )
    text = format_bargain_line(deal)
    assert "Laura Georges" in text
    assert "1.000.000 → 215.000 Coins" in text
    assert "günstig auf PS" in text
    assert "785.000" not in text
