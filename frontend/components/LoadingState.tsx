export function LoadingState() {
  return <CardGridSkeleton />;
}

export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-4">
      <div className="skeleton h-16 rounded-[10px] border border-fpl-border bg-fpl-card" />
      <div className="rounded-[10px] border border-fpl-border bg-fpl-card p-4">
        <div className="mb-4 grid grid-cols-[1.2fr_0.7fr_0.7fr_0.7fr] gap-4">
          {[0, 1, 2, 3].map((index) => (
            <div key={index} className="skeleton h-4" />
          ))}
        </div>
        <div className="space-y-3">
          {Array.from({ length: rows }).map((_, index) => (
            <div key={index} className="grid grid-cols-[1.2fr_0.7fr_0.7fr_0.7fr] gap-4">
              <div className="skeleton h-9" />
              <div className="skeleton h-9" />
              <div className="skeleton h-9" />
              <div className="skeleton h-9" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function PitchSkeleton() {
  const rows = [1, 4, 4, 2];
  return (
    <div className="space-y-4">
      <div className="skeleton h-14 rounded-[10px] border border-fpl-border bg-fpl-card" />
      <div className="rounded-[10px] border border-fpl-border bg-[linear-gradient(180deg,#0d5c2e_0%,#0a4a25_50%,#0d5c2e_100%)] p-6">
        <div className="space-y-7">
          {rows.map((count, rowIndex) => (
            <div key={rowIndex} className="flex justify-center gap-5">
              {Array.from({ length: count }).map((_, index) => (
                <div key={index} className="flex w-[92px] flex-col items-center gap-2">
                  <div className="skeleton h-14 w-16" />
                  <div className="skeleton h-3 w-20" />
                  <div className="skeleton h-3 w-12" />
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-4 gap-3 rounded-[10px] border border-fpl-border bg-fpl-card p-4">
        {[0, 1, 2, 3].map((index) => (
          <div key={index} className="skeleton h-12" />
        ))}
      </div>
    </div>
  );
}

export function CardGridSkeleton({ cards = 6 }: { cards?: number }) {
  return (
    <div className="space-y-4">
      <div className="skeleton h-20 rounded-[10px] border border-fpl-border bg-fpl-card" />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: cards }).map((_, index) => (
          <div key={index} className="rounded-[10px] border border-fpl-border bg-fpl-card p-4">
            <div className="skeleton h-5 w-2/3" />
            <div className="skeleton mt-3 h-4 w-full" />
            <div className="skeleton mt-2 h-4 w-4/5" />
            <div className="mt-5 grid grid-cols-3 gap-2">
              <div className="skeleton h-12" />
              <div className="skeleton h-12" />
              <div className="skeleton h-12" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function HeroSkeleton() {
  return (
    <div className="space-y-4">
      <div className="skeleton h-14 rounded-[10px] border border-fpl-border bg-fpl-card" />
      <div className="rounded-[10px] border border-fpl-border bg-fpl-card p-6">
        <div className="grid gap-5 md:grid-cols-[96px_minmax(0,1fr)_160px] md:items-center">
          <div className="skeleton h-20 w-20" />
          <div>
            <div className="skeleton h-4 w-40" />
            <div className="skeleton mt-4 h-9 w-72 max-w-full" />
            <div className="skeleton mt-3 h-4 w-44" />
            <div className="skeleton mt-5 h-4 w-full" />
            <div className="skeleton mt-2 h-4 w-3/4" />
          </div>
          <div className="space-y-3">
            <div className="skeleton h-14" />
            <div className="skeleton h-6" />
          </div>
        </div>
      </div>
      <TableSkeleton rows={5} />
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
