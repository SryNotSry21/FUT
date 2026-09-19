import type { SlashCommand } from "../context";
import * as alert from "./alert";
import * as preis from "./preis";
import * as snipe from "./snipe";
import * as watchlist from "./watchlist";

export const commands: SlashCommand[] = [preis, snipe, alert, watchlist];

export function findCommand(name: string): SlashCommand | undefined {
  return commands.find((command) => command.data.name === name);
}
