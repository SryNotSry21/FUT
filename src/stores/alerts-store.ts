import { randomBytes } from "node:crypto";
import type { Platform } from "../market/platform";

export type AlertDirection = "below" | "above";

export interface PriceAlert {
  id: string;
  userId: string;
  playerId: string;
  playerName: string;
  rating: number;
  version: string;
  platform: Platform;
  threshold: number;
  direction: AlertDirection;
  createdAt: Date;
}

export class AlertStore {
  private readonly byUser = new Map<string, PriceAlert[]>();

  add(
    input: Omit<PriceAlert, "id" | "createdAt"> & { id?: string },
  ): PriceAlert {
    const alert: PriceAlert = {
      ...input,
      id: input.id ?? shortId(),
      createdAt: new Date(),
    };
    const existing = this.byUser.get(alert.userId) ?? [];
    existing.push(alert);
    this.byUser.set(alert.userId, existing);
    return alert;
  }

  list(userId: string): PriceAlert[] {
    return [...(this.byUser.get(userId) ?? [])];
  }

  remove(userId: string, alertId: string): PriceAlert | undefined {
    const existing = this.byUser.get(userId) ?? [];
    const index = existing.findIndex((alert) => alert.id === alertId);
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

  /** All alerts — used by the scheduler hook. */
  all(): PriceAlert[] {
    const result: PriceAlert[] = [];
    for (const alerts of this.byUser.values()) {
      result.push(...alerts);
    }
    return result;
  }

  clear(): void {
    this.byUser.clear();
  }
}

function shortId(): string {
  return randomBytes(3).toString("hex");
}
