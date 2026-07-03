"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip } from "recharts";

interface MiniSparklineProps {
  data: object[];
  dataKey: string;
  color?: string;
  height?: number;
  showTooltip?: boolean;
}

export function MiniSparkline({
  data,
  dataKey,
  color = "#00FF87",
  height = 46,
  showTooltip = false,
}: MiniSparklineProps) {
  if (!data.length) {
    return <div className="h-8 w-16 rounded bg-fpl-border/40" />;
  }

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          {showTooltip ? (
            <Tooltip contentStyle={{ background: "#240044", border: "1px solid #3D0066" }} />
          ) : null}
          <Line
            dataKey={dataKey}
            type="monotone"
            stroke={color}
            strokeWidth={2}
            dot={height > 50}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
