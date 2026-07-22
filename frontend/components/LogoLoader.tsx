"use client";

import { useEffect, useRef, useState } from "react";

const clamp = (value: number, minimum = 0, maximum = 1) =>
  Math.min(maximum, Math.max(minimum, value));

const drawOffset = (progress: number, start: number, end: number) =>
  1 - clamp((progress - start) / (end - start));

export function LogoLoader({ complete = false }: { complete?: boolean }) {
  const progressRef = useRef(0);
  const [progress, setProgress] = useState(0);
  const displayedProgress = complete ? 100 : progress;

  useEffect(() => {
    let frame = 0;
    const startingProgress = progressRef.current;
    const targetProgress = complete ? 100 : 94;
    const duration = complete ? 320 : 5000;
    const startedAt = performance.now();

    const tick = (now: number) => {
      const elapsed = clamp((now - startedAt) / duration);
      const nextProgress = Math.round(
        startingProgress + (targetProgress - startingProgress) * elapsed,
      );

      progressRef.current = nextProgress;
      setProgress(nextProgress);

      if (elapsed < 1) {
        frame = window.requestAnimationFrame(tick);
      }
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [complete]);

  const pathStyle = (start: number, end: number) => ({
    strokeDasharray: 1,
    strokeDashoffset: drawOffset(displayedProgress, start, end),
    transition: "stroke-dashoffset 70ms linear",
  });

  const detailOpacity = (start: number, end: number) =>
    clamp((displayedProgress - start) / (end - start));

  const message = complete
    ? "READY"
    : displayedProgress < 20
      ? "CONNECTING TO FPL DATA"
      : displayedProgress < 42
        ? "READING PLAYER SIGNALS"
        : displayedProgress < 64
          ? "CALCULATING FIXTURE FORM"
          : displayedProgress < 84
            ? "BUILDING DECISION MODEL"
            : "FINALISING RECOMMENDATIONS";

  return (
    <div
      data-testid="logo-loader"
      className="fixed inset-0 z-[110] flex flex-col items-center justify-center bg-[#0D0D0D]"
      role="status"
      aria-live="polite"
      aria-label={`Loading FPL Intelligence: ${displayedProgress}%`}
    >
      <svg
        data-testid="logo-loader-mark"
        viewBox="0 0 240 240"
        width="230"
        height="230"
        aria-hidden="true"
        style={{
          overflow: "visible",
          filter: "drop-shadow(0 0 9px rgba(0, 255, 135, 0.5))",
        }}
      >
        <g
          fill="none"
          stroke="#76ff9b"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path
            pathLength="1"
            strokeWidth="3.2"
            style={pathStyle(0, 43)}
            d="M120 12 102 22 87 18 90 31 72 34 78 47 58 48 67 63 48 68 59 82 43 94 56 105 45 121 60 128 54 147 70 148 68 169 86 161 92 184 120 211 148 184 154 161 172 169 170 148 186 147 180 128 195 121 184 105 197 94 181 82 192 68 173 63 182 48 162 47 168 34 150 31 153 18 138 22Z"
          />

          <path
            pathLength="1"
            strokeWidth="2.5"
            style={pathStyle(12, 49)}
            d="M91 70 75 81 67 104 77 131 94 148 104 161"
          />
          <path
            pathLength="1"
            strokeWidth="2.5"
            style={pathStyle(12, 49)}
            d="M149 70 165 81 173 104 163 131 146 148 136 161"
          />
          <path
            pathLength="1"
            strokeWidth="2.3"
            style={pathStyle(23, 55)}
            d="M63 72 79 67 69 88 61 102 74 110 64 127 80 132 73 150 90 147 88 166 103 158"
          />
          <path
            pathLength="1"
            strokeWidth="2.3"
            style={pathStyle(23, 55)}
            d="M177 72 161 67 171 88 179 102 166 110 176 127 160 132 167 150 150 147 152 166 137 158"
          />

          <path
            pathLength="1"
            strokeWidth="2.4"
            style={pathStyle(30, 68)}
            d="M120 39 120 95"
          />
          <path
            pathLength="1"
            strokeWidth="2.2"
            style={pathStyle(34, 70)}
            d="M120 70 103 53 103 37"
          />
          <path
            pathLength="1"
            strokeWidth="2.2"
            style={pathStyle(34, 70)}
            d="M120 70 137 53 137 37"
          />
          <path
            pathLength="1"
            strokeWidth="2"
            style={pathStyle(39, 73)}
            d="M110 61 94 47 94 34"
          />
          <path
            pathLength="1"
            strokeWidth="2"
            style={pathStyle(39, 73)}
            d="M130 61 146 47 146 34"
          />
          <path
            pathLength="1"
            strokeWidth="1.8"
            style={pathStyle(44, 76)}
            d="M102 51 82 42 82 31"
          />
          <path
            pathLength="1"
            strokeWidth="1.8"
            style={pathStyle(44, 76)}
            d="M138 51 158 42 158 31"
          />

          <path
            pathLength="1"
            strokeWidth="2.7"
            style={pathStyle(50, 78)}
            d="M78 107 91 103 101 110"
          />
          <path
            pathLength="1"
            strokeWidth="2.7"
            style={pathStyle(50, 78)}
            d="M162 107 149 103 139 110"
          />
          <path
            pathLength="1"
            strokeWidth="2.6"
            style={pathStyle(56, 82)}
            d="M95 139 107 151 120 156 133 151 145 139"
          />
          <path
            pathLength="1"
            strokeWidth="2.8"
            style={pathStyle(60, 85)}
            d="M111 154 120 161 129 154"
          />
          <path
            pathLength="1"
            strokeWidth="2"
            style={pathStyle(64, 88)}
            d="M96 164 96 179 110 191"
          />
          <path
            pathLength="1"
            strokeWidth="2"
            style={pathStyle(64, 88)}
            d="M144 164 144 179 130 191"
          />
        </g>

        <g
          fill="none"
          stroke="#ffc857"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path pathLength="1" style={pathStyle(72, 93)} d="M59 111 70 119 70 137" />
          <path pathLength="1" style={pathStyle(72, 93)} d="M181 111 170 119 170 137" />
          <path pathLength="1" style={pathStyle(78, 94)} d="M76 151 87 158 87 174" />
          <path pathLength="1" style={pathStyle(78, 94)} d="M164 151 153 158 153 174" />
          <path pathLength="1" style={pathStyle(82, 95)} d="M120 178 120 200" />
        </g>

        <g fill="#76ff9b" style={{ opacity: detailOpacity(40, 76) }}>
          <circle cx="82" cy="31" r="2.6" />
          <circle cx="94" cy="34" r="2.6" />
          <circle cx="103" cy="37" r="2.6" />
          <circle cx="137" cy="37" r="2.6" />
          <circle cx="146" cy="34" r="2.6" />
          <circle cx="158" cy="31" r="2.6" />
        </g>
      </svg>

      <div
        aria-hidden="true"
        style={{
          width: 260,
          height: 3,
          marginTop: 8,
          overflow: "hidden",
          borderRadius: 999,
          background: "rgba(0, 255, 135, 0.12)",
        }}
      >
        <div
          style={{
            width: `${displayedProgress}%`,
            height: "100%",
            borderRadius: 999,
            background: "linear-gradient(90deg, #23e6c2, #00ff87)",
            boxShadow: "0 0 12px rgba(0, 255, 135, 0.75)",
            transition: "width 80ms linear",
          }}
        />
      </div>

      <div
        data-testid="logo-loader-percent"
        className="mt-5 font-mono text-5xl font-bold text-fpl-green"
      >
        {displayedProgress}%
      </div>
      <div className="mt-4 text-sm font-bold tracking-[0.2em] text-white">FPL INTELLIGENCE</div>
      <div
        data-testid="logo-loader-message"
        className="mt-3 h-4 text-xs tracking-[0.12em] text-fpl-green/70"
      >
        {message}
      </div>
    </div>
  );
}
