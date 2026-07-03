"use client";

import { useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/LoadingState";
import { Panel } from "@/components/Panel";
import { PlayerRow } from "@/components/PlayerRow";
import { SectionHeader } from "@/components/SectionHeader";
import { StartLikelihood } from "@/components/StartLikelihood";
import { useDrawer } from "@/context/DrawerContext";
import { getPlayers } from "@/lib/api";
import { points, positionCode } from "@/lib/format";
import type { Player } from "@/lib/types";

type SortKey = keyof Player;

const columns: { label: string; key: SortKey }[] = [
  { label: "Player", key: "name" },
  { label: "Team", key: "team" },
  { label: "Pos", key: "position" },
  { label: "Price", key: "price" },
  { label: "Total Pts", key: "total_points" },
  { label: "Pts/Game", key: "ppg" },
  { label: "Form", key: "form" },
  { label: "Start Likelihood", key: "start_likelihood" },
  { label: "Value", key: "value" },
  { label: "Captain Score", key: "captain_score" },
  { label: "Transfer Score", key: "transfer_score" },
];

export default function StatsPage() {
  const { openDrawer } = useDrawer();
  const [players, setPlayers] = useState<Player[]>([]);
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [listMode, setListMode] = useState<"all" | "watchlist">("all");
  const [view, setView] = useState<"table" | "card">("table");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [search, setSearch] = useState("");
  const [position, setPosition] = useState("All");
  const [sortKey, setSortKey] = useState<SortKey>("captain_score");
  const [ascending, setAscending] = useState(false);
  const [page, setPage] = useState(1);

  useEffect(() => {
    getPlayers({ limit: 1000 })
      .then(setPlayers)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
    queueMicrotask(() => {
      setWatchlist(JSON.parse(window.localStorage.getItem("watchlist") ?? "[]") as string[]);
    });
  }, []);

  const filtered = useMemo(() => {
    const searchTerm = search.trim().toLowerCase();
    return players
      .filter((player) => listMode === "all" || watchlist.includes(player.name))
      .filter((player) => position === "All" || player.position === position)
      .filter((player) => !searchTerm || player.name.toLowerCase().includes(searchTerm))
      .sort((a, b) => compareValues(a[sortKey], b[sortKey], ascending));
  }, [ascending, listMode, players, position, search, sortKey, watchlist]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / 25));
  const visible = filtered.slice((page - 1) * 25, page * 25);

  function sortBy(key: SortKey) {
    if (key === sortKey) {
      setAscending((value) => !value);
    } else {
      setSortKey(key);
      setAscending(false);
    }
    setPage(1);
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState />;
  if (!players.length) return <EmptyState />;

  return (
    <div>
      <SectionHeader title="All Players" />
      <Panel>
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex rounded-lg border border-fpl-border bg-fpl-dark p-1">
            <Toggle active={listMode === "all"} onClick={() => setListMode("all")}>
              All Players
            </Toggle>
            <Toggle active={listMode === "watchlist"} onClick={() => setListMode("watchlist")}>
              My Watchlist
            </Toggle>
          </div>
          <div className="flex rounded-lg border border-fpl-border bg-fpl-dark p-1">
            <Toggle active={view === "table"} onClick={() => setView("table")}>
              Table view
            </Toggle>
            <Toggle active={view === "card"} onClick={() => setView("card")}>
              Card view
            </Toggle>
          </div>
          <input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder="Search player"
            className="w-64 rounded-lg border border-fpl-border bg-fpl-dark px-3 py-2 text-sm text-primary outline-none focus:border-fpl-green"
          />
          <select
            value={position}
            onChange={(event) => {
              setPosition(event.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-fpl-border bg-fpl-dark px-3 py-2 text-sm text-primary outline-none focus:border-fpl-green"
          >
            <option>All</option>
            <option>Goalkeeper</option>
            <option>Defender</option>
            <option>Midfielder</option>
            <option>Forward</option>
          </select>
        </div>

        {view === "table" ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="text-xs uppercase text-muted">
                <tr>
                  {columns.map((column) => (
                    <th key={column.key} className="pb-3 pr-4">
                      <button type="button" onClick={() => sortBy(column.key)} className="hover:text-primary">
                        {column.label}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>{visible.map((player) => <PlayerRow key={player.name} player={player} />)}</tbody>
            </table>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {visible.map((player) => (
              <button
                type="button"
                key={player.name}
                onClick={() => openDrawer(player.name)}
                className="rounded-xl border border-fpl-border bg-fpl-dark/25 p-4 text-left hover:bg-fpl-purple/20"
              >
                <div className="flex items-center gap-4">
                  <img
                    src={`https://fantasy.premierleague.com/dist/img/shirts/standard/shirt_${player.team_code ?? 1}-66.png`}
                    alt={`${player.team} kit`}
                    className="h-14 w-14 object-contain"
                  />
                  <div className="min-w-0">
                    <div className="truncate font-semibold text-primary">{player.name}</div>
                    <div className="text-xs text-muted">
                      {player.team} · {positionCode(player.position)}
                    </div>
                  </div>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  <CardMetric label="xP" value={points(player.captain_score)} />
                  <CardMetric label="Price" value={`£${points(player.price)}`} />
                  <div>
                    <div className="text-[11px] text-muted">Start</div>
                    <div className="mt-1">
                      <StartLikelihood value={player.start_likelihood} />
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        <div className="mt-5 flex items-center justify-between text-sm text-muted">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page === 1}
              onClick={() => setPage((value) => Math.max(1, value - 1))}
              className="rounded-lg border border-fpl-border px-3 py-1 disabled:opacity-40"
            >
              Prev
            </button>
            <button
              type="button"
              disabled={page === totalPages}
              onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
              className="rounded-lg border border-fpl-border px-3 py-1 disabled:opacity-40"
            >
              Next
            </button>
          </div>
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
        active ? "bg-fpl-green text-fpl-dark" : "text-muted hover:text-primary"
      }`}
    >
      {children}
    </button>
  );
}

function CardMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] text-muted">{label}</div>
      <div className="mt-1 font-mono text-sm font-bold text-primary">{value}</div>
    </div>
  );
}

function compareValues(a: Player[SortKey], b: Player[SortKey], ascending: boolean): number {
  const result =
    typeof a === "number" && typeof b === "number"
      ? a - b
      : String(a).localeCompare(String(b));
  return ascending ? result : -result;
}
