from futbot.legal import PRIVACY_TITLE, privacy_embed


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
