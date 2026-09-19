import type { PlayerCard, PriceProvider } from "../market/price-provider";

export type PlayerResolveResult =
  | { status: "found"; player: PlayerCard }
  | { status: "none" }
  | { status: "ambiguous"; players: PlayerCard[] };

function normalize(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .trim();
}

/**
 * Pick a single card from search results. Exact name+version wins;
 * a unique name match is accepted; otherwise the caller should show the list.
 */
export async function resolvePlayer(
  provider: PriceProvider,
  query: string,
): Promise<PlayerResolveResult> {
  const matches = await provider.searchPlayers(query);
  if (matches.length === 0) {
    return { status: "none" };
  }
  if (matches.length === 1) {
    return { status: "found", player: matches[0] };
  }

  const needle = normalize(query);
  const exact = matches.filter((player) => {
    const name = normalize(player.name);
    const withVersion = `${name} ${normalize(player.version)}`;
    const withRating = `${player.rating} ${name}`;
    return needle === name || needle === withVersion || needle === withRating || needle === `${name} ${player.rating}`;
  });
  if (exact.length === 1) {
    return { status: "found", player: exact[0] };
  }

  const uniqueNames = new Set(matches.map((player) => normalize(player.name)));
  if (uniqueNames.size === 1) {
    const preferred =
      matches.find((player) => /gold/i.test(player.version)) ??
      matches.sort((a, b) => b.rating - a.rating)[0];
    return { status: "found", player: preferred };
  }

  return { status: "ambiguous", players: matches };
}

export async function autocompletePlayers(
  provider: PriceProvider,
  query: string,
): Promise<{ name: string; value: string }[]> {
  const matches = await provider.searchPlayers(query.trim());
  const sliced = matches.slice(0, 25);
  return sliced.map((player) => ({
    name: `${player.rating} ${player.name} · ${player.version}`.slice(0, 100),
    value: player.id,
  }));
}
