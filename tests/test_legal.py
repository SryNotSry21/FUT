from futbot.branding import COPYRIGHT, INVITE_URL
from futbot.legal import PRIVACY_TITLE, privacy_embed, setup_guide_embed


def test_privacy_embed_is_german_and_complete() -> None:
    embed = privacy_embed()
    assert PRIVACY_TITLE in embed.title
    names = [field.name for field in embed.fields]
    assert "Welche Daten?" in names
    assert "Kontakt" in names
    text = " ".join(field.value for field in embed.fields)
    assert "EA-Zugangsdaten" in text
    assert "Discord-Nutzer-ID" in text
    assert "/unwatch" in text


def test_setup_guide_is_invite_only_not_bot_creation() -> None:
    embed = setup_guide_embed()
    assert "Einrichten" in embed.title
    names = [field.name for field in embed.fields]
    assert "1. Bot einladen" in names
    assert "3. `/setup` ausführen" in names
    body = " ".join([embed.description or "", *(field.value for field in embed.fields)])
    assert INVITE_URL in body
    assert "keinen eigenen Bot" in body
    assert "/setup" in body
    lowered = body.lower()
    assert "discord.com/developers" not in lowered
    assert "token" not in lowered
    assert "anwendung erstellen" not in lowered
    assert COPYRIGHT in (embed.footer.text or "")
