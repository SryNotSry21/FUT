import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { commands, findCommand } from "../src/commands";
import { loadMarketConfig } from "../src/config";
import { createBotContext } from "../src/context";
import {
  alertCreatedEmbed,
  priceEmbed,
  snipeEmbed,
  watchlistEmbed,
} from "../src/embeds/market-embeds";
import { CachedPriceProvider } from "../src/market/cached-provider";
import { FutbinAdapter, createFutbinHttpClient } from "../src/market/futbin-adapter";
import { MOCK_CATALOG } from "../src/market/mock-data";
import { DEFAULT_PLATFORM } from "../src/market/platform";
import { PriceCache } from "../src/market/price-cache";
import { startAlertScheduler } from "../src/scheduler/alert-checker";
import { AlertStore } from "../src/stores/alerts-store";
import type { ChatInputCommandInteraction, Client, EmbedBuilder } from "discord.js";

describe("v1 market skeleton", () => {
  const adapter = new FutbinAdapter();

  it("defaults the market platform to PlayStation", () => {
    assert.equal(DEFAULT_PLATFORM, "ps");
    assert.equal(loadMarketConfig().defaultPlatform, "ps");
  });

  it("registers the four v1 slash commands with German descriptions", () => {
    const names = commands.map((command) => command.data.name).sort();
    assert.deepEqual(names, ["alert", "preis", "snipe", "watchlist"]);

    const payloads = commands.map((command) => command.data.toJSON());
    const preis = payloads.find((payload) => payload.name === "preis");
    assert.ok(preis?.description?.includes("PlayStation"));

    const alert = payloads.find((payload) => payload.name === "alert");
    const alertSubs = "options" in alert! ? alert!.options : [];
    const subNames = (alertSubs ?? []).map((option) => option.name).sort();
    assert.deepEqual(subNames, ["list", "remove", "set"]);

    const watchlist = payloads.find((payload) => payload.name === "watchlist");
    const watchSubs = "options" in watchlist! ? watchlist!.options : [];
    assert.deepEqual((watchSubs ?? []).map((option) => option.name).sort(), [
      "add",
      "list",
      "remove",
    ]);
  });

  it("searches and prices cards through the FUTBIN mock adapter", async () => {
    const hits = await adapter.searchPlayers("Wirtz");
    assert.ok(hits.length >= 2);
    assert.ok(hits.every((player) => player.name.includes("Wirtz")));

    const gold = hits.find((player) => player.version === "Gold Rare");
    assert.ok(gold);
    const quote = await adapter.getPrice(gold.id, "ps");
    assert.ok(quote);
    assert.equal(quote.platform, "ps");
    assert.equal(quote.source, "futbin-mock");
    assert.equal(quote.currentPrice, 420_000);
  });

  it("finds underpriced snipe candidates on PlayStation", async () => {
    const snipes = await adapter.findUnderpriced({
      platform: "ps",
      minDiscountPercent: 8,
    });
    assert.ok(snipes.length >= 3);
    assert.ok(snipes.every((item) => item.quote.platform === "ps"));
    assert.ok(snipes.every((item) => item.discountPercent >= 8));
    assert.ok(
      snipes.some((item) => item.quote.player.name === "Lamine Yamal"),
      "Yamal is deliberately underpriced in the mock catalog",
    );
  });

  it("expires cache entries after TTL", async () => {
    const cache = new PriceCache({ ttlMs: 20 });
    cache.set("price:ps:demo", { coins: 1000 });
    assert.deepEqual(cache.get("price:ps:demo"), { coins: 1000 });
    await new Promise((resolve) => setTimeout(resolve, 30));
    assert.equal(cache.get("price:ps:demo"), undefined);
  });

  it("serves a second getPrice from the hourly cache", async () => {
    const cache = new PriceCache({ ttlMs: 60_000 });
    const inner = new FutbinAdapter();
    const cached = new CachedPriceProvider(inner, cache);
    const first = await cached.getPrice("mock-kane-90", "ps");
    const second = await cached.getPrice("mock-kane-90", "ps");
    assert.equal(first?.cacheHit, false);
    assert.equal(second?.cacheHit, true);
    assert.equal(second?.currentPrice, first?.currentPrice);
    assert.ok(cache.size() >= 1);
  });

  it("stores per-user alerts and watchlist in memory", () => {
    const ctx = createBotContext(loadMarketConfig());
    const alert = ctx.alerts.add({
      userId: "u1",
      playerId: "mock-kane-90",
      playerName: "Harry Kane",
      rating: 90,
      version: "Gold Rare",
      platform: "ps",
      threshold: 80_000,
      direction: "below",
    });
    assert.equal(ctx.alerts.list("u1").length, 1);
    assert.equal(ctx.alerts.remove("u1", alert.id)?.playerName, "Harry Kane");
    assert.equal(ctx.alerts.list("u1").length, 0);

    ctx.watchlist.add({
      userId: "u1",
      playerId: "mock-yamal-86",
      playerName: "Lamine Yamal",
      rating: 86,
      version: "Gold Rare",
    });
    ctx.watchlist.add({
      userId: "u1",
      playerId: "mock-yamal-86",
      playerName: "Lamine Yamal",
      rating: 86,
      version: "Gold Rare",
    });
    assert.equal(ctx.watchlist.list("u1").length, 1);
    assert.ok(ctx.watchlist.remove("u1", "mock-yamal-86"));
  });

  it("builds German embeds for price, snipe, alert and watchlist", async () => {
    const quote = await adapter.getPrice("mock-mbappe-91", "ps");
    assert.ok(quote);
    const price = priceEmbed(quote).toJSON();
    assert.match(String(price.title), /Mbappé/);
    assert.match(String(price.description), /PlayStation/);
    assert.ok(price.fields?.some((field) => field.name === "Aktueller Preis"));

    const snipes = await adapter.findUnderpriced({ platform: "ps" });
    const snipe = snipeEmbed(snipes, "ps", { minDiscountPercent: 8 }).toJSON();
    assert.equal(snipe.title, "Snipe-Kandidaten");
    assert.match(String(snipe.description), /kein automatischer Kauf/i);

    const alerts = new AlertStore();
    const created = alerts.add({
      userId: "u1",
      playerId: quote.player.id,
      playerName: quote.player.name,
      rating: quote.player.rating,
      version: quote.player.version,
      platform: "ps",
      threshold: 1_000_000,
      direction: "below",
    });
    const alertJson = alertCreatedEmbed(created).toJSON();
    assert.equal(alertJson.title, "Preisalarm gesetzt");

    const watch = watchlistEmbed([], new Map(), "ps").toJSON();
    assert.equal(watch.title, "Deine Watchlist");
    assert.ok(watch.fields?.some((field) => field.name === "Leer"));
  });

  it("does not enable live FUTBIN HTTP in v1", () => {
    const client = createFutbinHttpClient();
    assert.equal(client.enabled, false);
    assert.ok(MOCK_CATALOG.length >= 10);
  });

  it("scheduler hook flags alerts that crossed the cached price", async () => {
    const ctx = createBotContext(loadMarketConfig());
    const kane = await ctx.provider.getPrice("mock-kane-90", "ps");
    assert.ok(kane);
    ctx.alerts.add({
      userId: "123456789012345678",
      playerId: kane.player.id,
      playerName: kane.player.name,
      rating: kane.player.rating,
      version: kane.player.version,
      platform: "ps",
      threshold: kane.currentPrice + 1,
      direction: "below",
    });

    const sent: unknown[] = [];
    const fakeClient = {
      users: {
        fetch: async () => ({
          send: async (payload: unknown) => {
            sent.push(payload);
          },
        }),
      },
    } as unknown as Client;

    const scheduler = startAlertScheduler({
      intervalMs: 60_000,
      alerts: ctx.alerts,
      provider: ctx.provider,
      client: fakeClient,
      setIntervalFn: ((fn: () => void, _ms: number) => {
        void fn;
        return 0 as unknown as NodeJS.Timeout;
      }) as typeof setInterval,
      clearIntervalFn: (() => undefined) as typeof clearInterval,
    });

    try {
      const triggered = await scheduler.tick();
      assert.equal(triggered.length, 1);
      assert.equal(sent.length, 1);
      const again = await scheduler.tick();
      assert.equal(again.length, 0, "same price should be de-duplicated");
    } finally {
      scheduler.stop();
    }
  });

  it("command handlers reply with embeds via the mock adapter", async () => {
    const ctx = createBotContext(loadMarketConfig());

    const preis = await runCommand("preis", ctx, { spieler: "Kane" });
    assert.match(embedTitle(preis), /Harry Kane/);
    assert.ok(embedHasField(preis, "Aktueller Preis"));

    const snipe = await runCommand("snipe", ctx, {
      mindest_rabatt: 8,
    });
    assert.equal(embedTitle(snipe), "Snipe-Kandidaten");

    const alertSet = await runCommand(
      "alert",
      ctx,
      { spieler: "Yamal", preis: 700_000, richtung: "below" },
      "set",
    );
    assert.equal(embedTitle(alertSet), "Preisalarm gesetzt");

    const alertList = await runCommand("alert", ctx, {}, "list");
    assert.equal(embedTitle(alertList), "Deine Preisalarme");

    const watchAdd = await runCommand("watchlist", ctx, { spieler: "Musiala" }, "add");
    assert.equal(embedTitle(watchAdd), "Zur Watchlist hinzugefügt");

    const watchList = await runCommand("watchlist", ctx, {}, "list");
    assert.equal(embedTitle(watchList), "Deine Watchlist");
    assert.match(JSON.stringify(watchList), /Musiala/);

    const watchRemove = await runCommand("watchlist", ctx, { spieler: "Musiala" }, "remove");
    assert.equal(embedTitle(watchRemove), "Von der Watchlist entfernt");

    const missing = await runCommand("preis", ctx, { spieler: "GibtEsNichtXYZ" });
    assert.equal(embedTitle(missing), "Spieler nicht gefunden");
  });
});

