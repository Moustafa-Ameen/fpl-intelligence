"use client";

import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getCurrentGameweek, getFixtures } from "@/lib/api";
import type { Fixture } from "@/lib/types";

export function LiveMatchBar() {
  const [hidden, setHidden] = useState(false);
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [gameweek, setGameweek] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    queueMicrotask(() => {
      const explicit = window.localStorage.getItem("show_match_bar");
      const legacyHidden = window.localStorage.getItem("hide_match_bar") === "true";
      setHidden(explicit === "false" || legacyHidden);
    });
    Promise.all([getCurrentGameweek(), getFixtures()])
      .then(([gw, rows]) => {
        setGameweek(gw.current_gw);
        setFixtures(rows);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const live = fixtures.filter((fixture) => fixture.started && !fixture.finished);
  const nextFixture = useMemo(
    () =>
      fixtures
        .filter((fixture) => fixture.kickoff_time)
        .sort(
          (a, b) =>
            new Date(a.kickoff_time ?? "").getTime() -
            new Date(b.kickoff_time ?? "").getTime(),
        )[0],
    [fixtures],
  );

  function hide() {
    window.localStorage.setItem("show_match_bar", "false");
    window.localStorage.removeItem("hide_match_bar");
    setHidden(true);
  }

  if (hidden) {
    return (
      <button
        type="button"
        onClick={() => {
          window.localStorage.setItem("show_match_bar", "true");
          window.localStorage.removeItem("hide_match_bar");
          setHidden(false);
        }}
        className="mb-3 text-xs font-semibold text-fpl-green hover:text-primary"
      >
        Show fixture bar
      </button>
    );
  }

  return (
    <div className="fpl-card-shadow mb-6 flex h-12 items-center justify-between rounded-[10px] border border-fpl-border bg-fpl-card px-4">
      <div className="min-w-0 text-sm">
        {live.length ? (
          <div className="flex items-center gap-3">
            <span className="font-bold text-fpl-green">LIVE</span>
            <div className="truncate text-primary">
              {live
                .map(
                  (fixture) =>
                    `${fixture.team_h_short ?? fixture.team_h} ${fixture.team_h_score ?? ""}-${fixture.team_a_score ?? ""} ${fixture.team_a_short ?? fixture.team_a} (${fixture.minutes ?? "Live"}')`,
                )
                .join(" - ")}
            </div>
          </div>
        ) : nextFixture ? (
          <span className="truncate text-secondary">
            <span className="font-semibold text-primary">Next:</span>{" "}
            {nextFixture.team_h_name ?? `Team ${nextFixture.team_h}`} vs{" "}
            {nextFixture.team_a_name ?? `Team ${nextFixture.team_a}`} -{" "}
            {formatKickoff(nextFixture.kickoff_time)} -{" "}
            <span className="font-mono text-fpl-green">
              Starts in {formatCountdown(nextFixture.kickoff_time, now)}
            </span>
          </span>
        ) : (
          <span className="text-muted">Gameweek {gameweek ?? "-"} - Fixtures pending</span>
        )}
      </div>
      <button type="button" onClick={hide} className="rounded p-1 text-muted hover:text-primary">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

function formatKickoff(value?: string | null): string {
  if (!value) return "Date TBD";
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(new Date(value));
}

function formatCountdown(value: string | null | undefined, now: number): string {
  if (!value) return "TBD";
  const diff = Math.max(0, new Date(value).getTime() - now);
  const minutes = Math.floor(diff / 60000);
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const mins = minutes % 60;
  return `${days}d ${hours}h ${mins}m`;
}
