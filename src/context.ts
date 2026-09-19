import { CachedPriceProvider } from "./market/cached-provider";
import { FutbinAdapter } from "./market/futbin-adapter";
import { PriceCache } from "./market/price-cache";
import type { Platform } from "./market/platform";
import type { PriceProvider } from "./market/price-provider";
import { AlertStore } from "./stores/alerts-store";
import { WatchlistStore } from "./stores/watchlist-store";
import type { AppConfig } from "./config";
import type {
  AutocompleteInteraction,
  ChatInputCommandInteraction,
  SlashCommandBuilder,
  SlashCommandOptionsOnlyBuilder,
  SlashCommandSubcommandsOnlyBuilder,
} from "discord.js";

export interface BotContext {
  config: Pick<AppConfig, "defaultPlatform" | "priceCacheTtlMs" | "alertCheckIntervalMs">;
  cache: PriceCache;
  adapter: FutbinAdapter;
  provider: PriceProvider;
  alerts: AlertStore;
  watchlist: WatchlistStore;
  defaultPlatform: Platform;
}

type CommandBuilder =
  | SlashCommandBuilder
  | SlashCommandOptionsOnlyBuilder
  | SlashCommandSubcommandsOnlyBuilder;

export interface SlashCommand {
  data: CommandBuilder;
  execute: (interaction: ChatInputCommandInteraction, ctx: BotContext) => Promise<void>;
  autocomplete?: (interaction: AutocompleteInteraction, ctx: BotContext) => Promise<void>;
}

export function createBotContext(
  config: Pick<AppConfig, "defaultPlatform" | "priceCacheTtlMs" | "alertCheckIntervalMs">,
): BotContext {
  const cache = new PriceCache({ ttlMs: config.priceCacheTtlMs });
  const adapter = new FutbinAdapter();
  const provider = new CachedPriceProvider(adapter, cache);
  return {
    config,
    cache,
    adapter,
    provider,
    alerts: new AlertStore(),
    watchlist: new WatchlistStore(),
    defaultPlatform: config.defaultPlatform,
  };
}