function embedTitle(payload: { embeds?: EmbedBuilder[] }): string {
  return String(payload.embeds?.[0]?.toJSON().title ?? "");
}

function embedHasField(payload: { embeds?: EmbedBuilder[] }, name: string): boolean {
  return Boolean(payload.embeds?.[0]?.toJSON().fields?.some((field) => field.name === name));
}

async function runCommand(
  name: string,
  ctx: ReturnType<typeof createBotContext>,
  options: Record<string, string | number>,
  subcommand?: string,
): Promise<{ embeds?: EmbedBuilder[] }> {
  const command = findCommand(name);
  assert.ok(command, `missing command ${name}`);
  const replies: { embeds?: EmbedBuilder[] }[] = [];

  const interaction = {
    user: { id: "user-test-1" },
    options: {
      getSubcommand: () => subcommand,
      getString: (key: string) => {
        const value = options[key];
        return typeof value === "string" ? value : null;
      },
      getInteger: (key: string) => {
        const value = options[key];
        return typeof value === "number" ? value : null;
      },
    },
    deferReply: async () => undefined,
    reply: async (payload: { embeds?: EmbedBuilder[] }) => {
      replies.push(payload);
    },
    editReply: async (payload: { embeds?: EmbedBuilder[] }) => {
      replies.push(payload);
    },
  } as unknown as ChatInputCommandInteraction;

  await command.execute(interaction, ctx);
  assert.ok(replies[0], `${name} did not reply`);
  return replies[0];
}
