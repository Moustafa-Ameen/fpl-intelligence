interface SectionHeaderProps {
  title: string;
  subtitle?: string;
}

export function SectionHeader({ title, subtitle }: SectionHeaderProps) {
  return (
    <div className="mb-5">
      <h1 className="text-[20px] font-semibold text-primary">{title}</h1>
      {subtitle ? <p className="mt-1 text-[13px] text-secondary">{subtitle}</p> : null}
    </div>
  );
}
