"use client";

import { ArrowRight, ChevronDown, TrendingDown, TrendingUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/LoadingState";
import { MiniSparkline } from "@/components/MiniSparkline";
import { Panel } from "@/components/Panel";
import { SectionHeader } from "@/components/SectionHeader";
import { StartLikelihood } from "@/components/StartLikelihood";
import { useDrawer } from "@/context/DrawerContext";
import {
  getCurrentGameweek,
  getPlayerHistory,
  getSquad,
  getTeam,
  getTransferTargets,
} from "@/lib/api";
import { kitUrl, points, positionCode, price } from "@/lib/format";
import type { PlayerHistoryPoint, SquadPlayer, TeamData, TransferTarget } from "@/lib/types";

type Tab = "best" | "prices";
type PositionFilter = "All" | "GK" | "DEF" | "MID" | "FWD";

const positionFilters: PositionFilter[] = ["All", "GK", "DEF", "MID", "FWD"];

export default function TransfersPage() {
  const { openDrawer } = useDrawer();
  const [targets, setTargets] = useState<TransferTarget[]>([]);
  const [history, setHistory] = useState<Record<string, PlayerHistoryPoint[]>>({});
  const [squad, setSquad] = useState<SquadPlayer[]>([]);
  const [team, setTeam] = useState<TeamData | null>(null);
  const [teamConnected, setTeamConnected] = useState(false);
  const [tab, setTab] = useState<Tab>("best");
  const [position, setPosition] = useState<PositionFilter>("All");
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const teamId = window.localStorage.getItem("fpl_team_id");
    queueMicrotask(() => setTeamConnected(Boolean(teamId)));

    Promise.all([
      getTransferTargets(),
      teamId
        ? getCurrentGameweek()
            .then((gw) => getSquad(teamId, gw.current_gw ?? 1))
            .catch(() => [])
        : Promise.resolve([]),
      teamId ? getTeam(teamId).catch(() => null) : Promise.resolve(null),
    ])
      .then(async ([targetRows, squadRows, teamData]) => {
        setTargets(targetRows);
        setSquad(squadRows);
        setTeam(teamData);
        const pairs = await Promise.all(
          targetRows.slice(0, 25).map((player) =>
            getPlayerHistory(player.name)
              .then((rows) => [player.name, rows] as const)
              .catch(() => [player.name, []] as const),
          ),
        );
        setHistory(Object.fromEntries(pairs));
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const squadNames = useMemo(() => new Set(squad.map((player) => player.name)), [squad]);
  const weakestPlayer = useMemo(
    () => [...squad].sort((a, b) => predicted(a) - predicted(b))[0] ?? null,
    [squad],
  );
  const weakestPosition = weakestPlayer ? positionCode(weakestPlayer.position) : null;
  const allUpgradeGroups = useMemo(
    () => buildUpgradeGroups(squad, targets, squadNames),
    [squad, squadNames, targets],
  );
  const primaryUpgrades = useMemo(() => {
    if (!weakestPlayer || !weakestPosition) return [];
    return replacementsFor(weakestPlayer, targets, squadNames).slice(0, 2);
  }, [squadNames, targets, weakestPlayer, weakestPosition]);
  const topTargets = useMemo(
    () =>
      [...targets]
        .sort((a, b) => (b.transfer_score ?? 0) - (a.transfer_score ?? 0))
        .slice(0, 15),
    [targets],
  );
  const risers = useMemo(
    () =>
      [...targets]
        .sort((a, b) => moverScore(b) - moverScore(a))
        .slice(0, 5),
    [targets],
  );
  const fallers = useMemo(
    () =>
      [...targets]
        .filter((player) => (player.selected_by_percent ?? 0) >= 5)
        .sort((a, b) => (a.form ?? 0) - (b.form ?? 0))
        .slice(0, 5),
    [targets],
  );

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;
  if (!targets.length) return <EmptyState />;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Who should I bring in?"
        subtitle="Squad-aware upgrades, top transfer targets, and price movement signals."
      />

      <div className="rounded-lg border border-fpl-border bg-fpl-card/95 p-4 text-sm text-secondary">
        Remember: transfers beyond your free allowance cost <span className="font-mono text-fpl-red">-4 pts</span>{" "}
        each.{" "}
        {team?.free_transfers_available !== null && team?.free_transfers_available !== undefined
          ? `You have ${team.free_transfers_available} free transfer(s) available.`
          : "Check the FPL app for your free transfer count."}
      </div>

      <div className="flex w-fit rounded-lg border border-fpl-border bg-fpl-raised p-1">
        <Toggle active={tab === "best"} onClick={() => setTab("best")}>
          Best to sign
        </Toggle>
        <Toggle active={tab === "prices"} onClick={() => setTab("prices")}>
          Price movers
        </Toggle>
      </div>

      {tab === "best" ? (
        <div className="space-y-6">
          {teamConnected ? (
            <Panel>
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-[18px] font-semibold text-primary">Upgrade your squad</h2>
                  <p className="mt-1 text-[13px] text-secondary">
                    Realistic replacements based on your weakest projected player.
                  </p>
                </div>
                <div className="flex rounded-lg border border-fpl-border bg-fpl-raised p-1">
                  {positionFilters.map((item) => (
                    <Toggle key={item} active={position === item} onClick={() => setPosition(item)}>
                      {item}
                    </Toggle>
                  ))}
                </div>
              </div>

              {weakestPlayer ? (
                <div className="space-y-3">
                  <div className="rounded-lg border border-fpl-border bg-fpl-raised/60 p-3 text-sm text-secondary">
                    Weakest current projection:{" "}
                    <span className="font-semibold text-primary">{weakestPlayer.name}</span>{" "}
                    <span className="text-muted">({weakestPlayer.team}, {points(predicted(weakestPlayer))} pts)</span>
                  </div>

                  {(position === "All" || position === weakestPosition ? primaryUpgrades : []).map((upgrade) => (
                    <UpgradeRow key={`${upgrade.outgoing.name}-${upgrade.incoming.name}`} upgrade={upgrade} onSelect={openDrawer} />
                  ))}

                  {primaryUpgrades.length === 0 ? (
                    <p className="text-sm text-muted">No realistic same-position upgrades found within £1.5m.</p>
                  ) : null}

                  <button
                    type="button"
                    onClick={() => setExpanded((value) => !value)}
                    className="inline-flex items-center gap-1 text-sm font-semibold text-fpl-green hover:text-primary"
                  >
                    See more options
                    <ChevronDown className={`h-4 w-4 transition ${expanded ? "rotate-180" : ""}`} />
                  </button>

                  {expanded ? (
                    <div className="space-y-5 border-t border-white/[0.06] pt-4">
                      {allUpgradeGroups
                        .filter((group) => position === "All" || group.position === position)
                        .map((group) => (
                          <div key={group.position}>
                            <h3 className="mb-2 text-xs font-bold uppercase tracking-[0.12em] text-muted">
                              {group.position} upgrades
                            </h3>
                            <div className="space-y-3">
                              {group.replacements.map((upgrade) => (
                                <UpgradeRow
                                  key={`${group.position}-${upgrade.outgoing.name}-${upgrade.incoming.name}`}
                                  upgrade={upgrade}
                                  onSelect={openDrawer}
                                />
                              ))}
                            </div>
                          </div>
                        ))}
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="text-sm text-muted">Connect your FPL team ID to see squad upgrades.</p>
              )}
            </Panel>
          ) : (
            <Panel>
              <p className="text-sm text-muted">
                Connect your FPL team ID in Settings to see upgrade suggestions from your actual squad.
              </p>
            </Panel>
          )}

          <Panel>
            <div className="mb-4">
              <h2 className="text-[18px] font-semibold text-primary">Top picks regardless of squad</h2>
              <p className="mt-1 text-[13px] text-secondary">Top 15 players by transfer score.</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase text-muted">
                  <tr>
                    <th className="pb-3 pr-3">Kit</th>
                    <th className="pb-3 pr-3">Player</th>
                    <th className="pb-3 pr-3">Team</th>
                    <th className="pb-3 pr-3">Pos</th>
                    <th className="pb-3 pr-3 text-right">Price</th>
                    <th className="pb-3 pr-3 text-right">Predicted</th>
                    <th className="pb-3 pr-3 text-right">Start %</th>
                    <th className="pb-3 pr-3 text-right">Ownership</th>
                    <th className="pb-3 text-right">Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {topTargets.map((player, index) => (
                    <tr
                      key={player.name}
                      onClick={() => openDrawer(player.name)}
                      className={`cursor-pointer border-b border-fpl-border hover:bg-fpl-green/5 ${
                        index % 2 === 0 ? "bg-[#161616]" : "bg-[#181818]"
                      }`}
                    >
                      <td className="py-3 pr-3">
                        <img src={kitUrl(player.team_code)} alt={`${player.team} kit`} className="h-10 w-10 object-contain" />
                      </td>
                      <td className="py-3 pr-3 font-semibold text-primary">
                        {player.name}
                        {player.start_likelihood < 0.4 ? (
                          <span className="ml-2 rounded bg-fpl-amber/15 px-2 py-1 text-[11px] text-fpl-amber">
                            rotation risk
                          </span>
                        ) : null}
                      </td>
                      <td className="py-3 pr-3 text-muted">{player.team}</td>
                      <td className="py-3 pr-3 text-muted">{positionCode(player.position)}</td>
                      <td className="py-3 pr-3 text-right font-mono text-primary">{price(player.price)}</td>
                      <td className="py-3 pr-3 text-right font-mono text-fpl-green">
                        {points(projected(player))}
                      </td>
                      <td className="py-3 pr-3 text-right">
                        <StartLikelihood value={player.start_likelihood} />
                      </td>
                      <td className="py-3 pr-3 text-right font-mono text-primary">
                        {points(player.selected_by_percent, 0)}%
                      </td>
                      <td className="w-[74px] py-3 text-right">
                        <MiniSparkline data={(history[player.name] ?? []).slice(-5)} dataKey="price" color="#00FF87" height={34} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <PriceMoverPanel
            title="Likely to rise in price"
            icon={<TrendingUp className="h-4 w-4 text-fpl-green" />}
            rows={risers}
            tone="green"
            onSelect={openDrawer}
          />
          <PriceMoverPanel
            title="Likely to drop"
            icon={<TrendingDown className="h-4 w-4 text-fpl-red" />}
            rows={fallers}
            tone="red"
            onSelect={openDrawer}
          />
        </div>
      )}
    </div>
  );
}

function UpgradeRow({
  upgrade,
  onSelect,
}: {
  upgrade: Upgrade;
  onSelect: (name: string) => void;
}) {
  return (
    <div className="rounded-lg border border-fpl-border bg-[#161616] p-4">
      <div className="grid grid-cols-[minmax(0,1fr)_40px_minmax(0,1fr)_auto] items-center gap-3">
        <PlayerTransferSide player={upgrade.outgoing} label="OUT" onSelect={onSelect} />
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-fpl-border bg-black/20">
          <ArrowRight className="h-4 w-4 text-muted" />
        </div>
        <PlayerTransferSide player={upgrade.incoming} label="IN" onSelect={onSelect} />
        <div className="text-right font-mono text-sm font-bold text-fpl-green">
          +{points(upgrade.delta)} pts
          <div className="mt-1 font-sans text-[11px] font-semibold text-fpl-green">
            better predicted score
          </div>
        </div>
      </div>
    </div>
  );
}

function PlayerTransferSide({
  player,
  label,
  onSelect,
}: {
  player: SquadPlayer | TransferTarget;
  label: "OUT" | "IN";
  onSelect: (name: string) => void;
}) {
  return (
    <button type="button" onClick={() => onSelect(player.name)} className="flex min-w-0 items-center gap-3 text-left">
      <img src={kitUrl(player.team_code)} alt={`${player.team} kit`} className="h-12 w-12 shrink-0 object-contain" />
      <div className="min-w-0">
        <div className={`text-[10px] font-bold ${label === "OUT" ? "text-fpl-red" : "text-fpl-green"}`}>
          {label}
        </div>
        <div className="truncate text-sm font-semibold text-primary">{player.name}</div>
        <div className="truncate text-xs text-muted">
          {player.team} · {price(player.price ?? null)}
        </div>
      </div>
    </button>
  );
}

function PriceMoverPanel({
  title,
  icon,
  rows,
  tone,
  onSelect,
}: {
  title: string;
  icon: React.ReactNode;
  rows: TransferTarget[];
  tone: "green" | "red";
  onSelect: (name: string) => void;
}) {
  return (
    <Panel>
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-[18px] font-semibold text-primary">
            {icon}
            {title}
          </h2>
          <p className="mt-1 text-[11px] italic text-muted">Rule-based estimate — not a model prediction</p>
        </div>
      </div>
      <div className="space-y-3">
        {rows.map((player) => (
          <button
            type="button"
            key={player.name}
            onClick={() => onSelect(player.name)}
            className="grid w-full grid-cols-[44px_minmax(0,1fr)_auto] items-center gap-3 rounded-lg border border-fpl-border bg-[#161616] p-3 text-left hover:bg-fpl-raised"
          >
            <img src={kitUrl(player.team_code)} alt={`${player.team} kit`} className="h-10 w-10 object-contain" />
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-primary">{player.name}</div>
              <div className="mt-1 flex items-center gap-3 text-xs text-muted">
                <span>{price(player.price)}</span>
                <div className="h-1.5 w-24 rounded bg-fpl-border">
                  <div
                    className={`h-1.5 rounded ${tone === "green" ? "bg-fpl-green" : "bg-fpl-red"}`}
                    style={{ width: `${Math.min(100, player.selected_by_percent ?? 0)}%` }}
                  />
                </div>
              </div>
            </div>
            <div className="font-mono text-sm text-primary">{points(player.selected_by_percent, 0)}%</div>
          </button>
        ))}
      </div>
    </Panel>
  );
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
        active ? "bg-fpl-green text-fpl-dark" : "text-secondary hover:text-primary"
      }`}
    >
      {children}
    </button>
  );
}

interface Upgrade {
  outgoing: SquadPlayer;
  incoming: TransferTarget;
  delta: number;
}

function buildUpgradeGroups(
  squad: SquadPlayer[],
  targets: TransferTarget[],
  squadNames: Set<string>,
): { position: string; replacements: Upgrade[] }[] {
  return positionFilters
    .filter((item) => item !== "All")
    .flatMap((position) => {
      const outgoing = squad
        .filter((player) => positionCode(player.position) === position)
        .sort((a, b) => predicted(a) - predicted(b))[0];
      if (!outgoing) return [];
      const replacements = replacementsFor(outgoing, targets, squadNames).slice(0, 3);
      return replacements.length ? [{ position, replacements }] : [];
    });
}

function replacementsFor(
  outgoing: SquadPlayer,
  targets: TransferTarget[],
  squadNames: Set<string>,
): Upgrade[] {
  const outgoingProjection = predicted(outgoing);
  const outgoingPrice = outgoing.price ?? 0;
  return targets
    .filter((target) => {
      const priceGap = Math.abs(target.price - outgoingPrice);
      return (
        !squadNames.has(target.name) &&
        positionCode(target.position) === positionCode(outgoing.position) &&
        projected(target) > outgoingProjection &&
        priceGap <= 1.5
      );
    })
    .sort((a, b) => (b.transfer_score ?? 0) - (a.transfer_score ?? 0))
    .map((incoming) => ({
      outgoing,
      incoming,
      delta: projected(incoming) - outgoingProjection,
    }));
}

function predicted(player: SquadPlayer): number {
  return player.predicted_pts ?? 0;
}

function projected(player: TransferTarget): number {
  return player.adjusted_pts ?? player.predicted_pts ?? player.transfer_score ?? 0;
}

function moverScore(player: TransferTarget): number {
  return (player.selected_by_percent ?? 0) * (player.form ?? 0);
}

