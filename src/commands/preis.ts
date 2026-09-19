import {
  SlashCommandBuilder,
  type AutocompleteInteraction,
  type ChatInputCommandInteraction,
} from "discord.js";
import { parsePlatform } from "../market/platform";
import { autocompletePlayers, resolvePlayer } from "../market/resolve-player";
import { ambiguousEmbed, errorEmbed, notFoundEmbed, priceEmbed } from "../embeds/market-embeds";
import type { SlashCommand } from "../context";

export const data = new SlashCommandBuilder()
  .setName("preis")
  .setDescription("Aktuellen FUT-Marktpreis eines Spielers anzeigen (Standard: PlayStation)")
  .addStringOption((option) =>
    option
      .setName("spieler")
      .setDescription("Spielername oder Karten-ID")
      .setRequired(true)
      .setAutocomplete(true),
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
  const query = interaction.options.getString("spieler", true);
  const platform = parsePlatform(
    interaction.options.getString("plattform"),
    ctx.defaultPlatform,
  );

  const resolved = await resolveFromQueryOrId(ctx, query);
  if (resolved.status === "none") {
    await interaction.editReply({ embeds: [notFoundEmbed(query)] });
    return;
  }
  if (resolved.status === "ambiguous") {
    await interaction.editReply({ embeds: [ambiguousEmbed(query, resolved.players)] });
    return;
  }

  const quote = await ctx.provider.getPrice(resolved.player.id, platform);
  if (!quote) {
    await interaction.editReply({
      embeds: [errorEmbed("Für diese Karte liegt kein Preis im Adapter vor.")],
    });
    return;
  }

  await interaction.editReply({ embeds: [priceEmbed(quote)] });
}

export async function autocomplete(
  interaction: AutocompleteInteraction,
  ctx: Parameters<SlashCommand["execute"]>[1],
): Promise<void> {
  const focused = interaction.options.getFocused();
  const choices = await autocompletePlayers(ctx.provider, focused);
  await interaction.respond(choices);
}

async function resolveFromQueryOrId(
  ctx: Parameters<SlashCommand["execute"]>[1],
  query: string,
) {
  const byId = await ctx.provider.getPrice(query, ctx.defaultPlatform);
  if (byId) {
    return { status: "found" as const, player: byId.player };
  }
  return resolvePlayer(ctx.provider, query);
}
