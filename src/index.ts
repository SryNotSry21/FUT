import "dotenv/config";
import { Client, Events, GatewayIntentBits } from "discord.js";
import { findCommand } from "./commands";
import { loadConfig } from "./config";
import { createBotContext } from "./context";
import { errorEmbed } from "./embeds/market-embeds";
import { startAlertScheduler } from "./scheduler/alert-checker";

async function main(): Promise<void> {
  const config = loadConfig();
  const ctx = createBotContext(config);
  const client = new Client({ intents: [GatewayIntentBits.Guilds] });

  client.once(Events.ClientReady, (readyClient) => {
    console.log(`Logged in as ${readyClient.user.tag}`);
    console.log(
      `Market adapter: FUTBIN (mock) · default platform: ${ctx.defaultPlatform} · cache TTL: ${ctx.cache.ttlMs}ms`,
    );

    const scheduler = startAlertScheduler({
      intervalMs: config.alertCheckIntervalMs,
      alerts: ctx.alerts,
      provider: ctx.provider,
      client: readyClient,
    });

    const shutdown = (): void => {
      console.log("Shutting down…");
      scheduler.stop();
      client.destroy();
      process.exit(0);
    };
    process.once("SIGINT", shutdown);
    process.once("SIGTERM", shutdown);
  });

  client.on(Events.InteractionCreate, async (interaction) => {
    try {
      if (interaction.isAutocomplete()) {
        const command = findCommand(interaction.commandName);
        if (!command?.autocomplete) {
          await interaction.respond([]);
          return;
        }
        await command.autocomplete(interaction, ctx);
        return;
      }

      if (!interaction.isChatInputCommand()) {
        return;
      }

      const command = findCommand(interaction.commandName);
      if (!command) {
        await interaction.reply({
          ephemeral: true,
          embeds: [errorEmbed(`Unbekannter Befehl: \`/${interaction.commandName}\``)],
        });
        return;
      }

      await command.execute(interaction, ctx);
    } catch (error) {
      console.error("Interaction error", error);
      const embed = errorEmbed(
        "Da ist etwas schiefgelaufen. Bitte später erneut versuchen.",
      );
      try {
        if (interaction.isRepliable()) {
          if (interaction.deferred || interaction.replied) {
            await interaction.followUp({ ephemeral: true, embeds: [embed] });
          } else {
            await interaction.reply({ ephemeral: true, embeds: [embed] });
          }
        }
      } catch (replyError) {
        console.error("Failed to send error reply", replyError);
      }
    }
  });

  await client.login(config.discordToken);
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
