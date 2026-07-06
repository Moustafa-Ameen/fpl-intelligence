"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { LoadingState, ErrorState } from "@/components/LoadingState";
import { Panel } from "@/components/Panel";
import { SectionHeader } from "@/components/SectionHeader";
import { useDrawer } from "@/context/DrawerContext";
import { getCurrentGameweek, getFixtureTicker, getSquad } from "@/lib/api";
import { fixtureTickerWithFallback, visibleFixtures } from "@/lib/fixtures";
import type { FixtureTick, SquadPlayer } from "@/lib/types";

type FixtureRange = 3 | 5 | 8;

const fixtureRanges: FixtureRange[] = [3, 5, 8];

export default function FixturesPage() {
  const { openDrawer } = useDrawer();
  const [fixtures, setFixtures] = useState<FixtureTick[]>([]);
  const [squad, setSquad] = useState<SquadPlayer[]>([]);
  const [teamId, setTeamId] = useState("");
  const [range, setRange] = useState<FixtureRange>(5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const savedTeamId = window.localStorage.getItem("fpl_team_id") ?? "";
    queueMicrotask(() => {
      if (!cancelled) setTeamId(savedTeamId);
    });

    Promise.all([
      getFixtureTicker(),
      savedTeamId
        ? getCurrentGameweek()
            .then((gw) => getSquad(savedTeamId, gw.current_gw ?? 1))
            .catch(() => [])
        : Promise.resolve([]),
    ])
      .then(([fixtureRows, squadRows]) => {
        if (cancelled) return;
        setFixtures(fixtureRows);
        setSquad(squadRows);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const fixtureRows = useMemo(() => fixtureTickerWithFallback(fixtures), [fixtures]);
  const squadFixtureRows = useMemo(
    () =>
      squad
        .slice(0, 11)
        .map((player) => {
          const team = findTeamFixtureRow(fixtureRows, player);
          const upcoming = visibleFixtures(team, 5);
          const average = averageDifficulty(upcoming);
          return { player, fixtures: upcoming, average };
        })
        .sort((a, b) => a.average - b.average),
    [fixtureRows, squad],
  );
  const targetTeams = useMemo(
    () =>
      fixtureRows
        .map((team) => {
          const upcoming = visibleFixtures(team, range);
          const average = averageDifficulty(upcoming);
          return { team, fixtures: upcoming, average };
        })
        .sort((a, b) => a.average - b.average),
    [fixtureRows, range],
  );

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;

  return (
    <div>
      <SectionHeader
        title="Fixtures"
        subtitle="Fixture difficulty for your squad and transfer targets"
      />

      <div className="space-y-6">
        <Panel>
          <div className="mb-4">
            <h2 className="text-[18px] font-semibold text-primary">Your squad&apos;s upcoming fixtures</h2>
            <p className="mt-1 text-[13px] text-secondary">Tap a player to see more</p>
          </div>

          {teamId ? (
            <div className="space-y-2">
              {squadFixtureRows.map(({ player, fixtures: upcoming, average }) => (
                <button
                  type="button"
                  key={player.name}
                  onClick={() => openDrawer(player.name)}
                  className="grid w-full grid-cols-[40px_minmax(0,1fr)_auto] items-center gap-3 rounded-[10px] border border-fpl-border/70 px-3 py-3 text-left transition hover:border-fpl-green/40 hover:bg-fpl-raised"
                >
                  <img
                    src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${player.team_code ?? 1}-66.png`}
                    alt={`${player.team} kit`}
                    className="h-8 w-8 object-contain"
                  />
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-primary">{player.name}</div>
                    <div className="truncate text-xs text-muted">{player.team}</div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <div className="flex gap-1.5">
                      {upcoming.map((fixture, index) => (
                        <FdrChip key={`${player.name}-${fixture.gw}-${index}`} difficulty={fixture.difficulty} />
                      ))}
                    </div>
                    <div className={`text-[11px] ${scoreClass(average)}`}>
                      Avg difficulty: {average.toFixed(1)}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="rounded-[10px] border border-fpl-border bg-fpl-raised p-4">
              <p className="text-sm text-secondary">
                Connect your FPL team ID in Settings to see your squad&apos;s fixtures
              </p>
              <Link href="/settings" className="mt-3 inline-flex text-sm font-semibold text-fpl-green hover:text-primary">
                Open Settings
              </Link>
            </div>
          )}
        </Panel>

        <Panel>
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-[18px] font-semibold text-primary">Best teams to target</h2>
              <p className="mt-1 text-[13px] text-secondary">
                Teams with the easiest fixtures over the next {range} gameweeks
              </p>
            </div>
            <div className="flex rounded-lg border border-fpl-border bg-fpl-raised p-1">
              {fixtureRanges.map((option) => (
                <button
                  type="button"
                  key={option}
                  onClick={() => setRange(option)}
                  className={`rounded-md px-3 py-1.5 text-xs font-semibold ${
                    range === option ? "bg-fpl-green text-fpl-dark" : "text-secondary hover:text-primary"
                  }`}
                >
                  Next {option} GWs
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            {targetTeams.map(({ team, fixtures: upcoming, average }) => (
              <div
                key={team.team}
                className="grid grid-cols-[minmax(120px,1fr)_auto_48px] items-center gap-3 rounded-[10px] border border-fpl-border/70 px-3 py-3"
              >
                <div className={`truncate text-sm font-semibold ${average <= 2.5 ? "text-fpl-green" : "text-primary"}`}>
                  {team.team}
                </div>
                <div className="flex gap-1.5">
                  {upcoming.map((fixture, index) => (
                    <FdrChip key={`${team.team}-${fixture.gw}-${index}`} difficulty={fixture.difficulty} />
                  ))}
                </div>
                <div className={`text-right font-mono text-sm font-semibold ${scoreClass(average)}`}>
                  {average.toFixed(1)}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function findTeamFixtureRow(fixtureRows: FixtureTick[], player: SquadPlayer): FixtureTick {
  return (
    fixtureRows.find((team) => team.team_short === player.team || team.team === player.team) ?? {
      team: player.team,
      team_short: player.team,
      fixtures: [],
    }
  );
}

function averageDifficulty(fixtures: { difficulty: number }[]): number {
  if (!fixtures.length) return 3;
  return fixtures.reduce((sum, fixture) => sum + fixture.difficulty, 0) / fixtures.length;
}

function scoreClass(score: number): string {
  if (score <= 2.5) return "text-fpl-green";
  if (score <= 3.5) return "text-fpl-amber";
  return "text-fpl-red";
}

function FdrChip({ difficulty }: { difficulty: number }) {
  const color =
    difficulty <= 2
      ? "bg-fpl-green/15 text-fpl-green"
      : difficulty === 3
        ? "bg-fpl-amber/15 text-fpl-amber"
        : "bg-fpl-red/15 text-fpl-red";

  return (
    <span className={`inline-flex h-[22px] w-[26px] items-center justify-center rounded-[5px] font-mono text-[11px] font-bold ${color}`}>
      {difficulty}
    </span>
  );
}
