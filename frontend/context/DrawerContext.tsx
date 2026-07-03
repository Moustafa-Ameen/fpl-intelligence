"use client";

import { createContext, useContext, useMemo, useState } from "react";

interface DrawerContextValue {
  playerName: string | null;
  openDrawer: (playerName: string) => void;
  closeDrawer: () => void;
}

const DrawerContext = createContext<DrawerContextValue | null>(null);

export function DrawerProvider({ children }: { children: React.ReactNode }) {
  const [playerName, setPlayerName] = useState<string | null>(null);
  const value = useMemo(
    () => ({
      playerName,
      openDrawer: setPlayerName,
      closeDrawer: () => setPlayerName(null),
    }),
    [playerName],
  );

  return <DrawerContext.Provider value={value}>{children}</DrawerContext.Provider>;
}

export function useDrawer() {
  const context = useContext(DrawerContext);
  if (!context) {
    throw new Error("useDrawer must be used inside DrawerProvider");
  }
  return context;
}
