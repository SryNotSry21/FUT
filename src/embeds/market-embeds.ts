import { EmbedBuilder } from "discord.js";
import { PLATFORM_LABELS, type Platform } from "../market/platform";
import type { PlayerCard, PriceQuote, SnipeCandidate } from "../market/price-provider";
import type { PriceAlert } from "../stores/alerts-store";
import type { WatchlistEntry } from "../stores/watchlist-store";
import {
  formatCoins,
  playerHeadline,
  sourceLabel,
  trendLabel,
} from "../utils/format";
import { COLORS, FOOTER_ANALYSIS } from "./theme";

function baseEmbed(color: number): EmbedBuilder {
  return new EmbedBuilder().setColor(color).setTimestamp().setFooter({ text: FOOTER_ANALYSIS });
}

export function priceEmbed(quote: PriceQuote): EmbedBuilder {
  const { player } = quote;
  const delta = quote.currentPrice - quote.expectedPrice;
  const deltaText =
    delta === 0
      ? "auf dem Erwartungswert"
      : `${delta < 0 ? "" : "+"}${formatCoins(delta)} vs. Erwartung`;

  return baseEmbed(COLORS.price)
    .setTitle(playerHeadline(player.name, player.rating, player.version))
    .setDescription(
      `${player.position} · ${player.club} · ${player.nation}\nMarkt: **${PLATFORM_LABELS[quote.platform]}**`,
    )
    .addFields(
      { name: "Aktueller Preis", value: formatCoins(quote.currentPrice), inline: true },
      { name: "Erwartungswert", value: formatCoins(quote.expectedPrice), inline: true },
      { name: "24h-Trend", value: trendLabel(quote.change24hPercent), inline: true },
      { name: "Abweichung", value: deltaText, inline: true },
      {
        name: "Quelle",
        value: sourceLabel(quote.source, quote.cacheHit),
        inline: true,
      },
    );
}

export function snipeEmbed(
  candidates: SnipeCandidate[],
  platform: Platform,
  filters: { query?: string; maxPrice?: number; minDiscountPercent?: number },
): EmbedBuilder {
  const embed = baseEmbed(COLORS.snipe).setTitle("Snipe-Kandidaten");

  const filterBits = [
    `Plattform: **${PLATFORM_LABELS[platform]}**`,
    filters.query ? `Filter: **${filters.query}**` : "Ganzer Mock-Katalog",
    filters.maxPrice !== undefined ? `Max. ${formatCoins(filters.maxPrice)}` : undefined,
    `Mindest-Abschlag: **${filters.minDiscountPercent ?? 8} %**`,
  ].filter(Boolean);

  embed.setDescription(
    `${filterBits.join(" · ")}\nUnterbewertet gegenüber dem gespeicherten Erwartungswert — kein automatischer Kauf.`,
  );

  if (candidates.length === 0) {
    embed.addFields({
      name: "Keine Treffer",
      value:
        "Im aktuellen Cache liegt keine Karte ausreichend unter dem Erwartungspreis. Passe Filter an oder versuche es nach der nächsten Cache-Aktualisierung.",
    });
    return embed;
  }

  for (const candidate of candidates) {
    const { quote } = candidate;
    embed.addFields({
      name: `${playerHeadline(quote.player.name, quote.player.rating, quote.player.version)}  ·  −${candidate.discountPercent.toFixed(1)} %`,
      value: [
        `Jetzt **${formatCoins(quote.currentPrice)}** (Erwartung ${formatCoins(quote.expectedPrice)})`,
        `${quote.player.position} · ${quote.player.club} · ${trendLabel(quote.change24hPercent)}`,
      ].join("\n"),
    });
  }

  return embed;
}

export function alertCreatedEmbed(alert: PriceAlert): EmbedBuilder {
  const direction = alert.direction === "below" ? "fällt auf oder unter" : "steigt auf oder über";
  return baseEmbed(COLORS.alert)
    .setTitle("Preisalarm gesetzt")
    .setDescription(
      `Ich benachrichtige dich (per DM, sofern möglich), wenn **${alert.playerName}** auf **${PLATFORM_LABELS[alert.platform]}** ${direction} **${formatCoins(alert.threshold)}**.`,
    )
    .addFields(
      { name: "Karte", value: `${alert.rating} ${alert.version}`, inline: true },
      { name: "Alarm-ID", value: `\`${alert.id}\``, inline: true },
    );
}

