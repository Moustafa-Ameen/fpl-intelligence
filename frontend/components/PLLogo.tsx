export function PLLogo({
  size = 40,
  height,
  className = "",
}: {
  size?: number;
  height?: number;
  className?: string;
}) {
  return (
    <img
      src="/pl-lion.png"
      alt="Premier League"
      width={size}
      height={height ?? size}
      className={className}
      style={{ objectFit: "contain" }}
    />
  );
}
