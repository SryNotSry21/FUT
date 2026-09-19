import base64

import pytest

from futbot.branding import BOT_CLIENT_ID
from futbot.ownership import (
    UNOFFICIAL_COPY_MESSAGE,
    application_id_from_token,
    ensure_official_instance,
)


def _token_for(app_id: int) -> str:
    payload = base64.urlsafe_b64encode(str(app_id).encode("ascii")).decode("ascii").rstrip("=")
    return f"{payload}.fake.signature"


def test_official_token_is_accepted() -> None:
    token = _token_for(BOT_CLIENT_ID)
    assert application_id_from_token(token) == BOT_CLIENT_ID
    ensure_official_instance(token)
    ensure_official_instance(token, user_id=BOT_CLIENT_ID)


def test_foreign_token_is_rejected() -> None:
    token = _token_for(999_000_111)
    with pytest.raises(PermissionError, match="nicht als eigene Kopie"):
        ensure_official_instance(token)
    assert UNOFFICIAL_COPY_MESSAGE.startswith("EA FC 27 Markt-Bot")


def test_wrong_ready_user_is_rejected() -> None:
    token = _token_for(BOT_CLIENT_ID)
    with pytest.raises(PermissionError):
        ensure_official_instance(token, user_id=1)
