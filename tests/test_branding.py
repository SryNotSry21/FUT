from futbot.branding import BOT_NAME


def test_bot_name_fits_discord_nickname_limit() -> None:
    assert BOT_NAME == "EA FC 27 Markt-Bot von 21Drehen"
    assert 2 <= len(BOT_NAME) <= 32
