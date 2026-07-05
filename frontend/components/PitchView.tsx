"use client";

import type { SquadPlayer } from "@/lib/types";
import { PitchCard } from "./PitchCard";

export function PitchView({
  squad,
  averageByPosition,
  showBench = true,
}: {
  squad: SquadPlayer[];
  averageByPosition: Record<string, number>;
  showBench?: boolean;
}) {
  const starters = squad.slice(0, 11);
  const bench = squad.slice(11);
  const rows = [
    starters.filter((player) => player.position === "GKP" || player.position === "GK").slice(0, 1),
    starters.filter((player) => player.position === "DEF").slice(0, 5),
    starters.filter((player) => player.position === "MID").slice(0, 5),
    starters.filter((player) => player.position === "FWD").slice(0, 3),
  ];

  return (
    <div>
      <div className="relative overflow-hidden rounded-[10px] border border-fpl-border bg-[linear-gradient(180deg,#0d5c2e_0%,#0a4a25_50%,#0d5c2e_100%)]">
        <div className="pointer-events-none absolute left-0 right-0 top-1/2 border-t border-white/10" />
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-[120px] w-[120px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/10" />
        <div className="pointer-events-none absolute left-1/2 top-3 h-16 w-32 -translate-x-1/2 rounded-b-full border border-t-0 border-white/10" />
        <div className="pointer-events-none absolute bottom-3 left-1/2 h-16 w-32 -translate-x-1/2 rounded-t-full border border-b-0 border-white/10" />
        <div className="relative">
          {rows.map((players, index) => (
            <div
              key={index}
              className={`px-4 py-6 ${index > 0 ? "border-t border-dashed border-white/10" : ""}`}
            >
              <div className="flex flex-wrap justify-center gap-5 md:gap-7">
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

      {showBench ? (
        <div className="fpl-card-shadow mt-4 rounded-[10px] border border-fpl-border bg-fpl-card p-3">
          <div className="mb-2 text-[11px] font-bold uppercase tracking-[0.08em] text-muted">Bench</div>
          <div className="flex flex-wrap gap-5 md:gap-7">
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
      ) : null}
    </div>
  );
}
