"use client";

import { Crown } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { FixtureChip } from "@/components/FixtureChip";
import { EmptyState } from "@/components/LoadingState";
import { Panel } from "@/components/Panel";
import { StartLikelihood } from "@/components/StartLikelihood";
import { StatCard } from "@/components/StatCard";
import { useDrawer } from "@/context/DrawerContext";
import { getCurrentGameweek, getSquad } from "@/lib/api";
import { visibleFixtures } from "@/lib/fixtures";
import { initials, points, positionCode } from "@/lib/format";
import type {
  AccuracyResult,
  CaptainPick,
  FixtureTick,
  Player,
  SquadPlayer,
  TransferTarget,
} from "@/lib/types";

interface OverviewClientProps {
  players: Player[];
  captains: CaptainPick[];
  predictions: CaptainPick[];
  transfers: TransferTarget[];
  fixtures: FixtureTick[];
  gems: TransferTarget[];
  accuracy: AccuracyResult[];
}

export function OverviewClient({
  players,
  captains,
  predictions,
  transfers,
  fixtures,
  gems,
  accuracy,
}: OverviewClientProps) {
  const { openDrawer } = useDrawer();
  const [squad, setSquad] = useState<SquadPlayer[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const teamId = window.localStorage.getItem("fpl_team_id");
    queueMicrotask(() => setConnected(Boolean(teamId)));
    if (!teamId) return;

    getCurrentGameweek()
      .then((gw) => getSquad(teamId, gw.current_gw ?? 1))
      .then(setSquad)
      .catch(() => setSquad([]));
  }, []);

  const predictedGwPoints = useMemo(
    () =>
      predictions
        .slice(0, 11)
        .reduce((sum, player) => sum + (player.adjusted_pts ?? player.predicted_pts ?? 0), 0),
    [predictions],
  );
  const topCaptain = captains[0];
  const bestAccuracy = accuracy.find((row) => row.model === "FPL Intelligence (best)") ?? accuracy[0];
  const suggestions = buildSuggestions(squad, transfers, players);

  if (!players.length) return <EmptyState />;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Predicted GW Points"
          value={points(predictedGwPoints)}
          subLabel="Top 11 adjusted picks"
        />
        <StatCard
          label="Top Captain"
          value={topCaptain?.name ?? "-"}
          subLabel={`${points(topCaptain?.captain_score ?? topCaptain?.adjusted_pts)} score`}
        />
        <StatCard
          label="Model MAE"
          value={points(bestAccuracy?.adjusted_MAE ?? bestAccuracy?.raw_MAE)}
          subLabel="Lower is better"
        />
        <StatCard label="Players Tracked" value={players.length} subLabel="Current player pool" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,1fr)]">
        <div className="space-y-6">
          <Panel title="Suggested Moves">
            {!connected ? (
              <p className="mb-4 text-sm text-secondary">Connect your FPL team for personalised suggestions.</p>
            ) : null}
            <div className="space-y-4">
              {suggestions.slice(0, 2).map(({ incoming, outgoing, gain }) => (
                <div key={`${incoming.name}-${outgoing?.name}`} className="rounded-[10px] border border-fpl-border p-4">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <button
                      type="button"
                      onClick={() => outgoing && openDrawer(outgoing.name)}
                      className="text-left"
                    >
                      <span className="mr-2 rounded bg-fpl-red/15 px-2 py-1 text-[11px] font-bold text-fpl-red">
                        OUT
                      </span>
                      <span className="font-medium text-primary">{outgoing?.name ?? "Bench option"}</span>
                      <span className="text-sm text-secondary"> - {outgoing?.team ?? "Unknown"} - low xP</span>
                    </button>
                    <div className="text-muted">-&gt;</div>
                    <button type="button" onClick={() => openDrawer(incoming.name)} className="text-right">
                      <span className="mr-2 rounded bg-fpl-green/15 px-2 py-1 text-[11px] font-bold text-fpl-green">
                        IN
                      </span>
                      <span className="font-medium text-primary">{incoming.name}</span>
                      <span className="text-sm text-secondary">
                        {" "}
                        - {incoming.team} - {positionCode(incoming.position)} - GBP {points(incoming.price)}
                      </span>
                    </button>
                  </div>
                  <div className="mt-2 text-sm font-semibold text-fpl-green">
                    +{points(Math.max(gain, 0))} pts
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Captain Picks">
            <div className="space-y-3">
              {captains.slice(0, 3).map((player, index) => (
                <button
                  type="button"
                  key={player.name}
                  onClick={() => openDrawer(player.name)}
                  className="flex w-full items-center gap-4 rounded-[10px] border border-fpl-border p-4 text-left transition hover:bg-fpl-raised"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-full bg-fpl-raised text-xs font-bold text-primary">
                    {index === 0 ? <Crown className="h-5 w-5 text-fpl-gold" /> : initials(player.name)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-semibold text-primary">{player.name}</div>
                    <div className="text-[13px] text-secondary">
                      {player.team} - {player.reasoning ?? "Strong overall metrics"}
                    </div>
                  </div>
                  <div className="font-mono text-sm font-bold text-fpl-green">
                    {points(player.adjusted_pts ?? player.captain_score)} xP
                  </div>
                  <StartLikelihood value={player.start_likelihood} />
                </button>
              ))}
            </div>
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel title="Fixture Ticker">
            <div className="space-y-2">
              {fixtures.slice(0, 8).map((team) => (
                <div key={team.team} className="grid grid-cols-[1fr_auto] items-center gap-4">
                  <div className="truncate text-sm text-primary">{team.team}</div>
                  <div className="flex gap-2">
                    {visibleFixtures(team).map((fixture, index) => (
                      <FixtureChip key={`${team.team}-${fixture.gw}-${index}`} difficulty={fixture.difficulty} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Differential Picks">
            <div className="space-y-3">
              {gems.slice(0, 3).map((player) => (
                <button
                  type="button"
                  key={player.name}
                  onClick={() => openDrawer(player.name)}
                  className="w-full rounded-[10px] border border-fpl-border p-3 text-left hover:bg-fpl-raised"
                >
                  <div className="font-semibold text-primary">{player.name}</div>
                  <div className="mt-1 text-xs text-secondary">
                    {player.team} - {points(player.selected_by_percent, 0)}% owned
                  </div>
                  <div className="mt-3 h-1 rounded bg-fpl-border">
                    <div
                      className="h-1 rounded bg-fpl-green"
                      style={{ width: `${Math.min(player.selected_by_percent ?? 0, 100)}%` }}
                    />
                  </div>
                </button>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function buildSuggestions(
  squad: SquadPlayer[],
  transfers: TransferTarget[],
  players: Player[],
): { outgoing?: SquadPlayer | Player; incoming: TransferTarget; gain: number }[] {
  if (!squad.length) {
    const outCandidates = [...players].sort((a, b) => a.captain_score - b.captain_score).slice(0, 5);
    return transfers.slice(0, 2).map((incoming, index) => ({
      incoming,
      outgoing: outCandidates[index],
      gain: (incoming.adjusted_pts ?? incoming.transfer_score ?? 0) - (outCandidates[index]?.captain_score ?? 0),
    }));
  }

  const squadNames = new Set(squad.map((player) => player.name));
  const candidates = squad
    .filter((player) => !player.is_captain)
    .sort((a, b) => (a.predicted_pts ?? 0) - (b.predicted_pts ?? 0))
    .slice(0, 4);
  return candidates.flatMap((outgoing) => {
    const incoming = transfers.find(
      (player) =>
        !squadNames.has(player.name) &&
        positionCode(player.position) === outgoing.position &&
        (!outgoing.price || player.price <= outgoing.price + 0.5),
    );
    return incoming
      ? [
          {
            outgoing,
            incoming,
            gain: (incoming.adjusted_pts ?? incoming.transfer_score ?? 0) - (outgoing.predicted_pts ?? 0),
          },
        ]
      : [];
  });
}
