"use client";

import type { Player } from "@/lib/types";
import { points, positionCode } from "@/lib/format";
import { useDrawer } from "@/context/DrawerContext";
import { StartLikelihood } from "./StartLikelihood";

interface PlayerRowProps {
  player: Player;
}

export function PlayerRow({ player }: PlayerRowProps) {
  const { openDrawer } = useDrawer();

  return (
    <tr className="border-b border-fpl-border/80 text-sm odd:bg-fpl-dark/15 hover:bg-fpl-purple/15">
      <td className="py-3 pr-4 font-medium text-primary">
        <button type="button" onClick={() => openDrawer(player.name)} className="hover:text-fpl-green">
          {player.name}
        </button>
      </td>
      <td className="py-3 pr-4 text-muted">{player.team}</td>
      <td className="py-3 pr-4 text-muted">{positionCode(player.position)}</td>
      <td className="py-3 pr-4 font-mono text-primary">{points(player.price)}</td>
      <td className="py-3 pr-4 font-mono text-primary">{points(player.total_points, 0)}</td>
      <td className="py-3 pr-4 font-mono text-primary">{points(player.ppg)}</td>
      <td className="py-3 pr-4 font-mono text-primary">{points(player.form)}</td>
      <td className="py-3 pr-4">
        <StartLikelihood value={player.start_likelihood} />
      </td>
      <td className="py-3 pr-4 font-mono text-primary">{points(player.value)}</td>
      <td className="py-3 pr-4 font-mono text-primary">{points(player.captain_score)}</td>
      <td className="py-3 pr-4 font-mono text-primary">{points(player.transfer_score)}</td>
    </tr>
  );
}
