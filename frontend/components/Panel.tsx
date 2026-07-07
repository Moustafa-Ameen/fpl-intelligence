import type { ReactNode } from "react";

interface PanelProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, children, className = "" }: PanelProps) {
  return (
    <section className={`fpl-card-shadow rounded-lg border border-fpl-border bg-fpl-card/95 p-5 ${className}`}>
      {title ? (
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-[15px] font-semibold text-primary">{title}</h2>
          <span className="h-px min-w-8 flex-1 bg-gradient-to-r from-fpl-border to-transparent" />
        </div>
      ) : null}
      {children}
    </section>
  );
}
