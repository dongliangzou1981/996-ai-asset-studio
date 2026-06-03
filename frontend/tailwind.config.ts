import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        studio: {
          ink: "#0f172a",
          muted: "#64748b",
          line: "#e2e8f0",
          action: "#2563eb",
          success: "#16a34a",
          warning: "#d97706",
        },
      },
    },
  },
  plugins: [],
};

export default config;

