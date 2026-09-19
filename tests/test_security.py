from futbot.security import (
    CooldownMap,
    TtlCache,
    can_manage_watch,
    can_post_manual_alert,
)


def test_owner_or_admin_can_manage_watch() -> None:
    assert can_manage_watch(actor_id=1, owner_id=1, is_guild_manager=False) is True
    assert can_manage_watch(actor_id=2, owner_id=1, is_guild_manager=False) is False
    assert can_manage_watch(actor_id=2, owner_id=1, is_guild_manager=True) is True


def test_manual_alert_requires_watch_or_admin() -> None:
    assert can_post_manual_alert(actor_id=1, owner_id=1, is_guild_manager=False) is True
    assert can_post_manual_alert(actor_id=1, owner_id=None, is_guild_manager=False) is False
    assert can_post_manual_alert(actor_id=9, owner_id=1, is_guild_manager=False) is False
    assert can_post_manual_alert(actor_id=9, owner_id=None, is_guild_manager=True) is True


def test_cooldown_and_cache() -> None:
    cool = CooldownMap(seconds=60)
    assert cool.hit(42) is True
    assert cool.hit(42) is False
    assert cool.remaining(42) > 0
    cache = TtlCache(ttl_seconds=30)
    cache.set("mbappe", ["card"])
    assert cache.get("mbappe") == ["card"]
