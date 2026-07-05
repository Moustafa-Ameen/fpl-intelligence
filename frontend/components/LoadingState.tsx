export function LoadingState() {
  return (
    <div className="space-y-4">
      <div className="h-24 animate-pulse rounded-[10px] border border-border-muted bg-card" />
      <div className="h-64 animate-pulse rounded-[10px] border border-border-muted bg-card" />
    </div>
  );
}

export function ErrorState() {
  return (
    <div className="rounded-[10px] border border-border-muted bg-card p-5 text-sm text-muted">
      Could not load data. Make sure the FPL Intelligence API is running on port 8000.
    </div>
  );
}

export function EmptyState() {
  return (
    <div className="rounded-[10px] border border-border-muted bg-card p-5 text-sm text-muted">
      No data available yet.
    </div>
  );
}
