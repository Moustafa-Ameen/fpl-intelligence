import type { ReactNode } from "react";

interface PanelProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, children, className = "" }: PanelProps) {
  return (
    <section className={`rounded-xl border border-fpl-border bg-fpl-card p-5 ${className}`}>
      {title ? <h2 className="mb-4 text-xl font-semibold text-primary">{title}</h2> : null}
      {children}
    </section>
  );
}
