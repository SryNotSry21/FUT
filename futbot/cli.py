from __future__ import annotations

import argparse

from futbot.bot import main as run_bot


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="EA FC 27 Markt-Bot von 21Drehen")
    parser.add_argument(
        "command",
        nargs="?",
        default="bot",
        choices=("bot",),
        help="Nur die offizielle Discord-Instanz starten",
    )
    parser.parse_args(argv)
    run_bot()
