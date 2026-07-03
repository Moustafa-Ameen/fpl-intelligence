"use client";

import type { SquadPlayer } from "@/lib/types";
import { points } from "@/lib/format";
import { useDrawer } from "@/context/DrawerContext";
import { StartLikelihood } from "./StartLikelihood";

interface PitchCardProps {
  player: SquadPlayer;
  average: number;
  bench?: boolean;
}

export function PitchCard({ player, average, bench = false }: PitchCardProps) {
  const { openDrawer } = useDrawer();
  const predicted = player.predicted_pts ?? 0;
  const color = predicted >= average ? "text-fpl-green" : "text-fpl-red";
  const teamCode = player.team_code ?? 1;

  return (
    <button
      type="button"
      onClick={() => openDrawer(player.name)}
      className={`relative flex w-[70px] flex-col items-center rounded-lg p-1.5 text-center transition hover:bg-white/10 md:w-[90px] ${
        bench ? "opacity-70" : ""
      }`}
    >
      <div className="relative">
        <img
          src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${teamCode}-66.png`}
          alt={`${player.team} kit`}
          className="h-10 w-12 object-contain md:h-12"
        />
        {player.is_captain || player.is_vice_captain ? (
          <span
            className={`absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
              player.is_captain ? "bg-fpl-gold text-fpl-dark" : "bg-slate-300 text-fpl-dark"
            }`}
          >
            {player.is_captain ? "C" : "V"}
          </span>
        ) : null}
      </div>
      <div className="mt-1 w-full truncate text-xs font-bold text-white">
        {player.web_name ?? player.name.split(" ").at(-1)}
      </div>
      <div className={`font-mono text-[11px] font-bold ${color}`}>{points(predicted)} xP</div>
      <StartLikelihood value={player.start_likelihood} />
    </button>
  );
}
