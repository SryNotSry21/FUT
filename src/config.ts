import { DEFAULT_PLATFORM, parsePlatform, type Platform } from "./market/platform";

export interface AppConfig {
  discordToken: string;
  discordClientId: string;
  discordGuildId?: string;
  defaultPlatform: Platform;
  priceCacheTtlMs: number;
  alertCheckIntervalMs: number;
}

function required(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(
      `Missing required environment variable ${name}. Copy .env.example to .env and fill in Discord credentials.`,
    );
  }
  return value;
}

function optionalNumber(name: string, fallback: number): number {
  const raw = process.env[name]?.trim();
  if (!raw) {
    return fallback;
  }
  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${name} must be a positive number (got ${raw})`);
  }
  return parsed;
}

/** Full bot config. Requires Discord credentials. */
export function loadConfig(): AppConfig {
  return {
    ...loadMarketConfig(),
    discordToken: required("DISCORD_TOKEN"),
    discordClientId: required("DISCORD_CLIENT_ID"),
    discordGuildId: process.env.DISCORD_GUILD_ID?.trim() || undefined,
  };
}

/**
 * Market-side config only (cache TTL, default platform).
 * Safe to call in tests without Discord credentials.
 */
export function loadMarketConfig(): Pick<
  AppConfig,
  "defaultPlatform" | "priceCacheTtlMs" | "alertCheckIntervalMs"
> {
  return {
    defaultPlatform: parsePlatform(process.env.DEFAULT_PLATFORM, DEFAULT_PLATFORM),
    priceCacheTtlMs: optionalNumber("PRICE_CACHE_TTL_MS", 60 * 60 * 1000),
    alertCheckIntervalMs: optionalNumber("ALERT_CHECK_INTERVAL_MS", 15 * 60 * 1000),
  };
}
