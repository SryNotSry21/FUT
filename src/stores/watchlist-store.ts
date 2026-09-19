export interface WatchlistEntry {
  userId: string;
  playerId: string;
  playerName: string;
  rating: number;
  version: string;
  addedAt: Date;
}

export class WatchlistStore {
  private readonly byUser = new Map<string, WatchlistEntry[]>();

  add(input: Omit<WatchlistEntry, "addedAt">): WatchlistEntry {
    const existing = this.byUser.get(input.userId) ?? [];
    const duplicate = existing.find((entry) => entry.playerId === input.playerId);
    if (duplicate) {
      return duplicate;
    }
    const entry: WatchlistEntry = { ...input, addedAt: new Date() };
    existing.push(entry);
    this.byUser.set(input.userId, existing);
    return entry;
  }

  list(userId: string): WatchlistEntry[] {
    return [...(this.byUser.get(userId) ?? [])];
  }

  remove(userId: string, playerId: string): WatchlistEntry | undefined {
    const existing = this.byUser.get(userId) ?? [];
    const index = existing.findIndex((entry) => entry.playerId === playerId);
    if (index === -1) {
      return undefined;
    }
    const [removed] = existing.splice(index, 1);
    if (existing.length === 0) {
      this.byUser.delete(userId);
    } else {
      this.byUser.set(userId, existing);
    }
    return removed;
  }

  clear(): void {
    this.byUser.clear();
  }
}
