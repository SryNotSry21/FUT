from futbot.market.parse import parse_global_search_hit, parse_player_card


MBAPPE = {
    "eaId": 231747,
    "overall": 91,
    "commonName": "Kylian Mbappé",
    "cardName": "Mbappé",
    "rarityName": "Rare",
    "position": "ST",
    "url": "/players/231747-kylian-mbappe/27-231747/",
    "cardImageUrl": "https://example.com/card.webp",
    "club": {"name": "Real Madrid"},
    "nation": {"name": "France"},
    "league": {"name": "LALIGA EA SPORTS"},
    "basePlayerEaId": 231747,
    "quality": "GOLD",
    "currentDbPrice": None,
    "momentumPercentage": None,
}


def test_parse_player_card() -> None:
    card = parse_player_card(MBAPPE)
    assert card.ea_id == 231747
    assert card.name == "Kylian Mbappé"
    assert card.rating == 91
    assert card.position == "ST"
    assert card.club == "Real Madrid"
    assert card.nation == "France"
    assert card.url.startswith("https://www.fut.gg/")
    assert "91 ST" in card.label


def test_parse_global_search_hit() -> None:
    payload = {
        "id": "player:231747",
        "meta": {
            "kind": "player",
            "basePlayerEaId": 231747,
            "firstName": "Kylian",
            "lastName": "Mbappé",
            "url": "/players/231747-kylian-mbappe/27-231747/",
            "position": "ST",
            "overall": 91,
        },
    }
    card = parse_global_search_hit(payload)
    assert card is not None
    assert card.ea_id == 231747
    assert card.name == "Kylian Mbappé"
