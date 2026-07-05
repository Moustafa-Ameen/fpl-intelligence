import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: ReactNode;
  subLabel?: string;
}

export function StatCard({ label, value, subLabel }: StatCardProps) {
  return (
    <div className="fpl-card-shadow min-h-[120px] rounded-[10px] border border-fpl-border bg-fpl-card p-5">
      <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">
        {label}
      </div>
      <div className="mt-4 font-mono text-[26px] font-bold leading-tight text-primary">{value}</div>
      {subLabel ? <div className="mt-1 text-[13px] text-secondary">{subLabel}</div> : null}
    </div>
  );
}
