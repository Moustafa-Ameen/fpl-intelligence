import assert from "node:assert/strict";
import test from "node:test";
import { matchesPlayerSearch, normalized } from "./format.ts";

test("compare search matches an unaccented player name", () => {
  assert.equal(matchesPlayerSearch("Esteve", "Maxime Estève"), true);
});

test("compare search preserves matching for an accented query", () => {
  assert.equal(matchesPlayerSearch("Estève", "Maxime Estève"), true);
});

test("stats search uses the same accent-insensitive matching", () => {
  const players = [{ name: "Maxime Estève" }, { name: "Maxime Lopez" }];
  const searchTerm = "Esteve";
  const filtered = players.filter((player) => matchesPlayerSearch(searchTerm, player.name));
  assert.deepEqual(filtered.map((player) => player.name), ["Maxime Estève"]);
  assert.equal(normalized("Estève"), normalized("Esteve"));
});
