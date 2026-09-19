import {
  SlashCommandBuilder,
  type AutocompleteInteraction,
  type ChatInputCommandInteraction,
} from "discord.js";
import { parsePlatform } from "../market/platform";
import { autocompletePlayers } from "../market/resolve-player";
import { snipeEmbed } from "../embeds/market-embeds";
import type { SlashCommand } from "../context";

export const data = new SlashCommandBuilder()
  .setName("snipe")
  .setDescription("Unterbewertete Karten im Preis-Cache finden (Snipe-Kandidaten)")
  .addStringOption((option) =>
    option
      .setName("spieler")
      .setDescription("Optional: Name, um die Suche einzugrenzen")
      .setAutocomplete(true),
  )
  .addIntegerOption((option) =>
    option
      .setName("max_preis")
      .setDescription("Maximaler Preis in Münzen")
      .setMinValue(150)
      .setMaxValue(200_000_000),
  )
  .addIntegerOption((option) =>
    option
      .setName("mindest_rabatt")
      .setDescription("Mindest-Abschlag gegenüber dem Erwartungspreis in Prozent")
      .setMinValue(1)
      .setMaxValue(90),
  )
  .addStringOption((option) =>
    option
      .setName("plattform")
      .setDescription("Markt-Plattform (Standard: PlayStation)")
      .addChoices(
        { name: "PlayStation (Standard)", value: "ps" },
        { name: "Xbox", value: "xbox" },
        { name: "PC", value: "pc" },
      ),
  );

export async function execute(
  interaction: ChatInputCommandInteraction,
  ctx: Parameters<SlashCommand["execute"]>[1],
): Promise<void> {
  await interaction.deferReply();
  const query = interaction.options.getString("spieler") ?? undefined;
  const maxPrice = interaction.options.getInteger("max_preis") ?? undefined;
  const minDiscountPercent = interaction.options.getInteger("mindest_rabatt") ?? 8;
  const platform = parsePlatform(
    interaction.options.getString("plattform"),
    ctx.defaultPlatform,
  );

  const playerId = query?.startsWith("mock-") ? query : undefined;
  const nameQuery = playerId ? undefined : query;

  const candidates = await ctx.provider.findUnderpriced({
    query: nameQuery,
    platform,
    maxPrice,
    minDiscountPercent,
  });

  const filtered = playerId
    ? candidates.filter((candidate) => candidate.quote.player.id === playerId)
    : candidates;

  await interaction.editReply({
    embeds: [
      snipeEmbed(filtered, platform, {
        query,
        maxPrice,
        minDiscountPercent,
      }),
    ],
  });
}

export async function autocomplete(
  interaction: AutocompleteInteraction,
  ctx: Parameters<SlashCommand["execute"]>[1],
): Promise<void> {
  const focused = interaction.options.getFocused();
  const choices = await autocompletePlayers(ctx.provider, focused);
  await interaction.respond(choices);
}
