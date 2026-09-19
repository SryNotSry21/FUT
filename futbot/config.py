from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


@dataclass(frozen=True)
class Settings:
    discord_token: str
    discord_guild_id: int | None
    game_year: int
    poll_interval_seconds: int
    default_threshold_pct: float
    scan_min_price: int
    alert_cooldown_minutes: int
    database_path: Path

    @property
    def game_year_str(self) -> str:
        return str(self.game_year)


def load_settings() -> Settings:
    guild_raw = os.getenv("DISCORD_GUILD_ID", "").strip()
    db_path = Path(os.getenv("DATABASE_PATH", "data/futbot.db"))
    return Settings(
        discord_token=os.getenv("DISCORD_TOKEN", "").strip(),
        discord_guild_id=int(guild_raw) if guild_raw else None,
        game_year=_int_env("FUT_GAME_YEAR", 27),
        poll_interval_seconds=_int_env("POLL_INTERVAL_SECONDS", 120),
        default_threshold_pct=_float_env("DEFAULT_THRESHOLD_PCT", 10.0),
        scan_min_price=_int_env("SCAN_MIN_PRICE", 10_000),
        alert_cooldown_minutes=_int_env("ALERT_COOLDOWN_MINUTES", 30),
        database_path=db_path,
    )
