from __future__ import annotations

import logging
import time
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands, tasks

from futbot.branding import COPYRIGHT, HELP_TITLE
from futbot.config import Settings
from futbot.db import Store, Watch
from futbot.formatting import (
    bargains_embed,
    compare_embed,
    format_coins,
    format_pct,
    move_embed,
    movers_embed,
    player_embed,
    search_embed,
)
from futbot.legal import privacy_embed, setup_guide_embed
from futbot.market.models import PlayerCard, Platform, PriceMove, WatchPlatform
from futbot.market.service import MarketService
from futbot.security import (
    CooldownMap,
    TtlCache,
    cached_call,
    can_manage_watch,
    can_post_manual_alert,
)

logger = logging.getLogger(__name__)

PlatformChoice = Literal["ps5", "pc", "beide"]


def _is_guild_manager(interaction: discord.Interaction) -> bool:
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms and perms.manage_guild)


class PlayerPickView(discord.ui.View):
    def __init__(self, cards: list[PlayerCard], callback, owner_id: int) -> None:
        super().__init__(timeout=60)
        self.callback_fn = callback
        self.owner_id = owner_id
        options = [
            discord.SelectOption(
                label=card.label[:100],
                value=str(card.ea_id),
                description=(card.club or card.rarity)[:100],
            )
            for card in cards[:25]
        ]
        self.select = discord.ui.Select(placeholder="Karte auswählen", options=options)
        self.select.callback = self._picked
        self.add_item(self.select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.owner_id:
            return True
        await interaction.response.send_message(
            "Nur wer den Befehl ausgeführt hat, kann die Karte auswählen.",
            ephemeral=True,
        )
        return False

    async def _picked(self, interaction: discord.Interaction) -> None:
        ea_id = int(self.select.values[0])
        await self.callback_fn(interaction, ea_id)
        self.stop()


class MarketCog(commands.Cog):
    def __init__(self, bot: commands.Bot, settings: Settings, store: Store, market: MarketService) -> None:
        self.bot = bot
        self.settings = settings
        self.store = store
        self.market = market
        self.poll_market.change_interval(seconds=settings.poll_interval_seconds)
        self._search_cache = TtlCache(ttl_seconds=45)
        self._autocomplete_cooldown = CooldownMap(seconds=2)
        self._alert_cooldown = CooldownMap(seconds=60)

    async def cog_load(self) -> None:
        self.poll_market.start()

    async def cog_unload(self) -> None:
        self.poll_market.cancel()

    async def _autocomplete_player(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        if len(current.strip()) < 3:
            return []
        if not self._autocomplete_cooldown.hit(interaction.user.id):
            return []
        try:
            cards = await cached_call(
                self._search_cache,
                current.strip().lower(),
                lambda: self.market.search(current, limit=8),
            )
        except Exception:
            logger.exception("Autocomplete search failed")
            return []
        return [
            app_commands.Choice(name=card.label[:100], value=str(card.ea_id))
            for card in cards[:20]
        ]

    @app_commands.command(name="preis", description="Aktuellen EA-FC-27-Marktpreis einer Karte anzeigen")
    @app_commands.describe(spieler="Name oder ausgewählte Karte")
    @app_commands.autocomplete(spieler=_autocomplete_player)
    async def preis(self, interaction: discord.Interaction, spieler: str) -> None:
        await interaction.response.defer()
        cards = await self._lookup(spieler)
        if not cards:
            await interaction.followup.send(f"Keine FC-27-Karte für **{spieler}** gefunden.")
            return
        if len(cards) == 1:
            quote = await self.market.quote_player(cards[0])
            await interaction.followup.send(embed=player_embed(quote))
            return

        async def picked(inter: discord.Interaction, ea_id: int) -> None:
            card = next(c for c in cards if c.ea_id == ea_id)
            quote = await self.market.quote_player(card)
            await inter.response.edit_message(content=None, embed=player_embed(quote), view=None)

        await interaction.followup.send(
            "Mehrere Karten gefunden — bitte eine auswählen:",
            embed=search_embed(spieler, cards),
            view=PlayerPickView(cards, picked, owner_id=interaction.user.id),
        )

    @app_commands.command(name="suche", description="FC-27-Spieler über die FUT.GG-API suchen")
    @app_commands.describe(spieler="Spielername")
    async def suche(self, interaction: discord.Interaction, spieler: str) -> None:
        await interaction.response.defer()
        cards = await self.market.search(spieler, limit=10)
        await interaction.followup.send(embed=search_embed(spieler, cards))

    @app_commands.command(name="vergleichen", description="Zwei FC-27-Kartenpreise vergleichen")
    @app_commands.describe(spieler1="Erste Karte", spieler2="Zweite Karte")
    @app_commands.autocomplete(spieler1=_autocomplete_player, spieler2=_autocomplete_player)
    async def vergleichen(
        self, interaction: discord.Interaction, spieler1: str, spieler2: str
    ) -> None:
        await interaction.response.defer()
        left_cards, right_cards = await self._lookup(spieler1), await self._lookup(spieler2)
        if not left_cards or not right_cards:
            await interaction.followup.send("Mindestens eine der Karten wurde nicht gefunden.")
            return
        left = await self.market.quote_player(left_cards[0])
        right = await self.market.quote_player(right_cards[0])
        await interaction.followup.send(embed=compare_embed(left, right))

    @app_commands.command(
        name="watch",
        description="Manuellen Preis-Alert für eine bestimmte Karte setzen",
    )
    @app_commands.describe(
        spieler="Karte, die überwacht werden soll",
        plattform="Welche Preise auslösen",
        schwelle_prozent="Prozentuale Änderung (Standard: Server-Wert)",
        schwelle_coins="Optional: absolute Coin-Änderung",
        unter="Optional: Alert, wenn der Preis unter diesen Wert fällt",
    )
    @app_commands.autocomplete(spieler=_autocomplete_player)
    async def watch(
        self,
        interaction: discord.Interaction,
        spieler: str,
        plattform: PlatformChoice = "beide",
        schwelle_prozent: app_commands.Range[float, 1, 90] | None = None,
        schwelle_coins: app_commands.Range[int, 100, 10_000_000] | None = None,
        unter: app_commands.Range[int, 500, 15_000_000] | None = None,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Nur auf einem Server nutzbar.", ephemeral=True)
            return
        await interaction.response.defer()
        cards = await self._lookup(spieler)
        if not cards:
            await interaction.followup.send(f"Keine Karte für **{spieler}** gefunden.")
            return
        settings = self.store.get_guild(interaction.guild.id)
        threshold = schwelle_prozent if schwelle_prozent is not None else settings.default_threshold_pct

        async def save(inter: discord.Interaction, card: PlayerCard) -> None:
            quote = await self.market.quote_player(card)
            existing = self.store.get_user_watch(interaction.guild.id, inter.user.id, card.ea_id)  # type: ignore[union-attr]
            watch = self.store.add_watch(
                guild_id=interaction.guild.id,  # type: ignore[union-attr]
                user_id=inter.user.id,
                player=card,
                platform=plattform,
                threshold_pct=float(threshold),
                threshold_coins=int(schwelle_coins) if schwelle_coins else None,
                target_below=int(unter) if unter else (existing.target_below if existing else None),
            )
            self.store.update_watch_prices(
                watch.id, quote.ps5.price, quote.pc.price, alerted=False
            )
            text = (
                f"Alert für **{card.label}** ist aktiv.\n"
                f"Schwelle: {format_pct(float(threshold))}"
                + (f" oder {format_coins(int(schwelle_coins))}" if schwelle_coins else "")
                + (f"\nUnter: {format_coins(watch.target_below)}" if watch.target_below else "")
                + f"\nPlattform: {plattform}\n"
                f"Aktuell PS {format_coins(quote.ps5.price)} · PC {format_coins(quote.pc.price)}"
            )
            if inter.response.is_done():
                await inter.followup.send(text, embed=player_embed(quote, title="Watch gesetzt"))
            else:
                await inter.response.edit_message(content=text, embed=player_embed(quote, title="Watch gesetzt"), view=None)

        if len(cards) == 1:
            await save(interaction, cards[0])
            return

        async def picked(inter: discord.Interaction, ea_id: int) -> None:
            card = next(c for c in cards if c.ea_id == ea_id)
            await save(inter, card)

        await interaction.followup.send(
            "Welche Karte soll überwacht werden?",
            embed=search_embed(spieler, cards),
            view=PlayerPickView(cards, picked, owner_id=interaction.user.id),
        )

    @app_commands.command(
        name="beobachten",
        description="Beobachtungsliste: Alert, wenn der Preis unter einen Zielwert fällt",
    )
    @app_commands.describe(
        spieler="Karte",
        unter="Alert, sobald der Preis diesen Wert erreicht oder unterschreitet",
        plattform="Welche Preise geprüft werden",
    )
    @app_commands.autocomplete(spieler=_autocomplete_player)
    async def beobachten(
        self,
        interaction: discord.Interaction,
        spieler: str,
        unter: app_commands.Range[int, 500, 15_000_000],
        plattform: PlatformChoice = "beide",
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Nur auf einem Server nutzbar.", ephemeral=True)
            return
        await interaction.response.defer()
        cards = await self._lookup(spieler)
        if not cards:
            await interaction.followup.send(f"Keine Karte für **{spieler}** gefunden.")
            return
        target = int(unter)

        async def save(inter: discord.Interaction, card: PlayerCard) -> None:
            quote = await self.market.quote_player(card)
            existing = self.store.get_user_watch(interaction.guild.id, inter.user.id, card.ea_id)  # type: ignore[union-attr]
            watch = self.store.add_watch(
                guild_id=interaction.guild.id,  # type: ignore[union-attr]
                user_id=inter.user.id,
                player=card,
                platform=plattform,
                threshold_pct=existing.threshold_pct if existing else 0.0,
                threshold_coins=existing.threshold_coins if existing else None,
                target_below=target,
            )
            self.store.update_watch_prices(
                watch.id, quote.ps5.price, quote.pc.price, alerted=False
            )
            already = []
            if plattform in ("ps5", "beide") and quote.ps5.price is not None and quote.ps5.price <= target:
                already.append(f"PS {format_coins(quote.ps5.price)}")
            if plattform in ("pc", "beide") and quote.pc.price is not None and quote.pc.price <= target:
                already.append(f"PC {format_coins(quote.pc.price)}")
            text = (
                f"**{card.label}** steht auf der Beobachtungsliste.\n"
                f"Alert, wenn der Preis **unter {format_coins(target)}** fällt.\n"
                f"Plattform: {plattform}\n"
                f"Aktuell PS {format_coins(quote.ps5.price)} · PC {format_coins(quote.pc.price)}"
            )
            if already:
                text += (
                    "\n\nDer Preis liegt **jetzt schon** darunter ("
                    + ", ".join(already)
                    + "). Der Alert kommt, sobald er erst wieder darüber liegt und dann erneut darunter fällt."
                )
            if inter.response.is_done():
                await inter.followup.send(text, embed=player_embed(quote, title="Beobachtung gesetzt"))
            else:
                await inter.response.edit_message(
                    content=text, embed=player_embed(quote, title="Beobachtung gesetzt"), view=None
                )

        if len(cards) == 1:
            await save(interaction, cards[0])
            return

        async def picked(inter: discord.Interaction, ea_id: int) -> None:
            card = next(c for c in cards if c.ea_id == ea_id)
            await save(inter, card)

        await interaction.followup.send(
            "Welche Karte soll beobachtet werden?",
            embed=search_embed(spieler, cards),
            view=PlayerPickView(cards, picked, owner_id=interaction.user.id),
        )

    @app_commands.command(name="unwatch", description="Manuellen Preis-Alert für eine Karte entfernen")
    @app_commands.describe(spieler="Karte")
    @app_commands.autocomplete(spieler=_autocomplete_player)
    async def unwatch(self, interaction: discord.Interaction, spieler: str) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Nur auf einem Server nutzbar.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        manager = _is_guild_manager(interaction)
        cards = await self._lookup(spieler)
        ea_id: int | None = cards[0].ea_id if cards else None
        if ea_id is None:
            matches = [
                watch
                for watch in self.store.list_watches(interaction.guild.id)
                if spieler.lower() in watch.name.lower() or spieler == str(watch.ea_id)
            ]
            if not matches:
                await interaction.followup.send("Kein passender Alert gefunden.")
                return
            ea_id = matches[0].ea_id
        watches = self.store.find_watches(interaction.guild.id, ea_id)
        if not watches:
            await interaction.followup.send("Diese Karte wurde nicht beobachtet.")
            return
        allowed = [
            watch
            for watch in watches
            if can_manage_watch(
                actor_id=interaction.user.id,
                owner_id=watch.user_id,
                is_guild_manager=manager,
            )
        ]
        if not allowed:
            await interaction.followup.send(
                "Du kannst nur deine eigenen Alerts entfernen."
            )
            return
        if manager:
            removed = self.store.remove_watch(interaction.guild.id, ea_id)
        else:
            removed = self.store.remove_watch(
                interaction.guild.id, ea_id, user_id=interaction.user.id
            )
        await interaction.followup.send(
            f"{removed} Alert(s) für **{watches[0].name}** entfernt."
        )

    @app_commands.command(name="watches", description="Alle manuellen Spieler-Alerts dieses Servers anzeigen")
    async def watches(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Nur auf einem Server nutzbar.", ephemeral=True)
            return
        manager = _is_guild_manager(interaction)
        watches = self.store.list_watches(
            interaction.guild.id,
            user_id=None if manager else interaction.user.id,
        )
        if not watches:
            await interaction.response.send_message("Keine manuellen Alerts. Setze einen mit `/watch`.")
            return
        lines = []
        for watch in watches:
            owner = f" · <@{watch.user_id}>" if manager else ""
            lines.append(
                f"• **{watch.name}** {watch.rating} {watch.position} · {watch.platform} · "
                + (
                    f"unter {format_coins(watch.target_below)}"
                    if watch.target_below
                    else format_pct(watch.threshold_pct)
                )
                + (
                    f" · {format_pct(watch.threshold_pct)}"
                    if watch.target_below and watch.threshold_pct
                    else ""
                )
                + (f" / {format_coins(watch.threshold_coins)}" if watch.threshold_coins else "")
                + f" · PS {format_coins(watch.last_price_ps5)} · PC {format_coins(watch.last_price_pc)}"
                + owner
            )
        embed = discord.Embed(title="Manuelle Alerts", description="\n".join(lines), color=0x2ECC71)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="beobachtungen",
        description="Deine Beobachtungsliste: Alerts unter einem Zielpreis",
    )
    async def beobachtungen(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Nur auf einem Server nutzbar.", ephemeral=True)
            return
        manager = _is_guild_manager(interaction)
        watches = [
            watch
            for watch in self.store.list_watches(
                interaction.guild.id,
                user_id=None if manager else interaction.user.id,
            )
            if watch.target_below
        ]
        if not watches:
            await interaction.response.send_message(
                "Keine Zielpreis-Beobachtungen. Setze eine mit `/beobachten spieler:… unter:…`."
            )
            return
        lines = []
        for watch in watches:
            owner = f" · <@{watch.user_id}>" if manager else ""
            lines.append(
                f"• **{watch.name}** {watch.rating} {watch.position} · {watch.platform} · "
                f"Alert unter {format_coins(watch.target_below)}"
                f" · PS {format_coins(watch.last_price_ps5)} · PC {format_coins(watch.last_price_pc)}"
                + owner
            )
        embed = discord.Embed(
            title="Beobachtungsliste",
            description="\n".join(lines),
            color=0x2ECC71,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="alert",
        description="Alert für eine Karte jetzt manuell senden (unabhängig von der Schwelle)",
    )
    @app_commands.describe(spieler="Karte")
    @app_commands.autocomplete(spieler=_autocomplete_player)
    async def alert_now(self, interaction: discord.Interaction, spieler: str) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Nur auf einem Server nutzbar.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        wait = self._alert_cooldown.remaining(interaction.user.id)
        if wait > 0:
            await interaction.followup.send(
                f"Bitte warte noch {int(wait) + 1}s, bevor du erneut `/alert` nutzt."
            )
            return
        cards = await self._lookup(spieler)
        if not cards:
            await interaction.followup.send("Karte nicht gefunden.")
            return
        card = cards[0]
        quote = await self.market.quote_player(card)
        watch = self.store.get_user_watch(interaction.guild.id, interaction.user.id, card.ea_id)
        manager = _is_guild_manager(interaction)
        if not can_post_manual_alert(
            actor_id=interaction.user.id,
            owner_id=watch.user_id if watch else None,
            is_guild_manager=manager,
        ):
            await interaction.followup.send(
                "Manuelle Alerts in den Kanal gehen nur für eigene `/watch`-Karten oder mit Server verwalten."
            )
            return
        old = watch.last_price_ps5 if watch else None
        new = quote.ps5.price
        if old is None or new is None:
            move = PriceMove(
                ea_id=card.ea_id,
                platform="ps5",
                old_price=old or new or 0,
                new_price=new or 0,
                delta=(new or 0) - (old or 0),
                pct=0.0,
                player=card,
            )
        else:
            move = PriceMove(
                ea_id=card.ea_id,
                platform="ps5",
                old_price=old,
                new_price=new,
                delta=new - old,
                pct=((new - old) / old) * 100 if old else 0.0,
                player=card,
            )
        channel = await self._alert_channel(interaction.guild)
        embed = move_embed(
            move,
            reason="Manuell ausgelöster Alert.",
            mention=interaction.user.mention,
        )
        if channel and channel.id != interaction.channel_id:
            await channel.send(embed=embed)
            self._alert_cooldown.hit(interaction.user.id)
            await interaction.followup.send("Alert wurde in den Alert-Kanal gesendet.", embed=embed)
        else:
            self._alert_cooldown.hit(interaction.user.id)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="markt", description="Aktuelle starke Marktbewegungen (FUT.GG Momentum)")
    @app_commands.describe(stunden="Zeitfenster in Stunden")
    async def markt(
        self,
        interaction: discord.Interaction,
        stunden: app_commands.Range[int, 6, 48] = 24,
    ) -> None:
        await interaction.response.defer()
        cards = await self.market.movers(hours=int(stunden))
        ranked = sorted(cards, key=lambda c: abs(c.momentum_pct or 0), reverse=True)
        fake_moves: list[PriceMove] = []
        drops: list[PriceMove] = []
        for card in ranked:
            pct = card.momentum_pct or 0.0
            price = card.listed_price or 0
            if price <= 0 or pct == 0:
                continue
            old = int(round(price / (1 + pct / 100))) if pct != -100 else price
            old = max(old, 1)
            move = PriceMove(
                ea_id=card.ea_id,
                platform="ps5",
                old_price=old,
                new_price=price,
                delta=price - old,
                pct=pct,
                player=card,
            )
            (drops if pct < 0 else fake_moves).append(move)
        await interaction.followup.send(
            embed=movers_embed(
                f"Markt-Momentum ({stunden}h)",
                fake_moves[:8],
                drops[:8],
                extra_lines=["Quelle: FUT.GG Momentum-API, angereichert mit Live-Preisblob."],
            )
            )

    @app_commands.command(
        name="schnappchen",
        description="Karten unter Marktwert: andere Plattform, letzter Scan oder Vorjahrespreis",
    )
    @app_commands.describe(
        min_prozent="Mindest-Abstand zum Vergleichspreis",
        min_preis="Mindestpreis der günstigen Seite",
    )
    async def schnappchen(
        self,
        interaction: discord.Interaction,
        min_prozent: app_commands.Range[float, 10, 80] = 20.0,
        min_preis: app_commands.Range[int, 1000, 500_000] = 15_000,
    ) -> None:
        await interaction.response.defer()
        platform_deals = await self.market.platform_bargains(
            min_price=int(min_preis),
            min_pct=float(min_prozent),
            limit=8,
        )
        previous = self.store.load_snapshot("ps5")
        market_deals = await self.market.below_recent_bargains(
            previous,
            "ps5",
            min_price=int(min_preis),
            min_pct=float(min_prozent),
            limit=8,
        )
        year_deals = await self.market.year_bargains(
            min_price=int(min_preis),
            min_pct=float(min_prozent),
            limit=8,
        )
        previous_year = self.market.game_year - 1
        await interaction.followup.send(
            embed=bargains_embed(
                platform_deals,
                market_deals,
                extra_lines=[
                    "Kein EA-Transfermarkt — einzelne unter Preis gelistete Auktionen sieht der Bot nicht.",
                    "Vergleich: FUT.GG-BIN vs. andere Plattform, letzter Scan oder Vorjahr.",
                    f"Schwelle {format_pct(float(min_prozent))} · ab {format_coins(int(min_preis))}",
                ],
                year_deals=year_deals,
                previous_game_year=previous_year,
            )
        )

    @app_commands.command(name="setup", description="Alert-Kanal und Auto-Scan auf diesem Server festlegen")
    @app_commands.describe(
        kanal="Kanal für automatische und manuelle Alerts",
        schwelle="Standard-Prozentschwelle für starke Bewegungen",
        auto_scan="Marktweit automatisch auf Pumps/Crashes scannen",
        min_preis="Mindestpreis für den Auto-Scan",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        kanal: discord.TextChannel,
        schwelle: app_commands.Range[float, 1, 50] = 10,
        auto_scan: bool = True,
        min_preis: app_commands.Range[int, 0, 1_000_000] = 10_000,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Nur auf einem Server nutzbar.", ephemeral=True)
            return
        settings = self.store.get_guild(interaction.guild.id)
        settings.alert_channel_id = kanal.id
        settings.default_threshold_pct = float(schwelle)
        settings.scan_enabled = auto_scan
        settings.scan_min_price = int(min_preis)
        self.store.upsert_guild(settings)
        await interaction.response.send_message(
            f"Alerts gehen nach {kanal.mention}.\n"
            f"Auto-Scan: {'an' if auto_scan else 'aus'} ab {format_coins(int(min_preis))}, "
            f"Schwelle {format_pct(float(schwelle))}."
        )

    @app_commands.command(name="hilfe", description="Befehle des EA FC 27 Markt-Bots von 21Drehen")
    async def hilfe(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title=HELP_TITLE,
            color=0x2ECC71,
            description=(
                "Der Bot zeigt Live-Preise zu EA FC 27 Ultimate Team und sendet Alerts "
                "bei starken Marktbewegungen.\n\n"
                "**Einrichten:** `/einrichten` — Bot einladen, Kanal wählen, `/setup`.\n"
                "**Automatisch:** Nach `/setup` scannt der Bot den Markt im Hintergrund.\n"
                "**Manuell:** `/watch` bei %-Änderung, `/beobachten` wenn der Preis unter einen Zielwert fällt."
            ),
        )
        embed.add_field(
            name="Befehle",
            value=(
                "`/einrichten` Setup auf diesem Server\n"
                "`/setup` Alert-Kanal (Admin)\n"
                "`/preis` aktueller Preis\n"
                "`/suche` Spieler suchen\n"
                "`/vergleichen` zwei Karten vergleichen\n"
                "`/watch` Alert bei %-Änderung\n"
                "`/beobachten` Alert unter Zielpreis\n"
                "`/unwatch` Alert entfernen\n"
                "`/watches` alle manuellen Alerts\n"
                "`/beobachtungen` Beobachtungsliste (Zielpreis)\n"
                "`/alert` Alert jetzt senden\n"
                "`/markt` Momentum / Top-Mover\n"
                "`/schnappchen` unter Marktwert / Plattform / Vorjahr\n"
                "`/datenschutz` Datenschutzerklärung"
            ),
            inline=False,
        )
        embed.set_footer(text=COPYRIGHT)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="einrichten",
        description="So richtest du diesen Bot auf dem Server ein (kein eigener Bot nötig)",
    )
    async def einrichten(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=setup_guide_embed())

    @app_commands.command(
        name="datenschutz",
        description="Datenschutzerklärung des EA FC 27 Markt-Bots von 21Drehen",
    )
    async def datenschutz(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(embed=privacy_embed())

    async def _lookup(self, query: str) -> list[PlayerCard]:
        query = query.strip()
        if query.isdigit():
            card = await self.market.player_by_id(int(query))
            return [card] if card else []
        return await self.market.search(query, limit=8)

    async def _alert_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        settings = self.store.get_guild(guild.id)
        if settings.alert_channel_id:
            channel = guild.get_channel(settings.alert_channel_id)
            if isinstance(channel, discord.TextChannel):
                return channel
        return None

    @tasks.loop(seconds=120)
    async def poll_market(self) -> None:
        try:
            await self._run_scan()
        except Exception:
            logger.exception("Market poll failed")

    @poll_market.before_loop
    async def before_poll(self) -> None:
        await self.bot.wait_until_ready()

    async def _run_scan(self) -> None:
        catalog = await self.market.catalog(force=True)
        now = time.time()
        watches = self.store.all_watches()
        guilds = {guild.id: guild for guild in self.bot.guilds}

        for watch in watches:
            guild = guilds.get(watch.guild_id)
            if guild is None:
                continue
            settings = self.store.get_guild(watch.guild_id)
            quote = catalog.quote(watch.as_player())
            tagged = self._watch_moves(watch, quote.ps5.price, quote.pc.price, settings.cooldown_minutes, now)
            if tagged:
                moves = [move for move, _reason in tagged]
                await self._hydrate_moves(moves)
                channel = await self._alert_channel(guild)
                if channel:
                    for move, (_original, reason) in zip(moves, tagged):
                        await channel.send(
                            embed=move_embed(
                                move,
                                reason=reason,
                                mention=f"<@{watch.user_id}>",
                            )
                        )
            self.store.update_watch_prices(
                watch.id, quote.ps5.price, quote.pc.price, alerted=bool(tagged)
            )

        for settings in self.store.all_guilds_with_alerts():
            if not settings.scan_enabled:
                continue
            guild = guilds.get(settings.guild_id)
            if guild is None:
                continue
            previous = self.store.load_snapshot(settings.scan_platform)
            current = catalog.snapshot(settings.scan_platform)
            if previous:
                risers, fallers = await self.market.scan_snapshot_moves(
                    previous,
                    settings.scan_platform,
                    threshold_pct=settings.default_threshold_pct,
                    min_price=settings.scan_min_price,
                    limit=8,
                )
                if risers or fallers:
                    watched_ids = {watch.ea_id for watch in self.store.list_watches(settings.guild_id)}
                    await self._hydrate_moves(risers)
                    await self._hydrate_moves(fallers)
                    channel = await self._alert_channel(guild)
                    if channel:
                        auto_risers = [m for m in risers if m.ea_id not in watched_ids]
                        auto_fallers = [m for m in fallers if m.ea_id not in watched_ids]
                        if auto_risers or auto_fallers:
                            await channel.send(
                                embed=movers_embed(
                                    "Automatischer Markt-Scan",
                                    auto_risers,
                                    auto_fallers,
                                    extra_lines=[
                                        f"Schwelle {format_pct(settings.default_threshold_pct)} · "
                                        f"ab {format_coins(settings.scan_min_price)} · "
                                        f"{settings.scan_platform.upper()}"
                                    ],
                                )
                            )
            self.store.save_snapshot(settings.scan_platform, current)

        # Keep a global snapshot even without guild scan so first /alert has a baseline.
        self.store.save_snapshot("ps5", catalog.snapshot("ps5"))
        self.store.save_snapshot("pc", catalog.snapshot("pc"))

    def _watch_moves(
        self,
        watch: Watch,
        ps5_price: int | None,
        pc_price: int | None,
        cooldown_minutes: int,
        now: float,
    ) -> list[tuple[PriceMove, str]]:
        platforms: list[tuple[Platform, int | None, int | None]] = []
        if watch.platform in ("ps5", "beide"):
            platforms.append(("ps5", watch.last_price_ps5, ps5_price))
        if watch.platform in ("pc", "beide"):
            platforms.append(("pc", watch.last_price_pc, pc_price))
        stored = watch.as_player()
        player = None if not watch.name or watch.name in {"Unbekannt", str(watch.ea_id)} else stored
        results: list[tuple[PriceMove, str]] = []
        seen: set[Platform] = set()
        for platform, old, new in platforms:
            move = self.market.watch_below_move(
                watch.ea_id, platform, old, new, watch.target_below, player=player
            )
            if move:
                results.append(
                    (
                        move,
                        f"Beobachtung · Preis unter {format_coins(watch.target_below)}",
                    )
                )
                seen.add(platform)
        if watch.last_alert_at and now - watch.last_alert_at < cooldown_minutes * 60:
            return results
        for platform, old, new in platforms:
            if platform in seen:
                continue
            move = self.market.watch_move(
                watch.ea_id,
                platform,
                old,
                new,
                watch.threshold_pct,
                watch.threshold_coins,
                player=player,
            )
            if move:
                reason = f"Manueller Watch · Schwelle {format_pct(watch.threshold_pct)}"
                if watch.threshold_coins:
                    reason += f" / {format_coins(watch.threshold_coins)}"
                results.append((move, reason))
        return results

    async def _hydrate_moves(self, moves: list[PriceMove]) -> None:
        await self.market.hydrate_moves(moves)


async def setup(bot: commands.Bot) -> None:
    raise RuntimeError("Use bot.py to add MarketCog with dependencies")
