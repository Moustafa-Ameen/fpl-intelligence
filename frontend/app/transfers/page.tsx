"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/LoadingState";
import { MiniSparkline } from "@/components/MiniSparkline";
import { Panel } from "@/components/Panel";
import { SectionHeader } from "@/components/SectionHeader";
import { StartLikelihood } from "@/components/StartLikelihood";
import { useDrawer } from "@/context/DrawerContext";
import { getCurrentGameweek, getPlayerHistory, getSquad, getTransferTargets } from "@/lib/api";
import { points, positionCode } from "@/lib/format";
import type { PlayerHistoryPoint, SquadPlayer, TransferTarget } from "@/lib/types";

const positions = ["All", "GK", "DEF", "MID", "FWD"];
const positionNames: Record<string, string> = {
  GK: "Goalkeeper",
  DEF: "Defender",
  MID: "Midfielder",
  FWD: "Forward",
};

export default function TransfersPage() {
  const { openDrawer } = useDrawer();
  const [targets, setTargets] = useState<TransferTarget[]>([]);
  const [history, setHistory] = useState<Record<string, PlayerHistoryPoint[]>>({});
  const [squad, setSquad] = useState<SquadPlayer[]>([]);
  const [mode, setMode] = useState<"general" | "squad">("general");
  const [position, setPosition] = useState("All");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const teamId = window.localStorage.getItem("fpl_team_id");
    Promise.all([
      getTransferTargets(),
      teamId
        ? getCurrentGameweek().then((gw) => getSquad(teamId, gw.current_gw ?? 1))
        : Promise.resolve([]),
    ])
      .then(async ([targetRows, squadRows]) => {
        setTargets(targetRows);
        setSquad(squadRows);
        const pairs = await Promise.all(
          targetRows.slice(0, 20).map((player) => getPlayerHistory(player.name).then((rows) => [player.name, rows] as const)),
        );
        setHistory(Object.fromEntries(pairs));
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const weakestPosition = useMemo(() => {
    if (!squad.length) return null;
    const byPosition = new Map<string, number[]>();
    for (const player of squad) {
      byPosition.set(player.position, [...(byPosition.get(player.position) ?? []), player.predicted_pts ?? 0]);
    }
    return [...byPosition.entries()].sort(
      (a, b) => average(a[1]) - average(b[1]),
    )[0]?.[0];
  }, [squad]);

  const filtered = useMemo(() => {
    const min = minPrice ? Number(minPrice) : Number.NEGATIVE_INFINITY;
    const max = maxPrice ? Number(maxPrice) : Number.POSITIVE_INFINITY;
    return targets.filter((player) => {
      const code = positionCode(player.position);
      const matchesPosition = position === "All" || player.position === positionNames[position];
      const squadMode = mode === "general" || !weakestPosition || code === weakestPosition;
      return matchesPosition && squadMode && player.price >= min && player.price <= max;
    });
  }, [maxPrice, minPrice, mode, position, targets, weakestPosition]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;
  if (!targets.length) return <EmptyState />;

  return (
    <div>
      <SectionHeader
        title="Players worth signing this week"
        subtitle="Ranked by value, form, and predicted points"
      />

      <Panel>
        <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex rounded-lg border border-fpl-border bg-fpl-raised p-1">
            <Toggle active={mode === "general"} onClick={() => setMode("general")}>
              General targets
            </Toggle>
            <Toggle active={mode === "squad"} onClick={() => setMode("squad")}>
              For your squad
            </Toggle>
          </div>
          <div className="flex rounded-lg border border-fpl-border bg-fpl-raised p-1">
            {positions.map((item) => (
              <Toggle key={item} active={position === item} onClick={() => setPosition(item)}>
                {item}
              </Toggle>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <input
              value={minPrice}
              onChange={(event) => setMinPrice(event.target.value)}
              placeholder="Min £"
              className="w-24 rounded-lg border border-fpl-border bg-fpl-raised px-3 py-2 text-xs text-primary outline-none focus:border-fpl-green"
            />
            <input
              value={maxPrice}
              onChange={(event) => setMaxPrice(event.target.value)}
              placeholder="Max £"
              className="w-24 rounded-lg border border-fpl-border bg-fpl-raised px-3 py-2 text-xs text-primary outline-none focus:border-fpl-green"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="text-xs uppercase text-muted">
              <tr>
                <th className="pb-3">Player</th>
                <th className="pb-3">Team</th>
                <th className="pb-3">Pos</th>
                <th className="pb-3">Price</th>
                <th className="pb-3">Trend</th>
                <th className="pb-3">Form</th>
                <th className="pb-3">Value</th>
                <th className="pb-3">Start Likelihood</th>
                <th className="pb-3">Ownership %</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 20).map((player) => {
                const trend = history[player.name] ?? [];
                const trendColor = sparkColor(trend);
                return (
                  <tr key={player.name} className="border-b border-fpl-border text-sm odd:bg-fpl-raised/40 hover:bg-fpl-raised">
                    <td className="py-3 pr-4 font-medium text-primary">
                      <button type="button" onClick={() => openDrawer(player.name)} className="hover:text-fpl-green">
                        {player.name}
                      </button>
                      {player.start_likelihood < 0.4 ? (
                        <span className="ml-2 rounded bg-fpl-amber/15 px-2 py-1 text-[11px] text-fpl-amber">
                          rotation risk
                        </span>
                      ) : null}
                    </td>
                    <td className="py-3 pr-4 text-muted">{player.team}</td>
                    <td className="py-3 pr-4 text-muted">{positionCode(player.position)}</td>
                    <td className="py-3 pr-4 font-mono text-primary">£{points(player.price)}</td>
                    <td className="w-[80px] py-3 pr-4">
                      <MiniSparkline data={trend.slice(-5)} dataKey="price" color={trendColor} height={34} />
                    </td>
                    <td className="py-3 pr-4 font-mono text-primary">{points(player.form)}</td>
                    <td className="py-3 pr-4 font-mono text-primary">{points(player.value)}</td>
                    <td className="py-3 pr-4">
                      <StartLikelihood value={player.start_likelihood} />
                    </td>
                    <td className="py-3 pr-4 font-mono text-primary">
                      {points(player.selected_by_percent, 0)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
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

function average(values: number[]) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function sparkColor(rows: PlayerHistoryPoint[]) {
  if (rows.length < 2) return "#A0A0A0";
  const first = rows[0].price;
  const last = rows.at(-1)?.price ?? first;
  if (last > first) return "#00FF87";
  if (last < first) return "#FF4444";
  return "#A0A0A0";
}
