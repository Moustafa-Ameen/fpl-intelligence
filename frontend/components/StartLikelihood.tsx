import { percent } from "@/lib/format";

interface StartLikelihoodProps {
  value: number | null | undefined;
}

export function StartLikelihood({ value }: StartLikelihoodProps) {
  const safe = value ?? 0;
  const color = safe >= 0.8 ? "bg-fpl-green" : safe >= 0.5 ? "bg-fpl-amber" : "bg-fpl-red";

  return (
    <span className="inline-flex items-center gap-2 text-xs text-muted">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {percent(value)}
    </span>
  );
}
