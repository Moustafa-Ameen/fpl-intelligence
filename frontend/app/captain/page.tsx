"use client";

import { Crown } from "lucide-react";
import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/LoadingState";
import { Panel } from "@/components/Panel";
import { SectionHeader } from "@/components/SectionHeader";
import { StartLikelihood } from "@/components/StartLikelihood";
import { useDrawer } from "@/context/DrawerContext";
import { getCaptaincyPredictions } from "@/lib/api";
import { points } from "@/lib/format";
import type { CaptainPick } from "@/lib/types";

export default function CaptainPage() {
  const { openDrawer } = useDrawer();
  const [picks, setPicks] = useState<CaptainPick[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    getCaptaincyPredictions()
      .then(setPicks)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;
  if (!picks.length) return <EmptyState />;

  const topPick = picks[0];

  return (
    <div>
      <SectionHeader
        title="Who should you captain this week?"
        subtitle="Based on predicted points × start likelihood"
      />

      <button
        type="button"
        onClick={() => openDrawer(topPick.name)}
        className="mb-6 min-h-40 w-full rounded-xl border-l-4 border-fpl-gold bg-[linear-gradient(135deg,#240044,#3D0066)] p-6 text-left"
      >
        <div className="flex items-start justify-between gap-6">
          <div>
            <h2 className="text-[28px] font-bold text-primary">{topPick.name}</h2>
            <div className="mt-1 text-sm text-muted">{topPick.team}</div>
            <p className="mt-4 text-sm text-muted">{topPick.reasoning ?? "Strong overall metrics"}</p>
          </div>
          <Crown className="h-9 w-9 text-fpl-gold" />
          <div className="text-right">
            <div className="font-mono text-[40px] font-bold text-fpl-gold">
              {points(topPick.predicted_pts ?? topPick.adjusted_pts)} xP
            </div>
            <div className="mt-2 inline-flex rounded-full bg-fpl-green/15 px-3 py-1">
              <StartLikelihood value={topPick.start_likelihood} />
            </div>
          </div>
        </div>
      </button>

      <Panel>
        <div className="space-y-2">
          {picks.map((player, index) => (
            <button
              type="button"
              key={player.name}
              onClick={() => openDrawer(player.name)}
              className="grid w-full grid-cols-[48px_1fr_auto_auto] items-center gap-4 rounded-lg px-4 py-3 text-left odd:bg-fpl-dark/20 hover:bg-fpl-purple/20"
            >
              <div className="font-mono text-sm text-muted">
                {index === 0 ? <Crown className="h-4 w-4 text-fpl-gold" /> : index + 1}
              </div>
              <div>
                <div className="font-semibold text-primary">{player.name}</div>
                <div className="text-xs text-muted">{player.team}</div>
              </div>
              <div className="font-mono font-bold text-fpl-green">{points(player.predicted_pts)} xP</div>
              <StartLikelihood value={player.start_likelihood} />
            </button>
          ))}
        </div>
      </Panel>

      <div className="mt-6 rounded-xl border border-fpl-border border-l-fpl-green bg-fpl-card p-5 text-sm italic text-muted">
        How is this calculated? We multiply each player&apos;s predicted points by their probability of
        playing 60+ minutes. This gives you a realistic expected score, not just raw form.
      </div>
    </div>
  );
}
