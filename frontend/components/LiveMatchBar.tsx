"use client";

import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getFixtures } from "@/lib/api";
import type { Fixture } from "@/lib/types";
import { PLLogo } from "./PLLogo";

const TEAM_BADGE_CODES: Record<string, number> = {
  "Man Utd": 1,
  "Manchester United": 1,
  MUN: 1,
  Leeds: 2,
  LEE: 2,
  Arsenal: 3,
  ARS: 3,
  Newcastle: 4,
  NEW: 4,
  Spurs: 6,
  Tottenham: 6,
  TOT: 6,
  "Aston Villa": 7,
  AVL: 7,
  Chelsea: 8,
  CHE: 8,
  "Coventry City": 9,
  Coventry: 9,
  COV: 9,
  Everton: 11,
  EVE: 11,
  Liverpool: 14,
  LIV: 14,
  "Nott'm Forest": 17,
  "Nottingham Forest": 17,
  NFO: 17,
  "West Ham": 21,
  WHU: 21,
  "Crystal Palace": 31,
  CRY: 31,
  Brighton: 36,
  BHA: 36,
  Wolves: 39,
  WOL: 39,
  "Man City": 43,
  "Manchester City": 43,
  MCI: 43,
  Fulham: 54,
  FUL: 54,
  "Hull City": 88,
  Hull: 88,
  HUL: 88,
  "Ipswich Town": 40,
  Ipswich: 40,
  IPS: 40,
  Sunderland: 56,
  SUN: 56,
  Bournemouth: 91,
  BOU: 91,
  Brentford: 94,
  BRE: 94,
};

export function LiveMatchBar() {
  const [hidden, setHidden] = useState(false);
  const [fixtures, setFixtures] = useState<Fixture[]>([]);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    queueMicrotask(() => {
      const explicit = window.localStorage.getItem("show_match_bar");
      const legacyHidden = window.localStorage.getItem("hide_match_bar") === "true";
      setHidden(explicit === "false" || legacyHidden);
    });
    getFixtures()
      .then(setFixtures)
      .catch(() => setFixtures([]));
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const liveFixture = useMemo(
    () => fixtures.find((fixture) => fixture.started && !fixture.finished) ?? null,
    [fixtures],
  );
  const nextFixture = useMemo(
    () =>
      fixtures
        .filter((fixture) => {
          if (!fixture.kickoff_time || fixture.started || fixture.finished) return false;
          return new Date(fixture.kickoff_time).getTime() >= now - 60_000;
        })
        .sort(
          (a, b) =>
            new Date(a.kickoff_time ?? "").getTime() -
            new Date(b.kickoff_time ?? "").getTime(),
        )[0] ?? null,
    [fixtures, now],
  );
  const match = liveFixture ?? nextFixture;

  function hide() {
    window.localStorage.setItem("hide_match_bar", "true");
    window.localStorage.removeItem("show_match_bar");
    setHidden(true);
  }

  if (hidden || !match) return null;

  const isLive = Boolean(match.started && !match.finished);
  const homeName = teamName(match, "home");
  const awayName = teamName(match, "away");

  return (
    <div className="mb-6 flex h-12 items-center gap-4 border-b border-[rgba(123,47,190,0.2)] bg-[#161616] px-3">
      <div className="flex w-8 shrink-0 justify-center">
        <PLLogo size={24} />
      </div>

      <div className="flex min-w-0 flex-1 justify-center">
        <div className="grid min-w-0 max-w-full grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 rounded-full border border-[#2A2A2A] bg-[#1F1F1F] px-4 py-1.5">
          <div className="flex min-w-0 items-center justify-end gap-2">
            <TeamBadge fixture={match} side="home" />
            <span className="truncate text-[13px] font-medium text-primary">{homeName}</span>
          </div>
          {isLive ? (
            <div className="flex items-center gap-2 whitespace-nowrap text-sm font-bold text-primary">
              <span className="h-2 w-2 animate-pulse rounded-full bg-fpl-green" />
              {match.team_h_score ?? 0} - {match.team_a_score ?? 0}
            </div>
          ) : (
            <div className="whitespace-nowrap text-center text-xs text-muted">
              {formatKickoff(match.kickoff_time)}
            </div>
          )}
          <div className="flex min-w-0 items-center gap-2">
            <span className="truncate text-[13px] font-medium text-primary">{awayName}</span>
            <TeamBadge fixture={match} side="away" />
          </div>
        </div>
      </div>

      <div className="hidden min-w-[132px] justify-end text-right font-mono text-xs text-fpl-green sm:flex">
        {isLive ? (
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-fpl-green" />
            LIVE - {match.minutes ?? "now"}
            {match.minutes ? "'" : ""}
          </span>
        ) : (
          `Starts in ${formatCountdown(match.kickoff_time, now)}`
        )}
      </div>

      <button type="button" onClick={hide} className="rounded p-1 text-muted hover:text-primary" aria-label="Hide fixture bar">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

function TeamBadge({ fixture, side }: { fixture: Fixture; side: "home" | "away" }) {
  const [failed, setFailed] = useState(false);
  const code = teamBadgeCode(fixture, side);

  if (!code || failed) return <span className="h-5 w-5 shrink-0" />;

  return (
    <img
      src={`https://resources.premierleague.com/premierleague/badges/50/t${code}.png`}
      alt=""
      width={20}
      height={20}
      className="h-5 w-5 shrink-0 object-contain"
      onError={() => setFailed(true)}
    />
  );
}

function teamName(fixture: Fixture, side: "home" | "away"): string {
  return side === "home"
    ? fixture.team_h_short ?? fixture.team_h_name ?? `Team ${fixture.team_h}`
    : fixture.team_a_short ?? fixture.team_a_name ?? `Team ${fixture.team_a}`;
}

function teamBadgeCode(fixture: Fixture, side: "home" | "away"): number {
  const short = side === "home" ? fixture.team_h_short : fixture.team_a_short;
  const name = side === "home" ? fixture.team_h_name : fixture.team_a_name;
  const fallback = side === "home" ? fixture.team_h : fixture.team_a;
  return TEAM_BADGE_CODES[short ?? ""] ?? TEAM_BADGE_CODES[name ?? ""] ?? fallback;
}

function formatKickoff(value?: string | null): string {
  if (!value) return "Date TBD";
  const date = new Date(value);
  const day = new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
  }).format(date);
  const time = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
  return `${day} \u00b7 ${time}`;
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
