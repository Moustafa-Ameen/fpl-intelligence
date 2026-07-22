"use client";

import { Menu } from "lucide-react";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { DrawerProvider } from "@/context/DrawerContext";
import { LiveMatchBar } from "./LiveMatchBar";
import { LogoLoader } from "./LogoLoader";
import { PlayerDrawer } from "./PlayerDrawer";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [progressState, setProgressState] = useState<"idle" | "loading" | "done">("loading");
  const pathname = usePathname();

  useEffect(() => {
    queueMicrotask(() => setProgressState("loading"));
    const doneTimer = window.setTimeout(() => setProgressState("done"), 5000);
    const idleTimer = window.setTimeout(() => setProgressState("idle"), 5600);
    return () => {
      window.clearTimeout(doneTimer);
      window.clearTimeout(idleTimer);
    };
  }, [pathname]);

  return (
    <DrawerProvider>
      {progressState !== "idle" ? <LogoLoader complete={progressState === "done"} /> : null}
      <button
        type="button"
        onClick={() => setMobileOpen(true)}
        className="fixed left-3 top-3 z-40 rounded-lg border border-fpl-border bg-fpl-card p-2 text-fpl-green shadow-lg md:hidden"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />
      <main className="decision-grid min-h-screen px-4 pb-4 pt-16 md:ml-[76px] md:px-6 md:py-4 lg:ml-[244px] lg:px-9 lg:py-7">
        <div className="mx-auto max-w-[1400px]">
          <LiveMatchBar />
          {children}
        </div>
      </main>
      <PlayerDrawer />
    </DrawerProvider>
  );
}
