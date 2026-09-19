export const PLATFORMS = ["ps", "xbox", "pc"] as const;

export type Platform = (typeof PLATFORMS)[number];

/** v1 default market: PlayStation (console / PS prices). */
export const DEFAULT_PLATFORM: Platform = "ps";

export const PLATFORM_LABELS: Record<Platform, string> = {
  ps: "PlayStation",
  xbox: "Xbox",
  pc: "PC",
};

export function isPlatform(value: string): value is Platform {
  return (PLATFORMS as readonly string[]).includes(value);
}

export function parsePlatform(
  value: string | null | undefined,
  fallback: Platform = DEFAULT_PLATFORM,
): Platform {
  if (value && isPlatform(value)) {
    return value;
  }
  return fallback;
}
