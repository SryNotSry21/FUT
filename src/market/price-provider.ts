import type { Platform } from "./platform";

export type PriceSource = "futbin-mock" | "futbin";

export interface PlayerCard {
  id: string;
  name: string;
  rating: number;
  version: string;
  position: string;
  club: string;
  nation: string;
}

export interface PriceQuote {
  player: PlayerCard;
  platform: Platform;
  /** Current BIN / market price in coins. */
  currentPrice: number;
  /**
   * Reference / expected price used for snipe detection
   * (e.g. recent average). Not a live EA trade.
   */
  expectedPrice: number;
  /** Optional 24h change in percent, positive = up. */
  change24hPercent?: number;
  updatedAt: Date;
  source: PriceSource;
  cacheHit?: boolean;
}

export interface SnipeCandidate {
  quote: PriceQuote;
  discountPercent: number;
}

export interface FindUnderpricedOptions {
  query?: string;
  platform: Platform;
  maxPrice?: number;
  minDiscountPercent?: number;
}

/**
 * Swappable market-data backend. v1 ships a FUTBIN adapter;
 * another provider can implement the same contract later.
 */
export interface PriceProvider {
  searchPlayers(query: string): Promise<PlayerCard[]>;
  getPrice(playerId: string, platform: Platform): Promise<PriceQuote | null>;
  findUnderpriced(options: FindUnderpricedOptions): Promise<SnipeCandidate[]>;
}
