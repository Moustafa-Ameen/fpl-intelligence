import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: ReactNode;
  subLabel?: string;
}

export function StatCard({ label, value, subLabel }: StatCardProps) {
  return (
    <div className="min-h-[120px] rounded-xl border border-fpl-border bg-fpl-card p-5">
      <div className="text-[11px] font-semibold uppercase tracking-[0.12em] text-muted">
        {label}
      </div>
      <div className="mt-4 font-mono text-[28px] font-bold leading-tight text-primary">{value}</div>
      {subLabel ? <div className="mt-1 text-xs text-muted">{subLabel}</div> : null}
    </div>
  );
}
