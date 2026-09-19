/**
 * In-memory cache with TTL. Shape is Redis-ready: swap `MemoryCacheBackend`
 * for a Redis implementation that honors the same get/set/delete contract.
 */

export interface CacheBackend {
  get<T>(key: string): T | undefined;
  set<T>(key: string, value: T, ttlMs: number): void;
  delete(key: string): void;
  clear(): void;
  size(): number;
}

interface CacheEntry {
  value: unknown;
  expiresAt: number;
}

export class MemoryCacheBackend implements CacheBackend {
  private readonly store = new Map<string, CacheEntry>();

  get<T>(key: string): T | undefined {
    const entry = this.store.get(key);
    if (!entry) {
      return undefined;
    }
    if (Date.now() >= entry.expiresAt) {
      this.store.delete(key);
      return undefined;
    }
    return entry.value as T;
  }

  set<T>(key: string, value: T, ttlMs: number): void {
    this.store.set(key, { value, expiresAt: Date.now() + ttlMs });
  }

  delete(key: string): void {
    this.store.delete(key);
  }

  clear(): void {
    this.store.clear();
  }

  size(): number {
    this.pruneExpired();
    return this.store.size;
  }

  private pruneExpired(): void {
    const now = Date.now();
    for (const [key, entry] of this.store) {
      if (now >= entry.expiresAt) {
        this.store.delete(key);
      }
    }
  }
}

export interface PriceCacheOptions {
  ttlMs?: number;
  backend?: CacheBackend;
}

const ONE_HOUR_MS = 60 * 60 * 1000;

export class PriceCache {
  readonly ttlMs: number;
  private readonly backend: CacheBackend;

  constructor(options: PriceCacheOptions = {}) {
    this.ttlMs = options.ttlMs ?? ONE_HOUR_MS;
    this.backend = options.backend ?? new MemoryCacheBackend();
  }

  get<T>(key: string): T | undefined {
    return this.backend.get<T>(key);
  }

  set<T>(key: string, value: T, ttlMs = this.ttlMs): void {
    this.backend.set(key, value, ttlMs);
  }

  delete(key: string): void {
    this.backend.delete(key);
  }

  clear(): void {
    this.backend.clear();
  }

  size(): number {
    return this.backend.size();
  }

  /**
   * Returns a cached value or computes, stores, and returns it.
   * `null` is not cached so transient misses can be retried.
   */
  async getOrSet<T>(
    key: string,
    factory: () => Promise<T>,
    ttlMs = this.ttlMs,
  ): Promise<{ value: T; cacheHit: boolean }> {
    const hit = this.get<T>(key);
    if (hit !== undefined) {
      return { value: hit, cacheHit: true };
    }
    const value = await factory();
    if (value !== null && value !== undefined) {
      this.set(key, value, ttlMs);
    }
    return { value, cacheHit: false };
  }
}
