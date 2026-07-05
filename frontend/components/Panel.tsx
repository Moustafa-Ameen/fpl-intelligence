import type { ReactNode } from "react";

interface PanelProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, children, className = "" }: PanelProps) {
  return (
    <section className={`fpl-card-shadow rounded-[10px] border border-fpl-border bg-fpl-card p-5 ${className}`}>
      {title ? <h2 className="mb-4 text-[18px] font-semibold text-primary">{title}</h2> : null}
      {children}
    </section>
  );
}
