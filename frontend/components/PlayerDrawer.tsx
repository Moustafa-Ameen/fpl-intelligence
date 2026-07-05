"use client";

import Link from "next/link";
import { Star, X } from "lucide-react";
import { useEffect, useState } from "react";
import {
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  getCaptaincyPredictions,
  getFixtureTicker,
  getPlayerHistory,
  getPlayers,
} from "@/lib/api";
import { points, positionCode } from "@/lib/format";
import type { CaptainPick, FixtureTick, Player, PlayerHistoryPoint } from "@/lib/types";
import { useDrawer } from "@/context/DrawerContext";
import { FixtureChip } from "./FixtureChip";
import { StartLikelihood } from "./StartLikelihood";

export function PlayerDrawer() {
  const { playerName, closeDrawer } = useDrawer();
  const [player, setPlayer] = useState<Player | null>(null);
  const [prediction, setPrediction] = useState<CaptainPick | null>(null);
  const [history, setHistory] = useState<PlayerHistoryPoint[]>([]);
  const [fixtures, setFixtures] = useState<FixtureTick | null>(null);
  const [captainRank, setCaptainRank] = useState<number | null>(null);
  const [watching, setWatching] = useState(false);

  useEffect(() => {
    if (!playerName) return;
    let cancelled = false;
    Promise.all([
      getPlayers({ limit: 1000 }),
      getCaptaincyPredictions(),
      getPlayerHistory(playerName),
      getFixtureTicker(),
    ]).then(([players, predictions, historyRows, fixtureRows]) => {
      if (cancelled) return;
      const found =
        players.find((row) => row.name.toLowerCase() === playerName.toLowerCase()) ??
        players.find((row) => row.name.toLowerCase().includes(playerName.toLowerCase()));
      const rankIndex = predictions.findIndex((row) => row.name.toLowerCase() === playerName.toLowerCase());
      setPlayer(found ?? null);
      setPrediction(predictions[rankIndex] ?? null);
      setCaptainRank(rankIndex >= 0 ? rankIndex + 1 : null);
      setHistory(historyRows);
      setFixtures(found ? fixtureRows.find((row) => row.team === found.team) ?? null : null);
      const watchlist = JSON.parse(window.localStorage.getItem("watchlist") ?? "[]") as string[];
      setWatching(watchlist.includes(playerName));
    });
    return () => {
      cancelled = true;
    };
  }, [playerName]);

  if (!playerName) return null;

  const displayPlayer = (player ?? { name: playerName, team: "-", position: "-", price: 0 }) as Player;
  const teamCode = displayPlayer.team_code ?? 1;
  const adjusted = prediction?.adjusted_pts ?? prediction?.predicted_pts ?? displayPlayer.captain_score;
  const captainBadge =
    captainRank && captainRank <= 5
      ? "Top pick"
      : captainRank && captainRank <= 10
        ? "Captain contender"
        : null;

  function toggleWatchlist() {
    const watchlist = JSON.parse(window.localStorage.getItem("watchlist") ?? "[]") as string[];
    const next = watching
      ? watchlist.filter((item) => item !== playerName)
      : [...new Set([...watchlist, playerName])];
    window.localStorage.setItem("watchlist", JSON.stringify(next));
    setWatching(!watching);
  }

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        aria-label="Close player drawer"
        onClick={closeDrawer}
        className="absolute inset-0 bg-black/70"
      />
      <aside className="absolute right-0 top-0 h-full w-full max-w-[400px] translate-x-0 overflow-y-auto border-l border-fpl-border bg-fpl-card p-5 shadow-2xl transition-transform duration-200">
        <button
          type="button"
          onClick={closeDrawer}
          className="absolute right-4 top-4 rounded-lg p-2 text-muted hover:bg-fpl-raised hover:text-primary"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex gap-4 pr-8">
          <img
            src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${teamCode}-66.png`}
            width={80}
            height={80}
            alt={`${displayPlayer.team} kit`}
            className="h-20 w-20 object-contain"
          />
          <div>
            <h2 className="text-xl font-bold text-primary">{displayPlayer.name}</h2>
            <p className="mt-1 text-sm text-secondary">
              {displayPlayer.team} - {positionCode(displayPlayer.position)}
            </p>
            <p className="mt-2 font-mono text-lg font-bold text-primary">
              GBP {points(displayPlayer.price)}m
            </p>
            {captainBadge ? (
              <span className="mt-2 inline-flex rounded-full border border-fpl-green bg-fpl-green/10 px-2 py-1 text-xs font-bold text-fpl-green">
                {captainBadge}
              </span>
            ) : null}
          </div>
        </div>

        <div className="mt-6 grid grid-cols-4 gap-2">
          <MiniStat label="Predicted" value={points(adjusted)} />
          <MiniStat label="Start" value={<StartLikelihood value={displayPlayer.start_likelihood} />} />
          <MiniStat label="Form" value={points(displayPlayer.form)} />
          <MiniStat label="Points" value={points(displayPlayer.total_points, 0)} />
        </div>
        <p className="mt-2 text-[11px] italic text-muted">
          Predictions based on most recent available gameweek data
        </p>

        <Trend title="Price trend (last 10 GW)" data={history} dataKey="price" color="#00FF87" />
        <Trend title="Points per GW (last 10)" data={history} dataKey="total_points" color="#FFD700" />

        <div className="mt-6">
          <h3 className="mb-3 text-sm font-semibold text-primary">Upcoming fixtures</h3>
          <div className="flex flex-wrap gap-2">
            {(fixtures?.fixtures ?? []).slice(0, 3).map((fixture, index) => (
              <span
                key={`${fixture.gw}-${index}`}
                className="inline-flex items-center gap-1 rounded-lg border border-fpl-border px-2 py-1 text-xs text-secondary"
              >
                {fixture.opponent} {fixture.home ? "H" : "A"}
                <FixtureChip difficulty={fixture.difficulty} />
              </span>
            ))}
            {!fixtures?.fixtures.length ? <span className="text-sm text-muted">Fixtures pending</span> : null}
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3">
          <button type="button" onClick={toggleWatchlist} className="fpl-button px-3 py-2 text-sm">
            <Star className="mr-1 inline h-4 w-4" />
            {watching ? "Watching" : "Add to watchlist"}
          </button>
          <Link href="/captain" onClick={closeDrawer} className="fpl-secondary-button px-3 py-2 text-center text-sm">
            Captain this week
          </Link>
        </div>
      </aside>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-fpl-border bg-fpl-raised p-2">
      <div className="text-[11px] uppercase tracking-[0.08em] text-muted">{label}</div>
      <div className="mt-1 font-mono text-lg font-bold text-primary">{value}</div>
    </div>
  );
}

function Trend({
  title,
  data,
  dataKey,
  color,
}: {
  title: string;
  data: PlayerHistoryPoint[];
  dataKey: "price" | "total_points";
  color: string;
}) {
  const chartData = data.slice(-10);
  const values = chartData.map((row) => Number(row[dataKey])).filter((value) => Number.isFinite(value));
  const isPrice = dataKey === "price";
  const min = values.length ? Math.min(...values) - (isPrice ? 0.2 : 1) : 0;
  const max = values.length ? Math.max(...values) + (isPrice ? 0.2 : 1) : isPrice ? 1 : 10;
  const height = isPrice ? 200 : 180;
  const startValue = chartData[0]?.[dataKey];

  return (
    <div className="mt-6">
      <h3 className="mb-2 text-sm font-semibold text-primary">{title}</h3>
      <div className="rounded-lg border border-fpl-border bg-fpl-raised p-2" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
            <XAxis
              dataKey="gw"
              tick={{ fill: "#A0A0A0", fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: "#2A2A2A" }}
            />
            <YAxis
              domain={[min, max]}
              tick={{ fill: "#A0A0A0", fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: "#2A2A2A" }}
              tickFormatter={(value) => (isPrice ? `GBP ${Number(value).toFixed(1)}` : `${value}pts`)}
              width={48}
            />
            <Tooltip
              contentStyle={{ background: "#161616", border: "1px solid #2A2A2A", color: "#FFFFFF" }}
              labelFormatter={(value) => `GW ${value}`}
            />
            {startValue !== undefined ? (
              <ReferenceLine y={startValue} stroke="#A0A0A0" strokeDasharray="4 4" />
            ) : null}
            <Line
              dataKey={dataKey}
              type="monotone"
              stroke={color}
              strokeWidth={2}
              dot={{ r: 2, fill: color }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
