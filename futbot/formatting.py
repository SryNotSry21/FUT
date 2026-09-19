from __future__ import annotations

from datetime import datetime, timezone

import discord

from futbot.branding import FOOTER
from futbot.market.models import Bargain, PlayerCard, PlayerQuote, PriceMove

BRAND_COLOR = 0x2ECC71
DROP_COLOR = 0xE74C3C
RISE_COLOR = 0x3498DB
NEUTRAL_COLOR = 0xF1C40F

PLATFORM_LABEL = {"ps5": "PlayStation / Konsole", "pc": "PC"}


def format_coins(value: int | None) -> str:
    if value is None:
        return "—"
    return f"{format_coin_amount(value)} Coins"


def format_coin_amount(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def format_pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    text = f"{value:.1f}".replace(".", ",")
    return f"{sign}{text} %"


def format_delta(delta: int, pct: float) -> str:
    arrow = "▼" if delta < 0 else "▲"
    sign = "+" if delta > 0 else ""
    coins = f"{sign}{format_coin_amount(abs(delta))}"
    return f"{arrow} {coins} ({format_pct(pct)})"


def format_price_path(move: PriceMove) -> str:
    """Old price → new price plus percent, never the raw coin delta as a fake start price."""
    arrow = "▼" if move.is_drop else "▲"
    return (
        f"{arrow} {format_coin_amount(move.old_price)} → {format_coin_amount(move.new_price)} Coins "
        f"({format_pct(move.pct)})"
    )


def player_embed(quote: PlayerQuote, title: str | None = None) -> discord.Embed:
    player = quote.player
    embed = discord.Embed(
        title=title or player.label,
        url=player.url or None,
        color=BRAND_COLOR,
        timestamp=datetime.now(timezone.utc),
        description=_player_description(player),
    )
    embed.add_field(name="PS / Konsole", value=format_coins(quote.ps5.price), inline=True)
    embed.add_field(name="PC", value=format_coins(quote.pc.price), inline=True)
    spread = _spread(quote)
    embed.add_field(name="PS vs PC", value=spread, inline=True)
    if player.image_url:
        embed.set_thumbnail(url=player.image_url)
        embed.set_footer(text=FOOTER)
    return embed


def compare_embed(left: PlayerQuote, right: PlayerQuote) -> discord.Embed:
    embed = discord.Embed(
        title="Preisvergleich",
        color=NEUTRAL_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name=left.player.label, value=_quote_block(left), inline=True)
    embed.add_field(name=right.player.label, value=_quote_block(right), inline=True)
    ps_diff = _diff(left.ps5.price, right.ps5.price)
    pc_diff = _diff(left.pc.price, right.pc.price)
    embed.add_field(
        name="Differenz (links − rechts)",
        value=f"PS: {ps_diff}\nPC: {pc_diff}",
        inline=False,
    )
    if left.player.image_url:
        embed.set_thumbnail(url=left.player.image_url)
    embed.set_footer(text=FOOTER)
    return embed


def move_embed(move: PriceMove, reason: str, mention: str | None = None) -> discord.Embed:
    player = move.player
    title = "Preis-Alert"
    if player:
        shown = move_display_name(move)
        title = f"{'Crash' if move.is_drop else 'Pump'}: {player.name if player.name != 'Unbekannt' else shown}"
    color = DROP_COLOR if move.is_drop else RISE_COLOR
    description = reason
    if mention:
        description = f"{mention}\n{reason}"
    embed = discord.Embed(
        title=title,
        url=player.url if player and player.url else None,
        description=description,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    if player:
        embed.add_field(name="Karte", value=player.label, inline=False)
        if player.club:
            embed.add_field(name="Verein", value=player.club, inline=True)
    embed.add_field(name="Plattform", value=PLATFORM_LABEL.get(move.platform, move.platform), inline=True)
    embed.add_field(name="Alt", value=format_coins(move.old_price), inline=True)
    embed.add_field(name="Neu", value=format_coins(move.new_price), inline=True)
    embed.add_field(name="Veränderung", value=format_delta(move.delta, move.pct), inline=False)
    if player and player.image_url:
        embed.set_thumbnail(url=player.image_url)
    embed.set_footer(text=FOOTER)
    return embed


def movers_embed(
    title: str,
    risers: list[PriceMove],
    fallers: list[PriceMove],
    extra_lines: list[str] | None = None,
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        color=BRAND_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    if extra_lines:
        embed.description = "\n".join(extra_lines)
    embed.add_field(name="▲ Steigerungen", value=_move_list(risers) or "Keine", inline=False)
    embed.add_field(name="▼ Abstürze", value=_move_list(fallers) or "Keine", inline=False)
    embed.set_footer(text=FOOTER)
    return embed


def bargains_embed(
    platform_deals: list[Bargain],
    market_deals: list[Bargain],
    extra_lines: list[str] | None = None,
    year_deals: list[Bargain] | None = None,
    previous_game_year: int | None = None,
) -> discord.Embed:
    embed = discord.Embed(
        title="Unter Marktwert",
        color=NEUTRAL_COLOR,
        timestamp=datetime.now(timezone.utc),
        description="\n".join(
            extra_lines
            or [
                "Kein EA-Transfermarkt — keine einzelnen Snipes.",
                "Vergleich: FUT.GG-Preis vs. andere Plattform, letzter Scan oder Vorjahr.",
            ]
        ),
    )
    embed.add_field(
        name="Günstiger als die andere Plattform",
        value=_bargain_list(platform_deals) or "Keine",
        inline=False,
    )
    embed.add_field(
        name="Unter dem letzten Marktpreis",
        value=_bargain_list(market_deals) or "Keine",
        inline=False,
    )
    year_label = (
        f"Günstiger als FC {previous_game_year}"
        if previous_game_year
        else "Günstiger als letztes Jahr"
    )
    embed.add_field(
        name=year_label,
        value=_bargain_list(year_deals or []) or "Keine",
        inline=False,
    )
    embed.set_footer(text=FOOTER)
    return embed


def search_embed(query: str, cards: list[PlayerCard]) -> discord.Embed:
    embed = discord.Embed(
        title=f"Suche: {query}",
        color=BRAND_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    if not cards:
        embed.description = "Keine FC-27-Karten gefunden."
        return embed
    lines = []
    for card in cards:
        lines.append(f"**{card.label}** — {card.club or '—'} · `{card.ea_id}`")
    embed.description = "\n".join(lines)
    if cards[0].image_url:
        embed.set_thumbnail(url=cards[0].image_url)
    return embed


def _player_description(player: PlayerCard) -> str:
    bits = [part for part in (player.club, player.nation, player.league) if part]
    return " · ".join(bits) if bits else "EA FC 27"


def _quote_block(quote: PlayerQuote) -> str:
    return (
        f"{quote.player.club or '—'}\n"
        f"PS: {format_coins(quote.ps5.price)}\n"
        f"PC: {format_coins(quote.pc.price)}"
    )


def _spread(quote: PlayerQuote) -> str:
    if quote.ps5.price is None or quote.pc.price is None:
        return "—"
    delta = quote.ps5.price - quote.pc.price
    if quote.pc.price <= 0:
        return format_coins(delta)
    pct = (delta / quote.pc.price) * 100
    cheaper = "PS günstiger" if delta < 0 else "PC günstiger" if delta > 0 else "gleich"
    return f"{format_delta(delta, pct)}\n{cheaper}"


def _diff(left: int | None, right: int | None) -> str:
    if left is None or right is None:
        return "—"
    delta = left - right
    pct = (delta / right) * 100 if right else 0.0
    return format_delta(delta, pct)


def move_display_name(move: PriceMove) -> str:
    player = move.player
    if player and player.name and player.name != "Unbekannt":
        return player.label
    if player and player.name:
        return f"{player.name} · {player.rating} {player.position}".strip()
    return f"ID {move.ea_id}"


def _move_list(moves: list[PriceMove]) -> str:
    lines = []
    for move in moves[:8]:
        lines.append(f"**{move_display_name(move)}** {format_price_path(move)}")
    return "\n".join(lines)


def bargain_display_name(deal: Bargain) -> str:
    if deal.player and deal.player.name and deal.player.name != "Unbekannt":
        return deal.player.label
    return f"ID {deal.ea_id}"


def format_bargain_line(deal: Bargain) -> str:
    cheap_label = "PS" if deal.cheap_platform == "ps5" else "PC"
    fair_label = "PS" if deal.fair_platform == "ps5" else "PC"
    path = (
        f"▼ {format_coin_amount(deal.fair_price)} → {format_coin_amount(deal.cheap_price)} Coins "
        f"({format_pct(-deal.pct_below)})"
    )
    if deal.reason == "plattform":
        return f"**{bargain_display_name(deal)}** {path} · günstig auf {cheap_label} (vs {fair_label})"
    if deal.reason == "vorjahr":
        return f"**{bargain_display_name(deal)}** {path} · vs letztes Jahr ({fair_label})"
    return f"**{bargain_display_name(deal)}** {path}"


def _bargain_list(deals: list[Bargain]) -> str:
    return "\n".join(format_bargain_line(deal) for deal in deals[:8])
