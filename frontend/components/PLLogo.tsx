"use client";

import { useState } from "react";

const PL_LOGO_URLS = [
  "https://resources.premierleague.com/premierleague/photos/competitions/00000004/competition-logo.png",
  "https://fantasy.premierleague.com/static/media/pl-main-logo.png",
  "https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg",
];

export function PLLogo({ size = 40, className = "" }: { size?: number; className?: string }) {
  const [urlIndex, setUrlIndex] = useState(0);

  if (urlIndex >= PL_LOGO_URLS.length) return null;

  return (
    <img
      src={PL_LOGO_URLS[urlIndex]}
      alt="Premier League"
      width={size}
      height={size}
      className={className}
      style={{ objectFit: "contain", opacity: 0.85 }}
      onError={() => setUrlIndex((index) => index + 1)}
    />
  );
}

