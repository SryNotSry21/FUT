import {
  SlashCommandBuilder,
  type AutocompleteInteraction,
  type ChatInputCommandInteraction,
} from "discord.js";
import { parsePlatform } from "../market/platform";
import { autocompletePlayers, resolvePlayer } from "../market/resolve-player";
import {
  alertCreatedEmbed,
  alertListEmbed,
  alertRemovedEmbed,
  ambiguousEmbed,
  errorEmbed,
  missingAlertEmbed,
  notFoundEmbed,
} from "../embeds/market-embeds";
import type { SlashCommand } from "../context";
import type { AlertDirection } from "../stores/alerts-store";

export const data = new SlashCommandBuilder()
  .setName("alert")
  .setDescription("Preisalarme setzen, auflisten oder entfernen")
  .addSubcommand((sub) =>
    sub
      .setName("set")
      .setDescription("Alarm erstellen, wenn der Preis eine Schwelle kreuzt")
      .addStringOption((option) =>
        option
          .setName("spieler")
          .setDescription("Spielername oder Karten-ID")
          .setRequired(true)
          .setAutocomplete(true),
      )
      .addIntegerOption((option) =>
        option
          .setName("preis")
          .setDescription("Schwellenpreis in Münzen")
          .setRequired(true)
          .setMinValue(150)
          .setMaxValue(200_000_000),
      )
      .addStringOption((option) =>
        option
          .setName("richtung")
          .setDescription("Unter oder über der Schwelle benachrichtigen")
          .setRequired(true)
          .addChoices(
            { name: "Unter der Schwelle (oder gleich)", value: "below" },
            { name: "Über der Schwelle (oder gleich)", value: "above" },
          ),
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
      ),
  )
  .addSubcommand((sub) =>
    sub.setName("list").setDescription("Deine aktiven Preisalarme anzeigen"),
  )
  .addSubcommand((sub) =>
    sub
      .setName("remove")
      .setDescription("Einen Preisalarm anhand der ID entfernen")
      .addStringOption((option) =>
        option
          .setName("id")
          .setDescription("Alarm-ID aus /alert list")
          .setRequired(true)
          .setAutocomplete(true),
      ),
  );

export async function execute(
  interaction: ChatInputCommandInteraction,
  ctx: Parameters<SlashCommand["execute"]>[1],
): Promise<void> {
  const sub = interaction.options.getSubcommand();
  if (sub === "list") {
    await interaction.reply({
      ephemeral: true,
      embeds: [alertListEmbed(ctx.alerts.list(interaction.user.id))],
    });
    return;
  }

  if (sub === "remove") {
    const id = interaction.options.getString("id", true);
    const removed = ctx.alerts.remove(interaction.user.id, id);
    await interaction.reply({
      ephemeral: true,
      embeds: [removed ? alertRemovedEmbed(removed) : missingAlertEmbed(id)],
    });
    return;
  }

  await interaction.deferReply({ ephemeral: true });
  const query = interaction.options.getString("spieler", true);
  const threshold = interaction.options.getInteger("preis", true);
  const direction = interaction.options.getString("richtung", true) as AlertDirection;
  const platform = parsePlatform(
    interaction.options.getString("plattform"),
    ctx.defaultPlatform,
  );

  const byId = await ctx.provider.getPrice(query, platform);
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

  if (direction !== "below" && direction !== "above") {
    await interaction.editReply({
      embeds: [errorEmbed("Ungültige Richtung. Nutze die vorgegebenen Auswahlwerte.")],
    });
    return;
  }

  const alert = ctx.alerts.add({
    userId: interaction.user.id,
    playerId: resolved.player.id,
    playerName: resolved.player.name,
    rating: resolved.player.rating,
    version: resolved.player.version,
    platform,
    threshold,
    direction,
  });

  await interaction.editReply({ embeds: [alertCreatedEmbed(alert)] });
}

export async function autocomplete(
  interaction: AutocompleteInteraction,
  ctx: Parameters<SlashCommand["execute"]>[1],
): Promise<void> {
  const focused = interaction.options.getFocused(true);
  if (focused.name === "id") {
    const alerts = ctx.alerts.list(interaction.user.id);
    const needle = focused.value.toLowerCase();
    const choices = alerts
      .filter(
        (alert) =>
          alert.id.startsWith(needle) || alert.playerName.toLowerCase().includes(needle),
      )
      .slice(0, 25)
      .map((alert) => ({
        name: `${alert.id} · ${alert.playerName}`.slice(0, 100),
        value: alert.id,
      }));
    await interaction.respond(choices);
    return;
  }

  const choices = await autocompletePlayers(ctx.provider, focused.value);
  await interaction.respond(choices);
}
