"use client";

import { ArrowRight, Crown, Info, Repeat2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/LoadingState";
import { Panel } from "@/components/Panel";
import { SectionHeader } from "@/components/SectionHeader";
import { StartLikelihood } from "@/components/StartLikelihood";
import { useDrawer } from "@/context/DrawerContext";
import { getCaptaincyPredictions, getCurrentGameweek, getSquad } from "@/lib/api";
import { kitUrl, points, positionCode } from "@/lib/format";
import type { CaptainPick, SquadPlayer } from "@/lib/types";

export default function CaptainPage() {
  const { openDrawer } = useDrawer();
  const [picks, setPicks] = useState<CaptainPick[]>([]);
  const [squad, setSquad] = useState<SquadPlayer[]>([]);
  const [teamConnected, setTeamConnected] = useState(false);
  const [showMethod, setShowMethod] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const teamId = window.localStorage.getItem("fpl_team_id");
    queueMicrotask(() => setTeamConnected(Boolean(teamId)));

    Promise.all([
      getCaptaincyPredictions(),
      teamId
        ? getCurrentGameweek()
            .then((gw) => getSquad(teamId, gw.current_gw ?? 1))
            .catch(() => [])
        : Promise.resolve([]),
    ])
      .then(([predictionRows, squadRows]) => {
        setPicks(predictionRows);
        setSquad(squadRows);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const squadNames = useMemo(() => new Set(squad.map((player) => player.name.toLowerCase())), [squad]);
  const squadCaptainRows = useMemo(
    () =>
      squad
        .map((player) => {
          const prediction = picks.find((pick) => pick.name.toLowerCase() === player.name.toLowerCase());
          return toCaptainPick(player, prediction);
        })
        .sort((a, b) => score(b) - score(a)),
    [picks, squad],
  );
  const rankingRows = teamConnected && squadCaptainRows.length ? squadCaptainRows : picks;

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;
  if (!picks.length) return <EmptyState />;

  const globalTop = picks[0];
  const heroPick = rankingRows[0] ?? globalTop;
  const viceCaptain = rankingRows.find((player) => player.name !== heroPick.name);
  const globalTopNotOwned = teamConnected && globalTop && !squadNames.has(globalTop.name.toLowerCase());

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Who should I captain this week?"
        subtitle="A squad-aware captaincy view using predicted points and start likelihood."
      />

      <button
        type="button"
        onClick={() => openDrawer(heroPick.name)}
        className="fpl-card-shadow w-full rounded-lg border border-fpl-border border-l-4 border-l-fpl-gold bg-[linear-gradient(135deg,#0d1a0d_0%,#161616_100%)] p-6 text-left shadow-[-4px_0_20px_rgba(255,215,0,0.2)]"
      >
        <div className="grid gap-5 md:grid-cols-[96px_minmax(0,1fr)_auto] md:items-center">
          <img
            src={kitUrl(heroPick.team_code)}
            alt={`${heroPick.team} kit`}
            className="h-20 w-20 object-contain"
          />
          <div className="min-w-0">
            <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-fpl-gold">
              {teamConnected ? "Your captain pick this week" : "Top captain pick this week"}
            </div>
            <h2 className="mt-2 truncate text-[28px] font-bold leading-tight text-primary">{heroPick.name}</h2>
            <div className="mt-1 text-sm text-secondary">
              {heroPick.team} · {positionCode(heroPick.position)}
            </div>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-secondary">
              {heroPick.reasoning ?? "Best blend of predicted points and likelihood of starting."}
            </p>
            {viceCaptain ? (
              <p className="mt-3 text-[13px] text-muted">or consider {viceCaptain.name} as VC</p>
            ) : null}
          </div>
          <div className="text-left md:text-right">
            <div className="font-mono text-[48px] font-bold leading-none text-fpl-gold">
              {points(score(heroPick))}
            </div>
            <div className="mt-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted">
              Adjusted score
            </div>
            <div className="mt-4 inline-flex rounded-full bg-fpl-green/15 px-3 py-1">
              <StartLikelihood value={heroPick.start_likelihood} />
            </div>
          </div>
        </div>
      </button>

      {globalTopNotOwned ? (
        <div className="flex items-center gap-3 rounded-lg border border-fpl-gold/20 bg-fpl-card/80 px-4 py-3 text-sm text-secondary">
          <Repeat2 className="h-4 w-4 shrink-0 text-fpl-gold" />
          <span>
            {globalTop.name} is the top predicted captain this week but isn&apos;t in your squad.
            Consider transferring him in.
          </span>
        </div>
      ) : null}

      {!teamConnected ? (
        <div className="rounded-lg border border-fpl-border bg-fpl-card/80 px-4 py-3 text-sm text-muted">
          Connect your team for a personalised pick.
        </div>
      ) : null}

      <Panel title="Full captain ranking">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-fpl-card text-xs uppercase text-muted">
              <tr>
                <th className="pb-3 pr-3">Rank</th>
                <th className="pb-3 pr-3">Kit</th>
                <th className="pb-3 pr-3">Player</th>
                <th className="pb-3 pr-3">Team</th>
                <th className="pb-3 pr-3 text-right">Predicted Pts</th>
                <th className="pb-3 pr-3 text-right">Start %</th>
                <th className="pb-3 text-right">Score</th>
              </tr>
            </thead>
            <tbody>
              {rankingRows.map((player, index) => (
                <tr
                  key={`${player.name}-${index}`}
                  className={`cursor-pointer border-b border-fpl-border transition hover:bg-fpl-green/5 ${
                    index === 0
                      ? "border-l-4 border-l-fpl-gold bg-fpl-gold/[0.04]"
                      : index % 2 === 0
                        ? "bg-[#161616]"
                        : "bg-[#181818]"
                  }`}
                  onClick={() => openDrawer(player.name)}
                >
                  <td className="py-3 pr-3 pl-3 font-mono text-muted">
                    {index === 0 ? <Crown className="h-4 w-4 text-fpl-gold" /> : index + 1}
                  </td>
                  <td className="py-3 pr-3">
                    <img
                      src={kitUrl(player.team_code)}
                      alt={`${player.team} kit`}
                      className="h-10 w-10 object-contain"
                    />
                  </td>
                  <td className="py-3 pr-3 font-semibold text-primary">{player.name}</td>
                  <td className="py-3 pr-3 text-muted">{player.team}</td>
                  <td className="py-3 pr-3 text-right font-mono text-primary">{points(player.predicted_pts)}</td>
                  <td className="py-3 pr-3 text-right">
                    <StartLikelihood value={player.start_likelihood} />
                  </td>
                  <td className="py-3 text-right font-mono font-bold text-fpl-green">{points(score(player))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel>
        <button
          type="button"
          onClick={() => setShowMethod((value) => !value)}
          className="flex w-full items-center justify-between gap-3 text-left"
        >
          <span className="flex items-center gap-2 text-sm font-semibold text-primary">
            <Info className="h-4 w-4 text-fpl-gold" />
            How is captaincy score calculated?
          </span>
          <span className="text-xs text-muted">{showMethod ? "Hide" : "Show"}</span>
        </button>

        {showMethod ? (
          <div className="mt-5">
            <div className="grid gap-3 md:grid-cols-[1fr_32px_1fr_32px_1fr] md:items-center">
              <MethodStep label="Predicted points" value="8.4 pts" />
              <ArrowRight className="mx-auto hidden h-5 w-5 text-muted md:block" />
              <MethodStep label="Start likelihood" value="86%" />
              <ArrowRight className="mx-auto hidden h-5 w-5 text-muted md:block" />
              <MethodStep label="Adjusted score" value="7.2" accent />
            </div>
            <p className="mt-4 text-sm leading-6 text-secondary">
              Captain scores double points. Triple Captain scores triple, so use your TC chip on a
              double gameweek player when the fixture quality and minutes outlook are strong.
            </p>
          </div>
        ) : null}
      </Panel>
    </div>
  );
}

function toCaptainPick(player: SquadPlayer, prediction?: CaptainPick): CaptainPick {
  return {
    name: player.name,
    team: prediction?.team ?? player.team,
    position: prediction?.position ?? player.position,
    price: prediction?.price ?? player.price ?? undefined,
    start_likelihood: prediction?.start_likelihood ?? player.start_likelihood ?? 0,
    captain_score: prediction?.captain_score ?? player.predicted_pts ?? 0,
    predicted_pts: prediction?.predicted_pts ?? player.predicted_pts ?? 0,
    adjusted_pts: prediction?.adjusted_pts ?? prediction?.captain_score ?? player.predicted_pts ?? 0,
    team_code: prediction?.team_code ?? player.team_code,
    reasoning: prediction?.reasoning ?? "Best captain option from your connected squad.",
  };
}

function score(player: CaptainPick): number {
  return player.adjusted_pts ?? player.captain_score ?? player.predicted_pts ?? 0;
}

function MethodStep({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-lg border border-fpl-border bg-fpl-raised p-4 text-center">
      <div className="text-[11px] uppercase tracking-[0.12em] text-muted">{label}</div>
      <div className={`mt-2 font-mono text-xl font-bold ${accent ? "text-fpl-green" : "text-primary"}`}>
        {value}
      </div>
    </div>
  );
}

