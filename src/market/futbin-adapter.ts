/**
 * FUTBIN market adapter.
 *
 * LIVE HTTP IS NOT ENABLED. This class serves a mock/sample catalog so slash
 * commands work out of the box without contacting FUTBIN or EA.
 *
 * Before wiring real HTTP:
 * - Read FUTBIN Terms of Service, robots.txt, and any API/licensing notes.
 * - Cache aggressively (this project already has a ~1h PriceCache).
 * - Rate-limit conservatively (e.g. ≤ 1 req/s, honor 429 / Retry-After).
 * - Send a clear User-Agent and avoid parallel stampede on cache expiry.
 * - Prefer documented/public JSON over brittle HTML scraping if available.
 *
 * NEVER in this adapter or elsewhere in this bot:
 * - Unofficial EA Sports FC Companion App / FUT web-app / UTAS automation
 * - Buying, bidding, listing, or any trading against EA servers
 * - Session hijacking, credential stuffing, or account farming
 *
 * This bot is market *analysis* only (prices, snipes vs cache, alerts, watchlist).
 */

import { findListingById, MOCK_CATALOG, type MockListing } from "./mock-data";
import type { Platform } from "./platform";
import type {
  FindUnderpricedOptions,
  PlayerCard,
  PriceProvider,
  PriceQuote,
  SnipeCandidate,
} from "./price-provider";

const DEFAULT_MIN_DISCOUNT = 8;
const SNIPE_RESULT_LIMIT = 8;

export class FutbinAdapter implements PriceProvider {
  /**
   * TODO(live-futbin): GET a player search endpoint, map hits to PlayerCard.
   * Keep mock search as a fallback/dev fixture.
   */
  async searchPlayers(query: string): Promise<PlayerCard[]> {
    const needle = normalize(query);
    if (!needle) {
      return MOCK_CATALOG.map((listing) => listing.player);
    }

    return MOCK_CATALOG.filter((listing) => matchesPlayer(listing.player, needle)).map(
      (listing) => listing.player,
    );
  }

  /**
   * TODO(live-futbin): GET current BIN / prp by player id and platform
   * (ps / xbox / pc). Map timestamps into `updatedAt`.
   */
  async getPrice(playerId: string, platform: Platform): Promise<PriceQuote | null> {
    const listing = findListingById(playerId);
    if (!listing) {
      return null;
    }
    return quoteFromListing(listing, platform);
  }

  /**
   * TODO(live-futbin): derive "expected" from a moving average or FUTBIN
   * cheapest-sold / graph — not from live EA trade actions.
   */
  async findUnderpriced(options: FindUnderpricedOptions): Promise<SnipeCandidate[]> {
    const minDiscount = options.minDiscountPercent ?? DEFAULT_MIN_DISCOUNT;
    const needle = options.query ? normalize(options.query) : "";

    const candidates: SnipeCandidate[] = [];
    for (const listing of MOCK_CATALOG) {
      if (needle && !matchesPlayer(listing.player, needle)) {
        continue;
      }
      const quote = quoteFromListing(listing, options.platform);
      if (options.maxPrice !== undefined && quote.currentPrice > options.maxPrice) {
        continue;
      }
      if (quote.expectedPrice <= 0 || quote.currentPrice >= quote.expectedPrice) {
        continue;
      }
      const discountPercent =
        ((quote.expectedPrice - quote.currentPrice) / quote.expectedPrice) * 100;
      if (discountPercent < minDiscount) {
        continue;
      }
      candidates.push({ quote, discountPercent });
    }

    candidates.sort((a, b) => b.discountPercent - a.discountPercent);
    return candidates.slice(0, SNIPE_RESULT_LIMIT);
  }
}

function quoteFromListing(listing: MockListing, platform: Platform): PriceQuote {
  return {
    player: listing.player,
    platform,
    currentPrice: listing.prices[platform],
    expectedPrice: listing.expected[platform],
    change24hPercent: listing.change24hPercent,
    updatedAt: new Date(),
    source: "futbin-mock",
  };
}

function matchesPlayer(player: PlayerCard, needle: string): boolean {
  const haystacks = [player.name, player.club, player.nation, player.version, String(player.rating)];
  return haystacks.some((value) => normalize(value).includes(needle));
}

function normalize(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .trim();
}

/**
 * Placeholder for a future live client. Intentionally unused until ToS and
 * rate limits are reviewed.
 *
 * TODO(live-futbin):
 * 1. Base URL (example only): https://www.futbin.com
 * 2. Serialized request queue + Retry-After
 * 3. Parse platform prices (ps, xbox, pc) — never EA companion cookies
 */
export function createFutbinHttpClient(): {
  enabled: false;
  note: string;
} {
  return {
    enabled: false,
    note: "Live FUTBIN HTTP is disabled in v1. Use mock data via FutbinAdapter.",
  };
}
