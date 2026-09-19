import type { Client } from "discord.js";
import { EmbedBuilder } from "discord.js";
import { PLATFORM_LABELS } from "../market/platform";
import type { PriceProvider } from "../market/price-provider";
import { formatCoins } from "../utils/format";
import type { AlertStore, PriceAlert } from "../stores/alerts-store";
import { COLORS } from "../embeds/theme";

export interface AlertSchedulerOptions {
  intervalMs: number;
  alerts: AlertStore;
  provider: PriceProvider;
  client: Client;
  /** Injected for tests. Defaults to setInterval. */
  setIntervalFn?: typeof setInterval;
  clearIntervalFn?: typeof clearInterval;
}

export interface AlertScheduler {
  stop: () => void;
  /** Run one pass immediately (also used by tests). */
  tick: () => Promise<PriceAlert[]>;
}

/**
 * Placeholder scheduler: compares in-memory alerts against the (hourly) cache
 * via PriceProvider.getPrice. Does not contact EA or place trades.
 *
 * When an alert fires it tries to DM the user. Failures are logged only.
 */
export function startAlertScheduler(options: AlertSchedulerOptions): AlertScheduler {
  const setIntervalFn = options.setIntervalFn ?? setInterval;
  const clearIntervalFn = options.clearIntervalFn ?? clearInterval;
  const fired = new Set<string>();

  const tick = async (): Promise<PriceAlert[]> => {
    const triggered: PriceAlert[] = [];
    for (const alert of options.alerts.all()) {
      const quote = await options.provider.getPrice(alert.playerId, alert.platform);
      if (!quote) {
        continue;
      }
      const crossed =
        alert.direction === "below"
          ? quote.currentPrice <= alert.threshold
          : quote.currentPrice >= alert.threshold;
      if (!crossed) {
        continue;
      }
      const dedupeKey = `${alert.id}:${quote.currentPrice}`;
      if (fired.has(dedupeKey)) {
        continue;
      }
      fired.add(dedupeKey);
      triggered.push(alert);
      await notifyUser(options.client, alert, quote.currentPrice);
    }
    return triggered;
  };

  const handle = setIntervalFn(() => {
    void tick().catch((error: unknown) => {
      console.error("[alert-scheduler] tick failed", error);
    });
  }, options.intervalMs);

  if (typeof handle === "object" && handle && "unref" in handle) {
    (handle as NodeJS.Timeout).unref?.();
  }

  return {
    stop: () => clearIntervalFn(handle),
    tick,
  };
}

async function notifyUser(
  client: Client,
  alert: PriceAlert,
  currentPrice: number,
): Promise<void> {
  const directionLabel = alert.direction === "below" ? "unter" : "über";
  const embed = new EmbedBuilder()
    .setColor(COLORS.alert)
    .setTitle("Preisalarm ausgelöst")
    .setDescription(
      `**${alert.playerName}** (${alert.rating} ${alert.version}) liegt jetzt **${directionLabel}** deiner Schwelle.`,
    )
    .addFields(
      {
        name: "Aktueller Preis",
        value: formatCoins(currentPrice),
        inline: true,
      },
      {
        name: "Schwelle",
        value: `${directionLabel} ${formatCoins(alert.threshold)}`,
        inline: true,
      },
      {
        name: "Plattform",
        value: PLATFORM_LABELS[alert.platform],
        inline: true,
      },
    )
    .setFooter({
      text: `Alarm-ID ${alert.id} · Kein Kauf/Gebot — nur Analyse`,
    })
    .setTimestamp();

  try {
    const user = await client.users.fetch(alert.userId);
    await user.send({ embeds: [embed] });
  } catch (error) {
    console.warn(
      `[alert-scheduler] could not DM user ${alert.userId} for alert ${alert.id}:`,
      error instanceof Error ? error.message : error,
    );
  }
}
