import type { FixtureTick } from "./types";

export function fixtureTickerRows(rows: FixtureTick[]): FixtureTick[] {
  return rows;
}

export function visibleFixtures(team: FixtureTick, count = 5) {
  return team.fixtures.slice(0, count).map((fixture) => ({
    ...fixture,
    opponent: fixture.opponent || "TBD",
    difficulty: fixture.difficulty ?? 3,
  }));
}
