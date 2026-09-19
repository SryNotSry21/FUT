from futbot.market.compare import (
    bargains_from_drops,
    comparable_year_card,
    finalize_ps_bargain,
    is_same_player_card,
    rank_platform_bargains,
    rank_ps_bargains,
    rank_year_bargains,
)
from futbot.formatting import bargains_embed, format_bargain_line
from futbot.market.models import Bargain, PlayerCard


def _card(ea_id: int, name: str, base: int | None = None) -> PlayerCard:
    return PlayerCard(
        ea_id=ea_id,
        name=name,
        rating=85,
        position="ST",
        rarity="Rare",
        club="",
        nation="",
        league="",
        url="",
        image_url="",
        base_player_ea_id=base if base is not None else ea_id,
    )


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
        fair_platform="ps5",
        fair_price=1_000_000,
        pct_below=78.5,
        reason="markt",
        player=card,
    )
    text = format_bargain_line(deal)
    assert "Laura Georges" in text
    assert "1.000.000 → 215.000 Coins" in text
    assert "letzter Scan" in text
    assert "PC" not in text
    assert "785.000" not in text


def test_year_bargain_uses_last_year_as_fair_value() -> None:
    deals = rank_year_bargains(
        current_ps5={209331: 150_000, 1: 500_000},
        current_pc={209331: 160_000},
        last_ps5={209331: 610_000},
        last_pc={209331: 580_000, 1: 510_000},
        min_price=15_000,
        min_pct=20,
        min_delta=20_000,
    )
    assert len(deals) == 1
    deal = deals[0]
    assert deal.ea_id == 209331
    assert deal.cheap_price == 150_000
    assert deal.fair_price == 610_000
    assert deal.reason == "vorjahr"
    assert deal.fair_platform == "ps5"


def test_year_bargain_ignores_missing_last_year_and_range_max() -> None:
    deals = rank_year_bargains(
        current_ps5={2: 40_000, 3: 200_000},
        current_pc={},
        last_ps5={3: 15_000_000},
        last_pc={},
        min_price=15_000,
        min_pct=20,
    )
    assert deals == []


def test_same_player_card_rejects_reused_id() -> None:
    current = _card(50573369, "Rafael Leão", base=241721)
    previous = _card(50573369, "Rafael Leão", base=241721)
    other = _card(50573369, "Other", base=99)
    assert is_same_player_card(current, previous) is True
    assert is_same_player_card(current, other) is False
    gold = _card(209331, "Mohamed Salah", base=209331)
    assert is_same_player_card(gold, None) is True
    promo = _card(50573369, "Rafael Leão", base=241721)
    assert is_same_player_card(promo, None) is False


def test_comparable_year_card_requires_similar_overall() -> None:
    weak = PlayerCard(
        ea_id=50573369,
        name="Rafael Leão",
        rating=83,
        position="LW",
        rarity="Rare",
        club="",
        nation="",
        league="",
        url="",
        image_url="",
        base_player_ea_id=241721,
    )
    last = PlayerCard(
        ea_id=50573369,
        name="Rafael Leão",
        rating=86,
        position="ST",
        rarity="Ultimate Scream",
        club="",
        nation="",
        league="",
        url="",
        image_url="",
        base_player_ea_id=241721,
    )
    same = _card(246863, "Felix Nmecha", base=246863)
    last_same = PlayerCard(
        ea_id=246863,
        name="Felix Nmecha",
        rating=86,
        position="CDM",
        rarity="UCL",
        club="",
        nation="",
        league="",
        url="",
        image_url="",
        base_player_ea_id=246863,
    )
    assert comparable_year_card(weak, last) is False
    assert comparable_year_card(same, last_same) is True


def test_rank_ps_bargains_uses_higher_of_scan_and_year() -> None:
    deals = rank_ps_bargains(
        current={10: 200_000, 11: 400_000},
        last_scan={10: 280_000, 11: 410_000},
        last_year={10: 500_000},
        min_price=15_000,
        min_pct=20,
        min_delta=20_000,
    )
    by_id = {deal.ea_id: deal for deal in deals}
    assert 10 in by_id
    assert by_id[10].fair_price == 500_000
    assert by_id[10].reason == "beides"
    assert 11 not in by_id


def test_rank_ps_bargains_drops_extreme_year_ratio() -> None:
    deals = rank_ps_bargains(
        current={12: 40_000},
        last_scan={},
        last_year={12: 650_000},
        min_price=15_000,
        min_pct=20,
        min_delta=20_000,
    )
    assert deals == []


def test_finalize_drops_weaker_year_card_and_keeps_scan() -> None:
    deal = Bargain(
        ea_id=1,
        cheap_platform="ps5",
        cheap_price=200_000,
        fair_platform="ps5",
        fair_price=500_000,
        pct_below=60.0,
        reason="beides",
        scan_fair=300_000,
        year_fair=500_000,
    )
    current = PlayerCard(
        ea_id=1,
        name="Test",
        rating=83,
        position="ST",
        rarity="Rare",
        club="",
        nation="",
        league="",
        url="",
        image_url="",
        base_player_ea_id=1,
    )
    previous = PlayerCard(
        ea_id=1,
        name="Test",
        rating=88,
        position="ST",
        rarity="TOTS",
        club="",
        nation="",
        league="",
        url="",
        image_url="",
        base_player_ea_id=1,
    )
    kept = finalize_ps_bargain(deal, current, previous, min_pct=20, min_delta=20_000)
    assert kept is not None
    assert kept.reason == "markt"
    assert kept.fair_price == 300_000
    assert kept.year_fair is None


def test_year_bargain_line_and_embed_mention_last_year() -> None:
    deal = Bargain(
        ea_id=209331,
        cheap_platform="ps5",
        cheap_price=150_000,
        fair_platform="ps5",
        fair_price=610_000,
        pct_below=75.4,
        reason="vorjahr",
        player=_card(209331, "Mohamed Salah"),
    )
    text = format_bargain_line(deal)
    assert "Mohamed Salah" in text
    assert "610.000 → 150.000 Coins" in text
    assert "vs FC 26" in text
    embed = bargains_embed([deal], previous_game_year=26)
    assert embed.title and "Schnapper" in embed.title
    assert "Mohamed Salah" in embed.fields[0].value
    assert "Günstiger als die andere Plattform" not in embed.fields[0].name
