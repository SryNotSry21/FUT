"""Legal texts shown in Discord (privacy, server setup)."""

from __future__ import annotations

from datetime import datetime, timezone

import discord

from futbot.branding import BOT_NAME, COPYRIGHT, FOOTER, INVITE_URL

PRIVACY_TITLE = "Datenschutzerklärung"
PRIVACY_UPDATED = "19. September 2026"


def privacy_embed() -> discord.Embed:
    embed = discord.Embed(
        title=f"{PRIVACY_TITLE} — {BOT_NAME}",
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc),
        description=(
            f"Stand: {PRIVACY_UPDATED}. Betreiber: **21Drehen**.\n"
            "Diese Erklärung gilt für die Discord-Anwendung. "
            "Ergänzend gelten die Datenschutzhinweise von Discord."
        ),
    )
    embed.add_field(
        name="Welche Daten?",
        value=(
            "• Discord-Nutzer-ID (Inhaber von `/watch` / `/beobachten`, Erwähnung beim Alert)\n"
            "• Server-ID und Alert-Kanal-ID (`/setup`)\n"
            "• Watch-Einstellungen (Karten-ID, Name, Plattform, Schwelle, optional Zielpreis)\n"
            "• Markt-Preis-Snapshots ohne Nutzerbezug"
        ),
        inline=False,
    )
    embed.add_field(
        name="Was wir nicht speichern",
        value=(
            "Keine Nachrichteninhalte, keine E-Mail, keine IP, keine Zahlungsdaten, "
            "**keine EA-Zugangsdaten**. Es gibt keinen EA-Login und keinen Message-Content-Intent."
        ),
        inline=False,
    )
    embed.add_field(
        name="Wozu und auf welcher Grundlage?",
        value=(
            "Damit der Bot Befehle und Alerts ausführen kann (Vertrag / angeforderte Leistung) "
            "und um den Dienst stabil zu betreiben (berechtigtes Interesse). "
            "Kein Verkauf von Daten, keine Werbung."
        ),
        inline=False,
    )
    embed.add_field(
        name="Empfänger",
        value=(
            "• **Discord** — Slash-Befehle und Antworten\n"
            "• **FUT.GG** — nur Spielername oder Karten-ID, nicht deine Discord-ID\n"
            "• Hoster der Bot-Datenbank, falls vorhanden"
        ),
        inline=False,
    )
    embed.add_field(
        name="Speicherdauer und deine Rechte",
        value=(
            "Watches bleiben bis `/unwatch`, Admin-Löschung oder Entfernen des Bots. "
            "Du kannst Auskunft, Berichtigung und Löschung verlangen "
            "(DSGVO, soweit anwendbar). Liste: `/watches` / `/beobachtungen`."
        ),
        inline=False,
    )
    embed.add_field(
        name="Kontakt",
        value="GitHub Issues: https://github.com/SryNotSry21/FUT/issues",
        inline=False,
    )
    embed.set_footer(text=FOOTER)
    return embed


def setup_guide_embed() -> discord.Embed:
    embed = discord.Embed(
        title=f"Einrichten — {BOT_NAME}",
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc),
        description=(
            "So nutzt du **diesen** Bot auf deinem Discord-Server. "
            "Du musst keinen eigenen Bot anlegen."
        ),
    )
    embed.add_field(
        name="1. Bot einladen",
        value=(
            "Du brauchst die Berechtigung **Server verwalten**.\n"
            f"[Bot einladen]({INVITE_URL})"
        ),
        inline=False,
    )
    embed.add_field(
        name="2. Channel vorbereiten",
        value=(
            "Lege einen Textkanal für Markt-Alerts an (z. B. `#markt-alerts`). "
            "Der Bot braucht dort: Nachrichten senden, Links einbetten, Slash-Befehle."
        ),
        inline=False,
    )
    embed.add_field(
        name="3. `/setup` ausführen",
        value=(
            "`/setup kanal:#markt-alerts schwelle:10 auto_scan:True min_preis:10000`\n"
            "• **kanal** — wohin Alerts gehen\n"
            "• **schwelle** — ab wie viel Prozent Preisänderung (z. B. 10)\n"
            "• **auto_scan** — marktweite Pumps/Crashes automatisch posten\n"
            "• **min_preis** — günstige Karten darunter ignorieren"
        ),
        inline=False,
    )
    embed.add_field(
        name="4. Optional: eigene Karten",
        value=(
            "• `/watch` — Alert bei starker %-Änderung\n"
            "• `/beobachten unter:2000000` — Alert, wenn der Preis unter deinen Zielwert fällt\n"
            "• `/schnappchen` — aktuell günstiger als die andere Plattform"
        ),
        inline=False,
    )
    embed.add_field(
        name="Hilfe",
        value="`/hilfe` alle Befehle · `/datenschutz` Daten · Diesen Bot nicht nachbauen oder kopieren.",
        inline=False,
    )
    embed.set_footer(text=f"{FOOTER} · {COPYRIGHT}")
    return embed
