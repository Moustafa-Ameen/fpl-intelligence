"use client";

import { AlertTriangle, CalendarClock, CheckCircle2, ChevronDown, Repeat2, RotateCcw, Shield, Sparkles, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { Panel } from "@/components/Panel";
import { SectionHeader } from "@/components/SectionHeader";
import { getChipTips } from "@/lib/api";
import type { ChipTipsResponse } from "@/lib/types";

const chips = [
  {
    key: "wc1",
    name: "Wildcard 1",
    subtitle: "first half",
    icon: RotateCcw,
    tip: "Best for an early rebuild when fixtures or injuries break your squad.",
  },
  {
    key: "wc2",
    name: "Wildcard 2",
    subtitle: "second half",
    icon: RotateCcw,
    tip: "Usually strongest before a major double gameweek or late-season fixture swing.",
  },
  {
    key: "fh",
    name: "Free Hit",
    subtitle: "one Gameweek only",
    icon: Zap,
    tip: "Save for a blank gameweek when many clubs do not play.",
  },
  {
    key: "bb",
    name: "Bench Boost",
    subtitle: "bench scores too",
    icon: Shield,
    tip: "Only powerful when all 15 squad members are expected to play.",
  },
  {
    key: "tc",
    name: "Triple Captain",
    subtitle: "captain scores 3×",
    icon: Sparkles,
    tip: "Best on a premium double-gameweek captain with strong minutes.",
  },
];

const expandable = [
  {
    name: "Wildcard",
    best: "Early in the season (WC1) or before DGW (WC2).",
    paired: "Bench Boost planning, double gameweek fixture swings",
    body:
      "Use when your squad is fundamentally broken — injuries, price falls, or a fixture swing that affects 4+ players. Ideally time it before a run of easy fixtures or before a double gameweek to maximise the rebuilt squad's value.",
  },
  {
    name: "Free Hit",
    best: "The biggest blank gameweek of the season.",
    paired: "Blank gameweek planning",
    body:
      "Save for a blank gameweek when 6+ teams don't play. You temporarily build a squad from the playing teams only, then your original squad returns. It's wasted on a normal week.",
  },
  {
    name: "Bench Boost",
    best: "A double gameweek where your bench plays twice.",
    paired: "Wildcard setup, double gameweek fixture runs",
    body:
      "Only powerful if your bench has strong players with double fixtures. Check your bench's upcoming fixtures before using. A bench of squad fillers on a double GW will still disappoint.",
  },
  {
    name: "Triple Captain",
    best: "Double gameweek, premium player, easy opponents.",
    paired: "Premium captaincy picks, fixture ticker",
    body:
      "Triple your captain's points. Best used on a premium player with a double gameweek fixture. Haaland or Salah with two home games is the dream scenario.",
  },
];

const timeline = [
  "WC1 early season",
  "TC first major DGW",
  "BB next DGW",
  "FH biggest blank GW",
  "WC2 late season rebuild",
];

export default function ChipsPage() {
  const [openChip, setOpenChip] = useState("Wildcard");
  const [chipTips, setChipTips] = useState<ChipTipsResponse | null>(null);
  const teamConnected = Boolean(chipTips && chipTips.status !== "no_team");

  useEffect(() => {
    let active = true;
    const teamId = window.localStorage.getItem("fpl_team_id") || undefined;
    getChipTips(teamId)
      .then((response) => {
        if (active) setChipTips(response);
      })
      .catch(() => {
        if (active) {
          setChipTips({
            status: "unavailable",
            message: "AI chip tips are temporarily unavailable. Try again shortly.",
            alerts: [],
          });
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <SectionHeader
        title="When should I use my chips?"
        subtitle="A calm chip strategy guide for wildcard, free hit, bench boost, and triple captain decisions."
      />

      <Panel>
        <div className="mb-4 flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-fpl-gold/30 bg-fpl-gold/10 text-fpl-gold">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-fpl-gold">AI Tip</div>
            <h2 className="mt-1 text-[18px] font-semibold text-primary">Personalized chip timing</h2>
            <p className="mt-1 text-[13px] text-secondary">
              Signals compare this gameweek with your own recent squad baseline.
            </p>
          </div>
        </div>
        {!chipTips ? (
          <div className="rounded-lg border border-fpl-border bg-[#161616] p-4 text-sm text-secondary">
            Checking your squad projections...
          </div>
        ) : chipTips.status === "no_team" ? (
          <div className="rounded-lg border border-fpl-border bg-[#161616] p-4 text-sm text-secondary">
            Connect your FPL team to receive chip timing tips based on your own squad.
          </div>
        ) : chipTips.status === "unavailable" ? (
          <div className="flex items-start gap-3 rounded-lg border border-fpl-amber/30 bg-fpl-amber/10 p-4 text-sm text-secondary">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-fpl-amber" />
            <div>{chipTips.message}</div>
          </div>
        ) : chipTips.status === "insufficient_data" ? (
          <div className="rounded-lg border border-fpl-border bg-[#161616] p-4 text-sm text-secondary">
            {chipTips.message}
          </div>
        ) : chipTips.alerts.length ? (
          <div className="grid gap-3 lg:grid-cols-2">
            {chipTips.alerts.map((alert) => (
              <div key={alert.key} className="rounded-lg border border-fpl-gold/35 bg-fpl-gold/[0.05] p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-sm font-semibold text-fpl-gold">{alert.chip}</div>
                    <p className="mt-2 text-sm leading-6 text-primary">{alert.message}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <div className="font-mono text-lg font-semibold text-fpl-gold">
                      {alert.strength_percent.toFixed(0)}%
                    </div>
                    <div className="text-[10px] uppercase tracking-[0.12em] text-muted">relative signal</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-fpl-green/20 bg-fpl-green/[0.04] p-4 text-sm text-secondary">
            {chipTips.message}
          </div>
        )}
      </Panel>

      <Panel>
        <div className="mb-4">
          <h2 className="text-[18px] font-semibold text-primary">Your chip status</h2>
          <p className="mt-1 text-[13px] text-secondary">
            FPL chip availability is not exposed in this local data feed, so status is shown as unknown.
          </p>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {chips.map((chip) => {
            const Icon = chip.icon;
            return (
              <div key={chip.key} className="rounded-lg border border-fpl-border bg-[#161616] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-semibold text-primary">{chip.name}</div>
                    <div className="mt-1 text-xs text-muted">{chip.subtitle}</div>
                  </div>
                  <Icon className="h-5 w-5 text-fpl-green" />
                </div>
                <div className="mt-4 rounded-full border border-fpl-border bg-fpl-raised px-3 py-1 text-[11px] text-muted">
                  {teamConnected ? "Unknown — check FPL app" : "Unknown — connect your team to see chip availability"}
                </div>
                <p className="mt-3 text-xs leading-5 text-secondary">{chip.tip}</p>
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel>
        <div className="mb-4">
          <h2 className="text-[18px] font-semibold text-primary">When to use each chip</h2>
          <p className="mt-1 text-[13px] text-secondary">Click a chip to expand the expert timing note.</p>
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          {expandable.map((chip) => {
            const isOpen = chip.name === openChip;
            return (
              <button
                type="button"
                key={chip.name}
                onClick={() => setOpenChip(isOpen ? "" : chip.name)}
                className={`rounded-lg border p-4 text-left transition ${
                  isOpen ? "border-fpl-green bg-fpl-green/[0.06]" : "border-fpl-border bg-[#161616] hover:border-fpl-green/40"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="font-semibold text-primary">{chip.name}</div>
                  <ChevronDown className={`h-4 w-4 text-muted transition ${isOpen ? "rotate-180" : ""}`} />
                </div>
                {isOpen ? (
                  <div className="mt-4 space-y-3 text-sm leading-6 text-secondary">
                    <p>{chip.body}</p>
                    <div className="rounded-lg border border-fpl-border bg-black/20 p-3">
                      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-fpl-green">
                        <CalendarClock className="h-4 w-4" />
                        Best timing
                      </div>
                      <div className="mt-2 text-primary">{chip.best}</div>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted">
                      <Repeat2 className="h-4 w-4 text-fpl-gold" />
                      Commonly paired with: {chip.paired}
                    </div>
                  </div>
                ) : (
                  <p className="mt-2 text-sm text-muted">{chip.best}</p>
                )}
              </button>
            );
          })}
        </div>
      </Panel>

      <Panel>
        <div className="mb-5">
          <h2 className="text-[18px] font-semibold text-primary">Classic chip strategy timeline</h2>
          <p className="mt-1 text-[13px] text-secondary">A rough sequence many experienced FPL managers plan around.</p>
        </div>
        <div className="overflow-x-auto pb-2">
          <div className="flex min-w-[760px] items-center">
            {timeline.map((item, index) => (
              <div key={item} className="flex flex-1 items-center">
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-11 w-11 items-center justify-center rounded-full border border-fpl-green/40 bg-fpl-green/10 text-fpl-green">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                  <div className="max-w-[120px] text-center text-xs font-semibold text-primary">{item}</div>
                </div>
                {index < timeline.length - 1 ? <div className="mx-3 h-px flex-1 bg-fpl-border" /> : null}
              </div>
            ))}
          </div>
        </div>
        <div className="mt-5 rounded-lg border border-fpl-gold/30 bg-fpl-gold/[0.04] p-4 text-sm text-secondary">
          This is a rough guide. Fixtures and your squad situation should always drive the final call.
        </div>
      </Panel>
    </div>
  );
}
