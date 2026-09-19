import "dotenv/config";
import { REST, Routes } from "discord.js";
import { loadConfig } from "./config";
import { commands } from "./commands";

async function main(): Promise<void> {
  const config = loadConfig();
  const body = commands.map((command) => command.data.toJSON());
  const rest = new REST({ version: "10" }).setToken(config.discordToken);

  console.log(`Registering ${body.length} slash command(s)…`);

  if (config.discordGuildId) {
    const data = (await rest.put(
      Routes.applicationGuildCommands(config.discordClientId, config.discordGuildId),
      { body },
    )) as unknown[];
    console.log(
      `Registered ${data.length} guild command(s) on ${config.discordGuildId} (instant).`,
    );
    return;
  }

  const data = (await rest.put(Routes.applicationCommands(config.discordClientId), {
    body,
  })) as unknown[];
  console.log(
    `Registered ${data.length} global command(s). Propagation can take up to ~1 hour.`,
  );
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
