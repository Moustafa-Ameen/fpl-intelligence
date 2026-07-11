"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorState, PitchSkeleton } from "@/components/LoadingState";
import { Panel } from "@/components/Panel";
import { PitchView } from "@/components/PitchView";
import { SectionHeader } from "@/components/SectionHeader";
import { getCurrentGameweek, getSquad, getTeam } from "@/lib/api";
import { points, positionCode, price } from "@/lib/format";
import { selectCurrentSquadMetrics } from "@/lib/squadMetrics";
import type { SquadPlayer, TeamData } from "@/lib/types";

export default function SquadPage() {
  const [teamId, setTeamId] = useState("");
  const [squad, setSquad] = useState<SquadPlayer[]>([]);
  const [team, setTeam] = useState<TeamData | null>(null);
  const [showBench, setShowBench] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    queueMicrotask(() => {
      const savedTeamId = window.localStorage.getItem("fpl_team_id") ?? "";
      setShowBench(window.localStorage.getItem("show_bench_players") !== "false");
      setTeamId(savedTeamId);
      if (!savedTeamId) return;

      setLoading(true);
      getCurrentGameweek()
        .then((gw) => Promise.all([getSquad(savedTeamId, gw.current_gw ?? 1), getTeam(savedTeamId)]))
        .then(([squadRows, teamData]) => {
          setSquad(squadRows);
          setTeam(teamData);
        })
        .catch(() => setError(true))
        .finally(() => setLoading(false));
    });
  }, []);

  const metrics = useMemo(() => selectCurrentSquadMetrics(squad), [squad]);
  const displayedSquad = useMemo(() => [...metrics.starters, ...metrics.bench], [metrics]);
  const averageByPosition = useMemo(() => {
    const averages: Record<string, number> = {};
    for (const position of ["GKP", "GK", "DEF", "MID", "FWD"]) {
      const rows = displayedSquad.filter((player) => positionCode(player.position) === positionCode(position));
      averages[position] = rows.length
        ? rows.reduce((sum, player) => sum + (player.predicted_pts ?? 0), 0) / rows.length
        : 0;
    }
    return averages;
  }, [displayedSquad]);

  if (!teamId) {
    return (
      <div className="flex min-h-[65vh] items-center justify-center">
        <div className="fpl-card-shadow rounded-[10px] border border-fpl-border bg-fpl-card p-8 text-center text-muted">
          Enter your FPL team ID in the sidebar to see your squad predictions.
        </div>
      </div>
    );
  }

  if (loading) return <PitchSkeleton />;
  if (error) return <ErrorState />;
  if (!squad.length) return <EmptyState />;

  return (
    <div>
      <SectionHeader title="My Squad" subtitle={team?.team_name ?? `Team #${teamId}`} />
      <Panel>
        <PitchView squad={displayedSquad} averageByPosition={averageByPosition} showBench={showBench} />
        <div className="-mt-px grid grid-cols-2 overflow-hidden rounded-b-[10px] border border-fpl-border bg-fpl-card lg:grid-cols-4">
          <Summary label="Starting XI xP" value={points(metrics.totalStartingXp)} />
          <Summary label="Squad Value" value={price(team?.squad_value)} />
          <Summary label="Bank" value={price(team?.bank_value)} />
          <Summary label="Overall Rank" value={team?.overall_rank?.toLocaleString() ?? "-"} />
        </div>
      </Panel>
    </div>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-r border-t border-fpl-border bg-fpl-raised p-4 last:border-r-0 lg:border-t-0">
      <div className="text-[11px] uppercase tracking-[0.08em] text-muted">{label}</div>
      <div className="mt-2 font-mono text-xl font-bold text-primary">{value}</div>
    </div>
  );
}
