from pathlib import Path

from futbot.db import Store
from futbot.market.models import PlayerCard


def _card(ea_id: int = 231747) -> PlayerCard:
    return PlayerCard(
        ea_id=ea_id,
        name="Kylian Mbappé",
        rating=91,
        position="ST",
        rarity="Rare",
        club="Real Madrid",
        nation="France",
        league="LALIGA",
        url="https://www.fut.gg/players/231747-kylian-mbappe/27-231747/",
        image_url="",
    )


def test_watch_crud(tmp_path: Path) -> None:
    store = Store(tmp_path / "bot.db")
    guild_id = 1
    store.set_alert_channel(guild_id, 99)
    watch = store.add_watch(guild_id, user_id=5, player=_card(), platform="beide", threshold_pct=12, threshold_coins=50_000)
    assert watch.ea_id == 231747
    assert store.get_user_watch(guild_id, 5, 231747) is not None
    listed = store.list_watches(guild_id)
    assert len(listed) == 1
    store.update_watch_prices(watch.id, 3_800_000, 4_000_000, alerted=True)
    updated = store.get_user_watch(guild_id, 5, 231747)
    assert updated is not None
    assert updated.last_price_ps5 == 3_800_000
    assert updated.last_alert_at is not None
    assert store.remove_watch(guild_id, 231747, user_id=5) == 1
    assert store.list_watches(guild_id) == []
    store.close()


def test_target_below_watch_roundtrip(tmp_path: Path) -> None:
    store = Store(tmp_path / "bot.db")
    watch = store.add_watch(
        1,
        user_id=5,
        player=_card(),
        platform="ps5",
        threshold_pct=0,
        threshold_coins=None,
        target_below=2_000_000,
    )
    assert watch.target_below == 2_000_000
    again = store.get_user_watch(1, 5, 231747)
    assert again is not None
    assert again.target_below == 2_000_000
    store.close()


def test_percent_watch_can_add_target_below(tmp_path: Path) -> None:
    store = Store(tmp_path / "bot.db")
    store.add_watch(1, 5, _card(), "beide", threshold_pct=12, threshold_coins=None)
    updated = store.add_watch(
        1, 5, _card(), "beide", threshold_pct=12, threshold_coins=None, target_below=1_500_000
    )
    assert updated.threshold_pct == 12
    assert updated.target_below == 1_500_000
    store.close()


def test_watch_does_not_steal_other_users_alert(tmp_path: Path) -> None:
    store = Store(tmp_path / "bot.db")
    store.add_watch(1, user_id=5, player=_card(), platform="beide", threshold_pct=10, threshold_coins=None)
    store.add_watch(1, user_id=9, player=_card(), platform="ps5", threshold_pct=15, threshold_coins=None)
    watches = store.find_watches(1, 231747)
    assert {watch.user_id for watch in watches} == {5, 9}
    assert store.get_user_watch(1, 5, 231747) is not None
    assert store.get_user_watch(1, 9, 231747) is not None
    assert store.remove_watch(1, 231747, user_id=9) == 1
    remaining = store.find_watches(1, 231747)
    assert len(remaining) == 1
    assert remaining[0].user_id == 5
    store.close()


def test_market_snapshot_roundtrip(tmp_path: Path) -> None:
    store = Store(tmp_path / "bot.db")
    store.save_snapshot("ps5", {231747: 3800000, 37576: 11800000})
    loaded = store.load_snapshot("ps5")
    assert loaded[231747] == 3_800_000
    assert loaded[37576] == 11_800_000
    store.close()


def test_market_history_average_and_low(tmp_path: Path) -> None:
    store = Store(tmp_path / "bot.db")
    store.append_history("ps5", {10: 300_000, 11: 100_000})
    store.append_history("ps5", {10: 250_000, 11: 100_000})
    store.append_history("ps5", {10: 280_000, 11: 90_000})
    stats = store.load_price_stats("ps5")
    assert stats[10].low == 250_000
    assert stats[10].average == 276_666
    assert stats[10].last == 280_000
    assert stats[10].samples == 3
    assert stats[11].low == 90_000
    assert stats[11].average == 96_666
    store.close()


def test_market_history_keeps_a_sliding_window(tmp_path: Path) -> None:
    from futbot.db import MARKET_HISTORY_LIMIT

    store = Store(tmp_path / "bot.db")
    for index in range(MARKET_HISTORY_LIMIT + 5):
        store.append_history("ps5", {1: 100_000 + index})
    snapshots = store.load_history_snapshots("ps5")
    assert len(snapshots) == MARKET_HISTORY_LIMIT
    assert snapshots[0][1] == 100_000 + 5
    assert snapshots[-1][1] == 100_000 + MARKET_HISTORY_LIMIT + 4
    store.close()


def test_market_history_seeds_from_existing_snapshot(tmp_path: Path) -> None:
    store = Store(tmp_path / "bot.db")
    store.save_snapshot("ps5", {7: 222_000})
    store.close()
    again = Store(tmp_path / "bot.db")
    stats = again.load_price_stats("ps5")
    assert stats[7].average == 222_000
    assert stats[7].low == 222_000
    assert stats[7].samples == 1
    again.close()
