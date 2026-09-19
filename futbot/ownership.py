"""Refuse unofficial copies of the official Discord application."""

from __future__ import annotations

import base64

from futbot.branding import BOT_CLIENT_ID, BOT_NAME

UNOFFICIAL_COPY_MESSAGE = (
    f"{BOT_NAME} darf nicht als eigene Kopie betrieben werden. "
    "Nur die offizielle Discord-Anwendung von 21Drehen ist zulässig. "
    "Siehe LICENSE."
)


def application_id_from_token(token: str) -> int | None:
    """Read the Discord application id encoded in a bot token prefix."""
    try:
        payload = token.strip().split(".", 1)[0]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("ascii"))
        return int(decoded.decode("ascii"))
    except Exception:
        return None


def ensure_official_instance(token: str, *, user_id: int | None = None) -> None:
    """Raise PermissionError if this process is not the official bot."""
    token_id = application_id_from_token(token)
    if token_id is not None and token_id != BOT_CLIENT_ID:
        raise PermissionError(UNOFFICIAL_COPY_MESSAGE)
    if user_id is not None and user_id != BOT_CLIENT_ID:
        raise PermissionError(UNOFFICIAL_COPY_MESSAGE)
