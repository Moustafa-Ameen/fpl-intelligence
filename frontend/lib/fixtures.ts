import type { FixtureTick } from "./types";

export function visibleFixtures(team: FixtureTick) {
  if (team.fixtures.length) {
    return team.fixtures.slice(0, 5);
  }

  return Array.from({ length: 5 }, (_, index) => ({
    gw: index + 1,
    opponent: "TBD",
    home: true,
    difficulty: 3,
  }));
}
