import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: ReactNode;
  subLabel?: string;
}

export function StatCard({ label, value, subLabel }: StatCardProps) {
  return (
    <div className="fpl-card-shadow fpl-stat-card min-h-[118px] rounded-lg border border-fpl-border bg-fpl-card/95 p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted">{label}</div>
        <span className="h-2 w-2 rounded-full bg-fpl-green shadow-[0_0_14px_rgba(0,255,135,0.65)]" />
      </div>
      <div className="mt-4 font-mono text-[24px] font-bold leading-tight text-primary">{value}</div>
      {subLabel ? <div className="mt-2 text-[12px] text-secondary">{subLabel}</div> : null}
    </div>
  );
}
