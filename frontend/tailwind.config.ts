import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#1A0033",
        card: "#240044",
        "border-muted": "#3D0066",
        primary: "#F8FAFC",
        muted: "#B388CC",
        cyan: "#00FF87",
        up: "#00FF87",
        down: "#FF4444",
        amber: "#FFA500",
        "fpl-dark": "#1A0033",
        "fpl-card": "#240044",
        "fpl-border": "#3D0066",
        "fpl-green": "#00FF87",
        "fpl-gold": "#FFD700",
        "fpl-purple": "#7B2FBE",
        "fpl-red": "#FF4444",
        "fpl-amber": "#FFA500",
      },
    },
  },
  plugins: [],
};

export default config;
