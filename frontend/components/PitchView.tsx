"use client";

import type { SquadPlayer } from "@/lib/types";
import { PitchCard } from "./PitchCard";

export function PitchView({
  squad,
  averageByPosition,
}: {
  squad: SquadPlayer[];
  averageByPosition: Record<string, number>;
}) {
  const starters = squad.slice(0, 11);
  const bench = squad.slice(11);
  const rows = [
    ["GK", starters.filter((player) => player.position === "GKP" || player.position === "GK").slice(0, 1)],
    ["DEF", starters.filter((player) => player.position === "DEF").slice(0, 5)],
    ["MID", starters.filter((player) => player.position === "MID").slice(0, 5)],
    ["FWD", starters.filter((player) => player.position === "FWD").slice(0, 3)],
  ] as const;

  return (
    <div>
      <div className="relative overflow-hidden rounded-2xl border border-fpl-border bg-[linear-gradient(180deg,#0d5c2e_0%,#0a4a25_50%,#0d5c2e_100%)] p-5">
        <div className="pointer-events-none absolute left-0 right-0 top-1/2 border-t border-white/20" />
        <div className="pointer-events-none absolute left-1/2 top-3 h-16 w-32 -translate-x-1/2 rounded-b-full border border-t-0 border-white/20" />
        <div className="pointer-events-none absolute bottom-3 left-1/2 h-16 w-32 -translate-x-1/2 rounded-t-full border border-b-0 border-white/20" />
        <div className="relative space-y-7">
          {rows.map(([label, players]) => (
            <div key={label}>
              <div className="mb-2 text-center text-[10px] font-bold uppercase tracking-[0.16em] text-white/70">
                {label}
              </div>
              <div className="flex flex-wrap justify-center gap-2 md:gap-4">
                {players.map((player) => (
                  <PitchCard
                    key={player.name}
                    player={player}
                    average={averageByPosition[player.position] ?? 0}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-fpl-border bg-fpl-card p-3">
        <div className="mb-2 text-xs font-bold uppercase tracking-[0.12em] text-muted">Bench</div>
        <div className="flex flex-wrap gap-2 md:gap-4">
          {bench.map((player) => (
            <PitchCard
              key={player.name}
              player={player}
              average={averageByPosition[player.position] ?? 0}
              bench
            />
          ))}
        </div>
      </div>
    </div>
  );
}
