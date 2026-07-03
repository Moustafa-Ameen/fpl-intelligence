interface FixtureChipProps {
  difficulty?: number;
  label?: string | number;
}

export function FixtureChip({ difficulty, label }: FixtureChipProps) {
  const level = difficulty ?? 3;
  const color =
    level <= 2
      ? "bg-fpl-green/15 text-fpl-green"
      : level === 3
        ? "bg-fpl-amber/15 text-fpl-amber"
        : "bg-fpl-red/15 text-fpl-red";

  return (
    <span
      className={`inline-flex h-6 w-7 items-center justify-center rounded-md font-mono text-[11px] font-bold ${color}`}
    >
      {label ?? level}
    </span>
  );
}
