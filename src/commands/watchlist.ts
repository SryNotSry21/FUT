import {
  SlashCommandBuilder,
  type AutocompleteInteraction,
  type ChatInputCommandInteraction,
} from "discord.js";
import { autocompletePlayers, resolvePlayer } from "../market/resolve-player";
import {
  ambiguousEmbed,
  notFoundEmbed,
  missingWatchlistEmbed,
  watchlistAddedEmbed,
  watchlistEmbed,
  watchlistRemovedEmbed,
} from "../embeds/market-embeds";
import type { SlashCommand } from "../context";
import type { PriceQuote } from "../market/price-provider";

export const data = new SlashCommandBuilder()
  .setName("watchlist")
  .setDescription("Persönliche Watchlist verwalten")
  .addSubcommand((sub) =>
    sub
      .setName("add")
      .setDescription("Spieler zur Watchlist hinzufügen")
      .addStringOption((option) =>
        option
          .setName("spieler")
          .setDescription("Spielername oder Karten-ID")
          .setRequired(true)
          .setAutocomplete(true),
      ),
  )
  .addSubcommand((sub) =>
    sub.setName("list").setDescription("Deine Watchlist inkl. PlayStation-Preis anzeigen"),
  )
  .addSubcommand((sub) =>
    sub
      .setName("remove")
      .setDescription("Spieler von der Watchlist entfernen")
      .addStringOption((option) =>
        option
          .setName("spieler")
          .setDescription("Spielername oder Karten-ID")
          .setRequired(true)
          .setAutocomplete(true),
      ),
  );

export async function execute(
  interaction: ChatInputCommandInteraction,
  ctx: Parameters<SlashCommand["execute"]>[1],
): Promise<void> {
  const sub = interaction.options.getSubcommand();
  const userId = interaction.user.id;

  if (sub === "list") {
    await interaction.deferReply({ ephemeral: true });
    const entries = ctx.watchlist.list(userId);
    const quotes = new Map<string, PriceQuote | null>();
    await Promise.all(
      entries.map(async (entry) => {
        quotes.set(entry.playerId, await ctx.provider.getPrice(entry.playerId, ctx.defaultPlatform));
      }),
    );
    await interaction.editReply({
      embeds: [watchlistEmbed(entries, quotes, ctx.defaultPlatform)],
    });
    return;
  }

  if (sub === "remove") {
    const query = interaction.options.getString("spieler", true);
    const entries = ctx.watchlist.list(userId);
    const match =
      entries.find((entry) => entry.playerId === query) ??
      entries.find((entry) => entry.playerName.toLowerCase().includes(query.toLowerCase()));
    const removed = match ? ctx.watchlist.remove(userId, match.playerId) : undefined;
    await interaction.reply({
      ephemeral: true,
      embeds: [removed ? watchlistRemovedEmbed(removed) : missingWatchlistEmbed(query)],
    });
    return;
  }

  await interaction.deferReply({ ephemeral: true });
  const query = interaction.options.getString("spieler", true);
  const byId = await ctx.provider.getPrice(query, ctx.defaultPlatform);
  const resolved = byId
    ? { status: "found" as const, player: byId.player }
    : await resolvePlayer(ctx.provider, query);

  if (resolved.status === "none") {
    await interaction.editReply({ embeds: [notFoundEmbed(query)] });
    return;
  }
  if (resolved.status === "ambiguous") {
    await interaction.editReply({ embeds: [ambiguousEmbed(query, resolved.players)] });
    return;
  }

  const before = ctx.watchlist.list(userId).some((entry) => entry.playerId === resolved.player.id);
  const entry = ctx.watchlist.add({
    userId,
    playerId: resolved.player.id,
    playerName: resolved.player.name,
    rating: resolved.player.rating,
    version: resolved.player.version,
  });
  await interaction.editReply({ embeds: [watchlistAddedEmbed(entry, before)] });
}

export async function autocomplete(
  interaction: AutocompleteInteraction,
  ctx: Parameters<SlashCommand["execute"]>[1],
): Promise<void> {
  const sub = interaction.options.getSubcommand(false);
  const focused = interaction.options.getFocused();

  if (sub === "remove") {
    const needle = focused.toLowerCase();
    const choices = ctx.watchlist
      .list(interaction.user.id)
      .filter(
        (entry) =>
          entry.playerName.toLowerCase().includes(needle) ||
          entry.playerId.toLowerCase().includes(needle),
      )
      .slice(0, 25)
      .map((entry) => ({
        name: `${entry.rating} ${entry.playerName} · ${entry.version}`.slice(0, 100),
        value: entry.playerId,
      }));
    await interaction.respond(choices);
    return;
  }

  const choices = await autocompletePlayers(ctx.provider, focused);
  await interaction.respond(choices);
}
