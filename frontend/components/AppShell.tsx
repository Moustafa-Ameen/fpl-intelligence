"use client";

import { Menu } from "lucide-react";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { DrawerProvider } from "@/context/DrawerContext";
import { LiveMatchBar } from "./LiveMatchBar";
import { PlayerDrawer } from "./PlayerDrawer";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [progressState, setProgressState] = useState<"idle" | "loading" | "done">("idle");
  const pathname = usePathname();

  useEffect(() => {
    queueMicrotask(() => setProgressState("loading"));
    const doneTimer = window.setTimeout(() => setProgressState("done"), 650);
    const idleTimer = window.setTimeout(() => setProgressState("idle"), 900);
    return () => {
      window.clearTimeout(doneTimer);
      window.clearTimeout(idleTimer);
    };
  }, [pathname]);

  return (
    <DrawerProvider>
      {progressState !== "idle" ? (
        <div
          className={`fixed left-0 top-0 z-[100] h-0.5 bg-fpl-green ${
            progressState === "loading" ? "route-progress" : "route-progress-done"
          }`}
        />
      ) : null}
      <button
        type="button"
        onClick={() => setMobileOpen(true)}
        className="fixed left-3 top-3 z-40 rounded-lg border border-fpl-border bg-fpl-card p-2 text-fpl-green md:hidden"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />
      <main className="min-h-screen bg-fpl-dark px-4 py-4 md:ml-[72px] md:px-6 lg:ml-[220px] lg:px-9 lg:py-7">
        <div className="mx-auto max-w-[1400px]">
          <LiveMatchBar />
          {children}
        </div>
      </main>
      <PlayerDrawer />
    </DrawerProvider>
  );
}
