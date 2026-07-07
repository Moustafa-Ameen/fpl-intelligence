"use client";

import { ArrowRight, Crown, ShieldCheck, Sparkles, Target, TrendingUp } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { FixtureChip } from "@/components/FixtureChip";
import { EmptyState } from "@/components/LoadingState";
import { Panel } from "@/components/Panel";
import { StartLikelihood } from "@/components/StartLikelihood";
import { StatCard } from "@/components/StatCard";
import { useDrawer } from "@/context/DrawerContext";
import { getCurrentGameweek, getSquad } from "@/lib/api";
import { fixtureTickerWithFallback, visibleFixtures } from "@/lib/fixtures";
import { points, positionCode } from "@/lib/format";
import type {
  AccuracyResult,
  CaptainPick,
  FixtureTick,
  Player,
  SquadPlayer,
  TransferTarget,
} from "@/lib/types";

type ProjectionPlayer = Pick<
  CaptainPick,
  "name" | "team" | "position" | "team_code" | "start_likelihood" | "predicted_pts" | "adjusted_pts" | "captain_score"
>;

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

  const projectionPlayers = useMemo<ProjectionPlayer[]>(() => {
    if (squad.length) {
      return squad.slice(0, 11).map((player) => ({
        name: player.name,
        team: player.team,
        position: player.position,
        team_code: player.team_code,
        start_likelihood: player.start_likelihood ?? 0,
        predicted_pts: player.predicted_pts ?? 0,
        adjusted_pts: player.predicted_pts ?? 0,
        captain_score: player.predicted_pts ?? 0,
      }));
    }
    return predictions.slice(0, 11);
  }, [predictions, squad]);

  const predictedGwPoints = useMemo(
    () => projectionPlayers.reduce((sum, player) => sum + (player.adjusted_pts ?? player.predicted_pts ?? 0), 0),
    [projectionPlayers],
  );
  const topCaptain = captains[0];
  const bestAccuracy = accuracy.find((row) => row.model === "FPL Intelligence (best)") ?? accuracy[0];
  const suggestions = buildSuggestions(squad, transfers, players);
  const fixtureRows = fixtureTickerWithFallback(fixtures);

  if (!players.length) return <EmptyState />;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="fpl-card-shadow rounded-lg border border-fpl-border bg-[linear-gradient(135deg,rgba(0,255,135,0.1),rgba(16,21,20,0.96)_38%,rgba(143,76,248,0.12))] p-5">
          <div className="flex flex-wrap items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em] text-fpl-green">
            <Sparkles className="h-4 w-4" />
            FPL Intelligence
          </div>
          <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="text-[26px] font-semibold leading-tight text-primary md:text-[32px]">
                Gameweek decision cockpit
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">
                Captain edge, transfer delta, fixture difficulty, and model proof in one scanning view.
              </p>
            </div>
            <div className="rounded-lg border border-fpl-border bg-black/20 px-4 py-3">
              <div className="text-[10px] uppercase tracking-[0.14em] text-muted">Model status</div>
              <div className="mt-1 flex items-center gap-2 text-sm font-semibold text-primary">
                <span className="h-2 w-2 rounded-full bg-fpl-green shadow-[0_0_12px_rgba(0,255,135,0.75)]" />
                Model active · GW38 data
              </div>
            </div>
          </div>
        </div>

        <div className="fpl-card-shadow rounded-lg border border-fpl-border bg-fpl-card/95 p-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-muted">Squad link</div>
              <div className="mt-2 text-lg font-semibold text-primary">
                {connected ? "Personalized" : "Team ID needed"}
              </div>
            </div>
            <ShieldCheck className={`h-8 w-8 ${connected ? "text-fpl-green" : "text-muted"}`} />
          </div>
          <p className="mt-4 text-sm leading-6 text-secondary">
            {connected
              ? "Moves are filtered against your saved squad and current gameweek."
              : "Connect your FPL team ID to turn generic recommendations into squad-aware moves."}
          </p>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Predicted GW Points"
          value={points(predictedGwPoints)}
          subLabel="Top 11 adjusted picks"
        />
        <StatCard
          label="Top Captain"
          value={topCaptain?.name ?? "-"}
          subLabel={`Adjusted score ${points(topCaptain?.captain_score ?? topCaptain?.adjusted_pts)}`}
        />
        <StatCard
          label="Model MAE"
          value={points(bestAccuracy?.adjusted_MAE ?? bestAccuracy?.raw_MAE)}
          subLabel="Lower is better"
        />
        <StatCard label="Players Tracked" value={players.length} subLabel="Current player pool" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(340px,0.9fr)]">
        <div className="space-y-6">
          <Panel title={connected ? "Your predicted XI" : "Top predicted XI · this gameweek"}>
            <ProjectionPitch players={projectionPlayers} onSelect={openDrawer} />
          </Panel>

          <Panel title="Suggested Moves">
            {!connected ? (
              <p className="mb-4 text-sm italic text-muted">
                Connect your FPL team ID in Settings for personalised suggestions
              </p>
            ) : null}
            <div className="space-y-4">
              {suggestions.slice(0, 2).map(({ incoming, outgoing, gain }) => (
                <div
                  key={`${incoming.name}-${outgoing?.name}`}
                  className="fpl-suggested-move rounded-lg border border-fpl-border bg-fpl-raised/50 p-4"
                >
                  <div className="grid grid-cols-[minmax(0,1fr)_44px_minmax(0,1fr)] items-center gap-3">
                    <button
                      type="button"
                      onClick={() => outgoing && openDrawer(outgoing.name)}
                      className="flex min-w-0 items-center gap-3 text-left"
                    >
                      <img
                        src={kitUrl(outgoing?.team_code)}
                        alt={`${outgoing?.team ?? "Outgoing"} kit`}
                        className="h-12 w-12 shrink-0 object-contain"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex min-w-0 items-center gap-2">
                          <span className="shrink-0 rounded bg-fpl-red/15 px-2 py-1 text-[11px] font-bold text-fpl-red">
                            OUT
                          </span>
                          <span className="truncate text-sm font-bold text-primary">
                            {outgoing?.name ?? "Bench option"}
                          </span>
                        </div>
                        <div className="mt-1 truncate text-xs text-muted">
                          {outgoing?.team ?? "Unknown"} - low xP
                        </div>
                      </div>
                    </button>
                    <div className="move-arrow flex h-10 w-10 items-center justify-center rounded-full border border-fpl-border bg-black/20 text-muted">
                      <ArrowRight className="h-[18px] w-[18px] text-fpl-green" />
                    </div>
                    <button
                      type="button"
                      onClick={() => openDrawer(incoming.name)}
                      className="flex min-w-0 items-center gap-3 text-left"
                    >
                      <img
                        src={kitUrl(incoming.team_code)}
                        alt={`${incoming.team} kit`}
                        className="h-12 w-12 shrink-0 object-contain"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex min-w-0 items-center gap-2">
                          <span className="shrink-0 rounded bg-fpl-green/15 px-2 py-1 text-[11px] font-bold text-fpl-green">
                            IN
                          </span>
                          <span className="truncate text-sm font-bold text-primary">{incoming.name}</span>
                        </div>
                        <div className="mt-1 truncate text-xs text-muted">
                          {incoming.team} - {positionCode(incoming.position)} - {"\u00a3"}{points(incoming.price)}m
                        </div>
                      </div>
                    </button>
                  </div>
                  <div className="mt-3 border-t border-white/[0.06] pt-2 pl-1 text-[13px] font-semibold text-fpl-green">
                    +{points(Math.max(gain, 0))} predicted pts gain
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel title="Captain Edge">
            {topCaptain ? (
              <button
                type="button"
                onClick={() => openDrawer(topCaptain.name)}
                className="w-full rounded-lg border border-fpl-gold/25 bg-[linear-gradient(135deg,rgba(255,200,87,0.13),rgba(255,255,255,0.025))] p-4 text-left hover:border-fpl-gold/50"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.12em] text-fpl-gold">
                      <Crown className="h-4 w-4" />
                      Captain Edge
                    </div>
                    <div className="mt-3 truncate text-xl font-semibold text-primary">{topCaptain.name}</div>
                    <div className="mt-1 text-sm text-secondary">{topCaptain.team}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-2xl font-bold text-fpl-gold">
                      {points(topCaptain.captain_score ?? topCaptain.adjusted_pts)} xP
                    </div>
                    <div className="mt-2 flex justify-end">
                      <StartLikelihood value={topCaptain.start_likelihood} />
                    </div>
                  </div>
                </div>
                <p className="mt-4 text-sm leading-6 text-secondary">
                  {topCaptain.reasoning ?? "Best blend of projected points and start confidence."}
                </p>
              </button>
            ) : null}
          </Panel>

          <Panel title="Fixture Ticker">
            <div className="space-y-2">
              {fixtureRows.slice(0, 8).map((team) => (
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

          <Panel title="Differential Radar">
            <div className="space-y-3">
              {gems.slice(0, 3).map((player) => (
                <button
                  type="button"
                  key={player.name}
                  onClick={() => openDrawer(player.name)}
                  className="w-full rounded-lg border border-fpl-border bg-fpl-raised/45 p-3 text-left hover:bg-fpl-raised"
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

          <Panel title="Model Proof">
            <div className="grid grid-cols-2 gap-3">
              <ProofMetric
                icon={<Target className="h-4 w-4" />}
                label="Best MAE"
                value={points(bestAccuracy?.adjusted_MAE ?? bestAccuracy?.raw_MAE)}
              />
              <ProofMetric
                icon={<TrendingUp className="h-4 w-4" />}
                label="Pool"
                value={players.length.toLocaleString()}
              />
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
    .slice(0, 2);
  return candidates.flatMap((outgoing) => {
    const outgoingPosition = positionCode(outgoing.position);
    const outgoingPrice = outgoing.price;
    const outgoingProjected = outgoing.predicted_pts ?? 0;
    const incoming = transfers
      .filter((player) => {
        const incomingProjected = player.adjusted_pts ?? player.predicted_pts ?? 0;
        const priceGap = typeof outgoingPrice === "number" ? Math.abs(player.price - outgoingPrice) : 0;
        return (
          !squadNames.has(player.name) &&
          positionCode(player.position) === outgoingPosition &&
          incomingProjected > outgoingProjected &&
          priceGap <= 1
        );
      })
      .sort((a, b) => b.transfer_score - a.transfer_score)[0];
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

function ProjectionPitch({ players, onSelect }: { players: ProjectionPlayer[]; onSelect: (name: string) => void }) {
  const rows = projectionRows(players);
  return (
    <div className="relative overflow-hidden rounded-lg border border-fpl-border bg-[linear-gradient(180deg,#0b6a39_0%,#07502d_48%,#064325_100%)] p-4">
      <div className="pointer-events-none absolute inset-x-0 top-1/2 border-t border-white/12" />
      <div className="pointer-events-none absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/12" />
      <div className="pointer-events-none absolute inset-4 rounded border border-white/10" />
      <div className="relative grid min-h-[420px] content-between gap-5">
        {rows.map((row, index) => (
          <div key={index} className="flex flex-wrap justify-center gap-3 md:gap-4">
            {row.map((player) => (
              <ProjectionCard key={`${player.name}-${index}`} player={player} onSelect={onSelect} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function ProjectionCard({ player, onSelect }: { player: ProjectionPlayer; onSelect: (name: string) => void }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(player.name)}
      className="fpl-pitch-card w-[104px] rounded-lg bg-black/25 p-2 text-center backdrop-blur hover:bg-black/35"
      aria-label={player.name}
    >
      <img
        src={kitUrl(player.team_code)}
        alt={`${player.team} kit`}
        className="mx-auto h-[54px] w-[66px] object-contain"
      />
      <div className="mt-1 truncate text-[12px] font-semibold text-white">{player.name.split(" ").at(-1)}</div>
      <div className="font-mono text-xs font-bold text-fpl-green">
        {points(player.adjusted_pts ?? player.predicted_pts ?? player.captain_score)} xP
      </div>
    </button>
  );
}

function projectionRows(players: ProjectionPlayer[]) {
  const rowDefinitions = [
    { code: "GK", take: 1 },
    { code: "DEF", take: 5 },
    { code: "MID", take: 5 },
    { code: "FWD", take: 3 },
  ];
  const used = new Set<string>();
  const rows = rowDefinitions
    .map(({ code, take }) => {
      const row = players.filter((player) => positionCode(player.position) === code && !used.has(player.name)).slice(0, take);
      row.forEach((player) => used.add(player.name));
      return row;
    })
    .filter((row) => row.length);
  const remaining = players.filter((player) => !used.has(player.name));
  if (remaining.length) rows.push(remaining);
  return rows.length ? rows : [players];
}

function ProofMetric({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-fpl-border bg-fpl-raised p-3">
      <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.12em] text-muted">
        <span className="text-fpl-green">{icon}</span>
        {label}
      </div>
      <div className="mt-3 font-mono text-lg font-bold text-primary">{value}</div>
    </div>
  );
}

function kitUrl(teamCode?: number | null): string {
  return `https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${teamCode ?? 1}-66.png`;
}
