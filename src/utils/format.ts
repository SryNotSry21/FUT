export function formatCoins(amount: number): string {
  return `${amount.toLocaleString("de-DE")} Münzen`;
}

export function formatPercent(value: number, digits = 1): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)} %`;
}

export function trendLabel(change24hPercent: number | undefined): string {
  if (change24hPercent === undefined) {
    return "k. A.";
  }
  if (change24hPercent > 0.5) {
    return `▲ ${formatPercent(change24hPercent)}`;
  }
  if (change24hPercent < -0.5) {
    return `▼ ${formatPercent(change24hPercent)}`;
  }
  return `● ${formatPercent(change24hPercent)}`;
}

export function playerHeadline(
  name: string,
  rating: number,
  version: string,
): string {
  return `${rating} ${version} · ${name}`;
}

export function sourceLabel(source: string, cacheHit?: boolean): string {
  const base = source === "futbin-mock" ? "FUTBIN (Mock-Daten)" : "FUTBIN";
  return cacheHit ? `${base} · Cache-Treffer` : `${base} · frisch geladen`;
}
