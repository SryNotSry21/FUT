import type { Platform } from "./platform";
import type { PlayerCard } from "./price-provider";

export interface MockListing {
  player: PlayerCard;
  /** Current BIN by platform. */
  prices: Record<Platform, number>;
  /** Fair / expected price by platform (snipe baseline). */
  expected: Record<Platform, number>;
  change24hPercent: number;
}

/**
 * Sample EA FC 27 Ultimate Team catalog for offline demos.
 * IDs are mock FUTBIN-style keys, not live database IDs.
 */
export const MOCK_CATALOG: MockListing[] = [
  {
    player: {
      id: "mock-mbappe-91",
      name: "Kylian Mbappé",
      rating: 91,
      version: "Gold Rare",
      position: "ST",
      club: "Real Madrid",
      nation: "Frankreich",
    },
    prices: { ps: 1_850_000, xbox: 1_820_000, pc: 1_910_000 },
    expected: { ps: 1_880_000, xbox: 1_850_000, pc: 1_900_000 },
    change24hPercent: -1.4,
  },
  {
    player: {
      id: "mock-haaland-91",
      name: "Erling Haaland",
      rating: 91,
      version: "Gold Rare",
      position: "ST",
      club: "Manchester City",
      nation: "Norwegen",
    },
    prices: { ps: 1_120_000, xbox: 1_105_000, pc: 1_150_000 },
    expected: { ps: 1_140_000, xbox: 1_130_000, pc: 1_160_000 },
    change24hPercent: 0.8,
  },
  {
    player: {
      id: "mock-bellingham-90",
      name: "Jude Bellingham",
      rating: 90,
      version: "Gold Rare",
      position: "CAM",
      club: "Real Madrid",
      nation: "England",
    },
    prices: { ps: 980_000, xbox: 965_000, pc: 1_010_000 },
    expected: { ps: 1_050_000, xbox: 1_040_000, pc: 1_070_000 },
    change24hPercent: -5.2,
  },
  {
    player: {
      id: "mock-vinicius-90",
      name: "Vinícius Jr.",
      rating: 90,
      version: "Gold Rare",
      position: "LW",
      club: "Real Madrid",
      nation: "Brasilien",
    },
    prices: { ps: 1_240_000, xbox: 1_220_000, pc: 1_280_000 },
    expected: { ps: 1_260_000, xbox: 1_250_000, pc: 1_275_000 },
    change24hPercent: 2.1,
  },
  {
    player: {
      id: "mock-yamal-86",
      name: "Lamine Yamal",
      rating: 86,
      version: "Gold Rare",
      position: "RW",
      club: "FC Barcelona",
      nation: "Spanien",
    },
    prices: { ps: 890_000, xbox: 875_000, pc: 920_000 },
    expected: { ps: 1_050_000, xbox: 1_030_000, pc: 1_080_000 },
    change24hPercent: -8.6,
  },
  {
    player: {
      id: "mock-wirtz-89",
      name: "Florian Wirtz",
      rating: 89,
      version: "Gold Rare",
      position: "CAM",
      club: "Liverpool",
      nation: "Deutschland",
    },
    prices: { ps: 420_000, xbox: 410_000, pc: 445_000 },
    expected: { ps: 485_000, xbox: 480_000, pc: 500_000 },
    change24hPercent: -4.1,
  },
  {
    player: {
      id: "mock-musiala-88",
      name: "Jamal Musiala",
      rating: 88,
      version: "Gold Rare",
      position: "CAM",
      club: "FC Bayern München",
      nation: "Deutschland",
    },
    prices: { ps: 310_000, xbox: 305_000, pc: 325_000 },
    expected: { ps: 318_000, xbox: 312_000, pc: 330_000 },
    change24hPercent: 1.2,
  },
  {
    player: {
      id: "mock-palmer-85",
      name: "Cole Palmer",
      rating: 85,
      version: "Gold Rare",
      position: "RW",
      club: "Chelsea",
      nation: "England",
    },
    prices: { ps: 78_000, xbox: 76_000, pc: 82_000 },
    expected: { ps: 95_000, xbox: 94_000, pc: 98_000 },
    change24hPercent: -7.5,
  },
  {
    player: {
      id: "mock-salah-90",
      name: "Mohamed Salah",
      rating: 90,
      version: "Gold Rare",
      position: "RW",
      club: "Liverpool",
      nation: "Ägypten",
    },
    prices: { ps: 145_000, xbox: 142_000, pc: 155_000 },
    expected: { ps: 150_000, xbox: 148_000, pc: 158_000 },
    change24hPercent: -0.6,
  },
  {
    player: {
      id: "mock-kimmich-88",
      name: "Joshua Kimmich",
      rating: 88,
      version: "Gold Rare",
      position: "CDM",
      club: "FC Bayern München",
      nation: "Deutschland",
    },
    prices: { ps: 54_000, xbox: 52_000, pc: 58_000 },
    expected: { ps: 62_000, xbox: 61_000, pc: 65_000 },
    change24hPercent: -3.3,
  },
  {
    player: {
      id: "mock-pedri-87",
      name: "Pedri",
      rating: 87,
      version: "Gold Rare",
      position: "CM",
      club: "FC Barcelona",
      nation: "Spanien",
    },
    prices: { ps: 38_500, xbox: 37_000, pc: 41_000 },
    expected: { ps: 39_000, xbox: 38_000, pc: 41_500 },
    change24hPercent: 0.4,
  },
  {
    player: {
      id: "mock-kane-90",
      name: "Harry Kane",
      rating: 90,
      version: "Gold Rare",
      position: "ST",
      club: "FC Bayern München",
      nation: "England",
    },
    prices: { ps: 92_000, xbox: 90_000, pc: 97_000 },
    expected: { ps: 110_000, xbox: 108_000, pc: 115_000 },
    change24hPercent: -9.1,
  },
  {
    player: {
      id: "mock-saka-87",
      name: "Bukayo Saka",
      rating: 87,
      version: "Gold Rare",
      position: "RW",
      club: "Arsenal",
      nation: "England",
    },
    prices: { ps: 64_000, xbox: 63_000, pc: 68_000 },
    expected: { ps: 66_000, xbox: 65_000, pc: 69_000 },
    change24hPercent: 1.8,
  },
  {
    player: {
      id: "mock-debruyne-89",
      name: "Kevin De Bruyne",
      rating: 89,
      version: "Gold Rare",
      position: "CAM",
      club: "Napoli",
      nation: "Belgien",
    },
    prices: { ps: 28_000, xbox: 27_500, pc: 30_000 },
    expected: { ps: 34_500, xbox: 34_000, pc: 36_000 },
    change24hPercent: -6.4,
  },
  {
    player: {
      id: "mock-totw-wirtz-90",
      name: "Florian Wirtz",
      rating: 90,
      version: "TOTW",
      position: "CAM",
      club: "Liverpool",
      nation: "Deutschland",
    },
    prices: { ps: 175_000, xbox: 170_000, pc: 188_000 },
    expected: { ps: 210_000, xbox: 205_000, pc: 220_000 },
    change24hPercent: -11.2,
  },
];

export function findListingById(id: string): MockListing | undefined {
  return MOCK_CATALOG.find((entry) => entry.player.id === id);
}
