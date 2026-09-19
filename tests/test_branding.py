from pathlib import Path

from futbot.branding import BOT_CLIENT_ID, BOT_NAME, COPYRIGHT, INVITE_URL


def test_bot_name_fits_discord_nickname_limit() -> None:
    assert BOT_NAME == "EA FC 27 Markt-Bot von 21Drehen"
    assert 2 <= len(BOT_NAME) <= 32


def test_invite_url_is_official_oauth() -> None:
    assert str(BOT_CLIENT_ID) in INVITE_URL
    assert "discord.com/oauth2/authorize" in INVITE_URL
    assert "applications.commands" in INVITE_URL
    assert COPYRIGHT.startswith("© 2026 21Drehen")


def test_readme_is_invite_setup_not_bot_creation() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "/einrichten" in readme
    assert "/setup" in readme
    assert INVITE_URL in readme
    lowered = readme.lower()
    assert "discord.com/developers" not in lowered
    assert "discord_token" not in lowered
    assert "venv" not in lowered
    assert "docker-compose" not in lowered
    assert "bot erstellen" not in lowered or "keinen eigenen bot erstellen" in lowered
