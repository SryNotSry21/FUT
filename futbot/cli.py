from __future__ import annotations

import argparse
import asyncio

from futbot.config import load_settings
from futbot.formatting import format_coins, format_delta, format_pct
from futbot.market.compare import percent_change
from futbot.market.service import MarketService


async def cmd_lookup(query: str, game_year: int) -> None:
    market = MarketService(game_year=game_year)
    try:
        cards = await market.search(query, limit=8)
        if not cards:
            print(f"Keine Karte gefunden für: {query}")
            return
        catalog = await market.catalog()
        print(f"{len(cards)} Treffer für {query!r} (FC {game_year})")
        for card in cards:
            quote = catalog.quote(card)
            print(
                f"- {card.label} | {card.club or '—'} | "
                f"PS {format_coins(quote.ps5.price)} | PC {format_coins(quote.pc.price)} | "
                f"{card.url}"
            )
    finally:
        await market.aclose()


async def cmd_compare(left: str, right: str, game_year: int) -> None:
    market = MarketService(game_year=game_year)
    try:
        result = await market.compare_players(left, right)
        if result is None:
            print("Vergleich nicht möglich — eine Karte fehlt.")
            return
        a, b = result
        print(f"{a.player.label}")
        print(f"  PS {format_coins(a.ps5.price)}  PC {format_coins(a.pc.price)}")
        print(f"{b.player.label}")
        print(f"  PS {format_coins(b.ps5.price)}  PC {format_coins(b.pc.price)}")
        if a.ps5.price and b.ps5.price:
            delta = a.ps5.price - b.ps5.price
            print("PS-Differenz:", format_delta(delta, percent_change(b.ps5.price, a.ps5.price)))
    finally:
        await market.aclose()


async def cmd_movers(game_year: int, hours: int) -> None:
    market = MarketService(game_year=game_year)
    try:
        cards = await market.movers(hours=hours)
        print(f"Momentum {hours}h · {len(cards)} Karten")
        for card in cards[:15]:
            pct = format_pct(card.momentum_pct or 0)
            print(f"- {card.label}: {format_coins(card.listed_price)} ({pct})")
    finally:
        await market.aclose()


async def cmd_deals(game_year: int, min_pct: float, min_price: int) -> None:
    from futbot.formatting import format_bargain_line

    market = MarketService(game_year=game_year)
    try:
        deals = await market.platform_bargains(min_price=min_price, min_pct=min_pct, limit=12)
        print(f"Plattform-Schnäppchen · {len(deals)} Karten")
        for deal in deals:
            print("-", format_bargain_line(deal).replace("**", ""))
    finally:
        await market.aclose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EA FC 27 Markt-Bot von 21Drehen")
    sub = parser.add_subparsers(dest="command")
    lookup = sub.add_parser("lookup", help="Spieler suchen und Preise anzeigen")
    lookup.add_argument("spieler")
    compare = sub.add_parser("compare", help="Zwei Spieler vergleichen")
    compare.add_argument("spieler1")
    compare.add_argument("spieler2")
    movers = sub.add_parser("movers", help="Markt-Momentum anzeigen")
    movers.add_argument("--stunden", type=int, default=24)
    deals = sub.add_parser("deals", help="Karten unter Marktwert (PS vs PC)")
    deals.add_argument("--min-prozent", type=float, default=20.0)
    deals.add_argument("--min-preis", type=int, default=15_000)
    sub.add_parser("bot", help="Discord-Bot starten")
    return parser


def main(argv: list[str] | None = None) -> None:
    settings = load_settings()
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "bot"
    if command == "lookup":
        asyncio.run(cmd_lookup(args.spieler, settings.game_year))
    elif command == "compare":
        asyncio.run(cmd_compare(args.spieler1, args.spieler2, settings.game_year))
    elif command == "movers":
        asyncio.run(cmd_movers(settings.game_year, args.stunden))
    elif command == "deals":
        asyncio.run(cmd_deals(settings.game_year, args.min_prozent, args.min_preis))
    elif command == "bot":
        from futbot.bot import main as run_bot

        run_bot()
    else:
        parser.print_help()
