"use client";

import { useEffect, useMemo, useState } from "react";
import { FixtureChip } from "@/components/FixtureChip";
import { EmptyState, ErrorState, LoadingState } from "@/components/LoadingState";
import { Panel } from "@/components/Panel";
import { SectionHeader } from "@/components/SectionHeader";
import { getFixtureTicker } from "@/lib/api";
import { visibleFixtures } from "@/lib/fixtures";
import type { FixtureTick } from "@/lib/types";

export default function FixturesPage() {
  const [fixtures, setFixtures] = useState<FixtureTick[]>([]);
  const [mode, setMode] = useState<"team" | "gameweek">("team");
  const [tooltip, setTooltip] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    getFixtureTicker()
      .then(setFixtures)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const sorted = useMemo(
    () => [...fixtures].sort((a, b) => averageDifficulty(a, 5) - averageDifficulty(b, 5)),
    [fixtures],
  );
  const bestNextThree = sorted.slice(0, 5);
  const gameweeks = [1, 2, 3, 4, 5];

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;
  if (!fixtures.length) return <EmptyState />;

  return (
    <div>
      <SectionHeader title="Upcoming Fixtures" />
      <Panel className="mb-6">
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold text-primary">Best fixtures next 3 GWs</h2>
          <div className="flex rounded-lg border border-fpl-border bg-fpl-dark p-1">
            <Toggle active={mode === "team"} onClick={() => setMode("team")}>
              By team
            </Toggle>
            <Toggle active={mode === "gameweek"} onClick={() => setMode("gameweek")}>
              By gameweek
            </Toggle>
          </div>
        </div>
        <div className="space-y-2">
          {bestNextThree.map((team) => {
            const score = averageDifficulty(team, 3);
            return (
              <div key={team.team} className="grid grid-cols-[160px_1fr_44px] items-center gap-3">
                <div className="text-sm text-primary">{team.team}</div>
                <div className="h-2 rounded bg-fpl-border">
                  <div
                    className="h-2 rounded bg-fpl-green"
                    style={{ width: `${Math.max(15, 100 - score * 18)}%` }}
                  />
                </div>
                <div className="font-mono text-sm text-muted">{score.toFixed(1)}</div>
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel>
        <div className="mb-5 flex items-center gap-4 text-xs text-muted">
          <span className="inline-flex items-center gap-2">
            <FixtureChip difficulty={2} /> easy
          </span>
          <span className="inline-flex items-center gap-2">
            <FixtureChip difficulty={3} /> medium
          </span>
          <span className="inline-flex items-center gap-2">
            <FixtureChip difficulty={5} /> hard
          </span>
        </div>
        {mode === "team" ? (
          <div className="space-y-2">
            {sorted.map((team) => (
              <div
                key={team.team}
                className="grid grid-cols-[minmax(120px,180px)_repeat(5,44px)] items-center gap-3 rounded-lg border border-fpl-border/70 px-3 py-2"
              >
                <div className="font-medium text-primary">{team.team}</div>
                {visibleFixtures(team).map((fixture, index) => (
                  <button
                    type="button"
                    key={`${team.team}-${fixture.gw}-${index}`}
                    onClick={() =>
                      setTooltip(`${team.team} vs ${fixture.opponent} · ${fixture.home ? "Home" : "Away"} · difficulty ${fixture.difficulty}`)
                    }
                    className="text-center"
                  >
                    <FixtureChip difficulty={fixture.difficulty} />
                  </button>
                ))}
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {gameweeks.map((_, gwIndex) => (
              <div key={gwIndex} className="rounded-lg border border-fpl-border p-3">
                <div className="mb-2 text-sm font-semibold text-primary">GW {gwIndex + 1}</div>
                <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
                  {sorted
                    .map((team) => ({ team, fixture: visibleFixtures(team)[gwIndex] }))
                    .sort((a, b) => a.fixture.difficulty - b.fixture.difficulty)
                    .slice(0, 8)
                    .map(({ team, fixture }) => (
                      <button
                        type="button"
                        key={`${gwIndex}-${team.team}`}
                        onClick={() =>
                          setTooltip(`${team.team} vs ${fixture.opponent} · ${fixture.home ? "Home" : "Away"} · difficulty ${fixture.difficulty}`)
                        }
                        className="flex items-center justify-between rounded-lg bg-fpl-dark/30 px-3 py-2 text-sm"
                      >
                        <span>{team.team}</span>
                        <FixtureChip difficulty={fixture.difficulty} />
                      </button>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}
        {tooltip ? (
          <button
            type="button"
            onClick={() => setTooltip(null)}
            className="fixed bottom-6 right-6 z-40 rounded-xl border border-fpl-border bg-fpl-card px-4 py-3 text-sm text-primary shadow-xl"
          >
            {tooltip}
          </button>
        ) : null}
      </Panel>
    </div>
  );
}

function averageDifficulty(team: FixtureTick, count: number): number {
  const rows = visibleFixtures(team).slice(0, count);
  return rows.reduce((sum, fixture) => sum + fixture.difficulty, 0) / rows.length;
}

function Toggle({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-3 py-1.5 text-xs font-semibold ${
        active ? "bg-fpl-green text-fpl-dark" : "text-muted hover:text-primary"
      }`}
    >
      {children}
    </button>
  );
}
