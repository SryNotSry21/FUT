from futbot.formatting import format_coins, format_delta, format_pct


def test_format_coins_german_thousands() -> None:
    assert format_coins(3_800_000) == "3.800.000 Coins"
    assert format_coins(None) == "—"


def test_format_pct_and_delta() -> None:
    assert format_pct(-12.5) == "-12,5 %"
    assert "▼" in format_delta(-20_000, -10.0)
    assert "+" in format_delta(20_000, 10.0)
