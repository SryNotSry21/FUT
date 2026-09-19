from futbot.market.compare import crossed_below_target, is_significant_move, percent_change, rank_movers


def test_percent_change() -> None:
    assert percent_change(1000, 1200) == 20.0
    assert percent_change(1000, 800) == -20.0
    assert percent_change(0, 100) == 0.0


def test_significant_percent_threshold() -> None:
    triggered, delta, pct = is_significant_move(100_000, 80_000, threshold_pct=10)
    assert triggered is True
    assert delta == -20_000
    assert pct == -20.0


def test_below_threshold_is_ignored() -> None:
    triggered, delta, pct = is_significant_move(100_000, 95_000, threshold_pct=10)
    assert triggered is False
    assert delta == -5_000
    assert pct == -5.0


def test_coin_threshold_overrides_percent() -> None:
    triggered, delta, _pct = is_significant_move(
        1_000_000, 970_000, threshold_pct=10, threshold_coins=20_000
    )
    assert triggered is True
    assert delta == -30_000


def test_min_price_filters_fodder() -> None:
    triggered, _, _ = is_significant_move(
        800, 400, threshold_pct=10, min_price=10_000
    )
    assert triggered is False


def test_missing_prices_do_not_alert() -> None:
    triggered, delta, pct = is_significant_move(None, 1000, threshold_pct=10)
    assert triggered is False
    assert delta == 0
    assert pct == 0.0


def test_rank_movers_splits_risers_and_fallers() -> None:
    previous = {1: 10_000, 2: 50_000, 3: 80_000, 4: 20_000}
    current = {1: 15_000, 2: 40_000, 3: 81_000, 4: 20_000}
    risers, fallers = rank_movers(previous, current, threshold_pct=10, min_price=5_000)
    assert [row[0] for row in risers] == [1]
    assert [row[0] for row in fallers] == [2]
    assert risers[0][3] == 50.0


def test_crossed_below_target_only_on_way_down() -> None:
    assert crossed_below_target(2_100_000, 1_900_000, 2_000_000) is True
    assert crossed_below_target(1_900_000, 1_800_000, 2_000_000) is False
    assert crossed_below_target(2_100_000, 2_050_000, 2_000_000) is False
    assert crossed_below_target(None, 1_500_000, 2_000_000) is False
    assert crossed_below_target(2_100_000, 2_000_000, 2_000_000) is True
    assert crossed_below_target(2_100_000, 1_900_000, None) is False
