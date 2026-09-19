import { PriceCache } from "./price-cache";
import type { Platform } from "./platform";
import type {
  FindUnderpricedOptions,
  PlayerCard,
  PriceProvider,
  PriceQuote,
  SnipeCandidate,
} from "./price-provider";

/**
 * Decorator that serves PriceProvider calls from the hourly cache.
 * The inner adapter (FUTBIN) is only hit on miss.
 */
export class CachedPriceProvider implements PriceProvider {
  constructor(
    private readonly inner: PriceProvider,
    private readonly cache: PriceCache,
  ) {}

  async searchPlayers(query: string): Promise<PlayerCard[]> {
    const key = `search:${query.trim().toLowerCase()}`;
    const { value } = await this.cache.getOrSet(key, () => this.inner.searchPlayers(query));
    return value;
  }

  async getPrice(playerId: string, platform: Platform): Promise<PriceQuote | null> {
    const key = `price:${platform}:${playerId}`;
    const { value, cacheHit } = await this.cache.getOrSet(key, () =>
      this.inner.getPrice(playerId, platform),
    );
    if (!value) {
      return null;
    }
    return { ...value, cacheHit };
  }

  async findUnderpriced(options: FindUnderpricedOptions): Promise<SnipeCandidate[]> {
    const key = [
      "snipe",
      options.platform,
      options.query?.trim().toLowerCase() ?? "",
      options.maxPrice ?? "",
      options.minDiscountPercent ?? "",
    ].join(":");
    const { value, cacheHit } = await this.cache.getOrSet(key, () =>
      this.inner.findUnderpriced(options),
    );
    return value.map((candidate) => ({
      ...candidate,
      quote: { ...candidate.quote, cacheHit },
    }));
  }
}
