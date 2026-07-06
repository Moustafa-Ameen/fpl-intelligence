"use client";

import {
  BarChart3,
  CalendarDays,
  Crown,
  Edit2,
  Home,
  Shield,
  Settings,
  TrendingUp,
  Trophy,
  Users,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { getCurrentGameweek, getHealth } from "@/lib/api";
import { NavLink } from "./NavLink";
import { PLLogo } from "./PLLogo";

const navGroups = [
  {
    label: "Main",
    items: [
      { href: "/", label: "Overview", icon: Home },
      { href: "/squad", label: "My Squad", icon: Shield },
    ],
  },
  {
    label: "Decisions",
    items: [
      { href: "/captain", label: "Who to Captain", icon: Crown },
      { href: "/transfers", label: "Who to Sign", icon: TrendingUp },
      { href: "/fixtures", label: "Fixtures", icon: CalendarDays },
    ],
  },
  {
    label: "Insights",
    items: [
      { href: "/stats", label: "All Players", icon: Users },
      { href: "/proof", label: "Proof It Works", icon: BarChart3 },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export function Sidebar({
  mobileOpen,
  onCloseMobile,
}: {
  mobileOpen: boolean;
  onCloseMobile: () => void;
}) {
  const [gameweek, setGameweek] = useState<number | null>(null);
  const [teamId, setTeamId] = useState("");
  const [draftId, setDraftId] = useState("");
  const [apiOk, setApiOk] = useState(false);

  useEffect(() => {
    getCurrentGameweek()
      .then((data) => setGameweek(data.current_gw))
      .catch(() => setGameweek(null));
    getHealth()
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false));

    queueMicrotask(() => {
      const saved = window.localStorage.getItem("fpl_team_id") ?? "";
      setTeamId(saved);
      setDraftId(saved);
    });
  }, []);

  function saveTeamId() {
    const clean = draftId.trim();
    if (!clean) return;
    window.localStorage.setItem("fpl_team_id", clean);
    setTeamId(clean);
  }

  function editTeamId() {
    window.localStorage.removeItem("fpl_team_id");
    setTeamId("");
  }

  return (
    <>
      {mobileOpen ? (
        <button
          type="button"
          aria-label="Close menu"
          onClick={onCloseMobile}
          className="fixed inset-0 z-30 bg-black/70 md:hidden"
        />
      ) : null}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[220px] flex-col border-r border-[rgba(123,47,190,0.2)] bg-[#111111] transition-transform md:translate-x-0 md:w-[72px] lg:w-[220px] ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <button
          type="button"
          onClick={onCloseMobile}
          className="absolute right-3 top-3 rounded p-1 text-muted hover:text-primary md:hidden"
        >
          <X className="h-4 w-4" />
        </button>
        <div className="px-5 pt-6 md:px-3 lg:px-5">
          <div className="flex items-center gap-2 text-base font-bold text-primary">
            <Zap className="h-5 w-5 text-fpl-green" />
            <span className="md:hidden lg:inline">FPL Intelligence</span>
          </div>
          <div className="mt-2 text-xs text-secondary md:hidden lg:block">
            {gameweek ? `Gameweek ${gameweek}` : "Gameweek loading"}
          </div>
          <div className="mx-auto mt-2 mb-5 flex justify-center md:hidden lg:flex">
            <PLLogo size={44} />
          </div>
        </div>

        <nav className="mt-3 space-y-6">
          {navGroups.map((group) => (
            <div key={group.label}>
              <div className="mb-2 px-5 text-[10px] font-bold uppercase tracking-[0.08em] text-muted md:hidden lg:block">
                {group.label}
              </div>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <NavLink key={item.href} href={item.href} icon={item.icon} onNavigate={onCloseMobile}>
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="mt-auto border-t border-[#1F1F1F] p-4 md:px-2 lg:p-4">
          <div className="md:hidden lg:block">
            {teamId ? (
              <div>
                <div className="text-xs font-semibold text-fpl-green">Team #{teamId} connected</div>
                <button
                  type="button"
                  onClick={editTeamId}
                  className="mt-2 inline-flex items-center gap-1 text-xs text-muted hover:text-primary"
                >
                  <Edit2 className="h-3 w-3" />
                  edit
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <input
                  value={draftId}
                  onChange={(event) => setDraftId(event.target.value)}
                  placeholder="Enter FPL Team ID"
                  className="w-full rounded-lg border border-fpl-border bg-fpl-raised px-3 py-2 text-xs text-primary outline-none focus:border-fpl-green"
                />
                <button type="button" onClick={saveTeamId} className="fpl-button w-full px-3 py-2 text-xs">
                  Confirm
                </button>
              </div>
            )}
            <div className="mt-4 flex items-center gap-2 text-[11px] text-muted">
              <span className={`h-2 w-2 rounded-full ${apiOk ? "bg-fpl-green" : "bg-fpl-red"}`} />
              Data from FPL Official API
            </div>
          </div>
          <Trophy className="mx-auto hidden h-5 w-5 text-fpl-green md:block lg:hidden" />
        </div>
      </aside>
    </>
  );
}