export function alertListEmbed(alerts: PriceAlert[]): EmbedBuilder {
  const embed = baseEmbed(COLORS.alert).setTitle("Deine Preisalarme");
  if (alerts.length === 0) {
    embed.setDescription(
      "Du hast noch keine Alarme. Setze einen mit `/alert set spieler:… preis:… richtung:…`.",
    );
    return embed;
  }
  embed.setDescription(`${alerts.length} aktive${alerts.length === 1 ? "r" : ""} Alarm${alerts.length === 1 ? "" : "e"} (In-Memory, gehen beim Neustart verloren).`);
  for (const alert of alerts) {
    const direction = alert.direction === "below" ? "≤" : "≥";
    embed.addFields({
      name: `${alert.playerName} · \`${alert.id}\``,
      value: `${alert.rating} ${alert.version} · ${PLATFORM_LABELS[alert.platform]} · ${direction} ${formatCoins(alert.threshold)}`,
    });
  }
  return embed;
}

export function alertRemovedEmbed(alert: PriceAlert): EmbedBuilder {
  return baseEmbed(COLORS.success)
    .setTitle("Preisalarm entfernt")
    .setDescription(`Alarm \`${alert.id}\` für **${alert.playerName}** wurde gelöscht.`);
}

export function watchlistEmbed(
  entries: WatchlistEntry[],
  quotes: Map<string, PriceQuote | null>,
  platform: Platform,
): EmbedBuilder {
  const embed = baseEmbed(COLORS.watchlist)
    .setTitle("Deine Watchlist")
    .setDescription(
      `Preise für **${PLATFORM_LABELS[platform]}** aus dem Stunden-Cache. In-Memory — leer nach Bot-Neustart.`,
    );

  if (entries.length === 0) {
    embed.addFields({
      name: "Leer",
      value: "Füge Spieler mit `/watchlist add spieler:…` hinzu.",
    });
    return embed;
  }

  for (const entry of entries) {
    const quote = quotes.get(entry.playerId);
    const priceLine = quote
      ? `${formatCoins(quote.currentPrice)} · ${trendLabel(quote.change24hPercent)}`
      : "Kein Preis im Cache";
    embed.addFields({
      name: playerHeadline(entry.playerName, entry.rating, entry.version),
      value: priceLine,
    });
  }
  return embed;
}

export function watchlistAddedEmbed(entry: WatchlistEntry, already: boolean): EmbedBuilder {
  return baseEmbed(already ? COLORS.muted : COLORS.success)
    .setTitle(already ? "Bereits auf der Watchlist" : "Zur Watchlist hinzugefügt")
    .setDescription(
      `**${playerHeadline(entry.playerName, entry.rating, entry.version)}** ${already ? "war schon gespeichert." : "wird in `/watchlist list` angezeigt."}`,
    );
}

export function watchlistRemovedEmbed(entry: WatchlistEntry): EmbedBuilder {
  return baseEmbed(COLORS.success)
    .setTitle("Von der Watchlist entfernt")
    .setDescription(`**${entry.playerName}** wurde gelöscht.`);
}

export function notFoundEmbed(query: string): EmbedBuilder {
  return baseEmbed(COLORS.danger)
    .setTitle("Spieler nicht gefunden")
    .setDescription(
      `Keine Karte im Mock-Katalog für **${query}**.\nVersuch z. B. Mbappé, Wirtz, Yamal, Kane oder Kimmich.`,
    );
}

export function ambiguousEmbed(query: string, players: PlayerCard[]): EmbedBuilder {
  const lines = players
    .slice(0, 8)
    .map((player) => `• **${playerHeadline(player.name, player.rating, player.version)}** · ${player.club}`)
    .join("\n");
  return baseEmbed(COLORS.muted)
    .setTitle("Mehrere Treffer")
    .setDescription(
      `Für **${query}** gibt es mehrere Karten. Sei spezifischer (Name + Version, z. B. \`Wirtz TOTW\`):\n\n${lines}`,
    );
}

export function errorEmbed(message: string): EmbedBuilder {
  return baseEmbed(COLORS.danger)
    .setTitle("Fehler")
    .setDescription(message);
}

export function missingAlertEmbed(id: string): EmbedBuilder {
  return baseEmbed(COLORS.danger)
    .setTitle("Alarm nicht gefunden")
    .setDescription(`Kein Alarm mit ID \`${id}\` in deiner Liste.`);
}

export function missingWatchlistEmbed(query: string): EmbedBuilder {
  return baseEmbed(COLORS.danger)
    .setTitle("Nicht auf der Watchlist")
    .setDescription(`**${query}** steht nicht auf deiner Watchlist.`);
}
