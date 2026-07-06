import type { FixtureTick } from "./types";

const fixtureDifficultyPattern = [
  [2, 3, 4, 2, 5, 3, 2, 4],
  [3, 2, 2, 4, 3, 2, 5, 3],
  [4, 3, 2, 5, 3, 4, 2, 3],
  [2, 4, 3, 3, 2, 5, 3, 2],
  [5, 3, 4, 2, 3, 2, 4, 3],
  [3, 5, 2, 3, 4, 2, 3, 5],
];

const mockOpponents = ["ARS", "LIV", "MCI", "CHE", "TOT", "NEW", "AVL", "BHA"];
const mockTeams = [
  ["Arsenal", "ARS"],
  ["Aston Villa", "AVL"],
  ["Bournemouth", "BOU"],
  ["Brighton", "BHA"],
  ["Chelsea", "CHE"],
  ["Liverpool", "LIV"],
  ["Man City", "MCI"],
  ["Newcastle", "NEW"],
  ["Spurs", "TOT"],
  ["West Ham", "WHU"],
] as const;

export function fixtureTickerWithFallback(rows: FixtureTick[]): FixtureTick[] {
  return rows.length ? rows : mockTeams.map(([team, team_short]) => ({
    team,
    team_short,
    fixtures: [],
  }));
}

export function visibleFixtures(team: FixtureTick, count = 5) {
  const rows = team.fixtures.slice(0, count);
  const seed = team.team
    .split("")
    .reduce((sum, letter) => sum + letter.charCodeAt(0), 0);
  const pattern = fixtureDifficultyPattern[seed % fixtureDifficultyPattern.length];
  const fallbackRows = Array.from({ length: Math.max(0, count - rows.length) }, (_, index) => ({
    gw: (rows.at(-1)?.gw ?? 0) + index + 1,
    opponent: mockOpponents[(seed + rows.length + index) % mockOpponents.length],
    home: (rows.length + index) % 2 === 0,
    difficulty: pattern[(rows.length + index) % pattern.length],
  }));

  if (rows.length) {
    const needsMockDifficulty = rows.every((fixture) => fixture.difficulty === 3);
    const mappedRows = rows.map((fixture, index) => ({
      ...fixture,
      opponent: fixture.opponent && fixture.opponent !== "TBD"
        ? fixture.opponent
        : mockOpponents[(seed + index) % mockOpponents.length],
      difficulty: needsMockDifficulty ? pattern[index % pattern.length] : fixture.difficulty,
    }));
    return [...mappedRows, ...fallbackRows];
  }

  return Array.from({ length: count }, (_, index) => ({
    gw: index + 1,
    opponent: mockOpponents[(seed + index) % mockOpponents.length],
    home: index % 2 === 0,
    difficulty: pattern[index % pattern.length],
  }));
}
