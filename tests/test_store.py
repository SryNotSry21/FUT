from pathlib import Path

from futbot.db import Store
from futbot.market.models import PlayerCard


def _card() -> PlayerCard:
    return PlayerCard(
        ea_id=231747,
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
    assert store.get_watch(guild_id, 231747) is not None
    listed = store.list_watches(guild_id)
    assert len(listed) == 1
    store.update_watch_prices(watch.id, 3_800_000, 4_000_000, alerted=True)
    updated = store.get_watch(guild_id, 231747)
    assert updated is not None
    assert updated.last_price_ps5 == 3_800_000
    assert updated.last_alert_at is not None
    assert store.remove_watch(guild_id, 231747) is True
    assert store.list_watches(guild_id) == []
    store.close()


def test_market_snapshot_roundtrip(tmp_path: Path) -> None:
    store = Store(tmp_path / "bot.db")
    store.save_snapshot("ps5", {231747: 3800000, 37576: 11800000})
    loaded = store.load_snapshot("ps5")
    assert loaded[231747] == 3_800_000
    assert loaded[37576] == 11_800_000
    store.close()
