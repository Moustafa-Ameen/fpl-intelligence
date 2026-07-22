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
      src="/fpl-intelligence-lion.png"
      alt="FPL Intelligence"
      width={size}
      height={height ?? size}
      className={className}
      style={{ objectFit: "contain" }}
    />
  );
}
