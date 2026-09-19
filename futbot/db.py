from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from futbot.market.models import PlayerCard, Platform, WatchPlatform


@dataclass
class GuildSettings:
    guild_id: int
    alert_channel_id: int | None = None
    default_threshold_pct: float = 10.0
    scan_enabled: bool = True
    scan_min_price: int = 10_000
    scan_platform: Platform = "ps5"
    cooldown_minutes: int = 30


@dataclass
class Watch:
    id: int
    guild_id: int
    user_id: int
    ea_id: int
    name: str
    rating: int
    position: str
    rarity: str
    club: str
    url: str
    image_url: str
    platform: WatchPlatform
    threshold_pct: float
    threshold_coins: int | None
    last_price_ps5: int | None
    last_price_pc: int | None
    last_alert_at: float | None
    created_at: float
    target_below: int | None = None

    def as_player(self) -> PlayerCard:
        return PlayerCard(
            ea_id=self.ea_id,
            name=self.name,
            rating=self.rating,
            position=self.position,
            rarity=self.rarity,
            club=self.club,
            nation="",
            league="",
            url=self.url,
            image_url=self.image_url,
        )


class Store:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init()

    def close(self) -> None:
        self._conn.close()

    def _init(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                alert_channel_id INTEGER,
                default_threshold_pct REAL NOT NULL DEFAULT 10,
                scan_enabled INTEGER NOT NULL DEFAULT 1,
                scan_min_price INTEGER NOT NULL DEFAULT 10000,
                scan_platform TEXT NOT NULL DEFAULT 'ps5',
                cooldown_minutes INTEGER NOT NULL DEFAULT 30
            );

            CREATE TABLE IF NOT EXISTS watches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                ea_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                rating INTEGER NOT NULL DEFAULT 0,
                position TEXT NOT NULL DEFAULT '',
                rarity TEXT NOT NULL DEFAULT '',
                club TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                image_url TEXT NOT NULL DEFAULT '',
                platform TEXT NOT NULL DEFAULT 'beide',
                threshold_pct REAL NOT NULL DEFAULT 10,
                threshold_coins INTEGER,
                last_price_ps5 INTEGER,
                last_price_pc INTEGER,
                last_alert_at REAL,
                created_at REAL NOT NULL,
                target_below INTEGER,
                UNIQUE(guild_id, user_id, ea_id)
            );

            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS market_state (
                platform TEXT PRIMARY KEY,
                prices_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            """
        )
        self._migrate_watch_uniqueness()
        self._migrate_target_below()
        self._conn.commit()

    def _migrate_watch_uniqueness(self) -> None:
        row = self._conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'watch_unique'"
        ).fetchone()
        if row and row["value"] == "guild_user_ea":
            return
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watches_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                ea_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                rating INTEGER NOT NULL DEFAULT 0,
                position TEXT NOT NULL DEFAULT '',
                rarity TEXT NOT NULL DEFAULT '',
                club TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                image_url TEXT NOT NULL DEFAULT '',
                platform TEXT NOT NULL DEFAULT 'beide',
                threshold_pct REAL NOT NULL DEFAULT 10,
                threshold_coins INTEGER,
                last_price_ps5 INTEGER,
                last_price_pc INTEGER,
                last_alert_at REAL,
                created_at REAL NOT NULL,
                UNIQUE(guild_id, user_id, ea_id)
            )
            """
        )
        self._conn.execute(
            """
            INSERT OR IGNORE INTO watches_v2 (
                id, guild_id, user_id, ea_id, name, rating, position, rarity, club,
                url, image_url, platform, threshold_pct, threshold_coins,
                last_price_ps5, last_price_pc, last_alert_at, created_at
            )
            SELECT
                id, guild_id, user_id, ea_id, name, rating, position, rarity, club,
                url, image_url, platform, threshold_pct, threshold_coins,
                last_price_ps5, last_price_pc, last_alert_at, created_at
            FROM watches
            """
        )
        self._conn.execute("DROP TABLE watches")
        self._conn.execute("ALTER TABLE watches_v2 RENAME TO watches")
        self._conn.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('watch_unique', 'guild_user_ea')"
        )

    def _migrate_target_below(self) -> None:
        columns = {row[1] for row in self._conn.execute("PRAGMA table_info(watches)").fetchall()}
        if "target_below" not in columns:
            self._conn.execute("ALTER TABLE watches ADD COLUMN target_below INTEGER")

    def get_guild(self, guild_id: int) -> GuildSettings:
        row = self._conn.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
        ).fetchone()
        if row is None:
            return GuildSettings(guild_id=guild_id)
        return GuildSettings(
            guild_id=row["guild_id"],
            alert_channel_id=row["alert_channel_id"],
            default_threshold_pct=row["default_threshold_pct"],
            scan_enabled=bool(row["scan_enabled"]),
            scan_min_price=row["scan_min_price"],
            scan_platform=row["scan_platform"],
            cooldown_minutes=row["cooldown_minutes"],
        )

    def upsert_guild(self, settings: GuildSettings) -> GuildSettings:
        self._conn.execute(
            """
            INSERT INTO guild_settings (
                guild_id, alert_channel_id, default_threshold_pct,
                scan_enabled, scan_min_price, scan_platform, cooldown_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                alert_channel_id = excluded.alert_channel_id,
                default_threshold_pct = excluded.default_threshold_pct,
                scan_enabled = excluded.scan_enabled,
                scan_min_price = excluded.scan_min_price,
                scan_platform = excluded.scan_platform,
                cooldown_minutes = excluded.cooldown_minutes
            """,
            (
                settings.guild_id,
                settings.alert_channel_id,
                settings.default_threshold_pct,
                int(settings.scan_enabled),
                settings.scan_min_price,
                settings.scan_platform,
                settings.cooldown_minutes,
            ),
        )
        self._conn.commit()
        return settings

    def set_alert_channel(self, guild_id: int, channel_id: int | None) -> GuildSettings:
        settings = self.get_guild(guild_id)
        settings.alert_channel_id = channel_id
        return self.upsert_guild(settings)

    def all_guilds_with_alerts(self) -> list[GuildSettings]:
        rows = self._conn.execute(
            "SELECT * FROM guild_settings WHERE alert_channel_id IS NOT NULL"
        ).fetchall()
        return [
            GuildSettings(
                guild_id=row["guild_id"],
                alert_channel_id=row["alert_channel_id"],
                default_threshold_pct=row["default_threshold_pct"],
                scan_enabled=bool(row["scan_enabled"]),
                scan_min_price=row["scan_min_price"],
                scan_platform=row["scan_platform"],
                cooldown_minutes=row["cooldown_minutes"],
            )
            for row in rows
        ]

    def add_watch(
        self,
        guild_id: int,
        user_id: int,
        player: PlayerCard,
        platform: WatchPlatform,
        threshold_pct: float,
        threshold_coins: int | None,
        target_below: int | None = None,
    ) -> Watch:
        now = time.time()
        self._conn.execute(
            """
            INSERT INTO watches (
                guild_id, user_id, ea_id, name, rating, position, rarity, club,
                url, image_url, platform, threshold_pct, threshold_coins,
                target_below, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, ea_id) DO UPDATE SET
                name = excluded.name,
                rating = excluded.rating,
                position = excluded.position,
                rarity = excluded.rarity,
                club = excluded.club,
                url = excluded.url,
                image_url = excluded.image_url,
                platform = excluded.platform,
                threshold_pct = excluded.threshold_pct,
                threshold_coins = excluded.threshold_coins,
                target_below = excluded.target_below
            """,
            (
                guild_id,
                user_id,
                player.ea_id,
                player.name,
                player.rating,
                player.position,
                player.rarity,
                player.club,
                player.url,
                player.image_url,
                platform,
                threshold_pct,
                threshold_coins,
                target_below,
                now,
            ),
        )
        self._conn.commit()
        watch = self.get_user_watch(guild_id, user_id, player.ea_id)
        assert watch is not None
        return watch

    def get_watch(self, guild_id: int, ea_id: int) -> Watch | None:
        row = self._conn.execute(
            "SELECT * FROM watches WHERE guild_id = ? AND ea_id = ? ORDER BY id LIMIT 1",
            (guild_id, ea_id),
        ).fetchone()
        return _watch_from_row(row) if row else None

    def get_user_watch(self, guild_id: int, user_id: int, ea_id: int) -> Watch | None:
        row = self._conn.execute(
            "SELECT * FROM watches WHERE guild_id = ? AND user_id = ? AND ea_id = ?",
            (guild_id, user_id, ea_id),
        ).fetchone()
        return _watch_from_row(row) if row else None

    def find_watches(self, guild_id: int, ea_id: int) -> list[Watch]:
        rows = self._conn.execute(
            "SELECT * FROM watches WHERE guild_id = ? AND ea_id = ?",
            (guild_id, ea_id),
        ).fetchall()
        return [_watch_from_row(row) for row in rows]

    def remove_watch(self, guild_id: int, ea_id: int, user_id: int | None = None) -> int:
        if user_id is None:
            cursor = self._conn.execute(
                "DELETE FROM watches WHERE guild_id = ? AND ea_id = ?",
                (guild_id, ea_id),
            )
        else:
            cursor = self._conn.execute(
                "DELETE FROM watches WHERE guild_id = ? AND ea_id = ? AND user_id = ?",
                (guild_id, ea_id, user_id),
            )
        self._conn.commit()
        return cursor.rowcount

    def list_watches(self, guild_id: int, user_id: int | None = None) -> list[Watch]:
        if user_id is None:
            rows = self._conn.execute(
                "SELECT * FROM watches WHERE guild_id = ? ORDER BY name",
                (guild_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM watches WHERE guild_id = ? AND user_id = ? ORDER BY name",
                (guild_id, user_id),
            ).fetchall()
        return [_watch_from_row(row) for row in rows]

    def all_watches(self) -> list[Watch]:
        rows = self._conn.execute("SELECT * FROM watches").fetchall()
        return [_watch_from_row(row) for row in rows]

    def update_watch_prices(
        self,
        watch_id: int,
        last_price_ps5: int | None,
        last_price_pc: int | None,
        alerted: bool,
    ) -> None:
        if alerted:
            self._conn.execute(
                """
                UPDATE watches
                SET last_price_ps5 = ?, last_price_pc = ?, last_alert_at = ?
                WHERE id = ?
                """,
                (last_price_ps5, last_price_pc, time.time(), watch_id),
            )
        else:
            self._conn.execute(
                """
                UPDATE watches
                SET last_price_ps5 = ?, last_price_pc = ?
                WHERE id = ?
                """,
                (last_price_ps5, last_price_pc, watch_id),
            )
        self._conn.commit()

    def load_snapshot(self, platform: Platform) -> dict[int, int]:
        row = self._conn.execute(
            "SELECT prices_json FROM market_state WHERE platform = ?",
            (platform,),
        ).fetchone()
        if row is None:
            return {}
        raw = json.loads(row["prices_json"])
        return {int(key): int(value) for key, value in raw.items()}

    def save_snapshot(self, platform: Platform, prices: dict[int, int]) -> None:
        self._conn.execute(
            """
            INSERT INTO market_state (platform, prices_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(platform) DO UPDATE SET
                prices_json = excluded.prices_json,
                updated_at = excluded.updated_at
            """,
            (platform, json.dumps({str(k): v for k, v in prices.items()}), time.time()),
        )
        self._conn.commit()


def _watch_from_row(row: sqlite3.Row) -> Watch:
    return Watch(
        id=row["id"],
        guild_id=row["guild_id"],
        user_id=row["user_id"],
        ea_id=row["ea_id"],
        name=row["name"],
        rating=row["rating"],
        position=row["position"],
        rarity=row["rarity"],
        club=row["club"],
        url=row["url"],
        image_url=row["image_url"],
        platform=row["platform"],
        threshold_pct=row["threshold_pct"],
        threshold_coins=row["threshold_coins"],
        last_price_ps5=row["last_price_ps5"],
        last_price_pc=row["last_price_pc"],
        last_alert_at=row["last_alert_at"],
        created_at=row["created_at"],
        target_below=row["target_below"] if "target_below" in row.keys() else None,
    )
