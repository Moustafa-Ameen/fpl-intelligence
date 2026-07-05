import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0D0D0D",
        card: "#161616",
        raised: "#1F1F1F",
        "border-muted": "#2A2A2A",
        primary: "#FFFFFF",
        secondary: "#A0A0A0",
        muted: "#606060",
        cyan: "#00FF87",
        up: "#00FF87",
        down: "#FF4444",
        amber: "#FFA500",
        "fpl-dark": "#0D0D0D",
        "fpl-card": "#161616",
        "fpl-raised": "#1F1F1F",
        "fpl-border": "#2A2A2A",
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
